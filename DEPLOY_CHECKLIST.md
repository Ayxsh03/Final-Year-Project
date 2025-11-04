# Azure Deployment Checklist ✅

Quick checklist to deploy your FpelAICCTV project to Azure.

## Architecture Overview

Your project consists of **3 components** running on a single Azure App Service:

1. **Frontend (React + Vite)** - Served as static files from `backend/static/`
2. **Backend API (FastAPI)** - Main application on port 8000, serves both API and frontend
3. **Detection Worker (YOLO)** - Runs as an Azure WebJob, processes camera streams

```
Azure App Service (Pv3 Plan)
├── Main Process: FastAPI Backend (startup.sh)
│   ├── Serves React Frontend (SPA)
│   ├── REST API (/api/*)
│   ├── Connects to Supabase
│   └── Serves images (/images/*)
└── WebJob: Detection Worker (continuous)
    ├── Loads YOLO model
    ├── Connects to cameras via RTSP
    ├── Detects people in video streams
    └── Sends events to FastAPI backend
```

**Key Points:**
- All 3 components share the same filesystem (`/home/site/wwwroot/`)
- Detection worker communicates with backend via localhost
- Only the backend needs external network access (port 8000)
- The YOLO model (`yolov8n.pt`) is ~13MB and deployed with your code

## Files Modified/Created

✅ **Created:**
- `startup.sh` - Main startup script for Azure App Service
- `runtime.txt` - Specifies Python 3.12
- `AZURE_DEPLOYMENT.md` - Comprehensive deployment guide
- `DEPLOY_CHECKLIST.md` - This checklist

✅ **Modified:**
- `.github/workflows/deploy-fpelaicctv.yml` - Fixed deployment workflow
- `vite.config.ts` - Changed output to `dist` instead of `backend/static`
- `backend/main.py` - Added production path handling for static files

## Pre-Deployment Steps

### 1. Configure Azure App Service Settings ⚠️ REQUIRED

Go to Azure Portal → Your App Service (`FpelAICCTV`) → **Configuration** → **Application settings**

Add these environment variables:

```
# Backend API Configuration
DATABASE_URL = postgresql://postgres:1KL72HcfqnFmpYEX@db.czwkrupnyvfwmkrvkmel.supabase.co:5432/postgres?sslmode=require
API_KEY = <generate-a-secure-key-here>
IMAGES_DIR = /home/images
STATIC_DIR = /home/site/wwwroot/backend/static
ALLOWED_ORIGINS = https://fpelaicctv.azurewebsites.net
DB_SSL_DISABLE_VERIFY = false
PYTHONUNBUFFERED = 1

# Detection Worker Configuration
API_BASE_URL = http://localhost:8000/api/v1
CONFIDENCE_THRESHOLD = 0.5
DETECTION_WIDTH = 640
DETECTION_HEIGHT = 480
FRAME_STRIDE = 5
EVENT_COOLDOWN_SECONDS = 5
TRACK_COOLDOWN_SECONDS = 30
```

**⚠️ IMPORTANT:** 
- Replace `<generate-a-secure-key-here>` with a strong random string
- Both the backend and detection worker use the same `API_KEY`
- The detection worker connects to the backend via `API_BASE_URL`

**Click "Save"** after adding all variables.

### 2. Configure Startup Command ⚠️ REQUIRED

In the same Configuration page → **General settings**:

- **Stack**: Python
- **Major version**: 3.12
- **Startup Command**: `bash startup.sh`

**Click "Save"**

### 3. Add GitHub Secret ⚠️ REQUIRED

1. Azure Portal → Your App Service → **Deployment Center** → Click **Manage publish profile** → Download
2. GitHub → Your Repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
3. Name: `AZURE_PUBLISH_PROFILE`
4. Value: Paste entire XML content from downloaded file
5. Click **Add secret**

### 4. Enable "Always On" ⚠️ RECOMMENDED

Configuration → **General settings** → **Always On**: **On** → Save

This prevents your app from going idle.

## Deployment Steps

### Option 1: Push to GitHub (Automatic)

```bash
cd Final-Year-Project

# Stage all changes
git add .

# Commit changes
git commit -m "Configure Azure deployment"

# Push to main branch
git push origin main
```

The GitHub Actions workflow will automatically:
1. Build the React frontend
2. Copy frontend to backend/static
3. Package everything
4. Deploy to Azure
5. Start the application

### Option 2: Manual Trigger

1. Go to GitHub → **Actions** tab
2. Select "Build and Deploy FpelAICCTV"
3. Click **Run workflow** → Select `main` → **Run workflow**

## Post-Deployment Verification

### 1. Check Deployment Status

- GitHub: **Actions** tab → Check if workflow succeeded (green checkmark)
- Azure: **Deployment Center** → **Logs** → Verify deployment

### 2. Test Your Application

Open these URLs in your browser:

- Frontend: https://fpelaicctv.azurewebsites.net/
- Health Check: https://fpelaicctv.azurewebsites.net/health
- API Docs: https://fpelaicctv.azurewebsites.net/api/docs

### 3. Check Logs (if issues occur)

Azure Portal → Your App Service → **Monitoring** → **Log stream**

Or use Azure CLI:
```bash
az webapp log tail --name FpelAICCTV --resource-group <your-resource-group>
```

## Common Issues & Quick Fixes

### Issue: "Application Error"
**Fix:** Check environment variables in Azure Configuration

### Issue: Frontend shows 404
**Fix:** Wait 2-3 minutes for deployment to complete, then refresh

### Issue: API endpoints return 500
**Fix:** Verify `DATABASE_URL` is correct in Azure settings

### Issue: WebJob not running
**Fix:** Azure Portal → WebJobs → Select `detection` → Click **Start**

## Next Steps After Successful Deployment

1. ✅ Test all features (cameras, detection, alerts)
2. ✅ Verify WebJob is running for camera detection
3. ✅ Set up Application Insights for monitoring
4. ✅ Configure custom domain (optional)
5. ✅ Set up auto-scaling rules
6. ✅ Enable backups

## Quick Commands Reference

### View Application Logs
```bash
az webapp log tail --name FpelAICCTV --resource-group <your-rg>
```

### Restart App Service
```bash
az webapp restart --name FpelAICCTV --resource-group <your-rg>
```

### SSH into App Service
```bash
az webapp ssh --name FpelAICCTV --resource-group <your-rg>
```

### Check Deployment History
```bash
az webapp deployment list --name FpelAICCTV --resource-group <your-rg>
```

## Support & Documentation

- 📖 Full Guide: See `AZURE_DEPLOYMENT.md`
- 🔧 Azure Docs: https://docs.microsoft.com/azure/app-service/
- 💬 GitHub Issues: Check workflow logs in Actions tab

---

**Ready to deploy?** Complete steps 1-4 above, then commit and push! 🚀
