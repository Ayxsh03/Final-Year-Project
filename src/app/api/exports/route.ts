import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/server';
import { toCSV } from '@/lib/utils/csv';
import { toParquet } from '@/lib/utils/parquet';

export async function POST(req: NextRequest) {
  const payload = await req.json();
  const db = supabaseAdmin();

  // Fetch filtered events
  let q = db.from('events').select('*').order('occurred_at', { ascending: false });
  if (payload.camera_id) q = q.eq('camera_id', payload.camera_id);
  if (payload.type) q = q.eq('event_type', payload.type);
  if (payload.min_conf) q = q.gte('confidence', payload.min_conf);
  if (payload.start) q = q.gte('occurred_at', payload.start);
  if (payload.end) q = q.lte('occurred_at', payload.end);
  if (payload.org_id) q = q.eq('org_id', payload.org_id);
  const { data, error } = await q;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Build files
  const csv = await toCSV(data ?? []);
  const parquet = await toParquet(data ?? []);

  const ts = Date.now();
  const user_id = payload.user_id ?? 'unknown';
  const csvPath = `exports/${user_id}/${ts}.csv`;
  const parquetPath = `exports/${user_id}/${ts}.parquet`;

  const s = supabaseAdmin();
  await s.storage.from('exports').upload(csvPath, csv, { contentType: 'text/csv', upsert: true });
  await s.storage.from('exports').upload(parquetPath, parquet, { contentType: 'application/octet-stream', upsert: true });

  const ttl = parseInt(process.env.EXPORT_URL_TTL_SECONDS || '86400', 10);
  const csvSigned = await s.storage.from('exports').createSignedUrl(csvPath, ttl);
  const parquetSigned = await s.storage.from('exports').createSignedUrl(parquetPath, ttl);

  const { data: job } = await s.from('exports_jobs').insert({
    user_id, org_id: payload.org_id, filter: payload, csv_path: csvPath, parquet_path: parquetPath, status: 'completed'
  }).select('*').maybeSingle();

  return NextResponse.json({ job_id: job?.id, csv_url: csvSigned.data?.signedUrl, parquet_url: parquetSigned.data?.signedUrl });
}
