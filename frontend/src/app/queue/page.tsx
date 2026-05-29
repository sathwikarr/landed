'use client'
import Link from 'next/link'

const DEMO = [
  { id:1, company:'Google', role:'Senior SWE', url:'https://careers.google.com', reason:'CAPTCHA on application form', portal:'greenhouse', score:91 },
  { id:2, company:'Meta', role:'Product Engineer', url:'https://metacareers.com', reason:'Unusual field: "Describe your approach to ambiguity"', portal:'lever', score:84 },
]

export default function Queue() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <span className="font-bold text-gray-900 text-lg">JobApply</span>
        <div className="flex gap-4 text-sm">
          <Link href="/dashboard" className="text-gray-500 hover:text-gray-900">Dashboard</Link>
          <Link href="/tracker" className="text-gray-500 hover:text-gray-900">Tracker</Link>
          <Link href="/queue" className="text-blue-600 font-medium">Review Queue</Link>
          <Link href="/settings" className="text-gray-500 hover:text-gray-900">Settings</Link>
        </div>
      </nav>
      <div className="max-w-3xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold mb-2">Human Review Queue</h1>
        <p className="text-sm text-gray-500 mb-6">Jobs that need your attention — CAPTCHA or unusual fields the agent couldn't handle.</p>
        {DEMO.length === 0
          ? <div className="card p-12 text-center text-gray-400">No items need review 🎉</div>
          : <div className="space-y-4">
              {DEMO.map(item => (
                <div key={item.id} className="card p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="font-semibold text-gray-900">{item.role} — {item.company}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{item.portal} · {item.score}% match</div>
                    </div>
                    <span className="bg-yellow-100 text-yellow-700 text-xs font-semibold px-2 py-1 rounded-full">Needs review</span>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 text-sm text-yellow-800 mb-4">
                    ⚠️ {item.reason}
                  </div>
                  <div className="flex gap-2">
                    <a href={item.url} target="_blank" className="btn-primary text-sm">Open & apply manually</a>
                    <button className="btn-secondary text-sm text-red-500 border-red-200 hover:bg-red-50">Skip this job</button>
                  </div>
                </div>
              ))}
            </div>
        }
      </div>
    </div>
  )
}
