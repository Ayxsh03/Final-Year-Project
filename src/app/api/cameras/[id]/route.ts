import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/server';

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const db = supabaseAdmin();
  const body = await req.json();
  if ('rtsp_url' in body) delete body['rtsp_url']; // keep secrets out of DB
  const { data, error } = await db.from('cameras').update(body).eq('id', params.id).select('*');
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ data });
}
