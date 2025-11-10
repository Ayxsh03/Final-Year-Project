-- Disable RLS on data tables accessed by backend API
-- The backend has its own API key authentication layer, so RLS is not needed for these tables
-- This fixes the issue where backend queries were being blocked by RLS policies

-- Drop existing policies on camera_devices
DROP POLICY IF EXISTS "Users can view cameras based on role" ON public.camera_devices;
DROP POLICY IF EXISTS "Admins can manage cameras" ON public.camera_devices;

-- Drop existing policies on detection_events
DROP POLICY IF EXISTS "Users can view events based on role" ON public.detection_events;
DROP POLICY IF EXISTS "Admins and operators can manage events" ON public.detection_events;

-- Drop existing policies on alert_logs
DROP POLICY IF EXISTS "Users can view alerts based on role" ON public.alert_logs;
DROP POLICY IF EXISTS "Admins and operators can manage alerts" ON public.alert_logs;

-- Disable RLS on data tables
ALTER TABLE public.camera_devices DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.detection_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_logs DISABLE ROW LEVEL SECURITY;

-- Note: profiles and activity_logs keep RLS enabled for security
-- These tables are accessed directly via Supabase client with user JWT tokens
