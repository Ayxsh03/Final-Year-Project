# Azure SSO + Supabase Auth Integration Guide

## Overview

Your app now supports **TWO authentication methods**:

1. **Supabase Auth** (existing) - Email/password via frontend `Auth.tsx`
2. **Azure SSO** (new) - Microsoft account login with profile auto-creation

Both methods store user profiles in your existing **`profiles` table**. No duplicate tables needed!

---

## Architecture

### Authentication Flow

```
┌─────────────────┐
│   Visit /login  │
└────────┬────────┘
         │
         ├─── Option 1: SSO Login ────────────┐
         │    • Click "Sign in with Microsoft" │
         │    • Azure AD authentication        │
         │    • Profile created in `profiles`  │
         │    • Session created                │
         │    • Redirect to app ✅             │
         │                                     │
         └─── Option 2: Email Login ──────────┤
              • Click "Sign in with Email"    │
              • Navigate to `/auth` (Auth.tsx)│
              • Supabase Auth handles login   │
              • Profile in `profiles` exists  │
              • Supabase session created      │
              • Redirect to app ✅             │
                                               │
              Both methods ──> Same App! ─────┘
```

### Database: Your Existing `profiles` Table

**Before SSO (original):**
- `id` (uuid, PK, FK to auth.users.id)
- `email`, `full_name`, `role`
- `created_at`, `updated_at`

**After SSO (enhanced):**
- All existing columns **+**
- `auth_provider` (text) - `'supabase'` or `'azure_sso'`
- `azure_id` (text) - Azure AD user ID
- `last_login` (timestamptz) - Track logins

---

## Setup Instructions

### 1. Update Your Supabase Database

Run this SQL in Supabase SQL Editor:

```sql
-- Add SSO support columns
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS auth_provider TEXT DEFAULT 'supabase',
ADD COLUMN IF NOT EXISTS azure_id TEXT,
ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ;

-- Add check constraint
ALTER TABLE public.profiles
ADD CONSTRAINT profiles_auth_provider_check
CHECK (auth_provider IN ('supabase', 'azure_sso'));

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_profiles_azure_id ON public.profiles(azure_id);
CREATE INDEX IF NOT EXISTS idx_profiles_auth_provider ON public.profiles(auth_provider);
```

**This is safe!** It adds columns without affecting existing data.

### 2. Configure Azure Environment Variables

In Azure App Service → Configuration → Application settings:

```env
# Existing (keep these)
DATABASE_URL=postgresql://...your-supabase-connection...
SESSION_SECRET_KEY=<your-generated-secret>

# New SSO settings
AZURE_TENANT_ID=<your-azure-tenant-id>
AZURE_CLIENT_ID=<your-app-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
REDIRECT_URI=https://your-app.azurewebsites.net/auth/callback
ALLOWED_DOMAIN=<optional-email-domain>  # e.g., fourthpartner.co
APP_NAME=FpelAICCTV Person Detection
```

### 3. Azure AD App Registration Setup

1. **Redirect URI:**
   - Go to Azure Portal → Azure AD → App registrations → Your app
   - Authentication → Add redirect URI:
     ```
     https://your-app.azurewebsites.net/auth/callback
     ```

2. **API Permissions:**
   - API permissions → Add permission
   - Microsoft Graph → Delegated permissions
   - Add: `User.Read`
   - Click "Grant admin consent"

3. **Client Secret:**
   - Certificates & secrets → New client secret
   - Copy the **Value** (not the ID) to `AZURE_CLIENT_SECRET`

### 4. Deploy Code Changes

```bash
# Your backend changes are ready
git add .
git commit -m "Add Azure SSO alongside Supabase Auth"
git push origin main
```

---

## How It Works

### For Supabase Users (Existing Flow - No Change)

1. User visits `/auth` (your Auth.tsx page)
2. Signs in/up with Supabase
3. Profile exists in `profiles` table with `auth_provider='supabase'`
4. Supabase session manages authentication
5. App works as before ✅

### For SSO Users (New Flow)

1. User visits `/login`
2. Clicks "Sign in with Microsoft"
3. Redirected to Azure AD
4. After Azure login, backend:
   - Checks if profile exists (by email or Azure ID)
   - If exists: Updates `last_login`, links `azure_id`
   - If new: Creates profile with `auth_provider='azure_sso'`
5. Backend creates session (separate from Supabase)
6. User redirected to app ✅

### Mixed Usage Example

**Scenario:** User has Supabase account, then uses SSO

1. Profile exists: `user@company.com`, `auth_provider='supabase'`
2. User clicks "Sign in with Microsoft" with same email
3. Backend finds existing profile by email
4. Updates: `azure_id='xyz'`, `last_login=NOW()`
5. **Does NOT change** `auth_provider='supabase'`
6. User can now login via **either method** ✅

---

## User Experience

### Login Page (`/login`)

**If SSO is configured:**
```
┌──────────────────────────────────┐
│   🔐 FpelAICCTV Person Detection │
│      Secure Authentication       │
├──────────────────────────────────┤
│                                  │
│  [🔲 Sign in with Microsoft]    │
│                                  │
│  🏢 SSO is restricted to         │
│     @yourcompany.com accounts    │
│                                  │
│        ────── OR ──────          │
│                                  │
│  [📧 Sign in with Email]         │
│                                  │
│  🔒 Secured by Azure AD          │
│      & Supabase Auth             │
└──────────────────────────────────┘
```

**If SSO not configured:**
```
┌──────────────────────────────────┐
│   🔐 FpelAICCTV Person Detection │
├──────────────────────────────────┤
│                                  │
│  SSO is not configured.          │
│  Please use traditional login.   │
│                                  │
│  [📧 Sign in with Email]         │
└──────────────────────────────────┘
```

---

## API Endpoints

### SSO Routes (Backend - New)

- `GET /login` - Shows login page with SSO option
- `GET /login/sso` - Initiates Azure SSO flow
- `GET /auth/callback` - Handles SSO callback, creates/links profile
- `GET /logout` - Clears session (SSO users)
- `GET /api/v1/user` - Returns current user from session

### Supabase Auth Routes (Frontend - Existing)

- `/auth` - Your Auth.tsx component (unchanged)
- Supabase client handles all auth operations

---

## Session Management

### SSO Users (Backend Session)
- Session stored in backend (SessionMiddleware)
- Contains: `id`, `email`, `name`, `role`, `auth_provider`
- Expires after 24 hours or browser close
- Cleared on `/logout`

### Supabase Users (Supabase Session)
- Session managed by Supabase client
- Frontend `Auth.tsx` checks `supabase.auth.getSession()`
- Independent from backend SSO session

### Checking Authentication in Frontend

```typescript
// For Supabase users (existing)
const { data: { session } } = await supabase.auth.getSession();
if (session) {
  // User is logged in via Supabase
}

// For SSO users (new - if you want to check from frontend)
const response = await fetch('/api/v1/user');
if (response.ok) {
  const user = await response.json();
  // User is logged in via SSO
}
```

---

## Security Features

### SSO
- ✅ CSRF protection (state parameter)
- ✅ Domain restriction (optional)
- ✅ Tenant validation
- ✅ Signed sessions with secret key
- ✅ Activity logging in `activity_logs`

### Supabase Auth
- ✅ Email verification
- ✅ Password strength requirements
- ✅ JWT tokens
- ✅ RLS policies (your existing setup)

---

## Testing

### Test SSO Flow

1. Visit `https://your-app.azurewebsites.net/login`
2. Click "Sign in with Microsoft"
3. Authenticate with Microsoft account
4. Should redirect to app with session
5. Check `profiles` table for new entry with `auth_provider='azure_sso'`
6. Check `activity_logs` for login event

### Test Supabase Flow (Should Still Work)

1. Visit `https://your-app.azurewebsites.net/auth`
2. Sign in with email/password
3. Should work as before
4. Profile in `profiles` with `auth_provider='supabase'`

### Test Cross-Login

1. Create Supabase account: `test@company.com`
2. Then login via SSO with same email
3. Should link accounts and work seamlessly

---

## Troubleshooting

### SSO not showing on login page
- ✅ Check all Azure env vars are set
- ✅ Verify `AZURE_TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET` are correct
- ✅ Check login page shows "SSO is not configured" message

### Profile not created after SSO
- ✅ Check `DATABASE_URL` is correct (Supabase connection string)
- ✅ Run the SQL migration to add columns
- ✅ Check application logs for SQL errors
- ✅ Verify `profiles` table exists

### Redirect loop after SSO
- ✅ Verify `REDIRECT_URI` matches Azure AD exactly
- ✅ Check `/auth/callback` is accessible
- ✅ Ensure `SESSION_SECRET_KEY` is set (persistent)

### Can't login with Supabase anymore
- ✅ `/auth` route should still work
- ✅ Check `Auth.tsx` is still in frontend
- ✅ Verify Supabase client is configured
- ✅ This integration **does not affect** Supabase auth

---

## Database Schema Reference

### profiles table (After Migration)

```sql
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  role TEXT DEFAULT 'viewer',
  
  -- SSO additions
  auth_provider TEXT DEFAULT 'supabase',
  azure_id TEXT,
  last_login TIMESTAMPTZ,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE,
  CHECK (role IN ('admin', 'operator', 'viewer')),
  CHECK (auth_provider IN ('supabase', 'azure_sso'))
);
```

### activity_logs table (Already Exists)

```sql
-- This table already references profiles/auth.users
-- SSO login events will be logged here automatically
```

---

## Benefits of This Approach

✅ **No duplicate tables** - Uses your existing `profiles`  
✅ **Backward compatible** - Supabase auth still works  
✅ **Flexible** - Users can choose their login method  
✅ **Enterprise ready** - SSO for organizations  
✅ **Self-service** - Email/password for individuals  
✅ **Unified profiles** - All users in one table  
✅ **Activity tracking** - Audit trail in `activity_logs`  
✅ **Domain control** - Restrict SSO by email domain  

---

## Migration Notes

### Existing Supabase Users
- ✅ **No action needed**
- ✅ Continue using `/auth` page
- ✅ Profiles remain unchanged
- ✅ Can optionally link SSO later

### New Users
- Can choose SSO or email signup
- Both methods create profile in same table
- Experience is seamless

---

## Next Steps

### Immediate
1. ✅ Run SQL migration on Supabase
2. ✅ Set Azure environment variables
3. ✅ Configure Azure AD redirect URI
4. ✅ Deploy and test

### Optional Enhancements
- Add logout button that handles both auth types
- Show auth provider badge in user profile UI
- Add admin panel to view auth methods
- Implement password reset for email users
- Add more OAuth providers (Google, GitHub)

---

## Support

**For SSO issues:**
- Check Azure App Service logs
- Review `activity_logs` table for events
- Verify Azure AD configuration

**For Supabase issues:**
- Check Supabase dashboard
- Review auth logs in Supabase
- Test with Supabase CLI

Your existing Supabase auth continues to work unchanged! SSO is simply an additional option. 🚀
