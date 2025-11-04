-- Extend alert_settings with schedule controls
alter table public.alert_settings
  add column if not exists allowed_days text[] default '{Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday}',
  add column if not exists start_time time,
  add column if not exists end_time time,
  add column if not exists timezone text default 'UTC';

-- No RLS change needed; existing policies apply

