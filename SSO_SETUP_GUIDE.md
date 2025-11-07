# Azure SSO Authentication Setup Guide

This guide will help you configure Azure Active Directory Single Sign-On (SSO) for your FpelAICCTV Person Detection System.

## 🎯 Overview

The application now supports Azure AD SSO authentication with the following features:

- **Secure Login**: OAuth2/OIDC authentication via Microsoft Azure AD
- **Session Management**: 24-hour session timeout with automatic re-authentication
- **Domain Restriction**: Optional restriction to specific email domains
- **Tenant Validation**: Ensures users belong to your Azure AD tenant
- **Auto-Logout**: Clears session when browser is closed

## 📋 Prerequisites

- Azure account with admin access to Azure Active Directory
- Python 3.12+ with pip
- Your application domain/URL (e.g., `http://localhost:8000` for local dev)

## 🔧 Part 1: Azure AD Configuration

### Step 1: Register Application in Azure AD

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Go to **Azure Active Directory** → **App registrations**
3. Click **+ New registration**
4. Fill in the details:
   - **Name**: `FpelAICCTV Person Detection` (or your preferred name)
   - **Supported account types**: Select "Accounts in this organizational directory only"
   - **Redirect URI**: 
     - Platform: `Web`
     - URI: `http://localhost:8000/auth/callback` (for local dev)
     - For production: `https://your-domain.com/auth/callback`
5. Click **Register**

### Step 2: Configure Authentication

1. In your app registration, go to **Authentication**
2. Under **Implicit grant and hybrid flows**, ensure:
   - ✅ **ID tokens** (for implicit and hybrid flows)
3. Under **Advanced settings**:
   - Set **Allow public client flows** to **No**
4. Click **Save**

### Step 3: Create Client Secret

1. Go to **Certificates & secrets** → **Client secrets**
2. Click **+ New client secret**
3. Add description: `FpelAICCTV App Secret`
4. Set expiration (recommended: 24 months)
5. Click **Add**
6. **IMPORTANT**: Copy the **Value** immediately (you won't be able to see it again!)
7. Store it securely - you'll need it for `AZURE_CLIENT_SECRET`

### Step 4: Configure API Permissions

1. Go to **API permissions**
2. Ensure the following Microsoft Graph permissions are present:
   - `openid` (default)
   - `profile` (default)
   - `email` (default)
   - `User.Read` (add if not present)
3. Click **Grant admin consent** for your organization

### Step 5: Collect Required Information

From the **Overview** page of your app registration, note down:

- **Application (client) ID** → This is your `AZURE_CLIENT_ID`
- **Directory (tenant) ID** → This is your `AZURE_TENANT_ID`
- **Client secret value** (from Step 3) → This is your `AZURE_CLIENT_SECRET`

## 🛠️ Part 2: Application Configuration

### Step 1: Install Dependencies

```bash
cd /Users/ayush/Documents/GitHub/Final-Year-Project
pip install -r backend/requirements.txt
```

This will install:
- `msal==1.24.1` - Microsoft Authentication Library
- `itsdangerous==2.1.2` - Session signing
- `jinja2==3.1.2` - Template rendering

### Step 2: Configure Environment Variables

Create or update your `.env` file:

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

Add the following SSO configuration:

```env
# Azure SSO Authentication
AZURE_TENANT_ID=your-tenant-id-from-azure
AZURE_CLIENT_ID=your-client-id-from-azure
AZURE_CLIENT_SECRET=your-client-secret-from-azure
REDIRECT_URI=http://localhost:8000/auth/callback

# Domain restriction (optional - leave empty to allow all domains)
# Example: fourthpartner.co (without @)
ALLOWED_DOMAIN=

# Session secret key (generate a random string for production)
SESSION_SECRET_KEY=your-secret-key-change-this-in-production

# Application name (shown on login page)
APP_NAME=FpelAICCTV Person Detection
```

### Step 3: Generate Secure Session Secret

For production, generate a secure random key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and use it for `SESSION_SECRET_KEY`.

### Step 4: Configure Domain Restriction (Optional)

To restrict access to a specific email domain:

```env
ALLOWED_DOMAIN=fourthpartner.co
```

This will only allow users with `@fourthpartner.co` email addresses to sign in.

Leave it empty to allow all Azure AD users in your tenant.

## 🚀 Part 3: Testing SSO

### Local Development

1. Start the application:

```bash
cd /Users/ayush/Documents/GitHub/Final-Year-Project
source venv/bin/activate  # if using virtual environment
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

3. You should be redirected to the login page
4. Click **"Sign in with Microsoft"**
5. You'll be redirected to Microsoft login
6. Sign in with your Azure AD credentials
7. After successful authentication, you'll be redirected back to the application

### Production Deployment

For production deployment (e.g., Azure App Service):

1. Update `REDIRECT_URI` in your `.env` or Azure App Settings:
   ```env
   REDIRECT_URI=https://your-domain.com/auth/callback
   ```

2. Add the same redirect URI in Azure AD App Registration:
   - Go to **Authentication** → **Platform configurations** → **Web**
   - Add redirect URI: `https://your-domain.com/auth/callback`

3. Update Azure App Service Application Settings with all SSO environment variables

## 🔒 Security Features

### Session Management

- **Duration**: 24 hours by default (configurable in `main.py`)
- **Auto-expire**: Sessions expire when browser is closed
- **CSRF Protection**: State parameter validates callback authenticity
- **Secure Cookies**: Session cookies are signed with `SESSION_SECRET_KEY`

### Route Protection

All routes are protected by default except:
- `/login` - Login page
- `/logout` - Logout endpoint
- `/auth/callback` - OAuth callback
- `/health` - Health check
- `/static/*` - Static files
- `/images/*` - Image files

### Domain & Tenant Validation

- **Domain Restriction**: Only allows specified email domain (if configured)
- **Tenant Validation**: Ensures users belong to your Azure AD tenant
- **Token Validation**: Validates JWT tokens from Azure AD

## 📱 User Experience

### Login Flow

1. User accesses the application → Redirected to login page
2. User clicks "Sign in with Microsoft" → Redirected to Azure AD
3. User enters credentials → Azure AD authenticates
4. User is redirected back → Session created, access granted

### Logout Flow

1. User clicks logout → Session cleared
2. User redirected to Azure AD logout → Azure AD session cleared
3. User redirected to login page → Ready to sign in again

## 🛠️ Troubleshooting

### "SSO not configured" Error

**Cause**: Missing Azure AD configuration variables

**Solution**: Ensure all required environment variables are set:
- `AZURE_TENANT_ID`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `REDIRECT_URI`

### "Invalid state" Error

**Cause**: CSRF token mismatch (usually due to session expiry)

**Solution**: Clear browser cookies and try again

### "Access restricted to @domain.com accounts"

**Cause**: User email domain doesn't match `ALLOWED_DOMAIN`

**Solution**: 
- Check if `ALLOWED_DOMAIN` is set correctly
- Ensure user is signing in with correct email address
- Remove `ALLOWED_DOMAIN` restriction if not needed

### "Wrong tenant. Access denied"

**Cause**: User belongs to different Azure AD tenant

**Solution**: Ensure user is using account from your organization's tenant

### Redirect URI Mismatch

**Cause**: Redirect URI in Azure AD doesn't match application configuration

**Solution**: 
1. Check `REDIRECT_URI` in `.env` matches Azure AD configuration
2. Ensure protocol matches (http vs https)
3. Ensure port matches (if using non-standard port)

## 🔍 API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | GET | Display login page or redirect to Azure AD |
| `/auth/callback` | GET/POST | Handle OAuth callback from Azure AD |
| `/logout` | GET | Clear session and logout from Azure AD |
| `/api/v1/user` | GET | Get current authenticated user info |

### Example: Get Current User

```bash
curl http://localhost:8000/api/v1/user \
  -H "Cookie: session=<your-session-cookie>"
```

Response:
```json
{
  "email": "user@fourthpartner.co",
  "name": "John Doe"
}
```

## 📊 Session Configuration

Default session settings (can be modified in `main.py`):

```python
app.add_middleware(
    SessionMiddleware, 
    secret_key=SESSION_SECRET_KEY, 
    max_age=86400  # 24 hours in seconds
)
```

To change session duration, modify `max_age`:
- 1 hour: `3600`
- 8 hours: `28800`
- 24 hours: `86400`
- 7 days: `604800`

## 🎨 Customization

### Login Page Branding

Edit `/Users/ayush/Documents/GitHub/Final-Year-Project/backend/templates/login.html`:

- Update `APP_NAME` environment variable to change title
- Modify CSS styles for custom branding
- Add company logo in the header section

### Session Behavior

To require re-authentication every time the website is closed (already implemented):

```python
# Session expires when browser closes (current behavior)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=86400)
```

The session cookie is a session cookie (no explicit expires time), so it's cleared when the browser closes.

## 📚 Additional Resources

- [Microsoft Identity Platform Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth 2.0 Authorization Code Flow](https://oauth.net/2/grant-types/authorization-code/)

## 💡 Best Practices

1. **Never commit secrets**: Keep `.env` file out of version control
2. **Rotate secrets regularly**: Update `AZURE_CLIENT_SECRET` every 12-24 months
3. **Use HTTPS in production**: Always use HTTPS for production deployments
4. **Monitor authentication logs**: Check Azure AD sign-in logs regularly
5. **Enable MFA**: Require multi-factor authentication for users
6. **Restrict domains**: Use `ALLOWED_DOMAIN` to limit access
7. **Regular security updates**: Keep dependencies updated

## ✅ Checklist

- [ ] Azure AD app registered
- [ ] Client secret created and saved securely
- [ ] Redirect URI configured in Azure AD
- [ ] Environment variables set in `.env`
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Session secret key generated (production)
- [ ] Domain restriction configured (optional)
- [ ] Application tested locally
- [ ] Production redirect URI configured (if deploying)
- [ ] HTTPS enabled (production)

---

**Need Help?** If you encounter any issues, check the troubleshooting section or review the Azure AD sign-in logs for detailed error messages.
