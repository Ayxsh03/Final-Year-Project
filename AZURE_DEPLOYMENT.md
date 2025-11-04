# Azure Deployment Guide for FpelAICCTV

This guide covers deploying your FastAPI + React application to Azure App Service.

## Prerequisites

- Azure Premium v3 Linux Service Plan (already created ✅)
- Resource Group (already created ✅)
- GitHub repository with workflow (configured ✅)

## Required Azure Configuration

### 1. App Service Configuration

Navigate to your Azure App Service `FpelAICCTV` and configure the following:

#### Application Settings (Environment Variables)

Go to **Configuration** → **Application settings** and add:

```
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
API_KEY=your-secure-api-key-here
IMAGES_DIR=/home/images
STATIC_DIR=/home/site/wwwroot/backend/static
ALLOWED_ORIGINS=https://fpelaicctv.azurewebsites.net,https://your-custom-domain.com
DB_SSL_DISABLE_VERIFY=false
PYTHONUNBUFFERED=1
```

**Important:** Replace the placeholder values with your actual Supabase credentials and secure API key.

#### General Settings

Go to **Configuration** → **General settings**:

- **Stack**: Python
- **Major version**: Python 3.12
- **Minor version**: 3.12 (latest)
- **Startup Command**: `bash startup.sh`

### 2. GitHub Secrets

Add the following secret to your GitHub repository:

1. Go to your Azure App Service → **Deployment Center**
2. Download the **Publish Profile**
3. In GitHub: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
4. Name: `AZURE_PUBLISH_PROFILE`
5. Value: Paste the entire contents of the publish profile XML file

### 3. Enable Continuous Deployment (Optional but Recommended)

In Azure App Service:
1. Go to **Deployment Center**
2. Source: **GitHub**
3. Authorize and select your repository
4. Branch: `main`
5. Save

## Deployment Process

### Automatic Deployment

Every push to the `main` branch will trigger:

1. ✅ Frontend build (React + Vite)
2. ✅ Copy frontend to `backend/static`
3. ✅ Python dependencies validation
4. ✅ Package creation (site.zip)
5. ✅ Deploy to Azure
6. ✅ Start FastAPI with `startup.sh`

### Manual Deployment

You can also trigger deployment manually:
1. Go to **Actions** tab in your GitHub repository
2. Select **Build and Deploy FpelAICCTV** workflow
3. Click **Run workflow** → Select `main` branch → **Run workflow**

## Project Structure After Deployment

```
/home/site/wwwroot/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt
│   ├── static/              # Built frontend files
│   │   ├── index.html
│   │   ├── assets/
│   │   └── ...
│   └── ...
├── detection_integration/
│   ├── multi_camera_detector.py
│   └── yolov8n.pt
├── App_Data/
│   └── jobs/
│       └── continuous/
│           └── detection/
│               └── run.sh    # WebJob for detection
├── startup.sh               # Main startup script
├── runtime.txt              # Python version
├── requirements.txt         # Root requirements
└── ...
```

## WebJobs (Background Detection)

The detection worker runs as an Azure WebJob:

- **Type**: Continuous
- **Location**: `App_Data/jobs/continuous/detection/`
- **Script**: `run.sh`
- **Logs**: Available in Azure Portal → WebJobs → Logs

To check WebJob status:
1. Go to Azure Portal → Your App Service → **WebJobs**
2. Verify `detection` job is running
3. Click **Logs** to see output

## Accessing Your Application

### Frontend (React)
- URL: `https://fpelaicctv.azurewebsites.net/`
- The React app is served from `/`
- All React routes are handled by SPA fallback

### Backend API (FastAPI)
- Base URL: `https://fpelaicctv.azurewebsites.net/api/`
- API Docs: `https://fpelaicctv.azurewebsites.net/api/docs`
- Health Check: `https://fpelaicctv.azurewebsites.net/health`

### Images
- Stored in: `/home/images` (persistent storage)
- Accessible via: `https://fpelaicctv.azurewebsites.net/images/`

## Troubleshooting

### Check Logs

#### Application Logs
```bash
az webapp log tail --name FpelAICCTV --resource-group <your-resource-group>
```

Or in Azure Portal:
- Go to **Monitoring** → **Log stream**

#### Deployment Logs
- GitHub: **Actions** tab → Select workflow run
- Azure Portal: **Deployment Center** → **Logs**

### Common Issues

#### 1. "Application Error" or 500 Error
- **Check**: Environment variables are set correctly in Azure
- **Fix**: Go to Configuration → Application settings → Verify all env vars

#### 2. Frontend Shows 404
- **Check**: `backend/static` directory exists and has files
- **Fix**: Trigger a new deployment to rebuild frontend

#### 3. Database Connection Fails
- **Check**: `DATABASE_URL` is correct and includes `?sslmode=require`
- **Fix**: Update connection string in Azure App Settings

#### 4. WebJob Not Running
- **Check**: WebJobs section in Azure Portal
- **Fix**: Manually start the job or check `run.sh` permissions

#### 5. Static Files Not Loading
- **Check**: CORS and ALLOWED_ORIGINS settings
- **Fix**: Add your Azure domain to ALLOWED_ORIGINS

### Debug Commands

SSH into your App Service (if enabled):
```bash
# Check if files were deployed
ls -la /home/site/wwwroot/

# Check static files
ls -la /home/site/wwwroot/backend/static/

# Check Python version
python --version

# Test startup script
bash /home/site/wwwroot/startup.sh

# Check processes
ps aux | grep python
```

## Scaling

Your Premium v3 plan supports:
- **Auto-scaling**: Configure in **Scale out** settings
- **Manual scaling**: Adjust in **Scale up** settings
- **Always On**: Should be enabled (under Configuration → General settings)

## Custom Domain (Optional)

To add a custom domain:
1. **Custom domains** → **Add custom domain**
2. Verify domain ownership
3. Add DNS records (CNAME or A record)
4. Configure SSL/TLS certificate

## Monitoring

Set up monitoring:
1. **Application Insights**: Enable for detailed telemetry
2. **Alerts**: Configure alerts for errors, high response times, etc.
3. **Metrics**: Monitor CPU, Memory, Response time

## Performance Optimization

- Enable **HTTP/2** in Configuration
- Configure **CDN** for static assets
- Enable **Application Insights** for performance monitoring
- Use **Azure Cache for Redis** if needed

## Security Checklist

- ✅ Change default `API_KEY` to a secure value
- ✅ Use strong database passwords
- ✅ Enable HTTPS only (disable HTTP)
- ✅ Configure CORS properly (don't use `*`)
- ✅ Keep secrets in Azure Key Vault (optional but recommended)
- ✅ Enable **Managed Identity** for Azure services
- ✅ Review **Network** settings and restrict access if needed

## Cost Optimization

- Review **Metrics** to ensure you're not over-provisioned
- Consider scaling down during off-hours
- Use **Azure Cost Management** to monitor spending
- Enable **auto-shutdown** for dev/test environments

## Support

For issues:
1. Check Azure Portal logs
2. Check GitHub Actions workflow logs
3. Review this deployment guide
4. Check Azure documentation: https://docs.microsoft.com/azure/app-service/

---

**Last Updated**: 2025-11-04
**Version**: 1.0
