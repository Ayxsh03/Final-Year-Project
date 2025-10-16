import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/server';

export async function GET() {
  const db = supabaseAdmin();
  const { error } = await db.from('events').select('id', { count: 'exact', head: true }).limit(1);
  if (error) return NextResponse.json({ status: 'degraded', error: error.message }, { status: 500 });
  return NextResponse.json({ status: 'ok', time: new Date().toISOString() });
}
