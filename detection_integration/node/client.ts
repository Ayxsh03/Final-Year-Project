import crypto from 'crypto';
import fs from 'fs';
import fetch from 'node-fetch';

const API_URL = process.env.INGEST_URL || 'http://localhost:3000/api/ingest/event';
const API_KEY = process.env.INGEST_API_KEY || 'pk_live_samplechangeme';
const SALT = process.env.API_KEY_DERIVATION_SALT || 'default-salt';

function deriveKey(apiKey: string, salt: string) {
  return crypto.pbkdf2Sync(apiKey, salt, 100_000, 32, 'sha256');
}
function bodySha256(b: Buffer) { return crypto.createHash('sha256').update(b).digest('hex'); }
function sign(method: string, path: string, ts: string, nonce: string, body: Buffer) {
  const key = deriveKey(API_KEY, SALT);
  const canonical = [method, path, ts, nonce, bodySha256(body)].join('\n');
  return 'v1=' + crypto.createHmac('sha256', key).update(canonical).digest('hex');
}

async function postEvent(evt: any) {
  const body = Buffer.from(JSON.stringify(evt));
  const ts = String(Math.floor(Date.now()/1000));
  const nonce = crypto.randomBytes(12).toString('hex');
  const sig = sign('POST', '/api/ingest/event', ts, nonce, body);
  const r = await fetch(API_URL, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-api-key': API_KEY, 'x-timestamp': ts, 'x-nonce': nonce, 'x-signature': sig },
    body
  });
  if (!r.ok) throw new Error(await r.text());
  console.log('OK', await r.json());
}

async function main() {
  const jpg = fs.readFileSync(__dirname + '/sample.jpg');
  const frame_base64 = 'data:image/jpeg;base64,' + jpg.toString('base64');
  await postEvent({
    camera_id: process.env.CAMERA_ID || '11111111-1111-1111-1111-111111111111',
    event_type: 'person_detected',
    confidence: 93.4,
    occurred_at: new Date().toISOString(),
    bbox: [10,20,100,200],
    frame_base64,
    meta: { model_version: 'node-demo', latency_ms: 25 }
  });
}
main().catch(console.error);
