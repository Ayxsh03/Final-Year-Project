-- Demo org and users
insert into public.organizations (id, name) values
  ('00000000-0000-0000-0000-000000000001', 'Demo Org')
on conflict (id) do nothing;

insert into public.users (id, org_id, role) values
  ('00000000-0000-0000-0000-0000000000a1', '00000000-0000-0000-0000-000000000001', 'admin'),
  ('00000000-0000-0000-0000-0000000000b1', '00000000-0000-0000-0000-000000000001', 'operator'),
  ('00000000-0000-0000-0000-0000000000c1', '00000000-0000-0000-0000-000000000001', 'viewer')
on conflict (id) do nothing;

insert into public.user_org (user_id, org_id) values
  ('00000000-0000-0000-0000-0000000000a1', '00000000-0000-0000-0000-000000000001'),
  ('00000000-0000-0000-0000-0000000000b1', '00000000-0000-0000-0000-000000000001'),
  ('00000000-0000-0000-0000-0000000000c1', '00000000-0000-0000-0000-000000000001')
on conflict do nothing;

insert into public.cameras (id, org_id, name, location, timezone, is_active, created_by) values
  ('11111111-1111-1111-1111-111111111111', '00000000-0000-0000-0000-000000000001', 'Office', 'HQ', 'UTC', true, '00000000-0000-0000-0000-0000000000a1')
on conflict (id) do nothing;

-- Fake events for 3 days
do $$
declare i int := 0;
declare nowts timestamptz := now();
begin
  while i < 2000 loop
    insert into public.events (org_id, camera_id, event_type, confidence, occurred_at, payload)
    values ('00000000-0000-0000-0000-000000000001',
            '11111111-1111-1111-1111-111111111111',
            'person_detected',
            (random()*40 + 60)::numeric(5,2),
            nowts - ((random()*72)::int || ' hours')::interval,
            jsonb_build_object('bbox', jsonb_build_array(10,20,100,200))
          );
    i := i + 1;
  end loop;
end $$;
