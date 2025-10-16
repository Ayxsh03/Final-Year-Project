// deno-lint-ignore-file no-explicit-any
import 'jsr:@supabase/functions-js/edge-runtime.d.ts'
import { serve } from "jsr:@supabase/functions-js/edge-runtime";
import { createClient } from 'npm:@supabase/supabase-js';

serve(async (req) => {
  const supabase = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!);
  const days = parseInt(Deno.env.get('FRAME_RETENTION_DAYS') ?? '30', 10);
  const cutoff = new Date(Date.now() - days*24*3600*1000).toISOString();
  const { data: events } = await supabase.from('events').select('id, frame_url, thumbnail_url').lte('occurred_at', cutoff).not('frame_url', 'is', null);
  const toRemove = [];
  for (const e of events ?? []) {
    if (e.frame_url) toRemove.push({ name: e.frame_url });
    if (e.thumbnail_url) toRemove.push({ name: e.thumbnail_url });
  }
  if (toRemove.length) {
    await supabase.storage.from('frames').remove(toRemove);
    await supabase.from('events').update({ frame_url: null, thumbnail_url: null }).lte('occurred_at', cutoff);
  }
  return new Response(JSON.stringify({ removed: toRemove.length }));
});
