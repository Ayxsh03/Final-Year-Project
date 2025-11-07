-- Add SSO support to existing profiles table
-- Run this on your Supabase database

-- Add columns for SSO tracking
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS auth_provider TEXT DEFAULT 'supabase',
ADD COLUMN IF NOT EXISTS azure_id TEXT,
ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ;

-- Add check constraint for auth_provider
ALTER TABLE public.profiles
DROP CONSTRAINT IF EXISTS profiles_auth_provider_check;

ALTER TABLE public.profiles
ADD CONSTRAINT profiles_auth_provider_check
CHECK (auth_provider IN ('supabase', 'azure_sso'));

-- Create index for Azure ID lookups
CREATE INDEX IF NOT EXISTS idx_profiles_azure_id ON public.profiles(azure_id);
CREATE INDEX IF NOT EXISTS idx_profiles_auth_provider ON public.profiles(auth_provider);

-- Update activity_logs to reference profiles
-- (activity_logs already references auth.users.id which profiles.id links to)

COMMENT ON COLUMN public.profiles.auth_provider IS 'Authentication provider: supabase or azure_sso';
COMMENT ON COLUMN public.profiles.azure_id IS 'Azure AD user ID for SSO users';
COMMENT ON COLUMN public.profiles.last_login IS 'Last login timestamp';
