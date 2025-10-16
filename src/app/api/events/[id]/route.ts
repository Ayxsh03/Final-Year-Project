import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/server';

export async function GET(_: NextRequest, { params }: { params: { id: string } }) {
  const db = supabaseAdmin();
  const { data, error } = await db.from('events').select('*').eq('id', params.id).maybeSingle();
  if (error || !data) return NextResponse.json({ error: 'not_found' }, { status: 404 });
  return NextResponse.json(data);
}
