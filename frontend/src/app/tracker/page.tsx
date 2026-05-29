'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { supabase } from '@/lib/supabase'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const STATUS_COLOR: Record<string, string> = { submitted:'bg-green-100 text-green-700', flagged:'bg-yellow-100 text-yellow-700', failed:'bg-red-100 text-red-700', pending:'bg-gray-100 text-gray-500', skipped:'bg-gray-100 text-gray-400' }

export default function Tracker() {
  const [apps, setApps] = useState<any[]>([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getUser().then(async ({ data }) => {
      if (!data.user) return
      const res = await fetch(`${API}/api/applications/${data.user.id}`)
      const json = await res.json()
      setApps(json.applications || [])
      setLoading(false)
    })
  }, [])

  const filtered = filter === 'all' ? apps : apps.filter(a => a.status === filter)
  const counts = { all: apps.length, submitted: apps.filter(a=>a.status==='submitted').length, flagged: apps.filter(a=>a.status==='flagged').length, failed: apps.filter(a=>a.status==='failed').length }

  const exportCSV = () => {
    const headers = 'Company,Role,Portal,Score,Resume,CV,Msg,Date,Status,URL\n'
    const rows = apps.map(a => `"${a.jobs?.company}","${a.jobs?.title}","${a.jobs?.source}","${Math.round((a.jobs?.score||0)*100)}%","${a.resume_version}","${a.cover_letter_sent}","${a.hiring_message_sent}","${new Date(a.created_at).toLocaleDateString()}","${a.status}","${a.jobs?.url}"`).join('\n')
    const blob = new Blob([headers+rows], {type:'text/csv'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href=url; a.download='applications.csv'; a.click()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <span className="font-bold text-gray-900 text-lg">JobApply</span>
        <div className="flex gap-4 text-sm">
          <Link href="/dashboard" className="text-gray-500 hover:text-gray-900">Dashboard</Link>
          <Link href="/tracker" className="text-blue-600 font-medium">Tracker</Link>
          <Link href="/queue" className="text-gray-500 hover:text-gray-900">Review Queue</Link>
          <Link href="/settings" className="text-gray-500 hover:text-gray-900">Settings</Link>
        </div>
      </nav>
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Application Tracker <span className="text-gray-400 font-normal text-lg">({counts.all})</span></h1>
          <button className="btn-secondary text-sm" onClick={exportCSV}>⬇ Export CSV</button>
        </div>
        <div className="flex gap-2 mb-4">
          {(['all','submitted','flagged','failed'] as const).map(s => (
            <button key={s} onClick={() => setFilter(s)} className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${filter===s?'bg-blue-600 text-white':'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}>
              {s} ({counts[s as keyof typeof counts]})
            </button>
          ))}
        </div>
        <div className="card overflow-hidden">
          {loading ? <div className="p-12 text-center text-gray-400">Loading…</div> : filtered.length === 0 ? <div className="p-12 text-center text-gray-400">No applications yet</div> : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>{['Company','Role','Portal','Match','Resume','CV','Msg','Applied','Status','Link'].map(h=><th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>)}</tr>
              </thead>
              <tbody>{filtered.map((a,i)=>(
                <tr key={a.id} className={`border-b border-gray-50 hover:bg-gray-50 ${i%2===0?'':'bg-gray-50/40'}`}>
                  <td className="px-4 py-3 font-semibold">{a.jobs?.company||'—'}</td>
                  <td className="px-4 py-3 text-gray-600">{a.jobs?.title||'—'}</td>
                  <td className="px-4 py-3"><span className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">{a.jobs?.source||'—'}</span></td>
                  <td className="px-4 py-3"><span className={`font-bold text-sm ${(a.jobs?.score||0)>=0.75?'text-green-600':(a.jobs?.score||0)>=0.6?'text-yellow-600':'text-red-500'}`}>{Math.round((a.jobs?.score||0)*100)}%</span></td>
                  <td className="px-4 py-3 text-xs text-gray-500">{a.resume_version||'—'}</td>
                  <td className="px-4 py-3 text-center">{a.cover_letter_sent?'✅':'—'}</td>
                  <td className="px-4 py-3 text-center">{a.hiring_message_sent?'✅':'—'}</td>
                  <td className="px-4 py-3 text-xs text-gray-400">{new Date(a.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3"><span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLOR[a.status]||''}`}>{a.status}</span></td>
                  <td className="px-4 py-3"><a href={a.jobs?.url||'#'} target="_blank" className="text-blue-500 hover:underline text-xs">View →</a></td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
