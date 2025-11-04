-- Settings for alerts (SMTP, WhatsApp, Telegram)
create table if not exists public.alert_settings (
  id uuid primary key default gen_random_uuid(),
  enabled boolean not null default true,
  notify_email boolean not null default false,
  notify_whatsapp boolean not null default false,
  notify_telegram boolean not null default false,

  -- Email/SMTP
  smtp_host text,
  smtp_port integer,
  smtp_username text,
  smtp_password text,
  smtp_from text,
  email_to text,

  -- WhatsApp Cloud API
  whatsapp_phone_number_id text,
  whatsapp_token text,
  whatsapp_to text,

  -- Telegram Bot
  telegram_bot_token text,
  telegram_chat_id text,

  updated_at timestamptz not null default now()
);

alter table public.alert_settings enable row level security;

-- Basic policies: authenticated users can read/update (tighten later as needed)
create policy if not exists "alert_settings select for authenticated"
  on public.alert_settings for select
  using ( auth.role() = 'authenticated' );

create policy if not exists "alert_settings upsert for authenticated"
  on public.alert_settings for all
  using ( auth.role() = 'authenticated' )
  with check ( auth.role() = 'authenticated' );

-- Ensure only one row typically used (optional, not enforced)
-- You can insert one seed row via SQL editor if desired.

