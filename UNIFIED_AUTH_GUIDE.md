# Unified Authentication System Guide

## Overview
Your application now supports **both traditional email/password authentication AND Azure SSO** in a unified login page. Users can:
- Create an account with email/password
- Login with email/password
- Login via Azure SSO (Microsoft accounts)
- Have their profile automatically created when logging in via SSO

## Architecture

### Backend Components

1. **Users Database Table** (`database/users_table.sql`)
   - Stores user profiles for both auth methods
   - Fields: `id`, `email`, `full_name`, `auth_provider`, `azure_id`, `password_hash`, `role`, etc.
   - Activity logs track user actions

2. **Authentication Endpoints**
   - `POST /api/v1/auth/register` - Register with email/password
   - `POST /api/v1/auth/login` - Login with email/password
   - `GET /login` - Display unified login page
   - `GET /login/sso` - Initiate SSO flow
   - `GET /auth/callback` - Handle SSO callback
   - `GET /logout` - Logout and clear session
   - `GET /api/v1/user` - Get current user info

3. **Session Management**
   - Backend creates session after successful login (any method)
   - Session stores: `id`, `email`, `name`, `role`, `auth_provider`
   - Session expires after 24 hours or browser close

### Frontend Integration

The login page (`/login`) shows:
- **Tab 1: Email Login** - Traditional login form + registration button
- **Tab 2: SSO Login** (if configured) - Microsoft sign-in button

After successful authentication (either method), users are redirected to `/` with a valid session.

## Setup Instructions

### 1. Database Setup

Run the SQL script to create users table:

```bash
psql $DATABASE_URL -f database/users_table.sql
```

Or execute in your database client:
- `users` table
- `activity_logs` table  
- Indexes and triggers

### 2. Environment Variables

Ensure these are set in Azure App Service → Configuration → Application settings:

**Required for both methods:**
```
DATABASE_URL=postgresql://...
SESSION_SECRET_KEY=<your-generated-secret>
APP_NAME=FpelAICCTV Person Detection
```

**Required only for SSO:**
```
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
REDIRECT_URI=https://your-app.azurewebsites.net/auth/callback
```

**Optional:**
```
ALLOWED_DOMAIN=yourcompany.com  # Restrict SSO to specific domain
```

### 3. Azure AD Configuration (for SSO)

1. Go to Azure Portal → Azure Active Directory → App registrations
2. Select your app registration
3. **Authentication → Redirect URIs:**
   - Add: `https://your-app.azurewebsites.net/auth/callback`
4. **API permissions:**
   - Add: Microsoft Graph → Delegated → `User.Read`
   - Grant admin consent
5. **Certificates & secrets:**
   - Copy your client secret value

### 4. Deploy Changes

Commit and push:

```bash
git add .
git commit -m "Add unified authentication system with SSO and traditional login"
git push origin main
```

## User Flows

### Flow 1: Traditional Registration & Login

1. User visits `/login`
2. Clicks "Create Account"
3. Enters email, full name, password
4. Profile created in `users` table with `auth_provider='email'`
5. User logs in with email/password
6. Session created, redirected to `/`

### Flow 2: SSO Login (First Time)

1. User visits `/login`
2. Switches to "SSO Login" tab
3. Clicks "Sign in with Microsoft"
4. Redirected to Azure AD for authentication
5. After successful Azure login, redirected to `/auth/callback`
6. Backend creates/retrieves user profile with `auth_provider='azure_sso'`
7. Session created with full user info
8. Redirected to `/`

### Flow 3: SSO Login (Returning User)

1. User visits `/login`
2. Clicks "Sign in with Microsoft"
3. Azure AD recognizes user, may auto-login
4. Backend retrieves existing user profile from database
5. Session created, redirected to `/`

### Flow 4: Mixed Usage

- User registered with email can also login via SSO (if same email domain)
- User first logged in via SSO can't use email/password (no password set)
- Profile is matched by email address across both methods

## API Endpoints

### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

### Get Current User
```http
GET /api/v1/user
# Returns user from session
```

### Logout
```http
GET /logout
# Clears session, redirects to login
```

## Session Data Structure

After successful authentication (any method), the session contains:

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "auth_provider": "email" | "azure_sso"
  }
}
```

## Frontend Integration

Your React app can check authentication status:

```typescript
// Check if user is logged in
fetch('/api/v1/user')
  .then(res => {
    if (res.ok) {
      return res.json(); // User is logged in
    } else {
      window.location.href = '/login'; // Redirect to login
    }
  });
```

## Security Features

1. **Password Hashing**: SHA-256 hash for email/password users
2. **Session Security**: Signed sessions with secret key, 24-hour expiration
3. **CSRF Protection**: State parameter in SSO flow
4. **Domain Restriction**: Optional email domain filtering for SSO
5. **Tenant Validation**: Ensures correct Azure AD tenant
6. **Activity Logging**: All auth events logged to `activity_logs` table

## Troubleshooting

### SSO Tab Not Showing
- Check that all Azure env variables are set
- Verify `sso_enabled` is true in login page context

### User Profile Not Created
- Verify users table exists in database
- Check DATABASE_URL is correct
- Review application logs for SQL errors

### Session Not Persisting
- Ensure SESSION_SECRET_KEY is set (not regenerated on restart)
- Check browser allows cookies
- Verify session middleware is properly configured

### SSO Redirect Loop
- Confirm REDIRECT_URI matches Azure AD config exactly
- Check `/auth/callback` route is accessible
- Verify state parameter matches

## Testing

### Local Testing

1. **Traditional Auth:**
   ```bash
   # Start server
   uvicorn backend.main:app --reload
   
   # Visit http://localhost:8000/login
   # Create account and login
   ```

2. **SSO (requires Azure config):**
   ```bash
   # Set env variables
   export AZURE_TENANT_ID=...
   export AZURE_CLIENT_ID=...
   export AZURE_CLIENT_SECRET=...
   export REDIRECT_URI=http://localhost:8000/auth/callback
   
   # Update Azure AD redirect URI to include localhost
   # Visit http://localhost:8000/login
   # Use SSO tab
   ```

### Production Testing

1. Visit `https://your-app.azurewebsites.net/login`
2. Test both tabs (Email and SSO)
3. Verify user profiles created in database
4. Check activity logs

## Migration Notes

### From Supabase Auth
If you were using Supabase authentication in Auth.tsx:
- Keep the old Auth.tsx for backward compatibility
- New users will use the unified `/login` page
- Existing Supabase users can create email/password accounts

### From Old SSO Implementation
- Old SSO setup is replaced by unified system
- User sessions are now database-backed
- Activity logs provide better audit trail

## Benefits

✅ **Unified Experience**: One login page for all auth methods  
✅ **User Profiles**: All users stored in your database  
✅ **Flexibility**: Users choose their preferred login method  
✅ **Audit Trail**: Activity logs track all auth events  
✅ **Scalability**: Easy to add more auth providers later  
✅ **Control**: You own the user data and authentication logic  

## Next Steps

1. **Customize Login UI**: Update `backend/templates/login.html` styling
2. **Add Password Reset**: Implement forgot password flow
3. **Email Verification**: Add email confirmation for new registrations
4. **Role-Based Access**: Use `user.role` for permission checks
5. **Admin Panel**: Build UI to manage users from database
6. **OAuth Providers**: Add Google, GitHub, etc. alongside Azure SSO

## Support

For issues or questions:
- Check application logs in Azure Portal
- Review `activity_logs` table for auth events
- Verify environment variables are set correctly
- Ensure database migrations completed successfully
