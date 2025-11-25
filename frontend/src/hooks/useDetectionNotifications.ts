import { useEffect } from 'react';
import { useToast } from './use-toast';

/**
 * Detection notifications hook
 * Realtime disabled - Supabase removed
 * TODO: Implement SSE or WebSocket for push notifications
 */
export function useDetectionNotifications() {
  const { toast } = useToast();

  useEffect(() => {
    // Realtime notifications disabled
    console.log('Detection notifications disabled - realtime feature pending implementation');

    return () => {
      // No cleanup needed
    };
  }, [toast]);
}
