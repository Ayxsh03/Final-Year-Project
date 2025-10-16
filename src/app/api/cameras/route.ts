import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/server';

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const org_id = url.searchParams.get('org_id');
  const db = supabaseAdmin();
  const { data, error } = await db.from('cameras').select('*').eq('org_id', org_id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ data });
}

export async function POST(req: NextRequest) {
  const db = supabaseAdmin();
  const body = await req.json();
  if (body.rtsp_url) delete body.rtsp_url; // never accept raw RTSP via API; use Vault
  const { data, error } = await db.from('cameras').insert(body).select('*');
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ data });
}
