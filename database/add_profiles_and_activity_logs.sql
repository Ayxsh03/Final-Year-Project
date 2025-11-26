-- Add profiles and activity_logs tables for SSO authentication support
-- SQL Server migration script
-- Run this on your Azure SQL Server database

-- ============================================================================
-- PROFILES TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'profiles')
BEGIN
    CREATE TABLE dbo.profiles (
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
    
    PRINT 'Created table: dbo.profiles';
END
ELSE
BEGIN
    PRINT 'Table dbo.profiles already exists, skipping creation';
END;
GO

-- ============================================================================
-- ACTIVITY LOGS TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'activity_logs')
BEGIN
    CREATE TABLE dbo.activity_logs (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        user_id UNIQUEIDENTIFIER REFERENCES dbo.profiles(id) ON DELETE SET NULL,
        action NVARCHAR(100) NOT NULL,
        email NVARCHAR(255),
        message NVARCHAR(MAX),
        created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
    );
    
    PRINT 'Created table: dbo.activity_logs';
END
ELSE
BEGIN
    PRINT 'Table dbo.activity_logs already exists, skipping creation';
END;
GO

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Profiles indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_profiles_email' AND object_id = OBJECT_ID('dbo.profiles'))
BEGIN
    CREATE INDEX idx_profiles_email ON dbo.profiles(email);
    PRINT 'Created index: idx_profiles_email';
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_profiles_azure_id' AND object_id = OBJECT_ID('dbo.profiles'))
BEGIN
    CREATE INDEX idx_profiles_azure_id ON dbo.profiles(azure_id);
    PRINT 'Created index: idx_profiles_azure_id';
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_profiles_auth_provider' AND object_id = OBJECT_ID('dbo.profiles'))
BEGIN
    CREATE INDEX idx_profiles_auth_provider ON dbo.profiles(auth_provider);
    PRINT 'Created index: idx_profiles_auth_provider';
END;

-- Activity logs indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_activity_logs_user_id' AND object_id = OBJECT_ID('dbo.activity_logs'))
BEGIN
    CREATE INDEX idx_activity_logs_user_id ON dbo.activity_logs(user_id);
    PRINT 'Created index: idx_activity_logs_user_id';
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_activity_logs_created_at' AND object_id = OBJECT_ID('dbo.activity_logs'))
BEGIN
    CREATE INDEX idx_activity_logs_created_at ON dbo.activity_logs(created_at DESC);
    PRINT 'Created index: idx_activity_logs_created_at';
END;

GO

-- ============================================================================
-- VERIFICATION
-- ============================================================================
PRINT '';
PRINT '========================================';
PRINT 'Migration Complete!';
PRINT '========================================';
PRINT '';
PRINT 'Tables created:';
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE' 
AND TABLE_NAME IN ('profiles', 'activity_logs')
ORDER BY TABLE_NAME;

PRINT '';
PRINT 'You can now deploy the application with SSO authentication support.';
GO
