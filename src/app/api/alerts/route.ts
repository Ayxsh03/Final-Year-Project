import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/server';

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const camera_id = url.searchParams.get('camera_id');
  const org_id = url.searchParams.get('org_id');
  const db = supabaseAdmin();
  let q = db.from('alert_rules').select('*');
  if (camera_id) q = q.eq('camera_id', camera_id);
  if (org_id) q = q.eq('org_id', org_id);
  const { data, error } = await q;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ data });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const db = supabaseAdmin();
  const { data, error } = await db.from('alert_rules').insert(body).select('*');
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ data });
}
