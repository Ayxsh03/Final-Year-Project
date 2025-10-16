
'use client';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase/client';

export default function EventsPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [cameraId, setCameraId] = useState('');
  const [type, setType] = useState('');
  const [minConf, setMinConf] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  async function load() {
    setLoading(true);
    let q = supabase.from('events').select('*').order('occurred_at', { ascending: false }).limit(500);
    if (cameraId) q = q.eq('camera_id', cameraId);
    if (type) q = q.eq('event_type', type);
    if (minConf) q = q.gte('confidence', Number(minConf));
    if (start) q = q.gte('occurred_at', start);
    if (end) q = q.lte('occurred_at', end);
    const { data } = await q;
    setEvents(data ?? []);
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  async function onExport(kind: 'both'|'csv'|'parquet') {
    setExporting(true);
    const res = await fetch('/api/exports', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ camera_id: cameraId || undefined, type: type || undefined, min_conf: minConf ? Number(minConf) : undefined, start: start || undefined, end: end || undefined })
    });
    const json = await res.json();
    setExporting(false);
    if (json.csv_url && (kind === 'both' || kind === 'csv')) window.open(json.csv_url, '_blank');
    if (json.parquet_url && (kind === 'both' || kind === 'parquet')) window.open(json.parquet_url, '_blank');
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">Events</h1>

      <div className="grid grid-cols-1 md:grid-cols-6 gap-2 mb-4">
        <input className="border rounded px-2 py-1" placeholder="Camera ID" value={cameraId} onChange={e=>setCameraId(e.target.value)} />
        <select className="border rounded px-2 py-1" value={type} onChange={e=>setType(e.target.value)}>
          <option value="">Any type</option>
          <option value="person_detected">person_detected</option>
          <option value="person_lost">person_lost</option>
          <option value="heartbeat">heartbeat</option>
          <option value="system">system</option>
        </select>
        <input className="border rounded px-2 py-1" placeholder="Min confidence" value={minConf} onChange={e=>setMinConf(e.target.value)} />
        <input className="border rounded px-2 py-1" type="datetime-local" value={start} onChange={e=>setStart(e.target.value)} />
        <input className="border rounded px-2 py-1" type="datetime-local" value={end} onChange={e=>setEnd(e.target.value)} />
        <button className="border rounded px-2 py-1" onClick={load}>Apply</button>
      </div>

      <div className="flex gap-2 mb-4">
        <button className="border rounded px-2 py-1" onClick={()=>onExport('csv')} disabled={exporting}>Download CSV</button>
        <button className="border rounded px-2 py-1" onClick={()=>onExport('parquet')} disabled={exporting}>Download Parquet</button>
      </div>

      {loading ? <div>Loading…</div> : (
        <div className="overflow-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left"><th>ID</th><th>Type</th><th>Camera</th><th>Conf</th><th>Time</th></tr></thead>
            <tbody>
              {events.map(e => (
                <tr key={e.id} className="border-b">
                  <td className="py-2">{e.id}</td>
                  <td>{e.event_type}</td>
                  <td className="font-mono">{e.camera_id}</td>
                  <td>{e.confidence ?? '-'}</td>
                  <td>{new Date(e.occurred_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
