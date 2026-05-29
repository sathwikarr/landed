'use client'
import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { supabase } from '@/lib/supabase'
import type { RunSession } from '@/lib/supabase'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const STATUS_COLOR: Record<string, string> = {
  submitted: 'bg-green-100 text-green-700',
  flagged: 'bg-yellow-100 text-yellow-700',
  failed: 'bg-red-100 text-red-700',
  pending: 'bg-gray-100 text-gray-500',
}

interface AppRow { company: string; title: string; portal: string; score: number; status: string; resume_version: string; cv_sent: boolean; msg_sent: boolean; timestamp: string }

export default function Dashboard() {
  const [user, setUser] = useState<{ id: string; email: string } | null>(null)
  const [running, setRunning] = useState(false)
  const [stats, setStats] = useState({ found: 0, applied: 0, flagged: 0, portal: '' })
  const [apps, setApps] = useState<AppRow[]>([])
  const [pastRuns, setPastRuns] = useState<RunSession[]>([])
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (data.user) setUser({ id: data.user.id, email: data.user.email || '' })
    })
  }, [])

  useEffect(() => {
    if (!user) return
    fetch(`${API}/api/runs/user/${user.id}`)
      .then(r => r.json()).then(d => setPastRuns(d.runs || []))
  }, [user])

  const startRun = async () => {
    if (!user) return
    setRunning(true); setApps([]); setStats({ found: 0, applied: 0, flagged: 0, portal: '' })

    const prefsRaw = localStorage.getItem('prefs')
    const prefs = prefsRaw ? JSON.parse(prefsRaw) : {}
    const resumeRes = await fetch(`${API}/api/resume/${user.id}/active`)
    const resumeData = resumeRes.ok ? await resumeRes.json() : {}

    const res = await fetch(`${API}/api/runs/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id, profile: { id: user.id, email: user.email, name: '' }, prefs, resume_text: resumeData.raw_text || '' }),
    })
    const { run_id } = await res.json()

    const es = new EventSource(`${API}/api/runs/${run_id}/stream`)
    esRef.current = es
    es.onmessage = (e) => {
      const ev = JSON.parse(e.data)
      if (ev.event === 'portal_searched') setStats(s => ({ ...s, found: ev.total_found || s.found, portal: ev.portal || s.portal }))
      else if (ev.event === 'application') {
        setStats(s => ({ ...s, applied: ev.status === 'submitted' ? s.applied + 1 : s.applied, flagged: ev.status === 'flagged' ? s.flagged + 1 : s.flagged }))
        setApps(prev => [{ company: ev.company, title: ev.title, portal: ev.portal, score: Math.round((ev.score || 0) * 100), status: ev.status, resume_version: ev.resume_version, cv_sent: ev.cover_letter_sent, msg_sent: ev.message_sent, timestamp: new Date().toLocaleTimeString() }, ...prev])
      } else if (ev.event === 'complete') { setRunning(false); es.close() }
    }
    es.onerror = () => { setRunning(false); es.close() }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <span className="font-bold text-gray-900 text-lg">JobApply</span>
        <div className="flex items-center gap-4 text-sm">
          <Link href="/dashboard" className="text-blue-600 font-medium">Dashboard</Link>
          <Link href="/tracker" className="text-gray-500 hover:text-gray-900">Tracker</Link>
          <Link href="/queue" className="text-gray-500 hover:text-gray-900">Review Queue</Link>
          <Link href="/settings" className="text-gray-500 hover:text-gray-900">Settings</Link>
          <button onClick={() => supabase.auth.signOut()} className="text-gray-400 hover:text-gray-600 text-xs">Sign out</button>
        </div>
      </nav>
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-sm text-gray-500">{running ? `Running — searching ${stats.portal}` : 'Ready to run'}</p>
          </div>
          {running
            ? <button className="btn-secondary text-red-600 border-red-200" onClick={() => { esRef.current?.close(); setRunning(false) }}>⏹ Stop</button>
            : <button className="btn-primary" onClick={startRun}>🚀 Start applying</button>}
        </div>

        <div className="grid grid-cols-4 gap-4 mb-6">
          {[{ label: 'Jobs found', value: stats.found, icon: '🔍' }, { label: 'Applied', value: stats.applied, icon: '✅', color: 'text-green-600' }, { label: 'Flagged', value: stats.flagged, icon: '⚠️', color: 'text-yellow-600' }, { label: 'Portal', value: stats.portal || '—', icon: '🌐' }].map(s => (
            <div key={s.label} className="card p-4">
              <div className="text-xl mb-1">{s.icon}</div>
              <div className={`text-2xl font-bold ${s.color || 'text-gray-900'}`}>{s.value}</div>
              <div className="text-xs text-gray-500">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="card overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
            <span className="font-semibold text-gray-900">Live applications</span>
            {running && <span className="flex items-center gap-1.5 text-xs text-green-600 font-medium"><span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />Live</span>}
          </div>
          {apps.length === 0
            ? <div className="px-5 py-12 text-center text-gray-400 text-sm">{running ? 'Searching for jobs…' : 'Hit "Start applying" to begin'}</div>
            : <div className="overflow-x-auto"><table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-100"><tr>{['Company','Role','Portal','Match','Resume','CV','Msg','Status','Time'].map(h => <th key={h} className="px-4 py-2 text-left text-xs font-medium text-gray-500">{h}</th>)}</tr></thead>
                <tbody>{apps.map((a, i) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-medium">{a.company}</td>
                    <td className="px-4 py-2.5 text-gray-600">{a.title}</td>
                    <td className="px-4 py-2.5"><span className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">{a.portal}</span></td>
                    <td className="px-4 py-2.5"><span className={`text-xs font-semibold ${a.score >= 75 ? 'text-green-600' : a.score >= 55 ? 'text-yellow-600' : 'text-red-500'}`}>{a.score}%</span></td>
                    <td className="px-4 py-2.5 text-xs text-gray-500">{a.resume_version}</td>
                    <td className="px-4 py-2.5 text-center">{a.cv_sent ? '✅' : '—'}</td>
                    <td className="px-4 py-2.5 text-center">{a.msg_sent ? '✅' : '—'}</td>
                    <td className="px-4 py-2.5"><span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLOR[a.status] || ''}`}>{a.status}</span></td>
                    <td className="px-4 py-2.5 text-xs text-gray-400">{a.timestamp}</td>
                  </tr>
                ))}</tbody>
              </table></div>}
        </div>

        {pastRuns.length > 0 && (
          <div className="mt-6 card overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 font-semibold text-gray-900">Past runs</div>
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100"><tr>{['Date','Status','Applied','Flagged'].map(h => <th key={h} className="px-4 py-2 text-left text-xs font-medium text-gray-500">{h}</th>)}</tr></thead>
              <tbody>{pastRuns.slice(0,5).map(r => (
                <tr key={r.id} className="border-b border-gray-50">
                  <td className="px-4 py-2.5 text-gray-500 text-xs">{new Date(r.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-2.5"><span className={`text-xs font-medium px-2 py-0.5 rounded-full ${r.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>{r.status}</span></td>
                  <td className="px-4 py-2.5 font-semibold text-green-600">{r.apps_submitted}</td>
                  <td className="px-4 py-2.5 text-yellow-600">{r.apps_flagged}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
