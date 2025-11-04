-- Insert real camera devices
INSERT INTO public.camera_devices (name, rtsp_url, location, status) VALUES
('Front Door Camera', 'rtsp://admin:password123@192.168.1.100:554/Streaming/Channels/101', 'Front Entrance', 'offline'),
('Parking Lot Camera', 'rtsp://admin:password123@192.168.1.101:554/Streaming/Channels/101', 'Parking Area', 'offline'),
('Back Office Camera', 'rtsp://admin:password123@192.168.1.102:554/Streaming/Channels/101', 'Back Office', 'offline');