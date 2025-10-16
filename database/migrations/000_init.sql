-- Extensions
create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;
create extension if not exists pg_trgm;
create extension if not exists pg_stat_statements;
create extension if not exists "pg_net";
create extension if not exists "pg_cron";

-- Organizations
create table if not exists public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz default now()
);

-- Users (profile) maps to auth.users
create table if not exists public.users (
  id uuid primary key, -- auth user id
  org_id uuid references public.organizations(id),
  role text not null check (role in ('admin','operator','viewer')),
  created_at timestamptz default now()
);

-- Mapping table in case of many-to-many
create table if not exists public.user_org (
  user_id uuid references public.users(id) on delete cascade,
  org_id uuid references public.organizations(id) on delete cascade,
  primary key(user_id, org_id)
);

-- Cameras
create table if not exists public.cameras (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  location text,
  timezone text not null default 'UTC',
  is_active boolean not null default true,
  created_by uuid references public.users(id),
  created_at timestamptz default now()
  -- RTSP is stored in Vault/env only, not as a column
);

-- Events
create table if not exists public.events (
  id bigserial primary key,
  org_id uuid not null references public.organizations(id) on delete cascade,
  camera_id uuid not null references public.cameras(id) on delete cascade,
  event_type text not null check (event_type in ('person_detected','person_lost','heartbeat','system')),
  confidence numeric(5,2),
  frame_url text,
  thumbnail_url text,
  occurred_at timestamptz not null,
  payload jsonb,
  external_event_id text unique,
  created_at timestamptz default now()
);

create index if not exists idx_events_camera_time on public.events(camera_id, occurred_at desc);
create index if not exists idx_events_payload_gin on public.events using gin(payload);

-- Alert rules
create table if not exists public.alert_rules (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  camera_id uuid not null references public.cameras(id) on delete cascade,
  name text not null,
  enabled boolean not null default true,
  rule_type text not null check (rule_type in ('person_presence','count_threshold','frequency')),
  threshold int,
  window_seconds int,
  severity text not null default 'low' check (severity in ('low','medium','high')),
  notify_via text[] not null default '{webhook}',
  webhook_url text,
  email_to text[],
  created_at timestamptz default now()
);

-- Alert logs
create table if not exists public.alert_logs (
  id bigserial primary key,
  org_id uuid not null references public.organizations(id) on delete cascade,
  alert_rule_id uuid not null references public.alert_rules(id) on delete cascade,
  event_id bigint not null references public.events(id) on delete cascade,
  status text not null check (status in ('triggered','suppressed','error')),
  message text,
  created_at timestamptz default now()
);
create index if not exists idx_alert_logs_created on public.alert_logs(created_at desc);
create index if not exists idx_alert_logs_rule_time on public.alert_logs(alert_rule_id, created_at desc);

-- API keys (no secrets stored; we store fingerprint)
create table if not exists public.api_keys (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  key_prefix text not null,
  fingerprint text not null unique,
  revoked boolean not null default false,
  created_by uuid references public.users(id),
  created_at timestamptz default now(),
  last_used_at timestamptz
);

-- Exports jobs
create table if not exists public.exports_jobs (
  id uuid primary key default gen_random_uuid(),
  org_id uuid references public.organizations(id) on delete set null,
  user_id uuid,
  filter jsonb,
  status text not null default 'completed' check (status in ('queued','running','completed','failed')),
  csv_path text,
  parquet_path text,
  created_at timestamptz default now(),
  completed_at timestamptz
);

-- Pending frame uploads (for storage outages)
create table if not exists public.pending_frame_uploads (
  id bigserial primary key,
  org_id uuid not null references public.organizations(id) on delete cascade,
  event_id bigint not null references public.events(id) on delete cascade,
  data_base64 text not null,
  content_type text not null default 'image/jpeg',
  path text not null,
  thumb_path text,
  created_at timestamptz default now()
);

-- Daily rollups
create table if not exists public.event_stats_daily (
  day date not null,
  org_id uuid not null,
  camera_id uuid not null,
  events_count int not null,
  avg_confidence numeric(5,2),
  primary key(day, org_id, camera_id)
);

-- Nonce table for replay protection
create table if not exists public.ingest_nonces (
  api_key_id uuid not null references public.api_keys(id) on delete cascade,
  nonce text not null,
  created_at timestamptz not null default now(),
  primary key(api_key_id, nonce)
);

-- Function to consume nonce (returns error if already used, and prunes old nonces)
create or replace function public.consume_ingest_nonce(p_api_key_id uuid, p_nonce text, p_ttl_seconds int)
returns void
language plpgsql
as $$
begin
  -- Delete expired
  delete from public.ingest_nonces where created_at < now() - make_interval(secs => p_ttl_seconds);
  -- Try to insert
  insert into public.ingest_nonces(api_key_id, nonce) values (p_api_key_id, p_nonce);
end;
$$;

-- RLS
alter table public.organizations enable row level security;
alter table public.users enable row level security;
alter table public.user_org enable row level security;
alter table public.cameras enable row level security;
alter table public.events enable row level security;
alter table public.alert_rules enable row level security;
alter table public.alert_logs enable row level security;
alter table public.api_keys enable row level security;
alter table public.exports_jobs enable row level security;
alter table public.pending_frame_uploads enable row level security;
alter table public.event_stats_daily enable row level security;
alter table public.ingest_nonces enable row level security;

-- Helper: is_admin/is_operator/is_viewer
create or replace function public.current_role()
returns text language sql stable as $$
  select coalesce((select role from public.users where id = auth.uid()), 'viewer')
$$;

-- Policies: organizations (members only)
create policy org_read on public.organizations for select using (
  exists(select 1 from public.user_org uo where uo.org_id = organizations.id and uo.user_id = auth.uid())
);
-- Users
create policy users_read on public.users for select using (
  exists(select 1 from public.user_org uo where uo.org_id = users.org_id and uo.user_id = auth.uid())
);
create policy users_admin_write on public.users for all using (
  exists(select 1 from public.users u where u.id = auth.uid() and u.role = 'admin')
);

-- user_org
create policy uo_read on public.user_org for select using (user_id = auth.uid());
create policy uo_admin_write on public.user_org for all using (
  exists(select 1 from public.users u where u.id = auth.uid() and u.role = 'admin')
);

-- Cameras
create policy cams_read on public.cameras for select using (
  exists(select 1 from public.user_org uo where uo.org_id = cameras.org_id and uo.user_id = auth.uid())
);
create policy cams_write_admin_operator on public.cameras for insert with check (
  exists(select 1 from public.users u where u.id = auth.uid() and u.role in ('admin','operator')) and
  exists(select 1 from public.user_org uo where uo.org_id = cameras.org_id and uo.user_id = auth.uid())
);
create policy cams_update_admin_operator on public.cameras for update using (
  exists(select 1 from public.users u where u.id = auth.uid() and u.role in ('admin','operator')) and
  exists(select 1 from public.user_org uo where uo.org_id = cameras.org_id and uo.user_id = auth.uid())
);

-- Events
create policy events_read on public.events for select using (
  exists(select 1 from public.user_org uo where uo.org_id = events.org_id and uo.user_id = auth.uid())
);
-- Server-side insert uses service role (bypass RLS)

-- Alert rules
create policy alerts_read on public.alert_rules for select using (
  exists(select 1 from public.user_org uo where uo.org_id = alert_rules.org_id and uo.user_id = auth.uid())
);
create policy alerts_write_admin_operator on public.alert_rules for all using (
  exists(select 1 from public.users u where u.id = auth.uid() and u.role in ('admin','operator')) and
  exists(select 1 from public.user_org uo where uo.org_id = alert_rules.org_id and uo.user_id = auth.uid())
);

-- Alert logs
create policy logs_read on public.alert_logs for select using (
  exists(select 1 from public.user_org uo where uo.org_id = alert_logs.org_id and uo.user_id = auth.uid())
);

-- API keys (admin only)
create policy apikeys_admin_read on public.api_keys for select using (
  exists(select 1 from public.users u where u.id = auth.uid() and u.role = 'admin')
);
create policy apikeys_admin_write on public.api_keys for all using (
  exists(select 1 from public.users u where u.id = auth.uid() and u.role = 'admin')
);

-- Exports jobs (viewer can read own org; insert happens server-side)
create policy exports_read on public.exports_jobs for select using (
  exists(select 1 from public.user_org uo where uo.org_id = exports_jobs.org_id and uo.user_id = auth.uid())
);

-- Pending uploads & nonces: deny all to clients
create policy pending_denied on public.pending_frame_uploads for all using (false) with check (false);
create policy nonce_denied on public.ingest_nonces for all using (false) with check (false);

-- Storage buckets (SQL)
insert into storage.buckets (id, name, public) values ('frames', 'frames', false) on conflict do nothing;
insert into storage.buckets (id, name, public) values ('exports', 'exports', false) on conflict do nothing;

-- Realtime replication
drop publication if exists supabase_realtime;
create publication supabase_realtime;
alter table public.events replica identity full;
alter table public.alert_logs replica identity full;
alter publication supabase_realtime add table public.events;
alter publication supabase_realtime add table public.alert_logs;
