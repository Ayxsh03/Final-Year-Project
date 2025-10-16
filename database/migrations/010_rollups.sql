create or replace function public.rollup_event_stats_daily()
returns void language plpgsql as $$
begin
  insert into public.event_stats_daily(day, org_id, camera_id, events_count, avg_confidence)
  select date_trunc('day', occurred_at)::date as day, org_id, camera_id, count(*), avg(confidence)
  from public.events
  group by 1,2,3
  on conflict (day, org_id, camera_id)
  do update set events_count = excluded.events_count, avg_confidence = excluded.avg_confidence;
end; $$;
