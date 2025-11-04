import { useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useNotifications } from '@/contexts/NotificationContext';

export const useDetectionNotifications = () => {
  const { addNotification } = useNotifications();

  useEffect(() => {
    // Subscribe to new detection events
    const channel = supabase
      .channel('detection-notifications')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'detection_events'
        },
        (payload) => {
          const event = payload.new as any;
          
          // Create notification for new detection
          addNotification({
            type: 'detection',
            title: 'New Person Detected',
            message: `Person detected at ${event.camera_name} with ${Math.round(event.confidence * 100)}% confidence`,
            data: {
              eventId: event.id,
              cameraId: event.camera_id,
              cameraName: event.camera_name,
              confidence: event.confidence,
              timestamp: event.timestamp,
              imagePath: event.image_path
            }
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [addNotification]);
};
