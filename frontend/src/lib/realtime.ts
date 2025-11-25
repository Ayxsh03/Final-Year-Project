import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

/**
 * Realtime sync disabled - Supabase removed.
 * TODO: Implement Server-Sent Events (SSE) or WebSocket for realtime updates.
 * For now, React Query will use polling intervals to keep data fresh.
 */
export function useRealtimeSync() {
  const qc = useQueryClient();

  useEffect(() => {
    // Realtime subscriptions disabled
    // Using React Query's refetchInterval for polling instead
    console.log('Realtime sync disabled - using polling');

    // Cleanup function (empty for now)
    return () => {
      // No subscriptions to clean up
    };
  }, [qc]);
}
