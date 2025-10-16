
-- Schedule daily rollup at 02:05 UTC
select cron.schedule('rollup_stats_daily',
  '5 2 * * *',
  $$ select
    net.http_post(
      url := current_setting('app.settings.functions_url', true) || '/rollup-stats',
      headers := jsonb_build_object('Authorization', 'Bearer ' || current_setting('app.settings.functions_service_role', true))
    ); $$
);

-- Schedule nightly purge of old frames at 03:15 UTC
select cron.schedule('purge_old_frames',
  '15 3 * * *',
  $$ select
    net.http_post(
      url := current_setting('app.settings.functions_url', true) || '/purge-frames',
      headers := jsonb_build_object('Authorization', 'Bearer ' || current_setting('app.settings.functions_service_role', true))
    ); $$
);
