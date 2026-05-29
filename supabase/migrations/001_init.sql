-- ============================================================
-- JobApply — Supabase schema
-- Run this in: Supabase Dashboard → SQL Editor → Run
-- ============================================================

-- Enable UUID extension
create extension if not exists "pgcrypto";

-- ── users (managed by Supabase Auth, we extend it) ──────────
create table if not exists public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text not null,
  name        text,
  saved_fields jsonb default '{}'::jsonb,
  created_at  timestamptz default now()
);
alter table public.profiles enable row level security;
create policy "Users can read own profile" on public.profiles for select using (auth.uid() = id);
create policy "Users can update own profile" on public.profiles for update using (auth.uid() = id);
create policy "Users can insert own profile" on public.profiles for insert with check (auth.uid() = id);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, name)
  values (new.id, new.email, new.raw_user_meta_data->>'name');
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ── user_preferences ────────────────────────────────────────
create table if not exists public.user_preferences (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null references public.profiles(id) on delete cascade,
  target_roles        text[] default '{}',
  locations           text[] default '{}',
  remote_pref         text default 'any' check (remote_pref in ('remote','hybrid','on_site','any')),
  salary_min          integer,
  salary_max          integer,
  experience_level    text default 'mid' check (experience_level in ('intern','junior','mid','senior','staff','principal')),
  years_of_experience integer,
  preferred_companies text[] default '{}',
  excluded_companies  text[] default '{}',
  platforms           text[] default '{"linkedin","indeed","glassdoor","dice","jobright"}',
  max_apps_per_day    integer default 10,
  generate_cover_letter boolean default true,
  send_hiring_message boolean default false,
  updated_at          timestamptz default now(),
  unique(user_id)
);
alter table public.user_preferences enable row level security;
create policy "Users manage own preferences" on public.user_preferences
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ── resumes ──────────────────────────────────────────────────
create table if not exists public.resumes (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references public.profiles(id) on delete cascade,
  file_url    text not null,
  file_name   text,
  parsed_json jsonb default '{}'::jsonb,
  raw_text    text,
  version     integer default 1,
  is_active   boolean default true,
  created_at  timestamptz default now()
);
alter table public.resumes enable row level security;
create policy "Users manage own resumes" on public.resumes
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ── jobs ─────────────────────────────────────────────────────
create table if not exists public.jobs (
  id          uuid primary key default gen_random_uuid(),
  source      text not null,
  title       text not null,
  company     text not null,
  location    text,
  remote      boolean default false,
  salary_min  integer,
  salary_max  integer,
  jd_text     text,
  url         text not null,
  ats_type    text,
  easy_apply  boolean default false,
  dedup_key   text unique,
  score       float,
  created_at  timestamptz default now()
);
alter table public.jobs enable row level security;
create policy "Jobs readable by all authenticated" on public.jobs for select using (auth.role() = 'authenticated');
create policy "Service role can insert jobs" on public.jobs for insert with check (true);

-- ── run_sessions ─────────────────────────────────────────────
create table if not exists public.run_sessions (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references public.profiles(id) on delete cascade,
  status          text default 'queued' check (status in ('queued','running','paused','completed','failed')),
  current_portal  text,
  current_job     text,
  jobs_found      integer default 0,
  jobs_after_dedup integer default 0,
  apps_submitted  integer default 0,
  apps_flagged    integer default 0,
  apps_failed     integer default 0,
  started_at      timestamptz,
  completed_at    timestamptz,
  created_at      timestamptz default now()
);
alter table public.run_sessions enable row level security;
create policy "Users manage own runs" on public.run_sessions
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ── applications ─────────────────────────────────────────────
create table if not exists public.applications (
  id                   uuid primary key default gen_random_uuid(),
  run_id               uuid references public.run_sessions(id) on delete cascade,
  user_id              uuid not null references public.profiles(id) on delete cascade,
  job_id               uuid references public.jobs(id),
  status               text default 'pending' check (status in ('pending','submitted','flagged','failed','skipped')),
  resume_version       text,
  cover_letter_sent    boolean default false,
  hiring_message_sent  boolean default false,
  hiring_message_preview text,
  cover_letter_text    text,
  submitted_at         timestamptz,
  notes                text,
  created_at           timestamptz default now()
);
alter table public.applications enable row level security;
create policy "Users manage own applications" on public.applications
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ── indexes ──────────────────────────────────────────────────
create index if not exists idx_applications_user_id on public.applications(user_id);
create index if not exists idx_applications_run_id  on public.applications(run_id);
create index if not exists idx_applications_status  on public.applications(status);
create index if not exists idx_run_sessions_user_id on public.run_sessions(user_id);
create index if not exists idx_jobs_dedup_key        on public.jobs(dedup_key);

-- ── realtime ─────────────────────────────────────────────────
-- Enable realtime on applications so dashboard updates live
alter publication supabase_realtime add table public.applications;
alter publication supabase_realtime add table public.run_sessions;
