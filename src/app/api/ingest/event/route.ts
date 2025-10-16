import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { verifyAndIdentify } from '@/lib/ingest/verify';
import { supabaseAdmin } from '@/lib/supabase/server';
import { v4 as uuidv4 } from 'uuid';
import sharp from 'sharp';

const EventSchema = z.object({
  camera_id: z.string().uuid(),
  event_type: z.enum(['person_detected','person_lost','heartbeat','system']),
  confidence: z.number().min(0).max(100).optional(),
  occurred_at: z.string().datetime(),
  bbox: z.array(z.number()).length(4).optional(),
  frame_base64: z.string().startsWith('data:image/').optional(),
  frame_url: z.string().url().optional(),
  meta: z.record(z.any()).optional(),
  external_event_id: z.string().optional(),
  allow_stale: z.boolean().optional()
});

export async function POST(req: NextRequest) {
  const raw = await req.text();
  const headers = req.headers;
  const id = await verifyAndIdentify(headers as any, raw);
  if (!id) return NextResponse.json({ error: 'invalid_signature_or_key' }, { status: 401 });

  const json = JSON.parse(raw || '{}');
  const parsed = EventSchema.safeParse(json);
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  const body = parsed.data;

  const drift = Math.abs(Date.now() - Date.parse(body.occurred_at));
  if (!body.allow_stale && drift > 5 * 60 * 1000) {
    return NextResponse.json({ error: 'stale_event' }, { status: 422 });
  }

  const db = supabaseAdmin();

  // Validate camera belongs to org
  const { data: camera, error: camErr } = await db
    .from('cameras')
    .select('id, org_id, is_active, timezone')
    .eq('id', body.camera_id)
    .eq('org_id', id.orgId)
    .maybeSingle();

  if (camErr || !camera || !camera.is_active) {
    return NextResponse.json({ error: 'camera_not_found_or_inactive' }, { status: 404 });
  }

  // Insert event first to get id
  const occurredAt = new Date(body.occurred_at).toISOString();
  const payload = {
    bbox: body.bbox,
    meta: body.meta
  };

  let frame_url: string | null = null;
  let thumbnail_url: string | null = null;
  let storedEventId: number | null = null;

  // Upsert by external_event_id if provided (idempotency)
  const insertEvt = {
    camera_id: body.camera_id,
    org_id: id.orgId,
    event_type: body.event_type,
    confidence: body.confidence ?? null,
    frame_url: null,
    thumbnail_url: null,
    occurred_at: occurredAt,
    payload,
    external_event_id: body.external_event_id ?? null
  };

  const { data: ins, error: insErr } = await db
    .from('events')
    .insert(insertEvt)
    .select('id')
    .maybeSingle();

  if (insErr) {
    // If unique violation for external_event_id, ignore (idempotent)
    return NextResponse.json({ status: 'duplicate_or_error', detail: insErr.message }, { status: 200 });
  }

  storedEventId = ins?.id ?? null;

  // If direct frame_url provided (e.g., pre-uploaded or snapshot URL), trust and store it
  if (body.frame_url && storedEventId) {
    frame_url = body.frame_url; thumbnail_url = body.frame_url;
    await db.from('events').update({ frame_url, thumbnail_url }).eq('id', storedEventId);
  }

  // Upload frame if provided
  if (body.frame_base64 && storedEventId) {
    const [meta, b64] = body.frame_base64.split(',');
    const buffer = Buffer.from(b64, 'base64');
    const yyyy = new Date(occurredAt).getUTCFullYear();
    const mm = String(new Date(occurredAt).getUTCMonth()+1).padStart(2, '0');
    const dd = String(new Date(occurredAt).getUTCDate()).padStart(2, '0');
    const key = `frames/${id.orgId}/${body.camera_id}/${yyyy}/${mm}/${dd}/${storedEventId}.jpg`;

    // Create thumbnail
    const thumbBuffer = await sharp(buffer).resize(320).jpeg({ quality: 75 }).toBuffer();
    const thumbKey = `frames/${id.orgId}/${body.camera_id}/${yyyy}/${mm}/${dd}/${storedEventId}_thumb.jpg`;

    const upload1 = await db.storage.from('frames').upload(key, buffer, { contentType: 'image/jpeg', upsert: true });
    const upload2 = await db.storage.from('frames').upload(thumbKey, thumbBuffer, { contentType: 'image/jpeg', upsert: true });
    if (!upload1.error && !upload2.error) {
      frame_url = key;
      thumbnail_url = thumbKey;
      await db.from('events').update({ frame_url: key, thumbnail_url: thumbKey }).eq('id', storedEventId);
    } else {
      // queue retry
      await db.from('pending_frame_uploads').insert({
        event_id: storedEventId,
        data_base64: b64,
        content_type: 'image/jpeg',
        path: key,
        thumb_path: thumbKey,
        org_id: id.orgId
      });
    }
  }

  // Evaluate alert rules (simplified)
  const { data: rules } = await db
    .from('alert_rules')
    .select('*')
    .eq('org_id', id.orgId)
    .eq('camera_id', body.camera_id)
    .eq('enabled', true);

  if (rules && storedEventId) {
    for (const r of rules) {
      let triggered = false;
      let message = '';
      if (r.rule_type === 'person_presence' && body.event_type === 'person_detected') {
        triggered = (body.confidence ?? 0) >= (r.threshold ?? 0);
        message = `Person detected with confidence ${(body.confidence ?? 0).toFixed(1)} (>= ${r.threshold}).`;
      } else if (r.rule_type === 'frequency') {
        const windowSec = r.window_seconds ?? 60;
        const start = new Date(Date.now() - windowSec * 1000).toISOString();
        const { count } = await db
          .from('events')
          .select('*', { count: 'exact', head: true })
          .eq('camera_id', body.camera_id)
          .eq('org_id', id.orgId)
          .eq('event_type', 'person_detected')
          .gte('occurred_at', start);
        triggered = (count ?? 0) >= (r.threshold ?? 1);
        message = `Frequency threshold: ${count} in ${windowSec}s (>= ${r.threshold}).`;
      }
      const status = triggered ? 'triggered' : 'suppressed';
      await db.from('alert_logs').insert({
        alert_rule_id: r.id, event_id: storedEventId, status, message, org_id: id.orgId
      });
    }
  }

  return NextResponse.json({ ok: true, event_id: storedEventId, frame_url, thumbnail_url });
}
