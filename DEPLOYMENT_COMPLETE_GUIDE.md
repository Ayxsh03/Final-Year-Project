# Complete Azure Deployment Guide for FpelAICCTV
## Single Azure App Service - No Additional Costs

This guide explains how to deploy your **complete system** (frontend + backend + detection worker) on a single Azure Premium v3 App Service.

---

## 🎯 What Gets Deployed

Your system runs **3 components** on one Azure App Service (no Docker, no containers):

### 1. React Frontend (Vite)
- **Local dev**: `npm run dev` on port 8080
- **Azure**: Static files in `backend/static/`, served by FastAPI

### 2. FastAPI Backend 
- **Local dev**: Docker container on port 8000
- **Azure**: Native Python app on port 8000 (no Docker needed)

### 3. Detection Worker (YOLO)
- **Local dev**: Separate terminal running `multi_camera_detector.py`
- **Azure**: Continuous WebJob (background process)

---

## 📦 How It Works on Azure

```
/home/site/wwwroot/                    # Your deployed code
├── backend/
│   ├── main.py                        # FastAPI app (main process)
│   └── static/                        # React build output
│       ├── index.html
│       └── assets/
├── detection_integration/
│   └── multi_camera_detector.py       # Detection worker
├── yolov8n.pt                         # YOLO model (~13MB)
├── App_Data/jobs/continuous/detection/
│   └── run.sh                         # WebJob launcher
├── startup.sh                         # Main app launcher
└── requirements.txt                   # Python dependencies

Process 1: startup.sh → FastAPI (serves frontend + API)
Process 2: WebJob runs run.sh → Detection worker
```

**Why this works:**
- Azure App Service on Linux supports Python natively
- No Docker overhead = faster startup, simpler deployment
- WebJobs run as separate background processes
- Both processes access the same filesystem
- Detection worker calls backend via `http://localhost:8000/api/v1`

---

## ⚙️ Prerequisites Checklist

### Azure Resources (Already Created ✅)
- [x] Azure Premium v3 Linux Service Plan
- [x] Resource Group
- [x] App Service created

### What You Need to Do
- [ ] Configure Azure App Service settings
- [ ] Add GitHub secret
- [ ] Commit and push code

---

## 🚀 Deployment Steps

### Step 1: Configure Azure App Service

Go to **Azure Portal** → Your App Service (`FpelAICCTV`) → **Configuration**

#### A. Add Application Settings

Click **"New application setting"** for each:

| Name | Value | Notes |
|------|-------|-------|
| `DATABASE_URL` | `postgresql://postgres:1KL72HcfqnFmpYEX@db.czwkrupnyvfwmkrvkmel.supabase.co:5432/postgres?sslmode=require` | Your Supabase connection |
| `API_KEY` | `your-secure-random-key` | Generate a strong key (e.g., `openssl rand -hex 32`) |
| `IMAGES_DIR` | `/home/images` | Persistent storage for detection images |
| `STATIC_DIR` | `/home/site/wwwroot/backend/static` | Frontend files location |
| `ALLOWED_ORIGINS` | `https://fpelaicctv.azurewebsites.net` | Your Azure URL |
| `API_BASE_URL` | `http://localhost:8000/api/v1` | For detection worker |
| `CONFIDENCE_THRESHOLD` | `0.5` | YOLO detection confidence |
| `DETECTION_WIDTH` | `640` | Video processing width |
| `DETECTION_HEIGHT` | `480` | Video processing height |
| `FRAME_STRIDE` | `5` | Process every Nth frame |
| `EVENT_COOLDOWN_SECONDS` | `5` | Cooldown between events |
| `PYTHONUNBUFFERED` | `1` | Better logging |
| `DB_SSL_DISABLE_VERIFY` | `false` | SSL verification for DB |

**Click "Save"** after adding all settings.

#### B. Configure General Settings

Still in **Configuration** → **General settings** tab:

- **Stack**: Python
- **Major version**: 3.12
- **Minor version**: 3.12 (latest)
- **Startup Command**: `bash startup.sh`
- **Always On**: **On** (Important! Keeps app running)

**Click "Save"**

---

### Step 2: Add GitHub Secret

1. **Download Publish Profile**:
   - Azure Portal → Your App Service → **Deployment Center**
   - Click **"Manage publish profile"** → Download

2. **Add to GitHub**:
   - GitHub → Your Repo → **Settings** → **Secrets and variables** → **Actions**
   - Click **"New repository secret"**
   - Name: `AZURE_PUBLISH_PROFILE`
   - Value: Paste the **entire XML content** from downloaded file
   - Click **"Add secret"**

---

### Step 3: Deploy Your Code

```bash
cd Final-Year-Project

# Make sure all new files are tracked
git add .

# Commit your deployment configuration
git commit -m "Configure Azure deployment - Frontend + Backend + Detection Worker"

# Push to main branch (triggers deployment)
git push origin main
```

---

### Step 4: Monitor Deployment

#### Watch GitHub Actions
1. Go to GitHub → **Actions** tab
2. Click on the running workflow
3. Watch the build steps:
   - ✅ Build React frontend
   - ✅ Copy to backend/static
   - ✅ Validate Python dependencies
   - ✅ Create deployment package
   - ✅ Deploy to Azure

This takes **5-10 minutes**.

#### Check Azure Logs
While deploying, you can watch Azure logs:

```bash
# If you have Azure CLI installed
az webapp log tail --name FpelAICCTV --resource-group <your-resource-group>
```

Or in Azure Portal:
- Your App Service → **Monitoring** → **Log stream**

---

## ✅ Verify Deployment

### 1. Check Main App (Frontend + Backend)

Open in browser:
- **Frontend**: https://fpelaicctv.azurewebsites.net/
- **Health**: https://fpelaicctv.azurewebsites.net/health
- **API Docs**: https://fpelaicctv.azurewebsites.net/api/docs

You should see your React app loading!

### 2. Check Detection Worker (WebJob)

Azure Portal → Your App Service → **WebJobs**:
- Should see: `detection` job
- Status: **Running** (green)
- Click **"Logs"** to see output

If not running:
1. Select the `detection` job
2. Click **"Start"**
3. Wait 30 seconds
4. Check logs again

### 3. Test Complete System

1. **Add a camera** via frontend
2. Check **WebJobs logs** - should show:
   ```
   Starting Detection Worker (WebJob)
   Loading YOLO model (yolov8n.pt)
   Connecting to camera...
   ```
3. View **live stream** in frontend
4. Wait for detections to appear

---

## 🔧 Troubleshooting

### Problem: "Application Error" on main URL

**Check**: Application logs
```bash
az webapp log tail --name FpelAICCTV --resource-group <your-rg>
```

**Common fixes**:
- Verify all environment variables are set in Azure Configuration
- Check that `DATABASE_URL` is correct
- Ensure `startup.sh` has execute permissions (workflow handles this)

**Solution**: Restart the app
```bash
az webapp restart --name FpelAICCTV --resource-group <your-rg>
```

---

### Problem: Frontend shows blank page or 404

**Check**: Static files were deployed
- Azure Portal → App Service → **SSH** (or Advanced Tools)
- Run: `ls -la /home/site/wwwroot/backend/static/`
- Should see `index.html` and `assets/`

**Fix**: Trigger a new deployment
```bash
git commit --allow-empty -m "Rebuild frontend"
git push origin main
```

---

### Problem: WebJob not starting

**Check**: WebJob status
- Azure Portal → WebJobs → Status

**Fix 1**: Manually start
1. Select `detection` job
2. Click **"Start"**

**Fix 2**: Check logs
- Click **"Logs"** link
- Look for errors about missing files or permissions

**Fix 3**: Verify files exist
- SSH into App Service
- Check: `ls -la /home/site/wwwroot/yolov8n.pt`
- Check: `ls -la /home/site/wwwroot/detection_integration/`

---

### Problem: Detection worker crashes

**Check WebJob logs** for specific errors:

**Error: "yolov8n.pt not found"**
- The model file didn't deploy
- **Fix**: Check that `yolov8n.pt` is in your repo (not in .gitignore)

**Error: "Cannot connect to API"**
- Backend not running
- **Fix**: Check main app logs, verify `API_BASE_URL=http://localhost:8000/api/v1`

**Error: "RTSP connection failed"**
- Camera not accessible
- **Fix**: Cameras must have public IPs or be accessible from Azure

---

### Problem: High memory usage

**Check**: Azure Portal → Metrics → Memory usage

**Optimize**:
1. Reduce number of active cameras
2. Increase `FRAME_STRIDE` (process fewer frames)
3. Reduce `DETECTION_WIDTH` and `DETECTION_HEIGHT`
4. Increase `EVENT_COOLDOWN_SECONDS`

Edit in Azure Configuration → Application settings → Save → Restart app

---

## 📊 Monitor Your App

### Application Insights (Recommended)

Enable for detailed monitoring:
1. Azure Portal → Your App Service → **Application Insights**
2. Click **"Turn on Application Insights"**
3. Create new resource or use existing
4. Monitors:
   - Request times
   - Failed requests
   - Exceptions
   - Dependencies (Supabase calls)

### Basic Monitoring

Azure Portal → Your App Service:
- **Metrics**: CPU, Memory, Response time
- **Log stream**: Live logs
- **Diagnose and solve problems**: Auto-suggestions

---

## 🔐 Security Best Practices

### 1. Change API Key
Generate a secure key:
```bash
openssl rand -hex 32
```
Update in Azure Configuration → `API_KEY`

### 2. Use Azure Key Vault (Optional)
Store secrets in Key Vault instead of App Settings:
- More secure
- Audit trail
- Automatic rotation

### 3. Restrict Network Access
If cameras are in specific locations:
- **Networking** → **Access restrictions**
- Add IP whitelist rules

### 4. Enable HTTPS Only
- **TLS/SSL settings** → **HTTPS Only**: On

### 5. Database Security
- Use strong Supabase password
- Enable Row Level Security (RLS) in Supabase
- Restrict database access to Azure IPs only

---

## 💰 Cost Optimization

Your Premium v3 plan is already paid, but here's how to optimize:

### 1. Auto-scale
**Scale out** → Add rule:
- Scale based on CPU percentage
- Scale up when CPU > 70%
- Scale down when CPU < 30%
- Min instances: 1
- Max instances: 3 (only pay more when needed)

### 2. Schedule Scaling
If cameras only active during business hours:
- Scale down to cheaper tier at night
- Use Azure Automation to change tiers on schedule

### 3. Monitor Costs
- **Cost Management** → **Cost analysis**
- Set budget alerts
- Review resource usage monthly

---

## 🔄 Updates and Maintenance

### Deploy Updates
```bash
# Make code changes
git add .
git commit -m "Update feature X"
git push origin main
# Deployment happens automatically
```

### Manual Restart
```bash
az webapp restart --name FpelAICCTV --resource-group <your-rg>
```

### View Deployment History
Azure Portal → **Deployment Center** → **Logs**

### Rollback to Previous Version
1. **Deployment Center** → **Logs**
2. Find successful deployment
3. Click **"Redeploy"**

---

## 📝 Quick Reference Commands

```bash
# View logs
az webapp log tail --name FpelAICCTV --resource-group <your-rg>

# Restart app
az webapp restart --name FpelAICCTV --resource-group <your-rg>

# SSH into app
az webapp ssh --name FpelAICCTV --resource-group <your-rg>

# Check app status
az webapp show --name FpelAICCTV --resource-group <your-rg> --query state

# List WebJobs
az webapp webjob continuous list --name FpelAICCTV --resource-group <your-rg>

# Start WebJob
az webapp webjob continuous start --name FpelAICCTV --resource-group <your-rg> --webjob-name detection

# Download logs
az webapp log download --name FpelAICCTV --resource-group <your-rg>
```

---

## 🎓 Understanding the Deployment

### Local Development vs Azure

| Component | Local | Azure |
|-----------|-------|-------|
| Frontend | `npm run dev` (port 8080) | Static files served by FastAPI |
| Backend | Docker container | Native Python process |
| Detection | Separate terminal | WebJob (background process) |
| Database | Supabase | Supabase (same) |
| Images | Local `./images/` | Azure `/home/images/` |

### File Locations on Azure

```
/home/site/wwwroot/           # Your app code (read-only after deploy)
/home/images/                 # Persistent storage (survives restarts)
/home/logs/                   # Application logs
/home/LogFiles/               # Platform logs
```

### Process Architecture

```
Azure App Service
│
├─ Main Container (SCM site)
│  └─ Kudu service (for deployments)
│
└─ App Container
   ├─ Process 1: bash startup.sh
   │  └─ python uvicorn backend.main:app
   │     ├─ Serves React frontend (/)
   │     ├─ Handles API (/api/*)
   │     └─ Serves images (/images/*)
   │
   └─ Process 2: WebJob (detection)
      └─ python multi_camera_detector.py
         ├─ Loads YOLO model
         ├─ Connects to cameras
         ├─ Runs detections
         └─ POSTs events to localhost:8000/api/v1
```

---

## 🆘 Getting Help

### Check Logs First
Most issues are visible in logs:
1. GitHub Actions logs (build issues)
2. Azure Log Stream (runtime issues)
3. WebJob logs (detection issues)

### Common Issues Checklist
- [ ] All environment variables set in Azure?
- [ ] Startup command configured?
- [ ] GitHub secret added?
- [ ] Always On enabled?
- [ ] WebJob running?
- [ ] Database connection working?

### Still Stuck?
- Check `AZURE_DEPLOYMENT.md` for detailed info
- Review GitHub Actions workflow output
- Use Azure "Diagnose and solve problems"

---

## ✨ Success Checklist

Your deployment is successful when:

- [x] Frontend loads at https://fpelaicctv.azurewebsites.net/
- [x] Can login and see dashboard
- [x] API docs accessible at /api/docs
- [x] Health endpoint returns {"status": "healthy"}
- [x] WebJob shows "Running" status
- [x] Can add cameras via UI
- [x] Can view camera streams
- [x] Detections appear in events list
- [x] Images saved to /home/images/

---

**You're all set! Your complete CCTV detection system is now running on Azure.** 🎉
