import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/server';

export async function GET(_: NextRequest, { params }: { params: { job_id: string } }) {
  const db = supabaseAdmin();
  const { data, error } = await db.from('exports_jobs').select('*').eq('id', params.job_id).maybeSingle();
  if (error || !data) return NextResponse.json({ error: 'not_found' }, { status: 404 });
  return NextResponse.json(data);
}
