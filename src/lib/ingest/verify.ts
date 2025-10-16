import crypto from 'crypto';
import { supabaseAdmin } from '@/lib/supabase/server';

export type CanonicalMessage = {
  method: string;
  path: string;
  timestamp: string; // epoch seconds as string
  nonce: string;
  bodyHash: string; // sha256 hex of raw body
};

function bodySha256(raw: string) {
  return crypto.createHash('sha256').update(raw).digest('hex');
}

function deriveKey(apiKey: string, salt: string) {
  // Deterministic derived signing key; server never stores raw key.
  return crypto.pbkdf2Sync(apiKey, salt, 100_000, 32, 'sha256');
}

function hmacHex(key: Buffer, msg: string) {
  return crypto.createHmac('sha256', key).update(msg).digest('hex');
}

export async function verifyAndIdentify(
  headers: Headers,
  rawBody: string
): Promise<{ apiKeyId: string; orgId: string } | null> {
  const apiKey = headers.get('x-api-key') || '';
  const ts = headers.get('x-timestamp') || '';
  const nonce = headers.get('x-nonce') || '';
  const sig = headers.get('x-signature') || ''; // expected: v1=hex

  if (!apiKey || !ts || !nonce || !sig.startsWith('v1=')) return null;
  const now = Math.floor(Date.now() / 1000);
  const drift = Math.abs(now - parseInt(ts, 10));
  if (!Number.isFinite(drift) || drift > 300) return null; // >5 minutes stale

  const salt = process.env.API_KEY_DERIVATION_SALT || 'default-salt';
  const derived = deriveKey(apiKey, salt);
  const fingerprint = crypto.createHash('sha256').update(apiKey).digest('hex');
  const bodyHash = bodySha256(rawBody);
  const canonical = ['POST', '/api/ingest/event', ts, nonce, bodyHash].join('\n');
  const expected = 'v1=' + hmacHex(derived, canonical);

  if (!crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(sig))) return null;

  const db = supabaseAdmin();
  const { data, error } = await db
    .from('api_keys')
    .select('id, org_id, revoked, fingerprint')
    .eq('fingerprint', fingerprint)
    .maybeSingle();

  if (error || !data || data.revoked) return null;

  // Replay protection: insert nonce; if exists, reject.
  const { error: nonceErr } = await db
    .rpc('consume_ingest_nonce', { p_api_key_id: data.id, p_nonce: nonce, p_ttl_seconds: 600 });
  if (nonceErr) return null;

  return { apiKeyId: data.id, orgId: data.org_id };
}

export function hashBody(raw: string) { return bodySha256(raw); }
export function canonicalFor(path: string, ts: string, nonce: string, rawBody: string) {
  return ['POST', path, ts, nonce, bodySha256(rawBody)].join('\n');
}
