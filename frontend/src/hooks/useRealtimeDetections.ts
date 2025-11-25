import { useEffect, useState } from 'react';

/**
 * Realtime detections hook
 * Realtime disabled - Supabase removed
 * TODO: Implement SSE or WebSocket for realtime detection updates
 */
export function useRealtimeDetections() {
  const [detections, setDetections] = useState<any[]>([]);

  useEffect(() => {
    // Realtime disabled
    console.log('Realtime detections disabled - using polling via React Query');

    return () => {
      // No cleanup needed
    };
  }, []);

  return { detections };
}