import os
import time
import json
import hmac
import hashlib
import uuid
import base64
import cv2
import queue
import threading
import requests
from datetime import datetime, timezone

API_URL = os.environ.get("INGEST_URL", "http://localhost:3000/api/ingest/event")
API_KEY = os.environ.get("INGEST_API_KEY", "pk_live_samplechangeme")
API_KEY_DERIVATION_SALT = os.environ.get("API_KEY_DERIVATION_SALT", "default-salt")
CAMERA_ID = os.environ.get("CAMERA_ID", "11111111-1111-1111-1111-111111111111")
ORG_TIMEZONE = os.environ.get("ORG_TIMEZONE", "UTC")
CONF_THRESHOLD = float(os.environ.get("CONF_THRESHOLD", "0.3"))
RTSP_URL = os.environ.get("RTSP_URL", "")

# Derive signing key deterministically (pbkdf2)
def derive_key(api_key: str, salt: str) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", api_key.encode(), salt.encode(), 100_000, dklen=32)

def body_sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def canonical(method: str, path: str, ts: str, nonce: str, body_hash: str) -> str:
    return "\n".join([method, path, ts, nonce, body_hash])

def sign(api_key: str, salt: str, method: str, path: str, ts: str, nonce: str, body: bytes) -> str:
    key = derive_key(api_key, salt)
    msg = canonical(method, path, ts, nonce, body_sha256(body)).encode()
    return "v1=" + hmac.new(key, msg, hashlib.sha256).hexdigest()

def encode_jpeg(frame) -> str:
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok: raise RuntimeError("JPEG encode failed")
    b64 = base64.b64encode(buf.tobytes()).decode()
    return "data:image/jpeg;base64," + b64

# Offline queue (jsonl)
QUEUE_FILE = os.environ.get("OFFLINE_QUEUE", "./offline_queue.jsonl")

def enqueue(item: dict):
    with open(QUEUE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(item) + "\n")

def flush_queue():
    if not os.path.exists(QUEUE_FILE): return
    lines = open(QUEUE_FILE, "r", encoding="utf-8").read().strip().splitlines()
    if not lines: return
    ok_lines = []
    for ln in lines:
        try:
            item = json.loads(ln)
            post_event(item)
        except Exception as e:
            ok_lines.append(ln)  # keep if still failing
    if ok_lines:
        open(QUEUE_FILE, "w", encoding="utf-8").write("\n".join(ok_lines) + "\n")
    else:
        os.remove(QUEUE_FILE)

def post_event(evt: dict):
    body = json.dumps(evt).encode()
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex
    sig = sign(API_KEY, API_KEY_DERIVATION_SALT, "POST", "/api/ingest/event", ts, nonce, body)
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
        "X-Timestamp": ts,
        "X-Nonce": nonce,
        "X-Signature": sig,
    }
    r = requests.post(API_URL, data=body, headers=headers, timeout=10)
    if r.status_code >= 400:
        raise RuntimeError(f"Ingest failed: {r.status_code} {r.text}")
    return r.json()

def run_loop():
    cap = cv2.VideoCapture(RTSP_URL if RTSP_URL else 0)  # fallback to webcam
    if not cap.isOpened():
        raise RuntimeError("Could not open video source")
    last_sent = 0.0
    cooldown = 5.0
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1); continue
        now = time.time()
        if now - last_sent < cooldown:  # throttle for demo
            continue
        last_sent = now
        # In a real system, run detection here, we're simulating one "person_detected":
        evt = {
            "camera_id": CAMERA_ID,
            "event_type": "person_detected",
            "confidence": 92.1,
            "occurred_at": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            "bbox": [100,120,300,420],
            "frame_base64": encode_jpeg(frame),
            "meta": { "model_version": "demo", "latency_ms": 42 }
        }
        try:
            print("Posting event...")
            flush_queue()  # try to push any queued events first
            post_event(evt)
        except Exception as e:
            print("Ingest error, enqueueing:", e)
            enqueue(evt)

if __name__ == "__main__":
    run_loop()
