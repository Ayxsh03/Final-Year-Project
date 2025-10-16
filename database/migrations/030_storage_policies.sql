
-- Enable RLS on storage.objects
alter table storage.objects enable row level security;

-- Deny direct reads for frames/exports buckets (prefer signed URLs)
drop policy if exists frames_no_direct_read on storage.objects;
create policy frames_no_direct_read on storage.objects
for select using (bucket_id not in ('frames','exports'));

-- Deny direct writes from clients for frames/exports
drop policy if exists frames_no_direct_write on storage.objects;
create policy frames_no_direct_write on storage.objects
for insert with check (bucket_id not in ('frames','exports'));

-- Note: Service role bypasses RLS. Signed URLs bypass RLS for downloads.
