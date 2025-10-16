// deno-lint-ignore-file no-explicit-any
import 'jsr:@supabase/functions-js/edge-runtime.d.ts'
import { serve } from "jsr:@supabase/functions-js/edge-runtime";
import { createClient } from 'npm:@supabase/supabase-js';

serve(async (req) => {
  const supabase = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!);
  const { data, error } = await supabase.rpc('rollup_event_stats_daily');
  if (error) return new Response(JSON.stringify({ ok: false, error: error.message }), { status: 500 });
  return new Response(JSON.stringify({ ok: true, data }), { headers: { 'content-type': 'application/json' } });
});
