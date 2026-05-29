'use client'
import { useState } from 'react'
import Link from 'next/link'

const STATUS_COLOR: Record<string, string> = { submitted:'bg-green-100 text-green-700', flagged:'bg-yellow-100 text-yellow-700', failed:'bg-red-100 text-red-700', pending:'bg-gray-100 text-gray-500' }

const DEMO = Array.from({length:12},(_,i)=>({
  id:i, company:['Stripe','Figma','Notion','Vercel','Linear','Loom','Retool','Rippling','Brex','Plaid','Ramp','Mercury'][i],
  title:'Software Engineer', portal:['linkedin','indeed','dice','jobright','glassdoor'][i%5],
  score:[88,82,79,75,71,68,65,62,60,58,55,53][i], status:['submitted','submitted','submitted','flagged','submitted','submitted','failed','submitted','submitted','submitted','submitted','submitted'][i],
  resume:'v3_tailored', cv:i%2===0, msg:i%3===0, date:'May 29, 2026', url:'#'
}))

export default function Tracker() {
  const [filter, setFilter] = useState('all')
  const filtered = filter === 'all' ? DEMO : DEMO.filter(a => a.status === filter)

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
          <h1 className="text-2xl font-bold">Application Tracker</h1>
          <button className="btn-secondary text-sm" onClick={() => {}}>⬇ Export CSV</button>
        </div>
        <div className="flex gap-2 mb-4">
          {['all','submitted','flagged','failed'].map(s => (
            <button key={s} onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${filter===s ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}>
              {s === 'all' ? `All (${DEMO.length})` : s}
            </button>
          ))}
        </div>
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>{['Company','Role','Portal','Match','Resume','CV','Msg','Applied','Status','Link'].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}</tr>
            </thead>
            <tbody>
              {filtered.map((a,i) => (
                <tr key={a.id} className={`border-b border-gray-50 hover:bg-gray-50 ${i%2===0?'':'bg-gray-50/40'}`}>
                  <td className="px-4 py-3 font-semibold text-gray-900">{a.company}</td>
                  <td className="px-4 py-3 text-gray-600">{a.title}</td>
                  <td className="px-4 py-3"><span className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">{a.portal}</span></td>
                  <td className="px-4 py-3"><span className={`font-bold text-sm ${a.score>=75?'text-green-600':a.score>=60?'text-yellow-600':'text-red-500'}`}>{a.score}%</span></td>
                  <td className="px-4 py-3 text-xs text-gray-500">{a.resume}</td>
                  <td className="px-4 py-3 text-center text-sm">{a.cv?'✅':'—'}</td>
                  <td className="px-4 py-3 text-center text-sm">{a.msg?'✅':'—'}</td>
                  <td className="px-4 py-3 text-xs text-gray-400">{a.date}</td>
                  <td className="px-4 py-3"><span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLOR[a.status]||''}`}>{a.status}</span></td>
                  <td className="px-4 py-3"><a href={a.url} className="text-blue-500 hover:underline text-xs">View →</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
