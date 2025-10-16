import { NextRequest, NextResponse } from 'next/server';
import { POST as single } from '@/app/api/ingest/event/route';

// Simple delegator: iterate over events in array
export async function POST(req: NextRequest) {
  const items = await req.json();
  if (!Array.isArray(items)) return NextResponse.json({ error: 'array_expected' }, { status: 400 });
  const results = [];
  for (const item of items) {
    const r = await fetch(new URL('/api/ingest/event', req.url), {
      method: 'POST',
      headers: req.headers,
      body: JSON.stringify(item)
    });
    results.push(await r.json());
  }
  return NextResponse.json({ results });
}
