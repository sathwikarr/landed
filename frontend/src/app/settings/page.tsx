'use client'
import { useState } from 'react'
import Link from 'next/link'

export default function Settings() {
  const [saved, setSaved] = useState(false)
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
        <div className="space-y-4">
          <div className="card p-5">
            <h3 className="font-semibold mb-3">Saved form fields</h3>
            <p className="text-sm text-gray-500 mb-3">Answers to fields the agent discovered and saved for future applications.</p>
            {[{k:'Phone',v:'+1 555 000 0000'},{k:'Work authorization',v:'US Citizen'},{k:'Visa sponsorship',v:'No'},{k:'LinkedIn URL',v:'linkedin.com/in/sathwik'},{k:'GitHub URL',v:'github.com/sathwikarr'}].map(f => (
              <div key={f.k} className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0">
                <span className="text-sm text-gray-500 w-40">{f.k}</span>
                <input className="input flex-1 text-sm" defaultValue={f.v} />
              </div>
            ))}
          </div>
          <div className="card p-5">
            <h3 className="font-semibold mb-3">Notification email</h3>
            <input className="input" defaultValue="sathwik@icloud.com" />
          </div>
          <button className="btn-primary" onClick={() => setSaved(true)}>
            {saved ? '✅ Saved' : 'Save settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
