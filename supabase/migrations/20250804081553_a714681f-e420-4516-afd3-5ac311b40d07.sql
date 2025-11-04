-- Create camera_devices table
CREATE TABLE public.camera_devices (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  name VARCHAR NOT NULL,
  rtsp_url VARCHAR NOT NULL,
  status VARCHAR DEFAULT 'offline' CHECK (status IN ('online', 'offline')),
  location VARCHAR,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create detection_events table
CREATE TABLE public.detection_events (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  person_id INTEGER NOT NULL,
  confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  camera_id UUID NOT NULL REFERENCES public.camera_devices(id),
  camera_name VARCHAR,
  image_path VARCHAR,
  alert_sent BOOLEAN DEFAULT false,
  metadata JSONB DEFAULT '{}'::jsonb,
  bbox_x1 DECIMAL,
  bbox_y1 DECIMAL, 
  bbox_x2 DECIMAL,
  bbox_y2 DECIMAL
);

-- Create alert_logs table
CREATE TABLE public.alert_logs (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  event_id UUID REFERENCES public.detection_events(id),
  camera_id UUID NOT NULL REFERENCES public.camera_devices(id),
  alert_type VARCHAR NOT NULL,
  status VARCHAR DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'retry')),
  message TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  sent_at TIMESTAMP WITH TIME ZONE,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Create user profiles table for authentication
CREATE TABLE public.profiles (
  id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  role TEXT DEFAULT 'viewer' CHECK (role IN ('admin', 'operator', 'viewer')),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.camera_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.detection_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create indexes for performance
CREATE INDEX idx_detection_events_timestamp ON public.detection_events(timestamp DESC);
CREATE INDEX idx_detection_events_camera_id ON public.detection_events(camera_id);
CREATE INDEX idx_detection_events_person_id ON public.detection_events(person_id);
CREATE INDEX idx_camera_devices_status ON public.camera_devices(status);
CREATE INDEX idx_alert_logs_event_id ON public.alert_logs(event_id);
CREATE INDEX idx_alert_logs_status ON public.alert_logs(status);

-- Create function for user role checking (security definer to avoid RLS recursion)
CREATE OR REPLACE FUNCTION public.get_user_role(user_id UUID)
RETURNS TEXT
LANGUAGE SQL
SECURITY DEFINER
STABLE
AS $$
  SELECT role FROM public.profiles WHERE id = user_id;
$$;

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_camera_devices_updated_at
  BEFORE UPDATE ON public.camera_devices
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- RLS Policies for camera_devices
CREATE POLICY "Users can view cameras based on role" 
  ON public.camera_devices FOR SELECT 
  USING (
    CASE 
      WHEN public.get_user_role(auth.uid()) = 'admin' THEN true
      WHEN public.get_user_role(auth.uid()) IN ('operator', 'viewer') THEN true
      ELSE false
    END
  );

CREATE POLICY "Admins can manage cameras" 
  ON public.camera_devices FOR ALL 
  USING (public.get_user_role(auth.uid()) = 'admin');

-- RLS Policies for detection_events  
CREATE POLICY "Users can view events based on role"
  ON public.detection_events FOR SELECT
  USING (
    CASE 
      WHEN public.get_user_role(auth.uid()) = 'admin' THEN true
      WHEN public.get_user_role(auth.uid()) IN ('operator', 'viewer') THEN true
      ELSE false
    END
  );

CREATE POLICY "Admins and operators can manage events"
  ON public.detection_events FOR ALL
  USING (public.get_user_role(auth.uid()) IN ('admin', 'operator'));

-- RLS Policies for alert_logs
CREATE POLICY "Users can view alerts based on role"
  ON public.alert_logs FOR SELECT
  USING (
    CASE 
      WHEN public.get_user_role(auth.uid()) = 'admin' THEN true
      WHEN public.get_user_role(auth.uid()) IN ('operator', 'viewer') THEN true
      ELSE false
    END
  );

CREATE POLICY "Admins and operators can manage alerts"
  ON public.alert_logs FOR ALL
  USING (public.get_user_role(auth.uid()) IN ('admin', 'operator'));

-- RLS Policies for profiles
CREATE POLICY "Users can view their own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles"
  ON public.profiles FOR SELECT
  USING (public.get_user_role(auth.uid()) = 'admin');

CREATE POLICY "Admins can manage all profiles"
  ON public.profiles FOR ALL
  USING (public.get_user_role(auth.uid()) = 'admin');

-- Function to handle new user registration
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, role)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
    'viewer'  -- Default role
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on user signup
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Insert sample camera device
INSERT INTO public.camera_devices (name, rtsp_url, status, location)
VALUES ('Camera 01', 'rtsp://localhost:8554/camera1', 'online', 'Main Entrance');