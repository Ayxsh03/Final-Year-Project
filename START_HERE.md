# 🚀 START HERE - Azure Deployment Quick Start

## What I Fixed for You

Your project has **3 components** that need to run together:
1. **React Frontend** (npm run dev locally)
2. **FastAPI Backend** (Docker locally)  
3. **Detection Worker** (Python script locally)

I've configured everything to run on **one Azure App Service** (your Pv3 plan) - no extra costs!

---

## ✅ What's Ready

### Files Created:
- ✅ `startup.sh` - Launches FastAPI backend
- ✅ `runtime.txt` - Specifies Python 3.12
- ✅ `App_Data/jobs/continuous/detection/run.sh` - Updated to launch detection worker

### Files Modified:
- ✅ `.github/workflows/deploy-fpelaicctv.yml` - Fixed deployment
- ✅ `vite.config.ts` - Builds frontend to correct location
- ✅ `backend/main.py` - Handles Azure paths

### Documentation:
- ✅ `DEPLOYMENT_COMPLETE_GUIDE.md` - Full guide with troubleshooting
- ✅ `DEPLOY_CHECKLIST.md` - Quick checklist
- ✅ `AZURE_DEPLOYMENT.md` - Detailed reference

---

## 🎯 What You Need to Do (10 minutes)

### Step 1: Configure Azure (5 min)

Go to **Azure Portal** → `FpelAICCTV` App Service → **Configuration**

**Add these Application Settings** (click "New application setting" for each):

```
DATABASE_URL = postgresql://postgres:1KL72HcfqnFmpYEX@db.czwkrupnyvfwmkrvkmel.supabase.co:5432/postgres?sslmode=require
API_KEY = YOUR_SECURE_KEY_HERE
IMAGES_DIR = /home/images
STATIC_DIR = /home/site/wwwroot/backend/static
ALLOWED_ORIGINS = https://fpelaicctv.azurewebsites.net
API_BASE_URL = http://localhost:8000/api/v1
CONFIDENCE_THRESHOLD = 0.5
DETECTION_WIDTH = 640
DETECTION_HEIGHT = 480
FRAME_STRIDE = 5
EVENT_COOLDOWN_SECONDS = 5
PYTHONUNBUFFERED = 1
DB_SSL_DISABLE_VERIFY = false
```

**Generate a secure API key**:
```bash
openssl rand -hex 32
```
Use this value for `API_KEY` above.

**Then set General Settings**:
- Stack: **Python**
- Version: **3.12**
- Startup Command: `bash startup.sh`
- Always On: **On**

Click **Save**!

---

### Step 2: Add GitHub Secret (2 min)

1. Azure Portal → `FpelAICCTV` → **Deployment Center** → Download **Publish Profile**
2. GitHub → Your Repo → **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret**:
   - Name: `AZURE_PUBLISH_PROFILE`
   - Value: Paste XML from downloaded file
4. **Add secret**

---

### Step 3: Deploy (3 min)

```bash
cd Final-Year-Project

# Add all new configuration files
git add .

# Commit
git commit -m "Configure Azure deployment - all 3 components"

# Deploy (triggers GitHub Actions)
git push origin main
```

Watch deployment at: GitHub → **Actions** tab (takes 5-10 minutes)

---

## ✅ Verify It Works

### 1. Check Main App
Open: https://fpelaicctv.azurewebsites.net/

You should see your React frontend!

### 2. Check API
- Health: https://fpelaicctv.azurewebsites.net/health
- Docs: https://fpelaicctv.azurewebsites.net/api/docs

### 3. Check Detection Worker
Azure Portal → `FpelAICCTV` → **WebJobs**
- Should show `detection` job **Running** (green)
- Click **Logs** to see output

---

## 🎉 You're Done!

Your complete system is now running:
- ✅ Frontend served from Azure
- ✅ Backend API running
- ✅ Detection worker processing cameras
- ✅ All connected to Supabase

---

## 🔧 If Something Goes Wrong

### Frontend not loading?
```bash
# Check logs
az webapp log tail --name FpelAICCTV --resource-group <your-rg>

# Restart
az webapp restart --name FpelAICCTV --resource-group <your-rg>
```

### WebJob not running?
Azure Portal → WebJobs → Select `detection` → Click **Start**

### Need more help?
- **Quick guide**: `DEPLOY_CHECKLIST.md`
- **Full guide**: `DEPLOYMENT_COMPLETE_GUIDE.md`
- **Detailed info**: `AZURE_DEPLOYMENT.md`

---

## 📊 How It Works

```
Azure App Service (Your Pv3 Plan)
│
├─ Main Process (Port 8000)
│  └─ FastAPI Backend
│     ├─ Serves React Frontend (/)
│     ├─ API Endpoints (/api/*)
│     ├─ Serves Images (/images/*)
│     └─ Connects to Supabase
│
└─ WebJob (Background Process)
   └─ Detection Worker
      ├─ Loads YOLO Model
      ├─ Connects to Cameras (RTSP)
      ├─ Detects People
      └─ Sends Events to Backend

All running on ONE service - no extra costs!
```

---

## 💡 Key Features

- **No Docker on Azure** - Runs natively (faster, simpler)
- **No separate compute** - Everything on one App Service
- **Persistent storage** - Images saved to `/home/images/`
- **Auto-scaling** - Can scale up/down as needed
- **CI/CD ready** - Every push to main deploys automatically
- **WebJobs** - Detection worker runs continuously in background

---

## 🎓 Next Steps

After deployment works:
1. Add your cameras via the frontend
2. Monitor WebJob logs to see detections
3. Check events in dashboard
4. Set up Application Insights for monitoring
5. Configure alert settings

---

## 📝 Quick Commands

```bash
# View logs
az webapp log tail --name FpelAICCTV --resource-group <your-rg>

# Restart app
az webapp restart --name FpelAICCTV --resource-group <your-rg>

# SSH into app
az webapp ssh --name FpelAICCTV --resource-group <your-rg>

# Check status
az webapp show --name FpelAICCTV --resource-group <your-rg> --query state
```

---

**Ready? Complete Steps 1-3 above and you're live!** 🚀

**Questions?** Check the detailed guides mentioned above.
