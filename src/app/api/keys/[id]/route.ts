import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/server';

export async function DELETE(_: NextRequest, { params }: { params: { id: string } }) {
  const db = supabaseAdmin();
  const { error } = await db.from('api_keys').update({ revoked: true }).eq('id', params.id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
