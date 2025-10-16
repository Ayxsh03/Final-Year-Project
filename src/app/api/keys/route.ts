import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';
import { supabaseAdmin } from '@/lib/supabase/server';

export async function POST(req: NextRequest) {
  const { name, org_id, created_by } = await req.json();
  const raw = 'pk_live_' + crypto.randomBytes(24).toString('hex');
  const fingerprint = crypto.createHash('sha256').update(raw).digest('hex');
  const key_prefix = fingerprint.slice(0, 8);
  const db = supabaseAdmin();
  const { data, error } = await db.from('api_keys').insert({ name, org_id, created_by, fingerprint, key_prefix }).select('*').maybeSingle();
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ api_key: raw, record: data });
}

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const org_id = url.searchParams.get('org_id');
  const db = supabaseAdmin();
  const { data, error } = await db.from('api_keys').select('id, name, created_at, key_prefix, revoked').eq('org_id', org_id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ data });
}
