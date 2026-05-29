import { createBrowserClient } from '@supabase/ssr'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey)

export type UserProfile = {
  id: string
  email: string
  name: string
  saved_fields: Record<string, string>
}

export type Application = {
  id: string
  run_id: string
  status: 'pending' | 'submitted' | 'flagged' | 'failed' | 'skipped'
  resume_version: string
  cover_letter_sent: boolean
  hiring_message_sent: boolean
  hiring_message_preview: string | null
  created_at: string
  jobs: { title: string; company: string; url: string; source: string; score: number }
}

export type RunSession = {
  id: string
  status: string
  current_portal: string | null
  current_job: string | null
  jobs_found: number
  apps_submitted: number
  apps_flagged: number
  created_at: string
}
