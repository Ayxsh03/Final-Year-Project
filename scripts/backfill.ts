
import { createClient } from '@supabase/supabase-js';

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const key = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(url, key);

async function main() {
  const org_id = process.env.ORG_ID || '00000000-0000-0000-0000-000000000001';
  const camera_id = process.env.CAMERA_ID || '11111111-1111-1111-1111-111111111111';
  for (let i=0; i<500; i++) {
    const occurred_at = new Date(Date.now() - Math.random()*72*3600*1000).toISOString();
    await supabase.from('events').insert({
      org_id, camera_id, event_type: 'person_detected',
      confidence: 60 + Math.random()*40,
      occurred_at, payload: { bbox: [10,20,100,200], source: 'backfill' }
    });
  }
  console.log('Done backfill');
}
main().catch(e => { console.error(e); process.exit(1); });
