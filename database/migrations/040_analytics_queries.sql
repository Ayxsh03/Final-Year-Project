
-- Events per hour/day per camera
create or replace view public.v_events_per_hour as
select date_trunc('hour', occurred_at) as hour, org_id, camera_id, count(*) as events
from public.events
group by 1,2,3;

create or replace view public.v_events_per_day as
select date_trunc('day', occurred_at)::date as day, org_id, camera_id, count(*) as events
from public.events
group by 1,2,3;

-- Alert trigger rate by rule
create or replace view public.v_alert_trigger_rate as
select alert_rule_id, org_id,
  sum(case when status='triggered' then 1 else 0 end)::float / nullif(count(*),0) as trigger_rate,
  count(*) as total
from public.alert_logs
group by 1,2;

-- Average/median confidence by camera
create or replace view public.v_confidence_stats as
select camera_id, org_id, avg(confidence) as avg_conf, percentile_cont(0.5) within group (order by confidence) as median_conf
from public.events
where confidence is not null
group by 1,2;

-- Top cameras by detections last 7/30 days
create or replace view public.v_top_cameras_7d as
select camera_id, org_id, count(*) as events
from public.events
where occurred_at >= now() - interval '7 days'
group by 1,2
order by events desc;

create or replace view public.v_top_cameras_30d as
select camera_id, org_id, count(*) as events
from public.events
where occurred_at >= now() - interval '30 days'
group by 1,2
order by events desc;

-- Heatmap of events by hour of day (0-23)
create or replace view public.v_events_hour_of_day as
select org_id, camera_id, extract(hour from occurred_at) as hour_of_day, count(*) as events
from public.events
group by 1,2,3;
