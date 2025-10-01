# Final-Year-Project 

# Person Detection Alerts — Webdashboard

End-to-end, production-ready starter that connects CCTV/RTSP ➜ AI model ➜ Backend ingest ➜ Supabase (Postgres + Storage + Realtime) ➜ React/Next.js dashboard.

## Tech
- Next.js 14 (App Router) + TypeScript, Tailwind, shadcn-style components
- Supabase (Postgres, Auth, RLS, Storage, Realtime, Edge Functions, Cron)
- Exports to CSV & Parquet, signed URLs
- HMAC-signed ingest with nonce + replay protection
- Realtime updates via Supabase Realtime (no polling)

## Quick start
1. `cp .env.example .env.local` and fill Supabase values.
2. Run migrations in `database/migrations/*.sql` (via Supabase SQL editor or CLI).
3. Seed with `database/seeds/seed.sql`.
4. `npm i && npm run dev`

## Ingest
POST `/api/ingest/event` with headers:
- `X-API-Key`: raw API key string
- `X-Timestamp`: epoch seconds
- `X-Nonce`: unique random per request
- `X-Signature`: `v1=` + HMAC-SHA256(derived_key, canonical_string)


See clients in `detection_integration/`.

## Buckets
- `frames` (private)
- `exports` (private)

## Realtime
Replication pub: `supabase_realtime` with `events`, `alert_logs`.

## OpenAPI
Served at `/api/docs` and file at `/openapi.yaml`.

## RLS
Row-level, org-scoped, with roles: admin/operator/viewer. See `database/migrations/000_init.sql`.





## Architecture (ASCII)

```
+----------------+       HMAC+nonce        +---------------------+       +--------------------+
|  RTSP Camera   | --- frames/snapshots -->|  Model Client       | ----> |  Next.js Ingest    |
|  (N streams)   |                          |  (Python/Node)      | POST  |  /api/ingest/event |
+----------------+                          +---------------------+       +--------------------+
                                                                              |
                                                                              v
                                                          +-------------------+------------------+
                                                          |     Supabase (Postgres + Storage)   |
                                                          |  tables: cameras, events, alerts... |
                                                          |  buckets: frames, exports           |
                                                          |  RLS + Realtime (publication)       |
                                                          +-------------------+------------------+
                                                                              |
                                                          Postgres Changes    v
                                                                              +------------------+
                                                                              |  Web Dashboard   |
                                                                              |  (Next.js + RLS) |
                                                                              +------------------+
```

## Setup steps
1. Create a new Supabase project.
2. Run SQL in `database/migrations/000_init.sql`, `010_rollups.sql`, `020_cron.sql`, `030_storage_policies.sql`, `040_analytics_queries.sql` (in that order).
3. Seed: run `database/seeds/seed.sql` in the SQL editor.
4. Copy `.env.example` to `.env.local` and fill values.
5. `npm i && npm run dev`.

## Common tasks
- **Generate API key:** `POST /api/keys` (admin).
- **Rotate API key:** Revoke old (`DELETE /api/keys/{id}`) then create new. Update model clients.
- **Create camera:** `POST /api/cameras` (store RTSP in Vault/env, not DB).
- **Create alert rule:** `POST /api/alerts`.
- **Export:** POST `/api/exports` then download from response URLs.
- **Docs:** open `/api/docs`.


