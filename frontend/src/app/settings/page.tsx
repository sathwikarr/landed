'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { supabase } from '@/lib/supabase'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Settings() {
  const [fields, setFields] = useState<Record<string, string>>({})
  const [userId, setUserId] = useState('')
  const [saved, setSaved] = useState(false)
  const FIELD_LABELS = ['phone','linkedin_url','github_url','website','location','work_authorization','visa_sponsorship','salary_expectation','years_of_experience']

  useEffect(() => {
    supabase.auth.getUser().then(async ({ data }) => {
      if (!data.user) return
      setUserId(data.user.id)
      const res = await fetch(`${API}/api/fields/${data.user.id}`)
      const json = await res.json()
      setFields(json.fields || {})
    })
  }, [])

  const saveAll = async () => {
    for (const [k, v] of Object.entries(fields)) {
      await fetch(`${API}/api/fields/save`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user_id: userId, field_name: k, field_value: v}) })
    }
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <span className="font-bold text-gray-900 text-lg">JobApply</span>
        <div className="flex gap-4 text-sm">
          <Link href="/dashboard" className="text-gray-500 hover:text-gray-900">Dashboard</Link>
          <Link href="/tracker" className="text-gray-500 hover:text-gray-900">Tracker</Link>
          <Link href="/queue" className="text-gray-500 hover:text-gray-900">Review Queue</Link>
          <Link href="/settings" className="text-blue-600 font-medium">Settings</Link>
        </div>
      </nav>
      <div className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold mb-6">Settings</h1>
        <div className="card p-5 mb-4">
          <h3 className="font-semibold mb-3">Saved form fields</h3>
          <p className="text-sm text-gray-500 mb-3">Pre-filled answers for every job application form.</p>
          {FIELD_LABELS.map(k => (
            <div key={k} className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0">
              <span className="text-sm text-gray-500 w-44 capitalize">{k.replace(/_/g,' ')}</span>
              <input className="input flex-1 text-sm" value={fields[k]||''} onChange={e => setFields(f => ({...f, [k]: e.target.value}))} placeholder={`Enter ${k.replace(/_/g,' ')}`} />
            </div>
          ))}
        </div>
        <button className="btn-primary" onClick={saveAll}>{saved ? '✅ Saved!' : 'Save settings'}</button>
      </div>
    </div>
  )
}
