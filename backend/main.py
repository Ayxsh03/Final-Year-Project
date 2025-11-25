from fastapi import FastAPI, HTTPException, Query, Depends, Header, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

import os
import json
import ssl

import os
import json
import ssl
import aioodbc
import pyodbc
import certifi  # type: ignore
import cv2      # type: ignore
import numpy as np  # type: ignore
import msal  # type: ignore
import secrets
import hashlib
import hmac
from urllib.parse import urlparse, urlencode

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, timedelta, timezone

app = FastAPI(title="Person Detection API", version="1.0.0")

# ---- Session & Template Setup ------------------------------------------------
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", secrets.token_urlsafe(32))

# Template engine for login page - check multiple possible locations
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR")
if not TEMPLATES_DIR:
    possible_template_paths = [
        "backend/templates",  # Relative to CWD (works in /tmp on Azure)
        "templates",
        "/home/site/wwwroot/backend/templates"  # Absolute path (last resort)
    ]
    for path in possible_template_paths:
        if os.path.isdir(path):
            TEMPLATES_DIR = os.path.abspath(path)
            break
    if not TEMPLATES_DIR:
        TEMPLATES_DIR = "backend/templates"
        os.makedirs(TEMPLATES_DIR, exist_ok=True)

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ---- Static & image dirs -----------------------------------------------------
IMAGES_DIR = os.getenv("IMAGES_DIR", "/home/images")
os.makedirs(IMAGES_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# For Azure deployment, paths change. Check multiple possible locations.
STATIC_DIR = os.getenv("STATIC_DIR")
if not STATIC_DIR:
    # Try common deployment paths (relative first, then absolute)
    possible_paths = [
        "backend/static",  # Relative to CWD (works in /tmp on Azure)
        "static",
        "/home/site/wwwroot/backend/static"  # Absolute path (last resort)
    ]
    for path in possible_paths:
        if os.path.isdir(path):
            STATIC_DIR = os.path.abspath(path)  # Convert to absolute
            break
    if not STATIC_DIR:
        STATIC_DIR = "backend/static"
        os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
# Serve built asset files at /assets so module scripts resolve with correct MIME type
app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

# ---- CORS --------------------------------------------------------------------
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Config / Secrets --------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. postgresql://.../db?sslmode=require
API_KEY = os.getenv("API_KEY", "111-1111-1-11-1-11-1-1")

# Azure SSO Configuration
# ... (existing config)

# ---- Debug Endpoints (Temporary) ---------------------------------------------
@app.get("/api/v1/debug/drivers")
async def list_odbc_drivers():
    """List all installed ODBC drivers."""
    try:
        drivers = pyodbc.drivers()
        return {"drivers": drivers, "os": os.name}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/debug/test-db")
async def test_db_connection_debug():
    """Test database connection with current settings."""
    try:
        conn_str = _build_connection_string(DATABASE_URL or "")
        # Mask password for safety in response
        safe_conn_str = conn_str
        if "Pwd=" in safe_conn_str:
            import re
            safe_conn_str = re.sub(r"Pwd=([^;]+)", "Pwd=***", safe_conn_str)
        
        # Try connecting
        conn = await aioodbc.connect(dsn=conn_str)
        async with conn.cursor() as cur:
            await cur.execute("SELECT @@VERSION")
            row = await cur.fetchone()
            version = row[0]
        await conn.close()
        
        return {
            "status": "success", 
            "version": version, 
            "connection_string_used": safe_conn_str
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "detail": type(e).__name__
        }
TENANT_ID = os.getenv("AZURE_TENANT_ID", "").strip()
CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "").strip()
ALLOWED_DOMAIN = (os.getenv("ALLOWED_DOMAIN") or "").lower().strip()
REDIRECT_URI = os.getenv("REDIRECT_URI") or "http://localhost:8000/auth/callback"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}" if TENANT_ID else ""
OIDC_SCOPE = ["User.Read"]
APP_NAME = os.getenv("APP_NAME", "FpelAICCTV Person Detection")


# ---- DB Helper Classes -------------------------------------------------------
class DatabaseWrapper:
    """Wrapper to make aioodbc compatible with asyncpg-style queries."""
    def __init__(self, conn):
        self.conn = conn

    async def fetch(self, query, *args):
        async with self.conn.cursor() as cur:
            # Replace $n with ?
            import re
            query = re.sub(r'\$\d+', '?', query)
            await cur.execute(query, args)
            if cur.description:
                columns = [column[0] for column in cur.description]
                rows = await cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            return []

    async def fetchrow(self, query, *args):
        rows = await self.fetch(query, *args)
        return rows[0] if rows else None

    async def fetchval(self, query, *args):
        rows = await self.fetch(query, *args)
        if rows:
            return list(rows[0].values())[0]
        return None

    async def execute(self, query, *args):
        async with self.conn.cursor() as cur:
            import re
            query = re.sub(r'\$\d+', '?', query)
            await cur.execute(query, args)
            await self.conn.commit()
            
    async def close(self):
        await self.conn.close()


def _build_connection_string(url: str) -> str:
    """Build ODBC connection string from URL or env var."""
    # If it's already a connection string (contains ';'), return as is
    if ";" in url and "Driver=" in url:
        return url
        
    # If it's a postgres URL, we need to convert or fail. 
    # We assume the user provides a proper SQL Server connection string in DATABASE_URL.
    # Format: Driver={ODBC Driver 17 for SQL Server};Server=myServerAddress;Database=myDataBase;Uid=myUsername;Pwd=myPassword;
    return url


# ---- Auth helpers ------------------------------------------------------------
async def validate_api_key(x_api_key: Optional[str] = Header(default=None)):
    if x_api_key is None or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


async def get_current_user(request: Request):
    """Get current user from session or raise 401."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_optional_user(request: Request):
    """Get current user from session or return None."""
    return request.session.get("user")


def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hmac.compare_digest(hash_password(password), password_hash)


async def get_or_create_sso_profile(conn: DatabaseWrapper, email: str, full_name: str, azure_id: str = None) -> dict:
    """Get existing SSO profile or create new one in Supabase profiles table."""
    # Try to find existing profile by email or Azure ID
    profile = await conn.fetchrow(
        """
        SELECT id, email, full_name, role, auth_provider 
        FROM profiles 
        WHERE email = $1 OR (azure_id = $2 AND azure_id IS NOT NULL)
        """,
        email, azure_id
    )
    
    if profile:
        # Update last login and Azure ID if needed
        await conn.execute(
            """
            UPDATE profiles 
            SET last_login = SYSDATETIMEOFFSET(), 
                azure_id = COALESCE(azure_id, $1),
                auth_provider = CASE 
                    WHEN auth_provider = 'supabase' THEN auth_provider 
                    ELSE 'azure_sso' 
                END
            WHERE id = $2
            """,
            azure_id, profile["id"]
        )
        return dict(profile)
    
    # Create new profile for SSO user
    # SQL Server NEWID() is used in default, but here we might need to return it
    # We use OUTPUT inserted.* to get the created row
    
    # Note: If id is not auto-generated by default in your schema for some reason, 
    # you might need to generate it in python or use NEWID() in insert.
    # Assuming id has DEFAULT NEWID()
    
    rows = await conn.fetch(
        """
        INSERT INTO profiles (email, full_name, auth_provider, azure_id, last_login, created_at, updated_at)
        OUTPUT inserted.id, inserted.email, inserted.full_name, inserted.role, inserted.auth_provider
        VALUES ($1, $2, 'azure_sso', $3, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET())
        """,
        email, full_name, azure_id
    )
    
    if not rows:
        raise Exception("Failed to create profile")
        
    new_profile = rows[0]
    
    # Log user creation
    await conn.execute(
        """
        INSERT INTO activity_logs (user_id, action, email, message, created_at)
        VALUES ($1, $2, $3, $4, SYSDATETIMEOFFSET())
        """,
        new_profile["id"], "sso_profile_created", email, f"SSO profile created for {email}"
    )
    
    return dict(new_profile)



# ---- DB dependency -----------------------------------------------------------
async def get_db():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not configured")
    
    conn_str = _build_connection_string(DATABASE_URL)
    try:
        # Connect using aioodbc
        conn = await aioodbc.connect(dsn=conn_str)
        wrapper = DatabaseWrapper(conn)
        try:
            yield wrapper
        finally:
            await wrapper.close()
    except Exception as e:
        print(f"DB Connection Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---- Auth Middleware ---------------------------------------------------------
class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to protect routes requiring authentication."""
    
    async def dispatch(self, request: Request, call_next):
        # Public paths that don't require authentication
        open_paths = {"/login/sso", "/logout", "/auth/callback", "/health", "/auth"}
        path = request.url.path
        
        # Allow access to static files, images, favicon, and public paths
        if any([
            path in open_paths,
            path.startswith("/static/"),
            path.startswith("/assets/"),
            path.startswith("/images/"),
            path == "/favicon.ico"
        ]):
            return await call_next(request)
        
        # Check if user is authenticated for protected paths
        user = request.session.get("user")
        
        # Protect UI routes (redirect to /auth)
        if not path.startswith("/api/"):
            if not user:
                return RedirectResponse(url="/auth", status_code=302)
        
        # For API routes, continue (will be protected by validate_api_key or get_current_user)
        return await call_next(request)


# Add the auth middleware
app.add_middleware(AuthMiddleware)
# IMPORTANT: SessionMiddleware must wrap inside middlewares to populate request.session
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=86400)  # 24 hours


# ---- Models ------------------------------------------------------------------
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    auth_provider: str = "email"


class DetectionEvent(BaseModel):
    timestamp: Optional[datetime] = None  # let server default if missing
    person_id: int
    confidence: float
    camera_id: UUID
    camera_name: str
    image_path: Optional[str] = None
    alert_sent: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    bbox_x1: Optional[float] = None
    bbox_y1: Optional[float] = None
    bbox_x2: Optional[float] = None
    bbox_y2: Optional[float] = None


class CameraDevice(BaseModel):
    id: Optional[str] = None
    name: str
    rtsp_url: str
    status: str = "offline"
    location: Optional[str] = None
    last_heartbeat: Optional[datetime] = None


class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    location: Optional[str] = None


class DashboardStats(BaseModel):
    total_events: int
    total_cameras: int
    online_cameras: int
    offline_cameras: int
    active_cameras: int
    people_detected: int
    events_trend: float
    devices_trend: float
    people_trend: float


class PeopleCountDevice(BaseModel):
    camera_id: str
    camera_name: str
    location: Optional[str] = None
    count: int
    last_detection: Optional[datetime] = None
    image_path: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class PeopleCountResponse(BaseModel):
    today: int
    week: int
    month: int
    year: int
    all: int
    devices: List[PeopleCountDevice]


class AlertSettings(BaseModel):
    id: Optional[str] = None
    enabled: bool = True

    # Email
    notify_email: bool = False
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 465
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    email_to: Optional[str] = None

    # WhatsApp
    notify_whatsapp: bool = False
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_token: Optional[str] = None
    whatsapp_to: Optional[str] = None

    # Telegram
    notify_telegram: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Scheduling
    allowed_days: List[str] = Field(default_factory=lambda: [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ])
    start_time: Optional[str] = None  # HH:MM
    end_time: Optional[str] = None    # HH:MM
    timezone: str = "UTC"

    # Reports
    daily_report_enabled: bool = False
    weekly_report_enabled: bool = False
    monthly_report_enabled: bool = False

    # Misc
    notify_vip_email: bool = False
    notify_regular_email: bool = False
    notify_attendance_to_branch: bool = False
    google_places_api_key: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AlertSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None

    # Email
    notify_email: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    email_to: Optional[str] = None

    # WhatsApp
    notify_whatsapp: Optional[bool] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_token: Optional[str] = None
    whatsapp_to: Optional[str] = None

    # Telegram
    notify_telegram: Optional[bool] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Scheduling
    allowed_days: Optional[List[str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None

    # Reports
    daily_report_enabled: Optional[bool] = None
    weekly_report_enabled: Optional[bool] = None
    monthly_report_enabled: Optional[bool] = None

    # Misc
    notify_vip_email: Optional[bool] = None
    notify_regular_email: Optional[bool] = None
    notify_attendance_to_branch: Optional[bool] = None

    # Google Places
    google_places_api_key: Optional[str] = None


class TestAlertRequest(BaseModel):
    alert_type: str  # "email", "whatsapp", "telegram"
    settings: dict   # relevant settings


# ---- Routes: Stats & Listings ------------------------------------------------
@app.get("/api/v1/events/stats", response_model=DashboardStats)
async def get_dashboard_stats(conn: DatabaseWrapper = Depends(get_db)):
    """Get dashboard statistics."""
    try:
        # Use stored procedure if available, or raw queries
        # We'll use raw queries adapted for SQL Server
        
        stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM detection_events WHERE CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE)) as total_events,
                (SELECT COUNT(*) FROM camera_devices) as total_cameras,
                (SELECT COUNT(*) FROM camera_devices WHERE status = 'online') as online_cameras,
                (SELECT COUNT(*) FROM camera_devices WHERE status = 'offline') as offline_cameras,
                (SELECT COUNT(DISTINCT camera_id) FROM detection_events WHERE CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE)) as active_cameras,
                (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE)) as people_detected
        """
        stats = await conn.fetchrow(stats_query)

        events_trend_query = """
            SELECT CASE 
                WHEN prev_count = 0 THEN 0
                ELSE CAST((curr_count - prev_count) AS DECIMAL) / prev_count * 100
            END as events_trend
            FROM (
                SELECT 
                    (SELECT COUNT(*) FROM detection_events WHERE CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE)) as curr_count,
                    (SELECT COUNT(*) FROM detection_events WHERE CAST(timestamp AS DATE) = DATEADD(day, -1, CAST(SYSDATETIMEOFFSET() AS DATE))) as prev_count
            ) trend_calc
        """
        events_trend = await conn.fetchval(events_trend_query)

        devices_trend_query = """
            SELECT CASE 
                WHEN prev_count = 0 THEN 0
                ELSE CAST((curr_count - prev_count) AS DECIMAL) / prev_count * 100
            END as devices_trend
            FROM (
                SELECT 
                    (SELECT COUNT(*) FROM camera_devices WHERE status = 'online') as curr_count,
                    (SELECT COUNT(*) FROM camera_devices WHERE status = 'online' AND updated_at < DATEADD(day, -1, SYSDATETIMEOFFSET())) as prev_count
            ) trend_calc
        """
        devices_trend = await conn.fetchval(devices_trend_query)

        people_trend_query = """
            SELECT CASE 
                WHEN prev_count = 0 THEN 0
                ELSE CAST((curr_count - prev_count) AS DECIMAL) / prev_count * 100
            END as people_trend
            FROM (
                SELECT 
                    (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE)) as curr_count,
                    (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE CAST(timestamp AS DATE) = DATEADD(day, -1, CAST(SYSDATETIMEOFFSET() AS DATE))) as prev_count
            ) trend_calc
        """
        people_trend = await conn.fetchval(people_trend_query)

        return DashboardStats(
            total_events=stats['total_events'] or 0,
            total_cameras=stats['total_cameras'] or 0,
            online_cameras=stats['online_cameras'] or 0,
            offline_cameras=stats['offline_cameras'] or 0,
            active_cameras=stats['active_cameras'] or 0,
            people_detected=stats['people_detected'] or 0,
            events_trend=events_trend or 0,
            devices_trend=devices_trend or 0,
            people_trend=people_trend or 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/people-count")
async def get_people_count(
    search: Optional[str] = None,
    conn: DatabaseWrapper = Depends(get_db),
):
    """Get people count statistics and device breakdown."""
    try:
        stats_query = """
            SELECT
                COUNT(DISTINCT CASE WHEN CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE) THEN person_id END) AS today,
                COUNT(DISTINCT CASE WHEN timestamp >= DATEADD(week, DATEDIFF(week, 0, SYSDATETIMEOFFSET()), 0) THEN person_id END) AS week,
                COUNT(DISTINCT CASE WHEN timestamp >= DATEADD(month, DATEDIFF(month, 0, SYSDATETIMEOFFSET()), 0) THEN person_id END) AS month,
                COUNT(DISTINCT CASE WHEN timestamp >= DATEADD(year, DATEDIFF(year, 0, SYSDATETIMEOFFSET()), 0) THEN person_id END) AS year,
                COUNT(DISTINCT person_id) AS [all]
            FROM detection_events
        """
        stats = await conn.fetchrow(stats_query)

        params: List = []
        where_clause = "WHERE CAST(d.timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE)"
        if search:
            where_clause += " AND (d.camera_name LIKE ? OR c.location LIKE ?)"
            params.append(f"%{search}%")
            params.append(f"%{search}%") # Need twice for OR

        # SQL Server doesn't support ARRAY_AGG nicely for this, so we use subqueries or just simple group by if we don't need array
        # The original query took the first image/metadata. We can use subqueries or OUTER APPLY.
        # Subqueries are easier to read here.
        
        device_query = f"""
            SELECT
                d.camera_id,
                d.camera_name,
                COALESCE(c.location, '') AS location,
                COUNT(DISTINCT d.person_id) AS count,
                MAX(d.timestamp) AS last_detection,
                (SELECT TOP 1 image_path FROM detection_events d2 WHERE d2.camera_id = d.camera_id ORDER BY d2.timestamp DESC) AS image_path,
                (SELECT TOP 1 metadata FROM detection_events d2 WHERE d2.camera_id = d.camera_id ORDER BY d2.timestamp DESC) AS metadata
            FROM detection_events d
            LEFT JOIN camera_devices c ON d.camera_id = c.id
            {where_clause}
            GROUP BY d.camera_id, d.camera_name, c.location
            ORDER BY d.camera_name
        """
        rows = await conn.fetch(device_query, *params)
        devices = [
            {
                "camera_id": str(r["camera_id"]),
                "camera_name": r["camera_name"],
                "location": r["location"],
                "count": r["count"],
                "last_detection": r["last_detection"],
                "image_path": r["image_path"],
                "metadata": r["metadata"] or {},
            }
            for r in rows
        ]

        return {
            "today": stats["today"],
            "week": stats["week"],
            "month": stats["month"],
            "year": stats["year"],
            "all": stats["all"],
            "devices": devices,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/events")
async def get_detection_events(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    date_filter: Optional[str] = Query(None, description="Date filter: today, week, month, all"),
    confidence_filter: Optional[str] = Query(None, description="Confidence filter: high, medium, low, all"),
    conn: DatabaseWrapper = Depends(get_db)
):
    """Get paginated detection events."""
    try:
        offset = (page - 1) * limit

        where_clause = "WHERE 1=1"
        params: List[Any] = []
        
        # Note: In aioodbc/pyodbc, params are passed as a list/tuple and placeholders are ?
        # We need to construct the query with ? placeholders.

        if search:
            where_clause += f" AND (camera_name LIKE ? OR CAST(person_id AS NVARCHAR) LIKE ?)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")

        if date_filter and date_filter != "all":
            if date_filter == "today":
                where_clause += " AND CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE)"
            elif date_filter == "week":
                where_clause += " AND timestamp >= DATEADD(week, DATEDIFF(week, 0, SYSDATETIMEOFFSET()), 0)"
            elif date_filter == "month":
                where_clause += " AND timestamp >= DATEADD(month, DATEDIFF(month, 0, SYSDATETIMEOFFSET()), 0)"

        if confidence_filter and confidence_filter != "all":
            if confidence_filter == "high":
                where_clause += " AND confidence >= 0.8"
            elif confidence_filter == "medium":
                where_clause += " AND confidence >= 0.6 AND confidence < 0.8"
            elif confidence_filter == "low":
                where_clause += " AND confidence < 0.6"

        count_query = f"SELECT COUNT(*) FROM detection_events {where_clause}"
        total = await conn.fetchval(count_query, *params)

        # SQL Server pagination using OFFSET FETCH
        query = f"""
            SELECT id, timestamp, person_id, confidence, camera_name, 
                   image_path, alert_sent, metadata
            FROM detection_events 
            {where_clause}
            ORDER BY timestamp DESC 
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        params.extend([offset, limit])

        rows = await conn.fetch(query, *params)
        events = [dict(row) for row in rows]

        return {
            "events": events,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Alerts ------------------------------------------------------------------
def format_alert_message(event: dict, format_type: str = "text") -> dict:
    """Format alert message with templates."""
    import pytz  # type: ignore

    timestamp = event.get('timestamp')
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except Exception:
            timestamp = datetime.now(pytz.UTC)
    elif not timestamp:
        timestamp = datetime.now(pytz.UTC)

    local_time = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

    confidence = float(event.get('confidence', 0))
    confidence_pct = f"{confidence * 100:.1f}%"

    if confidence >= 0.9:
        severity, severity_emoji = "HIGH", "🔴"
    elif confidence >= 0.7:
        severity, severity_emoji = "MEDIUM", "🟡"
    else:
        severity, severity_emoji = "LOW", "🟢"

    camera_name = event.get('camera_name', 'Unknown Camera')
    person_id = event.get('person_id', 'Unknown')
    event_id = event.get('id', 'Unknown')

    if format_type == "html":
        subject = f"🚨 Person Detected - {camera_name} ({confidence_pct})"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #d32f2f; margin-bottom: 20px;">{severity_emoji} Person Detection Alert</h2>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 10px 0; color: #333;">Detection Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 5px 0; font-weight: bold;">Severity:</td><td style="padding: 5px 0;">{severity} ({confidence_pct})</td></tr>
                        <tr><td style="padding: 5px 0; font-weight: bold;">Camera:</td><td style="padding: 5px 0;">{camera_name}</td></tr>
                        <tr><td style="padding: 5px 0; font-weight: bold;">Time:</td><td style="padding: 5px 0;">{local_time}</td></tr>
                        <tr><td style="padding: 5px 0; font-weight: bold;">Person ID:</td><td style="padding: 5px 0;">{person_id}</td></tr>
                        <tr><td style="padding: 5px 0; font-weight: bold;">Event ID:</td><td style="padding: 5px 0;">{event_id}</td></tr>
                    </table>
                </div>
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; border-left: 4px solid #2196f3;">
                    <p style="margin: 0; font-size: 14px; color: #555;">
                        <strong>WebDash Person Detection System</strong><br>
                        This alert was generated automatically based on your configured settings.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        subject = f"🚨 Person Detected - {camera_name} ({confidence_pct})"
        body = f"""{severity_emoji} PERSON DETECTION ALERT {severity_emoji}

📍 Camera: {camera_name}
⏰ Time: {local_time}
👤 Person ID: {person_id}
🎯 Confidence: {confidence_pct} ({severity} Priority)
🔍 Event ID: {event_id}

━━━━━━━━━━━━━━━━━━━━━━━━
WebDash Person Detection System
Automatic Alert Notification
━━━━━━━━━━━━━━━━━━━━━━━━"""

    return {"subject": subject, "body": body, "severity": severity, "confidence_pct": confidence_pct}


async def send_alerts_background(event: dict):
    """Send alerts via configured channels from DB settings with enhanced formatting."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import requests as http

    try:
        # Connect to database using aioodbc
        if not DATABASE_URL:
            print("DATABASE_URL not configured, skipping alerts")
            return
        
        conn_str = _build_connection_string(DATABASE_URL)
        raw_conn = await aioodbc.connect(dsn=conn_str)
        conn = DatabaseWrapper(raw_conn)
        
        settings_row = await conn.fetchrow("""
            SELECT TOP 1
                enabled,
                notify_email, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from, email_to,
                notify_whatsapp, whatsapp_phone_number_id, whatsapp_token, whatsapp_to,
                notify_telegram, telegram_bot_token, telegram_chat_id,
                allowed_days, start_time, end_time, timezone
            FROM alert_settings
            ORDER BY updated_at DESC
        """)
        await conn.close()
        
        settings = settings_row if settings_row else None

        if not settings or not settings.get("enabled"):
            return

        # Schedule guard
        try:
            import pytz  # type: ignore
            tzname = settings["timezone"] or "UTC"
            tz = pytz.timezone(tzname) if tzname else pytz.UTC
            now_local = datetime.now(tz)
            weekday_name = now_local.strftime("%A")
            allowed_days = settings["allowed_days"] or []
            if allowed_days and weekday_name not in allowed_days:
                return
            start_t = settings["start_time"]
            end_t = settings["end_time"]
            if start_t and end_t:
                current_t = now_local.time()
                if not (start_t <= current_t <= end_t):
                    return
        except Exception as _e:
            print(f"Schedule evaluation failed, proceeding without block: {_e}")

        # Messages
        text_message = format_alert_message(event, "text")
        html_message = format_alert_message(event, "html")

        # Email
        if settings["notify_email"] and settings["smtp_host"] and settings["email_to"]:
            try:
                msg = MIMEMultipart('alternative')
                msg["Subject"] = html_message["subject"]
                msg["From"] = settings["smtp_from"] or settings["smtp_username"]
                msg["To"] = settings["email_to"]

                msg.attach(MIMEText(text_message["body"], 'plain'))
                msg.attach(MIMEText(html_message["body"], 'html'))

                with smtplib.SMTP_SSL(settings["smtp_host"], int(settings["smtp_port"] or 465)) as server:
                    if settings["smtp_username"] and settings["smtp_password"]:
                        server.login(settings["smtp_username"], settings["smtp_password"])
                    server.sendmail(msg["From"], [settings["email_to"]], msg.as_string())
                print(f"Email alert sent successfully for event {event.get('id')}")
            except Exception as e:
                print(f"Email send failed: {e}")

        # WhatsApp
        if settings["notify_whatsapp"] and settings["whatsapp_phone_number_id"] and settings["whatsapp_token"] and settings["whatsapp_to"]:
            try:
                url = f"https://graph.facebook.com/v17.0/{settings['whatsapp_phone_number_id']}/messages"
                headers = {"Authorization": f"Bearer {settings['whatsapp_token']}", "Content-Type": "application/json"}
                payload = {"messaging_product": "whatsapp", "to": settings["whatsapp_to"], "type": "text",
                           "text": {"body": text_message["body"]}}
                resp = http.post(url, headers=headers, json=payload, timeout=10)
                if resp.status_code == 200:
                    print(f"WhatsApp alert sent successfully for event {event.get('id')}")
                else:
                    print(f"WhatsApp send failed with status {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"WhatsApp send failed: {e}")

        # Telegram
        if settings["notify_telegram"] and settings["telegram_bot_token"] and settings["telegram_chat_id"]:
            try:
                url = f"https://api.telegram.org/bot{settings['telegram_bot_token']}/sendMessage"
                payload = {"chat_id": settings["telegram_chat_id"], "text": text_message["body"], "parse_mode": "HTML"}
                resp = http.post(url, json=payload, timeout=10)
                if resp.status_code == 200:
                    print(f"Telegram alert sent successfully for event {event.get('id')}")
                else:
                    print(f"Telegram send failed with status {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"Telegram send failed: {e}")

    except Exception as e:
        print(f"Alert background error: {e}")


@app.post("/api/v1/events")
async def create_detection_event(
    event: DetectionEvent,
    conn: DatabaseWrapper = Depends(get_db),
    api_key_valid: bool = Depends(validate_api_key),
    background: BackgroundTasks = None
):
    """Create a new detection event."""
    try:
        # Ensure timestamp & metadata json
        ts = event.timestamp or datetime.now(timezone.utc)
        try:
            metadata_json = json.dumps(event.metadata or {})
        except (TypeError, ValueError):
            metadata_json = "{}"

        query = """
            INSERT INTO detection_events 
                (timestamp, person_id, confidence, camera_id, camera_name, image_path, alert_sent, metadata,
                 bbox_x1, bbox_y1, bbox_x2, bbox_y2)
            OUTPUT inserted.id, inserted.timestamp, inserted.person_id, inserted.confidence, inserted.camera_id, 
                   inserted.camera_name, inserted.image_path, inserted.alert_sent, inserted.metadata,
                   inserted.bbox_x1, inserted.bbox_y1, inserted.bbox_x2, inserted.bbox_y2
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?,
                 ?, ?, ?, ?)
        """

        row = await conn.fetchrow(
            query,
            ts,
            event.person_id,
            event.confidence,
            event.camera_id,
            event.camera_name,
            event.image_path,
            event.alert_sent,
            metadata_json,
            event.bbox_x1,
            event.bbox_y1,
            event.bbox_x2,
            event.bbox_y2,
        )

        if not row:
            raise HTTPException(status_code=500, detail="Failed to create event")

        result = {
            "id": str(row["id"]),
            "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], 'isoformat') else str(row["timestamp"]),
            "person_id": row["person_id"],
            "confidence": float(row["confidence"]),
            "camera_id": str(row["camera_id"]),
            "camera_name": row["camera_name"],
            "image_path": row["image_path"],
            "alert_sent": row["alert_sent"],
            "metadata": row["metadata"] or {}, # It might be a string in SQL Server, but fetchrow returns it as is. If it's a string, we might need to parse it if we want dict, but the response model expects dict?
            # Actually, if it's stored as NVARCHAR, it comes back as str.
            # We should parse it if the response model expects dict.
            # But the response model for this endpoint returns `result` which is a dict.
            # The `DetectionEvent` model has metadata as Dict.
            # So we should parse it.
            "bbox_x1": float(row["bbox_x1"]) if row["bbox_x1"] is not None else None,
            "bbox_y1": float(row["bbox_y1"]) if row["bbox_y1"] is not None else None,
            "bbox_x2": float(row["bbox_x2"]) if row["bbox_x2"] is not None else None,
            "bbox_y2": float(row["bbox_y2"]) if row["bbox_y2"] is not None else None,
        }
        
        if isinstance(result["metadata"], str):
             try:
                 result["metadata"] = json.loads(result["metadata"])
             except:
                 result["metadata"] = {}

        if background is not None:
            background.add_task(send_alerts_background, result)
        else:
            import asyncio as _asyncio
            _asyncio.create_task(send_alerts_background(result))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v1/cameras")
async def get_cameras(conn: DatabaseWrapper = Depends(get_db)):
    """Get all cameras."""
    try:
        query = """
            SELECT id, name, rtsp_url, status, location
            FROM camera_devices
            ORDER BY CASE WHEN status = 'online' THEN 1 ELSE 0 END DESC, name
        """
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/cameras", status_code=201)
async def create_camera(
    camera: CameraCreate,
    conn: DatabaseWrapper = Depends(get_db),
    api_key_valid: bool = Depends(validate_api_key)
):
    """Create a camera device (ingestion point)."""
    try:
        exists = await conn.fetchval("SELECT 1 FROM camera_devices WHERE name = ?", camera.name)
        if exists:
            raise HTTPException(status_code=409, detail="Camera with this name already exists")

        row = await conn.fetchrow(
            """
            INSERT INTO camera_devices (name, rtsp_url, status, location)
            OUTPUT inserted.id, inserted.name, inserted.rtsp_url, inserted.status, inserted.location, inserted.created_at, inserted.updated_at
            VALUES (?, ?, 'offline', ?)
            """,
            camera.name, camera.rtsp_url, camera.location
        )
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/cameras/{camera_id}/status")
async def update_camera_status(
    camera_id: str,
    status_data: dict,
    conn: DatabaseWrapper = Depends(get_db),
    api_key_valid: bool = Depends(validate_api_key)
):
    """Update camera status (online/offline), heartbeat, and timestamps."""
    try:
        status = status_data.get("status")
        if status not in ["online", "offline"]:
            raise HTTPException(status_code=400, detail="Status must be 'online' or 'offline'")

        exists = await conn.fetchval("SELECT 1 FROM camera_devices WHERE id = ?", camera_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Camera not found")

        await conn.execute(
            """
            UPDATE camera_devices 
            SET status = ?, last_heartbeat = SYSDATETIMEOFFSET(), updated_at = SYSDATETIMEOFFSET()
            WHERE id = ?
            """,
            status, camera_id
        )
        return {"message": f"Camera status updated to {status}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Analytics ---------------------------------------------------------------
@app.get("/api/v1/analytics/hourly")
async def get_hourly_data(conn: DatabaseWrapper = Depends(get_db)):
    """Get hourly event data for charts."""
    try:
        query = """
            SELECT 
                FORMAT(timestamp, 'HH:mm') as hour,
                COUNT(*) as events,
                COUNT(DISTINCT person_id) as footfall,
                0 as vehicles
            FROM detection_events 
            WHERE timestamp >= DATEADD(hour, -24, SYSDATETIMEOFFSET())
            GROUP BY FORMAT(timestamp, 'HH:mm'), DATEPART(hour, timestamp)
            ORDER BY DATEPART(hour, timestamp)
        """
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/trends")
async def get_trends(conn: DatabaseWrapper = Depends(get_db)):
    """Get trend data."""
    try:
        # We can call the stored procedure
        # EXEC get_dashboard_stats
        # But aioodbc/pyodbc execute might not return rows for EXEC if not handled right, 
        # but usually it does.
        # Alternatively, we can just reuse the logic from get_dashboard_stats or call it.
        # Let's try calling the procedure.
        
        rows = await conn.fetch("EXEC get_dashboard_stats")
        stats = rows[0] if rows else {}
        
        return {
            "events_trend": stats.get("events_trend", 0),
            "devices_trend": stats.get("devices_trend", 0),
            "people_trend": stats.get("people_trend", 0)
        }
    except Exception:
        # Fallback if the DB function isn't available
        return {"events_trend": 0, "devices_trend": 0, "people_trend": 0}


# ---- Streaming ---------------------------------------------------------------
@app.get("/api/v1/stream/demo")
async def demo_stream():
    """Demo stream endpoint that generates a simple pattern for testing."""
    import time

    def demo_frame_generator():
        try:
            frame_count = 0
            boundary = "frame"
            while True:
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                t = int(time.time() * 2) % 640
                cv2.circle(img, (t, 240), 30, (0, 255, 0), -1)
                cv2.circle(img, (640 - t, 240), 20, (255, 0, 0), -1)
                cv2.putText(img, f"Frame: {frame_count}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(img, f"Demo Stream", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if not ok:
                    continue
                bytes_ = buf.tobytes()
                yield (
                    b"--" + boundary.encode() + b"\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(bytes_)).encode() + b"\r\n\r\n" + bytes_ + b"\r\n"
                )
                frame_count += 1
                time.sleep(1/15)
        except Exception as e:
            print(f"Demo stream error: {e}")

    return StreamingResponse(
        demo_frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/v1/stream/{camera_id}")
async def stream_camera(camera_id: str, conn: DatabaseWrapper = Depends(get_db)):
    """Stream RTSP camera as MJPEG for simple live preview."""
    try:
        row = await conn.fetchrow(
            "SELECT rtsp_url, status FROM camera_devices WHERE id = ?",
            camera_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Camera not found")
        rtsp_url = row["rtsp_url"]

        print(f"Attempting to connect to camera {camera_id} at {rtsp_url}")

        def open_capture(url: str):
            import socket
            try:
                parsed = urlparse(url)
                host = parsed.hostname
                port = parsed.port or (80 if parsed.scheme == "http" else 443 if parsed.scheme == "https" else 554)
                print(f"Testing network connectivity to {host}:{port}")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                if result != 0:
                    print(f"Network connectivity failed to {host}:{port} - error code: {result}")
                    return None
            except Exception as e:
                print(f"Network test error: {e}")
                return None

            print(f"Opening OpenCV VideoCapture for {url}")
            cap = cv2.VideoCapture(url)
            import time
            time.sleep(2)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"Successfully read test frame: {frame.shape if frame is not None else 'No frame'}")
                else:
                    print("Failed to read test frame")
                    cap.release()
                    return None
            return cap

        cap = await run_in_threadpool(open_capture, rtsp_url)
        if not cap or not cap.isOpened():
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to camera at {rtsp_url}. Check network connectivity and RTSP URL."
            )

        boundary = "frame"

        def frame_generator():
            try:
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        break
                    h, w = frame.shape[:2]
                    max_w = 960
                    if w > max_w:
                        scale = max_w / float(w)
                        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    if not ok:
                        continue
                    bytes_ = buf.tobytes()
                    yield (
                        b"--" + boundary.encode() + b"\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: " + str(len(bytes_)).encode() + b"\r\n\r\n" + bytes_ + b"\r\n"
                    )
            finally:
                try:
                    cap.release()
                except Exception:
                    pass

        return StreamingResponse(
            frame_generator(),
            media_type=f"multipart/x-mixed-replace; boundary={boundary}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/cameras/{camera_id}/test")
async def test_camera_connection(camera_id: str, conn: DatabaseWrapper = Depends(get_db)):
    """Test camera connectivity without streaming."""
    try:
        row = await conn.fetchrow(
            "SELECT rtsp_url, status FROM camera_devices WHERE id = ?",
            camera_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Camera not found")

        rtsp_url = row["rtsp_url"]

        def test_connection(url: str):
            import socket
            from urllib.parse import urlparse
            result = {
                "rtsp_url": url,
                "network_reachable": False,
                "rtsp_connectable": False,
                "error": None
            }
            try:
                parsed = urlparse(url)
                host = parsed.hostname
                if parsed.scheme == 'http':
                    port = parsed.port or 80
                elif parsed.scheme == 'https':
                    port = parsed.port or 443
                else:
                    port = parsed.port or 554
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                conn_result = sock.connect_ex((host, port))
                sock.close()
                result["network_reachable"] = (conn_result == 0)

                if result["network_reachable"]:
                    cap = cv2.VideoCapture(url)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        result["rtsp_connectable"] = ret and frame is not None
                        if result["rtsp_connectable"]:
                            result["frame_size"] = frame.shape if frame is not None else None
                    cap.release()
                else:
                    result["error"] = f"Cannot reach {host}:{port}"
            except Exception as e:
                result["error"] = str(e)
            return result

        test_result = await run_in_threadpool(test_connection, rtsp_url)
        return test_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/cameras/{camera_id}/update-rtsp")
async def update_camera_rtsp(
    camera_id: str,
    rtsp_data: dict,
    conn: DatabaseWrapper = Depends(get_db),
    api_key_valid: bool = Depends(validate_api_key)
):
    """Update camera RTSP URL for testing."""
    try:
        rtsp_url = rtsp_data.get("rtsp_url")
        if not rtsp_url:
            raise HTTPException(status_code=400, detail="rtsp_url is required")

        exists = await conn.fetchval("SELECT 1 FROM camera_devices WHERE id = ?", camera_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Camera not found")

        await conn.execute(
            "UPDATE camera_devices SET rtsp_url = ?, updated_at = SYSDATETIMEOFFSET() WHERE id = ?",
            rtsp_url, camera_id
        )
        return {"message": "RTSP URL updated successfully", "rtsp_url": rtsp_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Alert Settings CRUD & Reports ------------------------------------------
@app.get("/api/v1/alert-settings", response_model=AlertSettings)
async def get_alert_settings(conn: DatabaseWrapper = Depends(get_db)):
    """Get current alert settings."""
    try:
        query = """
            SELECT TOP 1 id, enabled, notify_email, smtp_host, smtp_port, smtp_username, 
                   smtp_password, smtp_from, email_to, notify_whatsapp, whatsapp_phone_number_id,
                   whatsapp_token, whatsapp_to, notify_telegram, telegram_bot_token, 
                   telegram_chat_id, allowed_days, start_time, end_time, timezone,
                   daily_report_enabled, weekly_report_enabled, monthly_report_enabled,
                   notify_vip_email, notify_regular_email, notify_attendance_to_branch,
                   google_places_api_key, created_at, updated_at
            FROM alert_settings 
            ORDER BY updated_at DESC 
        """
        row = await conn.fetchrow(query)

        if not row:
            return AlertSettings()

        return AlertSettings(
            id=str(row["id"]),
            enabled=row["enabled"] or True,
            notify_email=row["notify_email"] or False,
            smtp_host=row["smtp_host"],
            smtp_port=row["smtp_port"] or 465,
            smtp_username=row["smtp_username"],
            smtp_password=row["smtp_password"],
            smtp_from=row["smtp_from"],
            email_to=row["email_to"],
            notify_whatsapp=row["notify_whatsapp"] or False,
            whatsapp_phone_number_id=row["whatsapp_phone_number_id"],
            whatsapp_token=row["whatsapp_token"],
            whatsapp_to=row["whatsapp_to"],
            notify_telegram=row["notify_telegram"] or False,
            telegram_bot_token=row["telegram_bot_token"],
            telegram_chat_id=row["telegram_chat_id"],
            allowed_days=list(row["allowed_days"]) if row["allowed_days"] else [
                "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
            ],
            start_time=str(row["start_time"]) if row["start_time"] else None,
            end_time=str(row["end_time"]) if row["end_time"] else None,
            timezone=row["timezone"] or "UTC",
            daily_report_enabled=row["daily_report_enabled"] or False,
            weekly_report_enabled=row["weekly_report_enabled"] or False,
            monthly_report_enabled=row["monthly_report_enabled"] or False,
            notify_vip_email=row["notify_vip_email"] or False,
            notify_regular_email=row["notify_regular_email"] or False,
            notify_attendance_to_branch=row["notify_attendance_to_branch"] or False,
            google_places_api_key=row["google_places_api_key"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/alert-settings", response_model=AlertSettings)
async def update_alert_settings(
    settings: AlertSettingsUpdate,
    conn: DatabaseWrapper = Depends(get_db)
):
    """Update alert settings (upsert)."""
    try:
        existing = await conn.fetchrow(
            "SELECT TOP 1 id FROM alert_settings ORDER BY updated_at DESC"
        )

        if existing:
            update_fields = []
            params: List[Any] = []
            # param_count is not needed for ? placeholders, just append to params

            for field, value in settings.model_dump(exclude_unset=True).items():
                if field in ['created_at', 'id']:
                    continue
                update_fields.append(f"{field} = ?")
                params.append(value)

            if update_fields:
                params.append(existing["id"])
                query = f"""
                    UPDATE alert_settings 
                    SET {', '.join(update_fields)}, updated_at = SYSDATETIMEOFFSET()
                    OUTPUT inserted.*
                    WHERE id = ?
                """
                row = await conn.fetchrow(query, *params)
            else:
                row = await conn.fetchrow(
                    "SELECT * FROM alert_settings WHERE id = ?", existing["id"]
                )
        else:
            data = settings.model_dump(exclude_unset=True)
            if 'allowed_days' not in data:
                data['allowed_days'] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

            # Convert list to string for SQL Server if needed (or assume JSON string)
            # The schema says NVARCHAR(MAX) for allowed_days
            if 'allowed_days' in data and isinstance(data['allowed_days'], list):
                 # We can store as JSON string or comma separated. 
                 # The pydantic model expects list on read. 
                 # Let's store as JSON string if we can, but the model might handle it.
                 # Actually, let's just let pydantic handle serialization if possible, 
                 # but aioodbc might not serialize list to JSON automatically.
                 # We should serialize it manually.
                 pass # We'll rely on the fact that we might need to serialize it. 
                 # But wait, `data` values are passed to execute. 
                 # If we pass a list to pyodbc, it might fail.
                 # Let's serialize allowed_days to json string.
            
            # Fix allowed_days serialization for insert
            if 'allowed_days' in data and isinstance(data['allowed_days'], list):
                import json
                data['allowed_days'] = json.dumps(data['allowed_days'])

            columns = list(data.keys())
            values = list(data.values())
            placeholders = ["?" for _ in range(len(values))]

            query = f"""
                INSERT INTO alert_settings ({', '.join(columns)})
                OUTPUT inserted.*
                VALUES ({', '.join(placeholders)})
            """
            row = await conn.fetchrow(query, *values)
            
        # Fix allowed_days deserialization for return
        if row and row['allowed_days'] and isinstance(row['allowed_days'], str):
             # We need to modify the row to match Pydantic model
             # But row is a dict (from our wrapper).
             # We can't modify it easily if it's not mutable or if we want to be clean.
             # We'll handle it in the return statement.
             pass

        if not row:
            raise HTTPException(status_code=500, detail="Failed to update settings")

        return AlertSettings(
            id=str(row["id"]),
            enabled=row["enabled"] or True,
            notify_email=row["notify_email"] or False,
            smtp_host=row["smtp_host"],
            smtp_port=row["smtp_port"] or 465,
            smtp_username=row["smtp_username"],
            smtp_password=row["smtp_password"],
            smtp_from=row["smtp_from"],
            email_to=row["email_to"],
            notify_whatsapp=row["notify_whatsapp"] or False,
            whatsapp_phone_number_id=row["whatsapp_phone_number_id"],
            whatsapp_token=row["whatsapp_token"],
            whatsapp_to=row["whatsapp_to"],
            notify_telegram=row["notify_telegram"] or False,
            telegram_bot_token=row["telegram_bot_token"],
            telegram_chat_id=row["telegram_chat_id"],
            allowed_days=list(row["allowed_days"]) if row["allowed_days"] else [
                "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
            ],
            start_time=str(row["start_time"]) if row["start_time"] else None,
            end_time=str(row["end_time"]) if row["end_time"] else None,
            timezone=row["timezone"] or "UTC",
            daily_report_enabled=row["daily_report_enabled"] or False,
            weekly_report_enabled=row["weekly_report_enabled"] or False,
            monthly_report_enabled=row["monthly_report_enabled"] or False,
            notify_vip_email=row["notify_vip_email"] or False,
            notify_regular_email=row["notify_regular_email"] or False,
            notify_attendance_to_branch=row["notify_attendance_to_branch"] or False,
            google_places_api_key=row["google_places_api_key"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/alert-settings/test")
async def test_alert_configuration(request: TestAlertRequest):
    """Test alert configuration before saving."""
    try:
        if request.alert_type == "email":
            return await test_email_config(request.settings)
        elif request.alert_type == "whatsapp":
            return await test_whatsapp_config(request.settings)
        elif request.alert_type == "telegram":
            return await test_telegram_config(request.settings)
        else:
            raise HTTPException(status_code=400, detail="Invalid alert type")
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_email_config(settings: dict):
    """Test email configuration."""
    try:
        import smtplib
        from email.mime.text import MIMEText

        smtp_host = settings.get('smtp_host')
        smtp_port = int(settings.get('smtp_port', 465))
        smtp_username = settings.get('smtp_username')
        smtp_password = settings.get('smtp_password')
        smtp_from = settings.get('smtp_from', smtp_username)
        email_to = settings.get('email_to')

        if not all([smtp_host, smtp_username, smtp_password, email_to]):
            return {"success": False, "error": "Missing required email settings"}

        msg = MIMEText("This is a test email from your WebDash Person Detection System.")
        msg["Subject"] = "WebDash Alert Test"
        msg["From"] = smtp_from
        msg["To"] = email_to

        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_from, [email_to], msg.as_string())

        return {"success": True, "message": "Test email sent successfully"}
    except Exception as e:
        return {"success": False, "error": f"Email test failed: {str(e)}"}


async def test_whatsapp_config(settings: dict):
    """Test WhatsApp configuration."""
    try:
        import requests as http

        phone_number_id = settings.get('whatsapp_phone_number_id')
        token = settings.get('whatsapp_token')
        to_number = settings.get('whatsapp_to')

        if not all([phone_number_id, token, to_number]):
            return {"success": False, "error": "Missing required WhatsApp settings"}

        url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": "This is a test message from your WebDash Person Detection System."}
        }

        response = http.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            return {"success": True, "message": "Test WhatsApp message sent successfully"}
        else:
            return {"success": False, "error": f"WhatsApp API error: {response.text}"}
    except Exception as e:
        return {"success": False, "error": f"WhatsApp test failed: {str(e)}"}


async def test_telegram_config(settings: dict):
    """Test Telegram configuration."""
    try:
        import requests as http

        bot_token = settings.get('telegram_bot_token')
        chat_id = settings.get('telegram_chat_id')

        if not all([bot_token, chat_id]):
            return {"success": False, "error": "Missing required Telegram settings"}

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": "This is a test message from your WebDash Person Detection System."}

        response = http.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            return {"success": True, "message": "Test Telegram message sent successfully"}
        else:
            return {"success": False, "error": f"Telegram API error: {response.text}"}
    except Exception as e:
        return {"success": False, "error": f"Telegram test failed: {str(e)}"}


# ---- Reports -----------------------------------------------------------------
async def generate_detection_report(period: str, conn: DatabaseWrapper) -> dict:
    """Generate detection report for specified period."""
    try:
        if period == "daily":
            date_filter = "CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE)"
            period_name = "Today"
        elif period == "weekly":
            date_filter = "timestamp >= DATEADD(week, DATEDIFF(week, 0, SYSDATETIMEOFFSET()), 0)"
            period_name = "This Week"
        elif period == "monthly":
            date_filter = "timestamp >= DATEADD(month, DATEDIFF(month, 0, SYSDATETIMEOFFSET()), 0)"
            period_name = "This Month"
        else:
            raise ValueError("Invalid period")

        stats_query = f"""
            SELECT 
                COUNT(*) as total_detections,
                COUNT(DISTINCT person_id) as unique_people,
                COUNT(DISTINCT camera_id) as active_cameras,
                AVG(confidence) as avg_confidence,
                MIN(timestamp) as first_detection,
                MAX(timestamp) as last_detection
            FROM detection_events 
            WHERE {date_filter}
        """
        stats = await conn.fetchrow(stats_query)

        camera_query = f"""
            SELECT 
                d.camera_name,
                COALESCE(c.location, 'Unknown Location') as location,
                COUNT(*) as detection_count,
                COUNT(DISTINCT d.person_id) as unique_people,
                AVG(d.confidence) as avg_confidence,
                MAX(d.timestamp) as last_detection
            FROM detection_events d
            LEFT JOIN camera_devices c ON d.camera_id = c.id
            WHERE {date_filter}
            GROUP BY d.camera_name, c.location
            ORDER BY detection_count DESC
        """
        cameras = await conn.fetch(camera_query)

        hourly_query = f"""
            SELECT 
                DATEPART(HOUR, timestamp) as hour,
                COUNT(*) as detections,
                COUNT(DISTINCT person_id) as unique_people
            FROM detection_events 
            WHERE {date_filter}
            GROUP BY DATEPART(HOUR, timestamp)
            ORDER BY hour
        """
        hourly_data = await conn.fetch(hourly_query)

        confidence_query = f"""
            SELECT 
                CASE 
                    WHEN confidence >= 0.9 THEN 'High (90%+)'
                    WHEN confidence >= 0.7 THEN 'Medium (70-89%)'
                    ELSE 'Low (<70%)'
                END as confidence_range,
                COUNT(*) as count
            FROM detection_events 
            WHERE {date_filter}
            GROUP BY CASE 
                    WHEN confidence >= 0.9 THEN 'High (90%+)'
                    WHEN confidence >= 0.7 THEN 'Medium (70-89%)'
                    ELSE 'Low (<70%)'
                END
            ORDER BY MIN(confidence) DESC
        """
        confidence_dist = await conn.fetch(confidence_query)

        return {
            "period": period_name,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_detections": stats["total_detections"] or 0,
                "unique_people": stats["unique_people"] or 0,
                "active_cameras": stats["active_cameras"] or 0,
                "avg_confidence": round(float(stats["avg_confidence"] or 0) * 100, 1),
                "first_detection": stats["first_detection"].isoformat() if stats["first_detection"] else None,
                "last_detection": stats["last_detection"].isoformat() if stats["last_detection"] else None
            },
            "camera_breakdown": [
                {
                    "camera_name": row["camera_name"],
                    "location": row["location"],
                    "detection_count": row["detection_count"],
                    "unique_people": row["unique_people"],
                    "avg_confidence": round(float(row["avg_confidence"] or 0) * 100, 1),
                    "last_detection": row["last_detection"].isoformat() if row["last_detection"] else None
                }
                for row in cameras
            ],
            "hourly_breakdown": [
                {
                    "hour": int(row["hour"]),
                    "detections": row["detections"],
                    "unique_people": row["unique_people"]
                }
                for row in hourly_data
            ],
            "confidence_distribution": [
                {"range": row["confidence_range"], "count": row["count"]}
                for row in confidence_dist
            ]
        }
    except Exception as e:
        raise Exception(f"Failed to generate report: {str(e)}")


def format_report_email(report_data: dict) -> str:
    """Format detection report as HTML email."""
    period = report_data["period"]
    summary = report_data["summary"]
    cameras = report_data["camera_breakdown"]
    hourly = report_data["hourly_breakdown"]
    confidence = report_data["confidence_distribution"]

    camera_rows = ""
    for cam in cameras[:10]:
        camera_rows += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{cam['camera_name']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{cam['location']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{cam['detection_count']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{cam['unique_people']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{cam['avg_confidence']}%</td>
        </tr>
        """

    confidence_bars = ""
    max_count = max([c['count'] for c in confidence], default=1)
    for conf in confidence:
        percentage = (conf['count'] / max_count) * 100
        confidence_bars += f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                <span style="font-size: 12px;">{conf['range']}</span>
                <span style="font-size: 12px; font-weight: bold;">{conf['count']}</span>
            </div>
            <div style="background-color: #f0f0f0; height: 20px; border-radius: 10px;">
                <div style="height: 20px; width: {percentage}%; border-radius: 10px; background-color: #2196f3;"></div>
            </div>
        </div>
        """

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WebDash Detection Report - {period}</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; margin: 0; padding: 20px;">
        <div style="max-width: 800px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 300;">📊 Detection Report</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">{period}</p>
                <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8;">Generated: {report_data['generated_at'][:19]}</p>
            </div>
            <div style="padding: 30px 20px;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    <div style="background-color: #f8f9ff; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #2196f3;">
                        <h3 style="margin: 0; font-size: 32px; color: #2196f3;">{summary['total_detections']}</h3>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Total Detections</p>
                    </div>
                    <div style="background-color: #f0fdf4; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #22c55e;">
                        <h3 style="margin: 0; font-size: 32px; color: #22c55e;">{summary['unique_people']}</h3>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Unique People</p>
                    </div>
                    <div style="background-color: #fefce8; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #eab308;">
                        <h3 style="margin: 0; font-size: 32px; color: #eab308;">{summary['active_cameras']}</h3>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Active Cameras</p>
                    </div>
                    <div style="background-color: #fdf2f8; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #ec4899;">
                        <h3 style="margin: 0; font-size: 32px; color: #ec4899;">{summary['avg_confidence']}%</h3>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Avg Confidence</p>
                    </div>
                </div>
                <div style="margin-bottom: 30px;">
                    <h2 style="color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px;">📹 Camera Performance</h2>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                            <thead>
                                <tr style="background-color: #f8f9fa;">
                                    <th style="padding: 12px 8px; text-align: left; border-bottom: 2px solid #dee2e6;">Camera</th>
                                    <th style="padding: 12px 8px; text-align: left; border-bottom: 2px solid #dee2e6;">Location</th>
                                    <th style="padding: 12px 8px; text-align: center; border-bottom: 2px solid #dee2e6;">Detections</th>
                                    <th style="padding: 12px 8px; text-align: center; border-bottom: 2px solid #dee2e6;">People</th>
                                    <th style="padding: 12px 8px; text-align: center; border-bottom: 2px solid #dee2e6;">Avg Confidence</th>
                                </tr>
                            </thead>
                            <tbody>
                                {camera_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div style="margin-bottom: 30px;">
                    <h2 style="color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px;">🎯 Detection Confidence</h2>
                    <div style="margin-top: 15px;">
                        {confidence_bars}
                    </div>
                </div>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; color: #666;">
                    <p style="margin: 0; font-size: 14px;">🤖 <strong>WebDash Person Detection System</strong></p>
                    <p style="margin: 5px 0 0 0; font-size: 12px;">Automated report generated by your security monitoring system</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/api/v1/reports/{period}")
async def get_detection_report(period: str, conn: DatabaseWrapper = Depends(get_db)):
    """Generate and return detection report for specified period."""
    if period not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid period. Must be 'daily', 'weekly', or 'monthly'")
    try:
        report_data = await generate_detection_report(period, conn)
        return report_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/reports/{period}/send")
async def send_detection_report(period: str, conn: DatabaseWrapper = Depends(get_db)):
    """Generate and send detection report via email."""
    if period not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid period. Must be 'daily', 'weekly', or 'monthly'")

    try:
        settings = await conn.fetchrow("""
            SELECT TOP 1 notify_email, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from, email_to
            FROM alert_settings
            ORDER BY updated_at DESC
        """)

        if not settings or not settings["notify_email"] or not settings["email_to"]:
            raise HTTPException(status_code=400, detail="Email notifications not configured")

        report_data = await generate_detection_report(period, conn)

        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart('alternative')
        msg["Subject"] = f"📊 WebDash Detection Report - {report_data['period']}"
        msg["From"] = settings["smtp_from"] or settings["smtp_username"]
        msg["To"] = settings["email_to"]

        html_content = format_report_email(report_data)
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP_SSL(settings["smtp_host"], int(settings["smtp_port"] or 465)) as server:
            if settings["smtp_username"] and settings["smtp_password"]:
                server.login(settings["smtp_username"], settings["smtp_password"])
            server.sendmail(msg["From"], [settings["email_to"]], msg.as_string())

        return {"message": f"Report sent successfully to {settings['email_to']}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send report: {str(e)}")


@app.post("/api/v1/reports/scheduled/run")
async def run_scheduled_reports(conn: DatabaseWrapper = Depends(get_db)):
    """Run scheduled reports based on settings."""
    try:
        settings = await conn.fetchrow("""
            SELECT TOP 1 daily_report_enabled, weekly_report_enabled, monthly_report_enabled,
                   notify_email, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from, email_to
            FROM alert_settings
            ORDER BY updated_at DESC
        """)

        if not settings or not settings["notify_email"]:
            return {"message": "Email reports not configured"}

        sent_reports = []
        now = datetime.now()

        if settings["daily_report_enabled"]:
            try:
                await send_detection_report("daily", conn)
                sent_reports.append("daily")
            except Exception as e:
                print(f"Failed to send daily report: {e}")

        if settings["weekly_report_enabled"] and now.weekday() == 0:
            try:
                await send_detection_report("weekly", conn)
                sent_reports.append("weekly")
            except Exception as e:
                print(f"Failed to send weekly report: {e}")

        if settings["monthly_report_enabled"] and now.day == 1:
            try:
                await send_detection_report("monthly", conn)
                sent_reports.append("monthly")
            except Exception as e:
                print(f"Failed to send monthly report: {e}")

        return {"message": "Scheduled reports processed", "sent_reports": sent_reports}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Health, SPA fallback ----------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}


@app.get("/api/v1/diagnostics/db")
async def db_diagnostics():
    """Return basic DB diagnostics and row counts for key tables."""
    try:
        if not DATABASE_URL:
            raise HTTPException(status_code=500, detail="DATABASE_URL is not configured")
        
        conn_str = _build_connection_string(DATABASE_URL)
        conn = await aioodbc.connect(dsn=conn_str)
        try:
            # Try counts for common tables; ignore missing tables gracefully
            async def safe_count(table: str) -> int:
                try:
                    async with conn.cursor() as cur:
                        await cur.execute(f"SELECT COUNT(*) FROM {table}")
                        val = (await cur.fetchone())[0]
                        return val
                except Exception:
                    return -1  # indicates table missing or error

            counts = {
                "activity_logs": await safe_count("activity_logs"),
                "detection_events": await safe_count("detection_events"),
                "camera_devices": await safe_count("camera_devices"),
                "alert_settings": await safe_count("alert_settings"),
                "profiles": await safe_count("profiles"),
            }

            # Parse DB host for comparison (mask creds)
            # For ODBC string, it's harder to parse standardly, but we can try
            db_info = {
                "connection_string_masked": "..." # Don't show full string
            }

            return {
                "ok": True,
                "db": db_info,
                "counts": counts,
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---- Auth Routes -------------------------------------------------------------
# Note: Traditional auth handled by Supabase (frontend Auth.tsx)
# SSO provides alternative login method

# Redirect /login to /auth for simplicity
@app.get("/login")
async def login_redirect():
    """Redirect old /login to new unified /auth page."""
    return RedirectResponse(url="/auth", status_code=302)


@app.get("/login/sso")
async def login_sso(request: Request):
    """Initiate SSO login flow."""
    # Generate state for CSRF protection
    request.session["state"] = secrets.token_urlsafe(16)
    
    # Check if SSO is configured
    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        return RedirectResponse(url="/auth?error=SSO+not+configured", status_code=302)
    
    # Create MSAL confidential client
    cca = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    
    # Get authorization URL
    auth_url = cca.get_authorization_request_url(
        scopes=OIDC_SCOPE,
        redirect_uri=REDIRECT_URI,
        state=request.session["state"],
        prompt="select_account"
    )
    
    return RedirectResponse(url=auth_url, status_code=302)


@app.route("/auth/callback", methods=["GET", "POST"])
async def auth_callback(request: Request):
    """Handle OAuth2 callback from Azure AD."""
    # Get form data or query params
    if request.method == "POST":
        form_data = await request.form()
        state = form_data.get("state")
        code = form_data.get("code")
        error = form_data.get("error")
        error_description = form_data.get("error_description")
    else:
        state = request.query_params.get("state")
        code = request.query_params.get("code")
        error = request.query_params.get("error")
        error_description = request.query_params.get("error_description")
    
    # Validate state
    if state != request.session.get("state"):
        return RedirectResponse(url=f"/auth?error=" + urlencode({"error": "Invalid state. Please try again."}), status_code=302)
    
    # Check for errors
    if error:
        err = error_description or error
        return RedirectResponse(url=f"/auth?" + urlencode({"error": err}), status_code=302)
    
    if not code:
        return RedirectResponse(url=f"/auth?" + urlencode({"error": "Authorization failed. No code received."}), status_code=302)
    
    # Exchange code for token
    cca = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    
    token = cca.acquire_token_by_authorization_code(
        code,
        scopes=[],
        redirect_uri=REDIRECT_URI
    )
    
    if "error" in token:
        msg = token.get("error_description") or token.get("error")
        code_val = token.get("error_codes")
        if code_val:
            msg = f"{msg} (AAD error codes: {code_val})"
        return RedirectResponse(url=f"/auth?" + urlencode({"error": msg}), status_code=302)
    
    # Extract user info from token claims
    claims = token.get("id_token_claims", {}) or {}
    email = claims.get("preferred_username") or claims.get("upn") or claims.get("email")
    
    if not email:
        return RedirectResponse(url=f"/auth?" + urlencode({"error": "No email found in token. Please contact your administrator."}), status_code=302)
    
    # Check domain restriction
    if ALLOWED_DOMAIN and not email.lower().endswith("@" + ALLOWED_DOMAIN):
        request.session.clear()
        return RedirectResponse(url=f"/auth?" + urlencode({"error": f"Access restricted to @{ALLOWED_DOMAIN} accounts only."}), status_code=302)
    
    # Check tenant restriction
    if claims.get("tid") and TENANT_ID and str(claims["tid"]).lower() != TENANT_ID.lower():
        request.session.clear()
        return RedirectResponse(url=f"/auth?" + urlencode({"error": "Wrong tenant. Access denied."}), status_code=302)
    
    # Get or create profile in database
    if not DATABASE_URL:
        return RedirectResponse(url=f"/auth?" + urlencode({"error": "Database not configured"}), status_code=302)
    
    conn_str = _build_connection_string(DATABASE_URL)
    raw_conn = await aioodbc.connect(dsn=conn_str)
    conn = DatabaseWrapper(raw_conn)
    try:
        profile = await get_or_create_sso_profile(
            conn,
            email=email,
            full_name=claims.get("name") or email.split("@")[0],
            azure_id=claims.get("oid") or claims.get("sub")
        )
        
        # Log login activity
        await conn.execute(
            """
            INSERT INTO activity_logs (user_id, action, email, message, created_at)
            VALUES (?, ?, ?, ?, SYSDATETIMEOFFSET())
            """,
            profile["id"], "logged_in", email, f"{email} logged in via Azure SSO"
        )
    finally:
        await conn.close()
    
    # Store profile in session
    request.session["user"] = {
        "id": str(profile["id"]),
        "email": profile["email"],
        "name": profile["full_name"],
        "role": profile.get("role", "viewer"),
        "auth_provider": profile.get("auth_provider", "azure_sso")
    }
    
    # Redirect to app root after successful SSO
    return RedirectResponse(url="/", status_code=302)


@app.get("/logout")
async def logout(request: Request):
    """Clear session and redirect to /auth."""
    request.session.clear()
    
    # Redirect to unified auth page
    return RedirectResponse(url="/auth", status_code=302)


@app.get("/api/v1/user")
async def get_user_info(user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return user


@app.get("/", include_in_schema=False)
async def serve_root(request: Request):
    """Serve the frontend or redirect to login."""
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/auth", status_code=302)
    
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend not built yet. Run Vite build and copy into backend/static.", "user": user}


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str, request: Request):
    """SPA fallback for React Router."""
    if full_path.startswith(("api/", "images/", "static/", "assets/")):
        raise HTTPException(status_code=404, detail="Not Found")
    
    user = request.session.get("user")
    if not user:
        # Allow unauthenticated access to /auth so the SPA can render the auth page
        if full_path == "auth":
            index_file = os.path.join(STATIC_DIR, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
            raise HTTPException(status_code=404, detail="Frontend not built")
        return RedirectResponse(url="/auth", status_code=302)
    
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Frontend not built")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
