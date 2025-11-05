# Azure App Service - Required Application Settings

Configure these in **Azure Portal** → Your App Service → **Configuration** → **Application settings**

## 🔴 Critical Settings (Required)

### ALLOWED_ORIGINS
**Value:**
```
https://fpelaicctv-hrhqbecqgyb4fxd0.centralindia-01.azurewebsites.net
```

**Purpose:** Enables CORS for your frontend to communicate with the API

---

### DATABASE_URL
**Value:** (Your PostgreSQL/Supabase connection string)
```
postgresql://user:password@host.supabase.co:5432/postgres?sslmode=require
```

**Purpose:** Database connection

---

### API_KEY
**Value:** (Change from default!)
```
your-secure-api-key-here
```

**Purpose:** API authentication

⚠️ **Security:** DO NOT use the default `111-1111-1-11-1-11-1-1` in production!

---

## 🟡 Optional Settings (Recommended)

### IMAGES_DIR
**Value:**
```
/home/images
```

**Purpose:** Directory for detection snapshots

---

### STATIC_DIR
**Value:**
```
/home/site/wwwroot/backend/static
```

**Purpose:** Frontend static files location (usually auto-detected)

---

### CONFIDENCE_THRESHOLD
**Value:**
```
0.5
```

**Purpose:** Detection confidence threshold (0.0 to 1.0)

---

### DETECTION_WIDTH
**Value:**
```
640
```

**Purpose:** Frame width for detection processing

---

### DETECTION_HEIGHT
**Value:**
```
480
```

**Purpose:** Frame height for detection processing

---

### FRAME_STRIDE
**Value:**
```
5
```

**Purpose:** Process every Nth frame (higher = better performance, lower accuracy)

---

## 🔍 How to Set in Azure Portal

1. Go to: https://portal.azure.com
2. Navigate to: **App Services** → **FpelAICCTV**
3. Click: **Configuration** (left sidebar)
4. Click: **+ New application setting**
5. Add each setting:
   - **Name**: `ALLOWED_ORIGINS`
   - **Value**: `https://fpelaicctv-hrhqbecqgyb4fxd0.centralindia-01.azurewebsites.net`
6. Click **OK** then **Save**
7. Restart the app

---

## ✅ Quick Copy-Paste Configuration

For Azure CLI or ARM template:

```json
{
  "ALLOWED_ORIGINS": "https://fpelaicctv-hrhqbecqgyb4fxd0.centralindia-01.azurewebsites.net",
  "DATABASE_URL": "postgresql://user:password@host:5432/db?sslmode=require",
  "API_KEY": "your-secure-key-here",
  "IMAGES_DIR": "/home/images",
  "CONFIDENCE_THRESHOLD": "0.5",
  "DETECTION_WIDTH": "640",
  "DETECTION_HEIGHT": "480",
  "FRAME_STRIDE": "5"
}
```

---

## 🚀 After Configuration

1. **Save** all settings
2. **Restart** the app service
3. Test frontend at: https://fpelaicctv-hrhqbecqgyb4fxd0.centralindia-01.azurewebsites.net
4. Test API at: https://fpelaicctv-hrhqbecqgyb4fxd0.centralindia-01.azurewebsites.net/docs
