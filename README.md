# FpelAICCTV - Person Detection & Tracking System

AI-powered person detection system with multi-camera RTSP support, real-time tracking, and alert management. Built with FastAPI (Python) + React (TypeScript).

## 🎯 Features

- **Multi-Camera Support**: Monitor multiple RTSP cameras simultaneously
- **Real-Time Detection**: YOLOv8-powered person detection with tracking
- **Web Dashboard**: Live camera feeds, detection events, analytics
- **Alert System**: Configurable alerts for detection events
- **RESTful API**: Complete FastAPI backend with Swagger docs
- **PostgreSQL Database**: Supabase-compatible schema

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend │ (TypeScript + Vite)
│   (Port 8000)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Backend│ (Python 3.12 + FastAPI)
│   (Port 8000)   │
└────────┬────────┘
         │
    ┌────┴────┬──────────────┐
    ▼         ▼              ▼
┌──────┐  ┌──────────┐  ┌──────────┐
│ RTSP │  │PostgreSQL│  │Detection │
│Camera│  │ Database │  │  Worker  │
└──────┘  └──────────┘  └──────────┘
```

## 🚀 Quick Start

### Option 1: Automated Local Setup (Recommended)

```bash
# Clone repository
git clone https://github.com/Ayxsh03/Final-Year-Project.git
cd Final-Year-Project

# Run automated setup
./setup-local.sh

# Configure environment
cp .env.example .env
nano .env  # Edit DATABASE_URL, API_KEY, etc.

# Start application
source venv/bin/activate
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Access at: http://localhost:8000

### Option 2: Docker Compose

```bash
# Configure environment
cp .env.example .env
nano .env

# Build frontend
npm install
npm run build
mkdir -p backend/static
cp -r dist/* backend/static/

# Start services
docker-compose up -d

# Initialize database
docker exec -i $(docker ps -q -f name=postgres) psql -U postgres -d detection_db < database/schema.sql
```

Access at: http://localhost:8000

### Option 3: Azure App Service

1. Configure Azure App Service (Python 3.12, Linux)
2. Set Application Settings (see `.env.example`)
3. Set startup command: `bash startup.sh`
4. Add GitHub secret: `AZURE_PUBLISH_PROFILE`
5. Push to main branch (GitHub Actions handles deployment)

See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for detailed instructions.

## 📋 Requirements

- **Python**: 3.12 (critical - all configs aligned)
- **Node.js**: 20+
- **PostgreSQL**: 15+ (or Supabase)
- **System**: Linux/macOS/Windows (Docker recommended for Windows)

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **asyncpg** - Async PostgreSQL driver
- **OpenCV** (headless) - Video processing
- **Ultralytics YOLOv8** - Object detection
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **shadcn/ui** - Component library

### Database
- **PostgreSQL 15+** - Relational database
- **Supabase** - Managed PostgreSQL (optional)

### Deployment
- **Azure App Service** - Cloud hosting
- **Docker** - Containerization
- **GitHub Actions** - CI/CD

## 📁 Project Structure

```
Final-Year-Project/
├── backend/                    # Python backend
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Docker configuration
│   ├── static/                # Frontend build output (auto-generated)
│   └── images/                # Detection snapshots
├── src/                       # React frontend source
│   ├── components/           # React components
│   ├── pages/                # Page components
│   └── lib/                  # Utilities
├── detection_integration/     # YOLO detection worker
│   └── multi_camera_detector.py
├── database/                  # Database schema
│   └── schema.sql
├── App_Data/                  # Azure WebJob scripts
│   └── jobs/continuous/detection/
├── .env.example              # Environment template
├── setup-local.sh            # Automated local setup
├── validate-deployment.sh    # Pre-deployment checks
├── docker-compose.yml        # Docker orchestration
└── DEPLOYMENT_GUIDE.md       # Complete deployment guide
```

## 🔧 Configuration

All configuration is done via environment variables. See `.env.example` for the complete list.

### Essential Variables

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/db?sslmode=require

# Security
API_KEY=your-secure-api-key

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Storage
IMAGES_DIR=./images  # Local: ./images | Docker: /app/images | Azure: /home/images

# Detection (optional tuning)
CONFIDENCE_THRESHOLD=0.5
DETECTION_WIDTH=640
DETECTION_HEIGHT=480
FRAME_STRIDE=5
```

## 📖 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide for Azure, Docker, and bare metal
- **[FIXES_APPLIED.md](FIXES_APPLIED.md)** - Summary of all fixes applied for Linux compatibility
- **[.env.example](.env.example)** - Environment variable template with detailed comments

## 🧪 Validation

Before deploying, run the validation script:

```bash
./validate-deployment.sh
```

This checks:
- ✅ Python version alignment (3.12)
- ✅ NumPy version consistency
- ✅ OpenCV headless configuration
- ✅ File permissions
- ✅ Required files present
- ✅ Dockerfile dependencies

## 🔒 Security Checklist

- [ ] Change default `API_KEY` in production
- [ ] Use strong database passwords
- [ ] Enable HTTPS (use reverse proxy + Let's Encrypt)
- [ ] Restrict `ALLOWED_ORIGINS` to your domain
- [ ] Secure RTSP camera credentials
- [ ] Set firewall rules appropriately
- [ ] Keep dependencies updated

## 🐛 Troubleshooting

### `ImportError: libGL.so.1: cannot open shared object file`

**Fixed!** All configurations now use `opencv-python-headless` and `startup.sh` enforces this on Azure.

### Frontend not loading

**For local dev**:
```bash
npm run build
mkdir -p backend/static
cp -r dist/* backend/static/
```

GitHub Actions handles this automatically for Azure deployments.

### Database connection fails

1. Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/db?sslmode=require`
2. For Supabase, ensure `?sslmode=require` is appended
3. Check firewall rules (port 5432)
4. Test connection: `psql $DATABASE_URL`

See **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for more troubleshooting.

## 🚦 API Endpoints

Once running, access interactive API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/cameras` - List cameras
- `POST /api/v1/cameras` - Add camera
- `GET /api/v1/events` - Detection events
- `GET /api/v1/stream/{camera_id}` - Live MJPEG stream
- `GET /api/v1/stats/dashboard` - Dashboard statistics

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## 📝 License

This project is developed as a Final Year Project. All rights reserved.

## 🙏 Acknowledgments

- **Ultralytics** - YOLOv8 object detection
- **FastAPI** - Modern Python web framework
- **React** - UI framework
- **shadcn/ui** - Component library

## 📞 Support

For deployment issues or questions:
1. Run `./validate-deployment.sh` to check configuration
2. Review logs (Azure Log Stream, Docker logs, or systemd journal)
3. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) troubleshooting section
4. Verify all environment variables are set correctly

---

**Status**: ✅ Ready for production deployment on Linux servers  
**Last Updated**: Nov 5, 2025  
**Python Version**: 3.12 (all components aligned)
