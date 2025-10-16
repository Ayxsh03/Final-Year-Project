import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/server';

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const camera_id = url.searchParams.get('camera_id');
  const type = url.searchParams.get('type');
  const min_conf = url.searchParams.get('min_conf');
  const start = url.searchParams.get('start');
  const end = url.searchParams.get('end');
  const limit = parseInt(url.searchParams.get('limit') || '100', 10);
  const cursor = parseInt(url.searchParams.get('cursor') || '0', 10);
  const org_id = url.searchParams.get('org_id');

  const db = supabaseAdmin();
  let query = db.from('events').select('*').order('occurred_at', { ascending: false }).range(cursor, cursor + limit - 1);
  if (camera_id) query = query.eq('camera_id', camera_id);
  if (type) query = query.eq('event_type', type);
  if (min_conf) query = query.gte('confidence', Number(min_conf));
  if (start) query = query.gte('occurred_at', start);
  if (end) query = query.lte('occurred_at', end);
  if (org_id) query = query.eq('org_id', org_id);

  const { data, error } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ data, next_cursor: cursor + data.length });
}
