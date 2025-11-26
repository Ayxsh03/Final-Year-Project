-- Person Detection System Database Schema (SQL Server)

-- Camera devices table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'camera_devices')
BEGIN
    CREATE TABLE camera_devices (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        name NVARCHAR(100) NOT NULL,
        rtsp_url NVARCHAR(500) NOT NULL,
        status NVARCHAR(20) DEFAULT 'offline' CHECK (status IN ('online', 'offline')),
        location NVARCHAR(200),
        last_heartbeat DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        updated_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
    );
END;
GO

-- Detection events table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'detection_events')
BEGIN
    CREATE TABLE detection_events (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        timestamp DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        person_id INTEGER NOT NULL,
        confidence DECIMAL(4,3) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
        camera_id UNIQUEIDENTIFIER NOT NULL REFERENCES camera_devices(id),
        camera_name NVARCHAR(100) NOT NULL,
        image_path NVARCHAR(500),
        alert_sent BIT DEFAULT 0,
        metadata NVARCHAR(MAX) DEFAULT '{}', -- JSON stored as string
        bbox_x1 NUMERIC(10,4),
        bbox_y1 NUMERIC(10,4),
        bbox_x2 NUMERIC(10,4),
        bbox_y2 NUMERIC(10,4),
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
    );
END;
GO

-- Alert logs table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'alert_logs')
BEGIN
    CREATE TABLE alert_logs (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        event_id UNIQUEIDENTIFIER REFERENCES detection_events(id),
        camera_id UNIQUEIDENTIFIER REFERENCES camera_devices(id),
        alert_type NVARCHAR(50) NOT NULL CHECK (alert_type IN ('telegram', 'siren', 'ip', 'manual')),
        status NVARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'retry')),
        message NVARCHAR(MAX),
        error_details NVARCHAR(MAX),
        sent_at DATETIMEOFFSET,
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
    );
END;
GO

-- Alert settings table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'alert_settings')
BEGIN
    CREATE TABLE alert_settings (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        enabled BIT DEFAULT 1,
        
        -- Email settings
        notify_email BIT DEFAULT 0,
        smtp_host NVARCHAR(255),
        smtp_port INTEGER DEFAULT 465,
        smtp_username NVARCHAR(255),
        smtp_password NVARCHAR(255),
        smtp_from NVARCHAR(255),
        email_to NVARCHAR(MAX), -- comma-separated emails
        
        -- WhatsApp settings
        notify_whatsapp BIT DEFAULT 0,
        whatsapp_phone_number_id NVARCHAR(255),
        whatsapp_token NVARCHAR(MAX),
        whatsapp_to NVARCHAR(50), -- E.164 format
        
        -- Telegram settings
        notify_telegram BIT DEFAULT 0,
        telegram_bot_token NVARCHAR(255),
        telegram_chat_id NVARCHAR(255),
        
        -- Scheduling settings
        -- SQL Server doesn't have native array type, storing as comma-separated string or JSON
        allowed_days NVARCHAR(MAX) DEFAULT 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday',
        start_time TIME,
        end_time TIME,
        timezone NVARCHAR(50) DEFAULT 'UTC',
        
        -- Report settings
        daily_report_enabled BIT DEFAULT 0,
        weekly_report_enabled BIT DEFAULT 0,
        monthly_report_enabled BIT DEFAULT 0,
        
        -- VIP and regular customer notification settings
        notify_vip_email BIT DEFAULT 0,
        notify_regular_email BIT DEFAULT 0,
        notify_attendance_to_branch BIT DEFAULT 0,
        
        -- Google Places API (from frontend)
        google_places_api_key NVARCHAR(255),
        
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        updated_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
    );
END;
GO

-- Profiles table (for user authentication and SSO)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'profiles')
BEGIN
    CREATE TABLE profiles (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        email NVARCHAR(255) UNIQUE NOT NULL,
        full_name NVARCHAR(255),
        auth_provider NVARCHAR(50) DEFAULT 'email' CHECK (auth_provider IN ('email', 'azure_sso', 'supabase')),
        azure_id NVARCHAR(255), -- Azure AD user ID for SSO
        password_hash NVARCHAR(255), -- For email/password users (nullable for SSO)
        role NVARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'operator', 'viewer', 'user')),
        last_login DATETIMEOFFSET,
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
        updated_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
    );
END;
GO

-- Activity logs table (for tracking user actions)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'activity_logs')
BEGIN
    CREATE TABLE activity_logs (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        user_id UNIQUEIDENTIFIER REFERENCES profiles(id) ON DELETE SET NULL,
        action NVARCHAR(100) NOT NULL,
        email NVARCHAR(255),
        message NVARCHAR(MAX),
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
    );
END;
GO

-- Indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_detection_events_timestamp' AND object_id = OBJECT_ID('detection_events'))
    CREATE INDEX idx_detection_events_timestamp ON detection_events(timestamp DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_detection_events_camera_id' AND object_id = OBJECT_ID('detection_events'))
    CREATE INDEX idx_detection_events_camera_id ON detection_events(camera_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_detection_events_person_id' AND object_id = OBJECT_ID('detection_events'))
    CREATE INDEX idx_detection_events_person_id ON detection_events(person_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_camera_devices_status' AND object_id = OBJECT_ID('camera_devices'))
    CREATE INDEX idx_camera_devices_status ON camera_devices(status);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_alert_logs_event_id' AND object_id = OBJECT_ID('alert_logs'))
    CREATE INDEX idx_alert_logs_event_id ON alert_logs(event_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_alert_settings_updated_at' AND object_id = OBJECT_ID('alert_settings'))
    CREATE INDEX idx_alert_settings_updated_at ON alert_settings(updated_at DESC);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_profiles_email' AND object_id = OBJECT_ID('profiles'))
    CREATE INDEX idx_profiles_email ON profiles(email);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_profiles_azure_id' AND object_id = OBJECT_ID('profiles'))
    CREATE INDEX idx_profiles_azure_id ON profiles(azure_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_profiles_auth_provider' AND object_id = OBJECT_ID('profiles'))
    CREATE INDEX idx_profiles_auth_provider ON profiles(auth_provider);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_activity_logs_user_id' AND object_id = OBJECT_ID('activity_logs'))
    CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_activity_logs_created_at' AND object_id = OBJECT_ID('activity_logs'))
    CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at DESC);
GO

-- Insert default settings
IF NOT EXISTS (SELECT * FROM alert_settings)
BEGIN
    INSERT INTO alert_settings (enabled) VALUES (1);
END;
GO

-- Insert sample camera
IF NOT EXISTS (SELECT * FROM camera_devices WHERE name = 'Office Camera')
BEGIN
    INSERT INTO camera_devices (name, rtsp_url, status, location) VALUES 
    ('Office Camera', 'rtsp://admin:4PEL%232025@192.168.29.134:554/h264', 'online', 'Main Office');
END;
GO

-- Stored Procedures

-- Update camera heartbeat
CREATE OR ALTER PROCEDURE update_camera_heartbeat
    @camera_name_param NVARCHAR(100)
AS
BEGIN
    UPDATE camera_devices 
    SET last_heartbeat = SYSDATETIMEOFFSET(), 
        status = 'online',
        updated_at = SYSDATETIMEOFFSET()
    WHERE name = @camera_name_param;
END;
GO

-- Get dashboard stats
CREATE OR ALTER PROCEDURE get_dashboard_stats
AS
BEGIN
    DECLARE @total_events INT;
    DECLARE @active_devices INT;
    DECLARE @inactive_devices INT;
    DECLARE @online_devices INT;
    DECLARE @offline_devices INT;
    DECLARE @people_detected INT;
    DECLARE @events_trend DECIMAL(10,1);
    DECLARE @people_trend DECIMAL(10,1);
    
    SELECT @total_events = COUNT(*) FROM detection_events WHERE CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE);
    SELECT @active_devices = COUNT(*) FROM camera_devices WHERE status = 'online';
    SELECT @inactive_devices = COUNT(*) FROM camera_devices WHERE status = 'offline';
    SELECT @online_devices = COUNT(*) FROM camera_devices WHERE status = 'online';
    SELECT @offline_devices = COUNT(*) FROM camera_devices WHERE status = 'offline';
    SELECT @people_detected = COUNT(DISTINCT person_id) FROM detection_events WHERE CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE);
    
    -- Trends
    WITH trend_calc AS (
        SELECT 
            (SELECT COUNT(*) FROM detection_events WHERE CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE)) as curr_count,
            (SELECT COUNT(*) FROM detection_events WHERE CAST(timestamp AS DATE) = DATEADD(day, -1, CAST(SYSDATETIMEOFFSET() AS DATE))) as prev_count
    )
    SELECT @events_trend = CASE 
        WHEN prev_count = 0 THEN 0
        ELSE CAST((curr_count - prev_count) AS DECIMAL) / prev_count * 100
    END
    FROM trend_calc;

    WITH trend_calc AS (
        SELECT 
            (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE CAST(timestamp AS DATE) = CAST(SYSDATETIMEOFFSET() AS DATE)) as curr_count,
            (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE CAST(timestamp AS DATE) = DATEADD(day, -1, CAST(SYSDATETIMEOFFSET() AS DATE))) as prev_count
    )
    SELECT @people_trend = CASE 
        WHEN prev_count = 0 THEN 0
        ELSE CAST((curr_count - prev_count) AS DECIMAL) / prev_count * 100
    END
    FROM trend_calc;

    SELECT 
        @total_events as total_events,
        @active_devices as active_devices,
        @inactive_devices as inactive_devices,
        @online_devices as online_devices,
        @offline_devices as offline_devices,
        @people_detected as people_detected,
        ISNULL(@events_trend, 0) as events_trend,
        0 as devices_trend,
        ISNULL(@people_trend, 0) as people_trend;
END;
GO
