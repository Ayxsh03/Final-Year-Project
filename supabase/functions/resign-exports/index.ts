// deno-lint-ignore-file no-explicit-any
import 'jsr:@supabase/functions-js/edge-runtime.d.ts'
import { serve } from "jsr:@supabase/functions-js/edge-runtime";
import { createClient } from 'npm:@supabase/supabase-js';

serve(async (req) => {
  const supabase = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!);
  const ttl = 86400;
  const { data: jobs } = await supabase.from('exports_jobs').select('*').eq('status', 'completed').gte('created_at', new Date(Date.now() - 7*24*3600*1000).toISOString());
  const result: any[] = [];
  for (const j of jobs ?? []) {
    const csv = await supabase.storage.from('exports').createSignedUrl(j.csv_path, ttl);
    const pq = await supabase.storage.from('exports').createSignedUrl(j.parquet_path, ttl);
    result.push({ id: j.id, csv: csv.data?.signedUrl, parquet: pq.data?.signedUrl });
  }
  return new Response(JSON.stringify(result), { headers: { 'content-type': 'application/json' } });
});
