import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';

export const useRealtimeDetections = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Subscribe to real-time detection events
    const channel = supabase
      .channel('detection-events-realtime')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'detection_events'
        },
        (payload) => {
          console.log('New detection event:', payload);
          
          // Invalidate and refetch relevant queries
          queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
          queryClient.invalidateQueries({ queryKey: ['detection-events'] });
          queryClient.invalidateQueries({ queryKey: ['hourly-data'] });
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'camera_devices'
        },
        (payload) => {
          console.log('Camera status updated:', payload);
          
          // Invalidate camera-related queries
          queryClient.invalidateQueries({ queryKey: ['cameras'] });
          queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [queryClient]);
};