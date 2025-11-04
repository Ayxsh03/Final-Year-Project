-- Enable realtime for detection_events table
ALTER TABLE public.detection_events REPLICA IDENTITY FULL;

-- Add table to realtime publication
ALTER PUBLICATION supabase_realtime ADD TABLE public.detection_events;

-- Enable realtime for camera_devices table  
ALTER TABLE public.camera_devices REPLICA IDENTITY FULL;
ALTER PUBLICATION supabase_realtime ADD TABLE public.camera_devices;