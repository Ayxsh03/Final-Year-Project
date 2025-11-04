-- Activity logs to track auth and other user actions
create table if not exists public.activity_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  email text,
  action text not null,
  message text,
  created_at timestamptz not null default now()
);

alter table public.activity_logs enable row level security;

-- Allow authenticated users to read logs; restrict writes to authenticated users
create policy "Activity logs are readable by authenticated users"
  on public.activity_logs for select
  using ( auth.role() = 'authenticated' );

create policy "Authenticated users can insert activity logs"
  on public.activity_logs for insert
  with check ( auth.role() = 'authenticated' );

create policy "Authenticated users can delete activity logs"
  on public.activity_logs for delete
  using ( auth.role() = 'authenticated' );

-- Index for ordering
create index if not exists idx_activity_logs_created_at on public.activity_logs(created_at desc);

-- Realtime
alter table public.activity_logs replica identity full;
alter publication supabase_realtime add table public.activity_logs;

