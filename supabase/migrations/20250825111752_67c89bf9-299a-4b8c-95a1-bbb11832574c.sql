-- Add missing get_dashboard_stats function for dashboard
CREATE OR REPLACE FUNCTION get_dashboard_stats()
RETURNS JSON AS $$
DECLARE
    stats JSON;
BEGIN
    SELECT json_build_object(
        'total_events', (SELECT COUNT(*) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE),
        'active_devices', (SELECT COUNT(*) FROM camera_devices WHERE status = 'online'),
        'inactive_devices', (SELECT COUNT(*) FROM camera_devices WHERE status = 'offline'),
        'online_devices', (SELECT COUNT(*) FROM camera_devices WHERE status = 'online'),
        'offline_devices', (SELECT COUNT(*) FROM camera_devices WHERE status = 'offline'),
        'people_detected', (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE),
        'events_trend', (
            SELECT CASE 
                WHEN prev_count = 0 THEN 0
                ELSE ROUND(((curr_count - prev_count)::DECIMAL / prev_count * 100), 1)
            END
            FROM (
                SELECT 
                    (SELECT COUNT(*) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE) as curr_count,
                    (SELECT COUNT(*) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE - INTERVAL '1 day') as prev_count
            ) trend_calc
        ),
        'devices_trend', 0,
        'people_trend', (
            SELECT CASE 
                WHEN prev_count = 0 THEN 0
                ELSE ROUND(((curr_count - prev_count)::DECIMAL / prev_count * 100), 1)
            END
            FROM (
                SELECT 
                    (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE) as curr_count,
                    (SELECT COUNT(DISTINCT person_id) FROM detection_events WHERE DATE(timestamp) = CURRENT_DATE - INTERVAL '1 day') as prev_count
            ) trend_calc
        )
    ) INTO stats;
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- Enable realtime for detection_events table
ALTER TABLE detection_events REPLICA IDENTITY FULL;
ALTER PUBLICATION supabase_realtime ADD TABLE detection_events;