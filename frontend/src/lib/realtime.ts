import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { supabase } from "../integrations/supabase/client";

/**
 * Subscribes to Supabase Realtime on detection_events and camera_devices
 * and invalidates React Query caches so UI updates instantly.
 */
export function useRealtimeSync() {
  const qc = useQueryClient();

  useEffect(() => {
    const chEvents = supabase
      .channel("realtime:detection_events")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "detection_events" },
        () => {
          qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
          qc.invalidateQueries({ queryKey: ["hourly-trends"] });
          qc.invalidateQueries({ queryKey: ["daily-trends"] });
          qc.invalidateQueries({ queryKey: ["events"] });
        }
      )
      .subscribe();

    const chCams = supabase
      .channel("realtime:camera_devices")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "camera_devices" },
        () => {
          qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
          qc.invalidateQueries({ queryKey: ["cameras"] });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(chEvents);
      supabase.removeChannel(chCams);
    };
  }, [qc]);
}
