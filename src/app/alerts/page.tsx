
'use client';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase/client';

export default function AlertsPage() {
  const [rules, setRules] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      const { data: r } = await supabase.from('alert_rules').select('*').order('created_at', { ascending: false }).limit(100);
      setRules(r ?? []);
      const { data: l } = await supabase.from('alert_logs').select('*').order('created_at', { ascending: false }).limit(200);
      setLogs(l ?? []);
    })();
    const ch = supabase.channel('realtime:public:alert_logs')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'alert_logs' }, (p) => setLogs((s)=>[p.new, ...s].slice(0,200)))
      .subscribe();
    return () => { supabase.removeChannel(ch); }
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Alerts</h1>

      <section>
        <h2 className="text-xl mb-2">Rules</h2>
        <table className="w-full text-sm">
          <thead><tr className="text-left"><th>Name</th><th>Camera</th><th>Type</th><th>Threshold</th><th>Window(s)</th><th>Enabled</th></tr></thead>
          <tbody>
            {rules.map(r => (
              <tr key={r.id} className="border-b">
                <td className="py-2">{r.name}</td>
                <td className="font-mono">{r.camera_id}</td>
                <td>{r.rule_type}</td>
                <td>{r.threshold ?? '-'}</td>
                <td>{r.window_seconds ?? '-'}</td>
                <td>{String(r.enabled)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2 className="text-xl my-2">Recent Logs</h2>
        <table className="w-full text-sm">
          <thead><tr className="text-left"><th>Time</th><th>Status</th><th>Message</th><th>Event</th><th>Rule</th></tr></thead>
          <tbody>
            {logs.map(l => (
              <tr key={l.id} className="border-b">
                <td className="py-2">{new Date(l.created_at).toLocaleString()}</td>
                <td>{l.status}</td>
                <td className="text-xs">{l.message}</td>
                <td>{l.event_id}</td>
                <td className="font-mono">{l.alert_rule_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
