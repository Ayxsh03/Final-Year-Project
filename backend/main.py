from fastapi import FastAPI, HTTPException, Query, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
import asyncpg
import json
from datetime import datetime, timedelta
from typing import List, Optional
import os
from pydantic import BaseModel, Field
import uuid

app = FastAPI(title="Person Detection API", version="1.0.0")

IMAGES_DIR = os.getenv("IMAGES_DIR", "absolute/path/to/shared/images") 
os.makedirs(IMAGES_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# CORS middleware
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

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL"
    # "postgresql://postgres:password@postgres:5432/detection_db"
)
API_KEY = os.getenv("API_KEY", "111-1111-1-11-1-11-1-1")

# API Key validation
async def validate_api_key(x_api_key: str | None = Header(default=None)):
    if x_api_key is None or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


import ssl
import certifi  # type: ignore
from urllib.parse import urlparse

def _build_ssl_context_for_db(url: str) -> Optional[ssl.SSLContext]:
    """Create an SSL context for Postgres, optionally disabling verification via env."""
    if not url:
        return None
    disable_verify = os.getenv("DB_SSL_DISABLE_VERIFY", "false").lower() in {"1", "true", "yes"}
    needs_ssl = "supabase.co" in url or "sslmode=require" in url
    if not needs_ssl and not disable_verify:
        return None
    ctx = ssl.create_default_context(cafile=certifi.where())
    if disable_verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    else:
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


async def get_db():
    ssl_ctx = _build_ssl_context_for_db(DATABASE_URL or "")
    conn = await asyncpg.connect(DATABASE_URL, ssl=ssl_ctx)
    try:
        yield conn
    finally:
        await conn.close()


# Pydantic models
# class DetectionEvent(BaseModel):
#     timestamp: datetime
#     person_id: int
#     confidence: float
#     camera_name: str
#     image_path: Optional[str] = None
#     alert_sent: bool = False
#     metadata: dict = Field(default_factory=dict)
    
#     class Config:
#         json_encoders = {
#             datetime: lambda v: v.isoformat()
#         }

from uuid import UUID
from typing import Any, Dict, Optional
from datetime import datetime

class DetectionEvent(BaseModel):
    timestamp: Optional[datetime] = None         # let server default if missing
    person_id: int
    confidence: float
    camera_id: UUID                               # <- IMPORTANT
    camera_name: str
    image_path: Optional[str] = None
    alert_sent: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # optional bbox fields (only if you plan to store them)
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
    
    # Email settings
    notify_email: bool = False
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 465
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    email_to: Optional[str] = None
    
    # WhatsApp settings
    notify_whatsapp: bool = False
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_token: Optional[str] = None
    whatsapp_to: Optional[str] = None
    
    # Telegram settings
    notify_telegram: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # Scheduling settings
    allowed_days: List[str] = Field(default_factory=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    start_time: Optional[str] = None  # HH:MM format
    end_time: Optional[str] = None    # HH:MM format
    timezone: str = "UTC"
    
    # Report settings
    daily_report_enabled: bool = False
    weekly_report_enabled: bool = False
    monthly_report_enabled: bool = False
    
    # VIP and regular customer notification settings
    notify_vip_email: bool = False
    notify_regular_email: bool = False
    notify_attendance_to_branch: bool = False
    
    # Google Places API
    google_places_api_key: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AlertSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    
    # Email settings
    notify_email: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    email_to: Optional[str] = None
    
    # WhatsApp settings
    notify_whatsapp: Optional[bool] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_token: Optional[str] = None
    whatsapp_to: Optional[str] = None
    
    # Telegram settings
    notify_telegram: Optional[bool] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # Scheduling settings
    allowed_days: Optional[List[str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None
    
    # Report settings
    daily_report_enabled: Optional[bool] = None
    weekly_report_enabled: Optional[bool] = None
    monthly_report_enabled: Optional[bool] = None
    
    # VIP and regular customer notification settings
    notify_vip_email: Optional[bool] = None
    notify_regular_email: Optional[bool] = None
    notify_attendance_to_branch: Optional[bool] = None
    
    # Google Places API
    google_places_api_key: Optional[str] = None

class TestAlertRequest(BaseModel):
    alert_type: str  # "email", "whatsapp", "telegram"
    settings: dict  # The relevant settings for testing

# API Routes

@app.get("/api/v1/events/stats", response_model=DashboardStats)
async def get_dashboard_stats(conn: asyncpg.Connection = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        # Calculate comprehensive dashboard stats
        stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE) as total_events,
                (SELECT COUNT(*) FROM camera_devices) as total_cameras,
                (SELECT COUNT(*) FROM camera_devices WHERE status = 'online') as online_cameras,
                (SELECT COUNT(*) FROM camera_devices WHERE status = 'offline') as offline_cameras,
                (SELECT COUNT(DISTINCT camera_id) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE) as active_cameras,
                (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE) as people_detected
        """
        stats = await conn.fetchrow(stats_query)
        
        # Calculate trends
        events_trend_query = """
            SELECT CASE 
                WHEN prev_count = 0 THEN 0
                ELSE ROUND(((curr_count - prev_count)::DECIMAL / prev_count * 100), 1)
            END as events_trend
            FROM (
                SELECT 
                    (SELECT COUNT(*) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE) as curr_count,
                    (SELECT COUNT(*) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE - INTERVAL '1 day') as prev_count
            ) trend_calc
        """
        events_trend = await conn.fetchval(events_trend_query)
        
        devices_trend_query = """
            SELECT CASE 
                WHEN prev_count = 0 THEN 0
                ELSE ROUND(((curr_count - prev_count)::DECIMAL / prev_count * 100), 1)
            END as devices_trend
            FROM (
                SELECT 
                    (SELECT COUNT(*) FROM camera_devices WHERE status = 'online') as curr_count,
                    (SELECT COUNT(*) FROM camera_devices WHERE status = 'online' AND updated_at < NOW() - INTERVAL '1 day') as prev_count
            ) trend_calc
        """
        devices_trend = await conn.fetchval(devices_trend_query)
        
        people_trend_query = """
            SELECT CASE 
                WHEN prev_count = 0 THEN 0
                ELSE ROUND(((curr_count - prev_count)::DECIMAL / prev_count * 100), 1)
            END as people_trend
            FROM (
                SELECT 
                    (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE) as curr_count,
                    (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE - INTERVAL '1 day') as prev_count
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
# async def get_people_count(conn: asyncpg.Connection = Depends(get_db)):
#     """Get people count grouped by camera"""
#     try:
#         query = """
#             SELECT camera_id, camera_name, COUNT(*) AS people_count, metadata
#             FROM detection_events
#             GROUP BY camera_id, camera_name, metadata
#             ORDER BY camera_name
#         """
#         rows = await conn.fetch(query)
#         devices = [
#             {
#                 "camera_id": str(r["camera_id"]),
#                 "camera_name": r["camera_name"],
#                 "count": r["people_count"],
#                 "metadata": (
#                     json.loads(raw_meta)
#                     if isinstance(raw_meta := r["metadata"], str)
#                     else (raw_meta or {})
#                 ),
#             }
#             for r in rows
#         ]
#         return {"devices": devices}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
async def get_people_count(
    search: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db),
):
    """Get people count statistics and device breakdown"""
    try:
        stats_query = """
            SELECT
                COUNT(DISTINCT person_id) FILTER (WHERE DATE(timestamp) = CURRENT_DATE) AS today,
                COUNT(DISTINCT person_id) FILTER (WHERE timestamp >= DATE_TRUNC('week', CURRENT_DATE)) AS week,
                COUNT(DISTINCT person_id) FILTER (WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE)) AS month,
                COUNT(DISTINCT person_id) FILTER (WHERE timestamp >= DATE_TRUNC('year', CURRENT_DATE)) AS year,
                COUNT(DISTINCT person_id) AS all
            FROM detection_events
        """
        stats = await conn.fetchrow(stats_query)

        params: List = []
        where_clause = "WHERE DATE(d.timestamp) = CURRENT_DATE"
        if search:
            where_clause += " AND (d.camera_name ILIKE $1 OR c.location ILIKE $1)"
            params.append(f"%{search}%")

        device_query = f"""
            SELECT
                d.camera_id,
                d.camera_name,
                COALESCE(c.location, '') AS location,
                COUNT(DISTINCT d.person_id) AS count,
                MAX(d.timestamp) AS last_detection,
                (ARRAY_AGG(d.image_path ORDER BY d.timestamp DESC))[1] AS image_path,
                (ARRAY_AGG(d.metadata ORDER BY d.timestamp DESC))[1] AS metadata
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
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get paginated detection events"""
    try:
        offset = (page - 1) * limit
        
        # Base query
        where_clause = "WHERE 1=1"
        params = []
        param_count = 0
        
        if search:
            param_count += 1
            where_clause += f" AND (camera_name ILIKE ${param_count} OR CAST(person_id AS TEXT) ILIKE ${param_count})"
            params.append(f"%{search}%")
        
        # Date filter
        if date_filter and date_filter != "all":
            param_count += 1
            if date_filter == "today":
                where_clause += f" AND DATE(timestamp) = CURRENT_DATE"
            elif date_filter == "week":
                where_clause += f" AND timestamp >= DATE_TRUNC('week', CURRENT_DATE)"
            elif date_filter == "month":
                where_clause += f" AND timestamp >= DATE_TRUNC('month', CURRENT_DATE)"
        
        # Confidence filter
        if confidence_filter and confidence_filter != "all":
            if confidence_filter == "high":
                where_clause += " AND confidence >= 0.8"
            elif confidence_filter == "medium":
                where_clause += " AND confidence >= 0.6 AND confidence < 0.8"
            elif confidence_filter == "low":
                where_clause += " AND confidence < 0.6"
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM detection_events {where_clause}"
        total = await conn.fetchval(count_query, *params)
        
        # Get events
        limit_param = param_count + 1
        offset_param = param_count + 2
        query = f"""
            SELECT id, timestamp, person_id, confidence, camera_name, 
                   image_path, alert_sent, metadata
            FROM detection_events 
            {where_clause}
            ORDER BY timestamp DESC 
            LIMIT ${limit_param} OFFSET ${offset_param}
        """
        params.extend([limit, offset])
        
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
    

from datetime import timezone

def format_alert_message(event: dict, format_type: str = "text") -> dict:
    """Format alert message with better templates"""
    from datetime import datetime
    import pytz
    
    # Parse timestamp if it's a string
    timestamp = event.get('timestamp')
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            timestamp = datetime.now(pytz.UTC)
    elif not timestamp:
        timestamp = datetime.now(pytz.UTC)
    
    # Format timestamp for display
    local_time = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Get confidence as percentage
    confidence = float(event.get('confidence', 0))
    confidence_pct = f"{confidence * 100:.1f}%"
    
    # Determine alert severity based on confidence
    if confidence >= 0.9:
        severity = "HIGH"
        severity_emoji = "🔴"
    elif confidence >= 0.7:
        severity = "MEDIUM"
        severity_emoji = "🟡"
    else:
        severity = "LOW"
        severity_emoji = "🟢"
    
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
    
    return {
        "subject": subject,
        "body": body,
        "severity": severity,
        "confidence_pct": confidence_pct
    }

async def send_alerts_background(event: dict):
    """Send alerts via configured channels from DB settings with enhanced formatting."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import requests as http

    try:
        # Read settings (single row)
        ssl_ctx = _build_ssl_context_for_db(DATABASE_URL or "")
        conn = await asyncpg.connect(DATABASE_URL, ssl=ssl_ctx)
        settings = await conn.fetchrow("""
            SELECT 
                enabled,
                notify_email, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from, email_to,
                notify_whatsapp, whatsapp_phone_number_id, whatsapp_token, whatsapp_to,
                notify_telegram, telegram_bot_token, telegram_chat_id,
                allowed_days, start_time, end_time, timezone
            FROM alert_settings
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        await conn.close()

        if not settings or not settings["enabled"]:
            return

        # Enforce schedule
        try:
            from datetime import datetime as _dt
            import pytz  # type: ignore
            tzname = settings["timezone"] or "UTC"
            tz = pytz.timezone(tzname) if tzname else pytz.UTC
            now_local = _dt.now(tz)
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

        # Format messages
        text_message = format_alert_message(event, "text")
        html_message = format_alert_message(event, "html")

        # EMAIL
        if settings["notify_email"] and settings["smtp_host"] and settings["email_to"]:
            try:
                msg = MIMEMultipart('alternative')
                msg["Subject"] = html_message["subject"]
                msg["From"] = settings["smtp_from"] or settings["smtp_username"]
                msg["To"] = settings["email_to"]
                
                # Add both text and HTML versions
                text_part = MIMEText(text_message["body"], 'plain')
                html_part = MIMEText(html_message["body"], 'html')
                
                msg.attach(text_part)
                msg.attach(html_part)

                with smtplib.SMTP_SSL(settings["smtp_host"], int(settings["smtp_port"] or 465)) as server:
                    if settings["smtp_username"] and settings["smtp_password"]:
                        server.login(settings["smtp_username"], settings["smtp_password"]) 
                    server.sendmail(msg["From"], [settings["email_to"]], msg.as_string())
                    
                print(f"Email alert sent successfully for event {event.get('id')}")
            except Exception as e:
                print(f"Email send failed: {e}")

        # WHATSAPP CLOUD API
        if settings["notify_whatsapp"] and settings["whatsapp_phone_number_id"] and settings["whatsapp_token"] and settings["whatsapp_to"]:
            try:
                url = f"https://graph.facebook.com/v17.0/{settings['whatsapp_phone_number_id']}/messages"
                headers = {
                    "Authorization": f"Bearer {settings['whatsapp_token']}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": settings["whatsapp_to"],
                    "type": "text",
                    "text": {"body": text_message["body"]}
                }
                response = http.post(url, headers=headers, json=payload, timeout=10)
                
                if response.status_code == 200:
                    print(f"WhatsApp alert sent successfully for event {event.get('id')}")
                else:
                    print(f"WhatsApp send failed with status {response.status_code}: {response.text}")
            except Exception as e:
                print(f"WhatsApp send failed: {e}")

        # TELEGRAM
        if settings["notify_telegram"] and settings["telegram_bot_token"] and settings["telegram_chat_id"]:
            try:
                url = f"https://api.telegram.org/bot{settings['telegram_bot_token']}/sendMessage"
                payload = {
                    "chat_id": settings["telegram_chat_id"], 
                    "text": text_message["body"],
                    "parse_mode": "HTML"  # Enable HTML formatting for Telegram
                }
                response = http.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    print(f"Telegram alert sent successfully for event {event.get('id')}")
                else:
                    print(f"Telegram send failed with status {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Telegram send failed: {e}")
                
    except Exception as e:
        print(f"Alert background error: {e}")


@app.post("/api/v1/events")
async def create_detection_event(
    event: DetectionEvent,
    conn: asyncpg.Connection = Depends(get_db),
    api_key_valid: bool = Depends(validate_api_key),
    background: BackgroundTasks = None
):
    """Create a new detection event"""
    try:
        # Prepare metadata as a JSON string
        metadata_json = "{}"
        if event.metadata:
            ts = event.timestamp or datetime.now(timezone.utc)
            try:
                metadata_json = json.dumps(event.metadata or {})
            except (TypeError, ValueError) as e:
                print(f"Warning: Could not serialize metadata: {e}")
                metadata_json = "{}"
        
        # Insert query - explicitly cast metadata to JSONB
        # query = """
        #     INSERT INTO detection_events 
        #     (timestamp, person_id, confidence, camera_name, image_path, alert_sent, metadata)
        #     VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
        #     RETURNING id, timestamp, person_id, confidence, camera_name, image_path, alert_sent, metadata
        # """
        query = """
            INSERT INTO detection_events 
                (timestamp, person_id, confidence, camera_id, camera_name, image_path, alert_sent, metadata,
                bbox_x1, bbox_y1, bbox_x2, bbox_y2)
            VALUES
                ($1,        $2,        $3,        $4,        $5,         $6,         $7,         $8::jsonb,
                $9,        $10,       $11,       $12)
            RETURNING id, timestamp, person_id, confidence, camera_id, camera_name, image_path, alert_sent, metadata,
                    bbox_x1, bbox_y1, bbox_x2, bbox_y2
        """
        
        # row = await conn.fetchrow(
        #     query,
        #     event.timestamp,
        #     event.person_id,
        #     event.confidence,
        #     event.camera_name,
        #     event.image_path,
        #     event.alert_sent,
        #     metadata_json
        # )
        row = await conn.fetchrow(
            query,
            ts,
            event.person_id,
            event.confidence,
            event.camera_id,           # <-- now required
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
        
        # Convert row to dict
        # result = {
        #     'id': str(row['id']),
        #     'timestamp': row['timestamp'].isoformat(),
        #     'person_id': row['person_id'],
        #     'confidence': float(row['confidence']),
        #     'camera_name': row['camera_name'],
        #     'image_path': row['image_path'],
        #     'alert_sent': row['alert_sent'],
        #     'metadata': row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata']) if row['metadata'] else {}
        # }
        result = {
            "id": str(row["id"]),
            "timestamp": row["timestamp"].isoformat(),
            "person_id": row["person_id"],
            "confidence": float(row["confidence"]),
            "camera_id": str(row["camera_id"]),
            "camera_name": row["camera_name"],
            "image_path": row["image_path"],
            "alert_sent": row["alert_sent"],
            "metadata": row["metadata"] or {},
            "bbox_x1": float(row["bbox_x1"]) if row["bbox_x1"] is not None else None,
            "bbox_y1": float(row["bbox_y1"]) if row["bbox_y1"] is not None else None,
            "bbox_x2": float(row["bbox_x2"]) if row["bbox_x2"] is not None else None,
            "bbox_y2": float(row["bbox_y2"]) if row["bbox_y2"] is not None else None,
        }
        
        # Fire-and-forget alerts
        if background is not None:
            background.add_task(send_alerts_background, result)
        else:
            # Fallback if background not injected
            import asyncio as _asyncio
            _asyncio.create_task(send_alerts_background(result))

        return result
        
    except asyncpg.PostgresError as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/cameras")
async def get_cameras(conn: asyncpg.Connection = Depends(get_db)):
    """Get all cameras"""
    try:
        query = """
            SELECT
                id,
                name,
                rtsp_url,
                status,
                location
            FROM camera_devices
            ORDER BY (status = 'online') DESC, name
        """
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/cameras", status_code=201)
async def create_camera(camera: CameraCreate, conn: asyncpg.Connection = Depends(get_db), api_key_valid: bool = Depends(validate_api_key)):
    """Create a camera device (ingestion point)."""
    try:
        # prevent duplicate by name
        exists = await conn.fetchval("SELECT 1 FROM camera_devices WHERE name = $1", camera.name)
        if exists:
            raise HTTPException(status_code=409, detail="Camera with this name already exists")

        row = await conn.fetchrow(
            """
            INSERT INTO camera_devices (name, rtsp_url, status, location)
            VALUES ($1, $2, 'offline', $3)
            RETURNING id, name, rtsp_url, status, location, created_at, updated_at
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
    conn: asyncpg.Connection = Depends(get_db), 
    api_key_valid: bool = Depends(validate_api_key)
):
    """Update camera status (online/offline)."""
    try:
        status = status_data.get("status")
        if status not in ["online", "offline"]:
            raise HTTPException(status_code=400, detail="Status must be 'online' or 'offline'")
        
        # Check if camera exists
        exists = await conn.fetchval("SELECT 1 FROM camera_devices WHERE id = $1", camera_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Update status
        await conn.execute(
            "UPDATE camera_devices SET status = $1, updated_at = now() WHERE id = $2",
            status, camera_id
        )
        
        return {"message": f"Camera status updated to {status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/api/v1/analytics/hourly")
async def get_hourly_data(conn: asyncpg.Connection = Depends(get_db)):
    """Get hourly event data for charts"""
    try:
        query = """
            SELECT 
                TO_CHAR(DATE_TRUNC('hour', timestamp), 'HH24:MI') as hour,
                COUNT(*) as events,
                COUNT(DISTINCT person_id) as footfall,
                0 as vehicles
            FROM detection_events 
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY DATE_TRUNC('hour', timestamp)
        """
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/trends")
async def get_trends(conn: asyncpg.Connection = Depends(get_db)):
    """Get trend data"""
    try:
        result = await conn.fetchval("SELECT get_dashboard_stats()")
        stats = json.loads(result)
        return {
            "events_trend": stats.get("events_trend", 0),
            "devices_trend": stats.get("devices_trend", 0),
            "people_trend": stats.get("people_trend", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/cameras/{camera_id}/status")
async def update_camera_status(
    camera_id: str,
    status_data: dict,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update camera status"""
    try:
        query = """
            UPDATE camera_devices 
            SET status = $1, last_heartbeat = NOW(), updated_at = NOW()
            WHERE id = $2
        """
        await conn.execute(query, status_data["status"], camera_id)
        return {"message": "Status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai-intelligence")
async def get_ai_intelligence_metrics(conn: asyncpg.Connection = Depends(get_db)):
    """Get AI Intelligence metrics and performance data"""
    try:
        # Calculate detection accuracy based on confidence scores
        confidence_stats = await conn.fetchrow("""
            SELECT 
                AVG(confidence) as avg_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence,
                COUNT(*) as total_detections,
                COUNT(*) FILTER (WHERE confidence >= 0.8) as high_confidence_detections,
                COUNT(*) FILTER (WHERE confidence >= 0.6 AND confidence < 0.8) as medium_confidence_detections,
                COUNT(*) FILTER (WHERE confidence < 0.6) as low_confidence_detections
            FROM detection_events 
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
        """)
        
        # Calculate processing metrics (simplified - based on detection frequency)
        recent_detections = await conn.fetchval("""
            SELECT COUNT(*) FROM detection_events 
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
        """)
        
        # Get camera performance data
        camera_stats = await conn.fetch("""
            SELECT 
                camera_name,
                COUNT(*) as detection_count,
                AVG(confidence) as avg_confidence,
                MAX(timestamp) as last_detection
            FROM detection_events 
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY camera_name
            ORDER BY detection_count DESC
        """)
        
        # Calculate model performance metrics
        total_detections = confidence_stats['total_detections'] or 0
        high_conf_detections = confidence_stats['high_confidence_detections'] or 0
        medium_conf_detections = confidence_stats['medium_confidence_detections'] or 0
        low_conf_detections = confidence_stats['low_confidence_detections'] or 0
        
        # Calculate accuracy percentages
        person_detection_accuracy = (high_conf_detections / max(total_detections, 1)) * 100
        object_classification_accuracy = ((high_conf_detections + medium_conf_detections) / max(total_detections, 1)) * 100
        behavior_analysis_accuracy = (high_conf_detections / max(total_detections, 1)) * 100
        
        # Estimate processing speed (simplified calculation)
        estimated_processing_speed = 50 if recent_detections > 10 else 30  # ms
        
        return {
            "detection_accuracy": round(confidence_stats['avg_confidence'] * 100, 1) if confidence_stats['avg_confidence'] else 0,
            "processing_speed": estimated_processing_speed,
            "active_models": 1,  # YOLOv8 person detection
            "model_performance": {
                "person_detection": round(person_detection_accuracy, 1),
                "object_classification": round(object_classification_accuracy, 1),
                "behavior_analysis": round(behavior_analysis_accuracy, 1)
            },
            "confidence_distribution": {
                "high": high_conf_detections,
                "medium": medium_conf_detections,
                "low": low_conf_detections
            },
            "camera_performance": [
                {
                    "camera_name": row['camera_name'],
                    "detection_count": row['detection_count'],
                    "avg_confidence": round(float(row['avg_confidence']) * 100, 1),
                    "last_detection": row['last_detection'].isoformat() if row['last_detection'] else None
                }
                for row in camera_stats
            ],
            "recent_activities": [
                {
                    "type": "detection",
                    "message": f"Processed {recent_detections} detections in the last hour",
                    "timestamp": "1h ago"
                },
                {
                    "type": "model",
                    "message": "YOLOv8 model running optimally",
                    "timestamp": "2h ago"
                },
                {
                    "type": "performance",
                    "message": f"Average confidence: {round(confidence_stats['avg_confidence'] * 100, 1)}%",
                    "timestamp": "3h ago"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import cv2  # type: ignore
import numpy as np  # type: ignore


@app.get("/api/v1/stream/demo")
async def demo_stream():
    """Demo stream endpoint that generates a simple pattern for testing."""
    import time
    
    def demo_frame_generator():
        try:
            frame_count = 0
            boundary = "frame"
            
            while True:
                # Generate a simple test pattern
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                
                # Add some moving elements for visual feedback
                t = int(time.time() * 2) % 640
                cv2.circle(img, (t, 240), 30, (0, 255, 0), -1)
                cv2.circle(img, (640 - t, 240), 20, (255, 0, 0), -1)
                
                # Add frame counter
                cv2.putText(img, f"Frame: {frame_count}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(img, f"Demo Stream", (10, 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Encode to JPEG
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
                time.sleep(1/15)  # ~15 FPS
                
        except Exception as e:
            print(f"Demo stream error: {e}")
    
    return StreamingResponse(
        demo_frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/v1/stream/{camera_id}")
async def stream_camera(camera_id: str, conn: asyncpg.Connection = Depends(get_db)):
    """Stream RTSP camera as MJPEG for simple live preview.
    Note: This is best-effort and not suitable for large-scale production.
    """
    try:
        row = await conn.fetchrow(
            "SELECT rtsp_url, status FROM camera_devices WHERE id = $1",
            camera_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Camera not found")
        rtsp_url = row["rtsp_url"]
        
        print(f"Attempting to connect to camera {camera_id} at {rtsp_url}")

        # OpenCV VideoCapture is blocking/sync; wrap open in threadpool for startup
        def open_capture(url: str):
            import socket
            from urllib.parse import urlparse
            
            # Basic network connectivity check
            try:
                parsed = urlparse(url)
                host = parsed.hostname
                port = parsed.port or 554  # Default RTSP port
                
                print(f"Testing network connectivity to {host}:{port}")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result != 0:
                    print(f"Network connectivity failed to {host}:{port} - error code: {result}")
                    return None
                else:
                    print(f"Network connectivity OK to {host}:{port}")
                    
            except Exception as e:
                print(f"Network test error: {e}")
                return None
            
            print(f"Opening OpenCV VideoCapture for {url}")
            cap = cv2.VideoCapture(url)
            
            # Give it a moment to initialize
            import time
            time.sleep(2)
            
            if cap.isOpened():
                print(f"Successfully opened camera stream")
                # Try to read one frame to verify it's working
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
                    # Optionally resize to reduce bandwidth
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
async def test_camera_connection(camera_id: str, conn: asyncpg.Connection = Depends(get_db)):
    """Test camera connectivity without streaming."""
    try:
        row = await conn.fetchrow(
            "SELECT rtsp_url, status FROM camera_devices WHERE id = $1",
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
                # Determine port based on scheme
                if parsed.scheme == 'http':
                    port = parsed.port or 80
                elif parsed.scheme == 'https':
                    port = parsed.port or 443
                else:  # rtsp or other
                    port = parsed.port or 554
                
                # Test network connectivity
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                conn_result = sock.connect_ex((host, port))
                sock.close()
                
                result["network_reachable"] = (conn_result == 0)
                
                if result["network_reachable"]:
                    # Test RTSP with OpenCV
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
async def update_camera_rtsp(camera_id: str, rtsp_data: dict, conn: asyncpg.Connection = Depends(get_db), api_key_valid: bool = Depends(validate_api_key)):
    """Update camera RTSP URL for testing."""
    try:
        rtsp_url = rtsp_data.get("rtsp_url")
        if not rtsp_url:
            raise HTTPException(status_code=400, detail="rtsp_url is required")
            
        # Check if camera exists
        exists = await conn.fetchval("SELECT 1 FROM camera_devices WHERE id = $1", camera_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Update RTSP URL
        await conn.execute(
            "UPDATE camera_devices SET rtsp_url = $1, updated_at = now() WHERE id = $2",
            rtsp_url, camera_id
        )
        
        return {"message": "RTSP URL updated successfully", "rtsp_url": rtsp_url}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/test-cameras")
async def get_test_camera_urls():
    """Get list of public test camera URLs for testing."""
    return {
        "public_test_streams": [
            {
                "name": "Big Buck Bunny (MP4 over HTTP)",
                "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "type": "HTTP MP4",
                "note": "This is an MP4 file, not RTSP, but OpenCV can handle it"
            },
            {
                "name": "Localhost Test Stream",
                "url": "rtsp://localhost:8554/test",
                "type": "RTSP",
                "note": "Would work if you had a local RTSP server running"
            }
        ],
        "instructions": {
            "using_phone_as_camera": {
                "apps": ["IP Webcam", "DroidCam", "EpocCam"],
                "typical_url_format": "http://YOUR_PHONE_IP:PORT/video",
                "example": "http://192.168.1.100:8080/video"
            },
            "using_obs_virtual_camera": {
                "note": "OBS can create virtual cameras, but RTSP output requires plugins"
            },
            "using_vlc_streaming": {
                "note": "VLC can re-stream files as RTSP",
                "command_example": "vlc input.mp4 --intf dummy --sout '#rtp{sdp=rtsp://:8554/test}'"
            }
        }
    }


# Alert Settings Endpoints

@app.get("/api/v1/alert-settings", response_model=AlertSettings)
async def get_alert_settings(conn: asyncpg.Connection = Depends(get_db)):
    """Get current alert settings"""
    try:
        query = """
            SELECT id, enabled, notify_email, smtp_host, smtp_port, smtp_username, 
                   smtp_password, smtp_from, email_to, notify_whatsapp, whatsapp_phone_number_id,
                   whatsapp_token, whatsapp_to, notify_telegram, telegram_bot_token, 
                   telegram_chat_id, allowed_days, start_time, end_time, timezone,
                   daily_report_enabled, weekly_report_enabled, monthly_report_enabled,
                   notify_vip_email, notify_regular_email, notify_attendance_to_branch,
                   google_places_api_key, created_at, updated_at
            FROM alert_settings 
            ORDER BY updated_at DESC 
            LIMIT 1
        """
        row = await conn.fetchrow(query)
        
        if not row:
            # Return default settings if none exist
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
            allowed_days=list(row["allowed_days"]) if row["allowed_days"] else ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
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
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update alert settings (upsert)"""
    try:
        # Check if settings exist
        existing = await conn.fetchrow(
            "SELECT id FROM alert_settings ORDER BY updated_at DESC LIMIT 1"
        )
        
        if existing:
            # Update existing settings
            update_fields = []
            params = []
            param_count = 0
            
            for field, value in settings.model_dump(exclude_unset=True).items():
                if field in ['created_at', 'id']:  # Skip these fields
                    continue
                param_count += 1
                update_fields.append(f"{field} = ${param_count}")
                if field == 'allowed_days' and isinstance(value, list):
                    params.append(value)  # PostgreSQL handles list directly
                else:
                    params.append(value)
            
            if update_fields:
                param_count += 1
                params.append(existing["id"])
                query = f"""
                    UPDATE alert_settings 
                    SET {', '.join(update_fields)}, updated_at = NOW()
                    WHERE id = ${param_count}
                    RETURNING *
                """
                row = await conn.fetchrow(query, *params)
        else:
            # Insert new settings
            data = settings.model_dump(exclude_unset=True)
            if 'allowed_days' not in data:
                data['allowed_days'] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            columns = list(data.keys())
            values = list(data.values())
            placeholders = [f"${i+1}" for i in range(len(values))]
            
            query = f"""
                INSERT INTO alert_settings ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
            """
            row = await conn.fetchrow(query, *values)
        
        if not row:
            raise HTTPException(status_code=500, detail="Failed to update settings")
            
        # Return updated settings
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
            allowed_days=list(row["allowed_days"]) if row["allowed_days"] else ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
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
    """Test alert configuration before saving"""
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
    """Test email configuration"""
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
        
        # Test email
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
    """Test WhatsApp configuration"""
    try:
        import requests as http
        
        phone_number_id = settings.get('whatsapp_phone_number_id')
        token = settings.get('whatsapp_token')
        to_number = settings.get('whatsapp_to')
        
        if not all([phone_number_id, token, to_number]):
            return {"success": False, "error": "Missing required WhatsApp settings"}
        
        url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
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
    """Test Telegram configuration"""
    try:
        import requests as http
        
        bot_token = settings.get('telegram_bot_token')
        chat_id = settings.get('telegram_chat_id')
        
        if not all([bot_token, chat_id]):
            return {"success": False, "error": "Missing required Telegram settings"}
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": "This is a test message from your WebDash Person Detection System."
        }
        
        response = http.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "message": "Test Telegram message sent successfully"}
        else:
            return {"success": False, "error": f"Telegram API error: {response.text}"}
    except Exception as e:
        return {"success": False, "error": f"Telegram test failed: {str(e)}"}

# Scheduled Reports Functionality

async def generate_detection_report(period: str, conn: asyncpg.Connection) -> dict:
    """Generate detection report for specified period"""
    try:
        # Determine date range based on period
        if period == "daily":
            date_filter = "DATE(timestamp) = CURRENT_DATE"
            period_name = "Today"
        elif period == "weekly":
            date_filter = "timestamp >= DATE_TRUNC('week', CURRENT_DATE)"
            period_name = "This Week"
        elif period == "monthly":
            date_filter = "timestamp >= DATE_TRUNC('month', CURRENT_DATE)"
            period_name = "This Month"
        else:
            raise ValueError("Invalid period")
        
        # Get summary statistics
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
        
        # Get camera breakdown
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
        
        # Get hourly breakdown for charts
        hourly_query = f"""
            SELECT 
                EXTRACT(HOUR FROM timestamp) as hour,
                COUNT(*) as detections,
                COUNT(DISTINCT person_id) as unique_people
            FROM detection_events 
            WHERE {date_filter}
            GROUP BY EXTRACT(HOUR FROM timestamp)
            ORDER BY hour
        """
        hourly_data = await conn.fetch(hourly_query)
        
        # Get confidence distribution
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
            GROUP BY confidence_range
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
                {
                    "range": row["confidence_range"],
                    "count": row["count"]
                }
                for row in confidence_dist
            ]
        }
    except Exception as e:
        raise Exception(f"Failed to generate report: {str(e)}")

def format_report_email(report_data: dict) -> str:
    """Format detection report as HTML email"""
    period = report_data["period"]
    summary = report_data["summary"]
    cameras = report_data["camera_breakdown"]
    hourly = report_data["hourly_breakdown"]
    confidence = report_data["confidence_distribution"]
    
    # Create camera table rows
    camera_rows = ""
    for cam in cameras[:10]:  # Limit to top 10 cameras
        camera_rows += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{cam['camera_name']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{cam['location']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{cam['detection_count']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{cam['unique_people']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{cam['avg_confidence']}%</td>
        </tr>
        """
    
    # Create confidence distribution bars
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
                <div style="background-color: #2196f3; height: 20px; width: {percentage}%; border-radius: 10px;"></div>
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
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 300;">📊 Detection Report</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">{period}</p>
                <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8;">Generated: {report_data['generated_at'][:19]}</p>
            </div>
            
            <!-- Summary Cards -->
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
                
                <!-- Camera Breakdown -->
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
                
                <!-- Confidence Distribution -->
                <div style="margin-bottom: 30px;">
                    <h2 style="color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px;">🎯 Detection Confidence</h2>
                    <div style="margin-top: 15px;">
                        {confidence_bars}
                    </div>
                </div>
                
                <!-- Footer -->
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
async def get_detection_report(period: str, conn: asyncpg.Connection = Depends(get_db)):
    """Generate and return detection report for specified period"""
    if period not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid period. Must be 'daily', 'weekly', or 'monthly'")
    
    try:
        report_data = await generate_detection_report(period, conn)
        return report_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reports/{period}/send")
async def send_detection_report(period: str, conn: asyncpg.Connection = Depends(get_db)):
    """Generate and send detection report via email"""
    if period not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid period. Must be 'daily', 'weekly', or 'monthly'")
    
    try:
        # Get alert settings
        settings = await conn.fetchrow("""
            SELECT notify_email, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from, email_to
            FROM alert_settings
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        
        if not settings or not settings["notify_email"] or not settings["email_to"]:
            raise HTTPException(status_code=400, detail="Email notifications not configured")
        
        # Generate report
        report_data = await generate_detection_report(period, conn)
        
        # Format and send email
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart('alternative')
        msg["Subject"] = f"📊 WebDash Detection Report - {report_data['period']}"
        msg["From"] = settings["smtp_from"] or settings["smtp_username"]
        msg["To"] = settings["email_to"]
        
        # Create HTML email
        html_content = format_report_email(report_data)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP_SSL(settings["smtp_host"], int(settings["smtp_port"] or 465)) as server:
            if settings["smtp_username"] and settings["smtp_password"]:
                server.login(settings["smtp_username"], settings["smtp_password"])
            server.sendmail(msg["From"], [settings["email_to"]], msg.as_string())
        
        return {"message": f"Report sent successfully to {settings['email_to']}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send report: {str(e)}")

# Scheduled task runner (this would typically be called by a CRON job or task scheduler)
@app.post("/api/v1/reports/scheduled/run")
async def run_scheduled_reports(conn: asyncpg.Connection = Depends(get_db)):
    """Run scheduled reports based on settings"""
    try:
        settings = await conn.fetchrow("""
            SELECT daily_report_enabled, weekly_report_enabled, monthly_report_enabled,
                   notify_email, smtp_host, smtp_port, smtp_username, smtp_password, smtp_from, email_to
            FROM alert_settings
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        
        if not settings or not settings["notify_email"]:
            return {"message": "Email reports not configured"}
        
        sent_reports = []
        
        # Check which reports should be sent (this is a simplified version)
        # In production, you'd want more sophisticated scheduling logic
        from datetime import datetime
        now = datetime.now()
        
        if settings["daily_report_enabled"]:
            try:
                await send_detection_report("daily", conn)
                sent_reports.append("daily")
            except Exception as e:
                print(f"Failed to send daily report: {e}")
        
        # Weekly reports on Mondays
        if settings["weekly_report_enabled"] and now.weekday() == 0:
            try:
                await send_detection_report("weekly", conn)
                sent_reports.append("weekly")
            except Exception as e:
                print(f"Failed to send weekly report: {e}")
        
        # Monthly reports on the 1st of the month
        if settings["monthly_report_enabled"] and now.day == 1:
            try:
                await send_detection_report("monthly", conn)
                sent_reports.append("monthly")
            except Exception as e:
                print(f"Failed to send monthly report: {e}")
        
        return {"message": f"Scheduled reports processed", "sent_reports": sent_reports}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)