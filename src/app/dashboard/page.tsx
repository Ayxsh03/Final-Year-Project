'use client';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase/client';

export default function Dashboard() {
  const [events24, setEvents24] = useState<number>(0);
  const [activeCameras, setActiveCameras] = useState<number>(0);
  const [alerts24, setAlerts24] = useState<number>(0);
  const [stream, setStream] = useState<any[]>([]);

  useEffect(() => {
    const init = async () => {
      const since = new Date(Date.now() - 24*3600*1000).toISOString();
      const { count: e } = await supabase.from('events').select('*', { count: 'exact', head: true }).gte('occurred_at', since);
      setEvents24(e ?? 0);
      const { count: c } = await supabase.from('cameras').select('*', { count: 'exact', head: true }).eq('is_active', true);
      setActiveCameras(c ?? 0);
      const { count: a } = await supabase.from('alert_logs').select('*', { count: 'exact', head: true }).gte('created_at', since);
      setAlerts24(a ?? 0);
    };
    init();

    const channel = supabase.channel('realtime:public:events')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'events' }, (payload) => {
        setStream((s) => [payload.new, ...s].slice(0, 50));
        setEvents24((x) => x + 1);
      })
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded border">Events (24h): <strong>{events24}</strong></div>
        <div className="p-4 rounded border">Active Cameras: <strong>{activeCameras}</strong></div>
        <div className="p-4 rounded border">Alerts (24h): <strong>{alerts24}</strong></div>
      </div>
      <div>
        <h2 className="text-xl mt-6 mb-2">Live Stream</h2>
        <ul className="space-y-2">
          {stream.map((e, i) => (
            <li key={i} className="text-sm p-2 rounded bg-muted/20">
              <span className="font-mono">#{e.id}</span> {e.event_type} @ {new Date(e.occurred_at).toLocaleString()}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
