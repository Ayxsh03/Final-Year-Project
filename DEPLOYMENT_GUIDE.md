# FpelAICCTV - Linux Server Deployment Guide

Complete guide for deploying the Person Detection system on Linux servers (Azure, Docker, or bare metal).

## 📋 Prerequisites

- **Python 3.12** (critical: all configs now aligned to 3.12)
- **PostgreSQL 15+** (Supabase or self-hosted)
- **Node.js 20+** (for frontend build)
- **Docker & Docker Compose** (optional, recommended)

## 🚀 Deployment Options

### Option 1: Azure App Service (Recommended for Production)

#### Step 1: Configure Azure App Service

1. **Create App Service**:
   - Runtime: Python 3.12
   - OS: Linux
   - Plan: Premium PV3 (for multi-camera workloads)

2. **Set Application Settings** (Configuration → Application settings):
   ```bash
   DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
   API_KEY=your-secure-api-key-here
   ALLOWED_ORIGINS=https://your-domain.azurewebsites.net
   IMAGES_DIR=/home/images
   CONFIDENCE_THRESHOLD=0.5
   DETECTION_WIDTH=640
   DETECTION_HEIGHT=480
   FRAME_STRIDE=5
   ```

3. **Set Startup Command**:
   ```
   bash startup.sh
   ```

#### Step 2: Deploy via GitHub Actions

1. **Add Repository Secrets**:
   - Go to GitHub repo → Settings → Secrets and variables → Actions
   - Add: `AZURE_PUBLISH_PROFILE` (download from Azure Portal)

2. **Push to main branch**:
   ```bash
   git add .
   git commit -m "Deploy to Azure"
   git push origin main
   ```

3. **Monitor deployment**:
   - GitHub Actions tab shows build/deploy progress
   - Azure Portal → Log stream shows runtime logs

#### Step 3: Verify Deployment

1. Check logs for:
   ```
   ✓ backend/main.py found
   ✓ requirements.txt found
   Ensuring OpenCV headless is installed...
   OpenCV packages: opencv-python-headless
   Starting FastAPI application...
   ```

2. Test endpoints:
   ```bash
   curl https://your-app.azurewebsites.net/api/v1/health
   ```

### Option 2: Docker Compose (Local/Self-Hosted)

#### Step 1: Configure Environment

```bash
# Copy and edit environment variables
cp .env.example .env
nano .env
```

Update `.env` with your values:
```env
DATABASE_URL=postgresql://postgres:password@postgres:5432/detection_db
API_KEY=your-api-key
IMAGES_DIR=/app/images
```

#### Step 2: Build Frontend

```bash
npm install
npm run build
```

Frontend assets will be built into `dist/` and GitHub Actions copies them to `backend/static/` during CI. For local development:

```bash
mkdir -p backend/static
cp -r dist/* backend/static/
```

#### Step 3: Start Services

```bash
# Start backend + Postgres
docker-compose up -d

# View logs
docker-compose logs -f api
```

#### Step 4: Initialize Database

```bash
# Run schema
docker exec -i $(docker ps -q -f name=postgres) psql -U postgres -d detection_db < database/schema.sql
```

#### Step 5: Access Application

- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/api/v1/health

### Option 3: Bare Metal Linux Server

#### Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.12
sudo apt install -y python3.12 python3.12-venv python3-pip

# Install system dependencies for headless OpenCV
sudo apt install -y libglib2.0-0 libgomp1

# Install PostgreSQL (optional, or use Supabase)
sudo apt install -y postgresql postgresql-contrib
```

#### Step 2: Clone and Setup

```bash
# Clone repository
git clone https://github.com/Ayxsh03/Final-Year-Project.git
cd Final-Year-Project

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Build Frontend

```bash
# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Build frontend
npm install
npm run build

# Copy to backend/static
mkdir -p backend/static
cp -r dist/* backend/static/
```

#### Step 4: Configure Environment

```bash
cp .env.example .env
nano .env
```

Set your values:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/detection_db
API_KEY=your-secure-key
IMAGES_DIR=/var/www/images
ALLOWED_ORIGINS=http://your-server-ip:8000
```

#### Step 5: Create Systemd Service

```bash
sudo nano /etc/systemd/system/fpelaicctv.service
```

```ini
[Unit]
Description=FpelAICCTV Person Detection API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Final-Year-Project
EnvironmentFile=/path/to/Final-Year-Project/.env
ExecStart=/path/to/Final-Year-Project/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable fpelaicctv
sudo systemctl start fpelaicctv
sudo systemctl status fpelaicctv
```

#### Step 6: Setup Nginx Reverse Proxy (Optional)

```bash
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/fpelaicctv
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /images/ {
        alias /var/www/images/;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/fpelaicctv /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔍 Troubleshooting

### Issue: `ImportError: libGL.so.1: cannot open shared object file`

**Cause**: Using `opencv-python` instead of `opencv-python-headless`

**Fix**: 
```bash
pip uninstall -y opencv-python opencv-contrib-python
pip install opencv-python-headless==4.10.0.84
```

This is already enforced in `startup.sh` for Azure deployments.

### Issue: `backend/static not found - frontend may not load`

**Cause**: Frontend not built or copied to `backend/static/`

**Fix**:
```bash
npm run build
mkdir -p backend/static
cp -r dist/* backend/static/
```

GitHub Actions handles this automatically during CI/CD.

### Issue: Database connection fails

**Fix**:
1. Check `DATABASE_URL` in environment
2. For Supabase, ensure `?sslmode=require` is appended
3. Verify database allows connections from your server IP
4. Check firewall rules (port 5432)

### Issue: Docker build fails with NumPy errors

**Cause**: NumPy version mismatch with Python 3.12

**Fix**: Already resolved - all `requirements.txt` files now use `numpy>=1.26.4,<2.0`

## 📊 Monitoring & Logs

### Azure App Service
```bash
# Stream logs
az webapp log tail --name FpelAICCTV --resource-group your-rg

# Or use Azure Portal → Log stream
```

### Docker
```bash
docker-compose logs -f api
```

### Systemd Service
```bash
sudo journalctl -u fpelaicctv -f
```

## 🔐 Security Checklist

- [ ] Change default `API_KEY` in production
- [ ] Use strong database passwords
- [ ] Enable HTTPS (use nginx + Let's Encrypt)
- [ ] Restrict `ALLOWED_ORIGINS` to your domain only
- [ ] Secure RTSP camera credentials
- [ ] Set firewall rules (UFW, Azure NSG)
- [ ] Regularly update dependencies: `pip list --outdated`

## 📁 Directory Structure

```
Final-Year-Project/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Docker config (Python 3.12)
│   ├── static/             # Frontend assets (built by CI/CD)
│   ├── images/             # Detection snapshots
│   └── logs/               # Application logs
├── detection_integration/
│   └── multi_camera_detector.py  # YOLO detection worker
├── database/
│   └── schema.sql          # PostgreSQL schema
├── App_Data/
│   └── jobs/continuous/detection/
│       └── run.sh          # Azure WebJob for detection
├── dist/                   # Vite build output (gitignored)
├── src/                    # React frontend source
├── requirements.txt        # Root Python deps (matches backend/)
├── runtime.txt             # Python 3.12
├── startup.sh              # Azure startup script
├── docker-compose.yml      # Docker orchestration
├── .env.example            # Environment template
└── yolov8n.pt             # YOLO model weights
```

## 🎯 Next Steps

1. **Test Detection**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/cameras \
     -H "X-API-Key: your-key" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Camera",
       "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream",
       "location": "Office"
     }'
   ```

2. **Run Detection Worker**:
   - Azure: Configured as WebJob in `App_Data/jobs/continuous/detection/`
   - Docker: Run separately: `python detection_integration/multi_camera_detector.py`
   - Systemd: Create additional service for detector

3. **Monitor Performance**:
   - Check CPU/RAM usage
   - Adjust `FRAME_STRIDE` and `DETECTION_WIDTH` for performance
   - Scale vertically (larger VM) or horizontally (separate detection workers)

## 🆘 Support

- Check logs first (search for ERROR/WARNING)
- Review environment variables (`.env` or Azure App Settings)
- Verify database connectivity
- Ensure all ports are open (8000, 5432)

---

**All configurations are now aligned for Python 3.12 and Linux compatibility!** 🚀
