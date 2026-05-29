import Link from 'next/link'

export default function Landing() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 bg-gradient-to-br from-blue-50 to-white">
      <div className="max-w-2xl w-full text-center">
        <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 text-sm font-semibold px-4 py-1.5 rounded-full mb-6">
          🤖 AI-powered · 100% automated
        </div>
        <h1 className="text-5xl font-bold text-gray-900 mb-4">Apply to jobs while you sleep</h1>
        <p className="text-xl text-gray-500 mb-8">
          Enter your preferences once. Our AI agents search LinkedIn, Indeed, Dice, and more —
          tailoring your resume for each job and applying automatically.
        </p>
        <div className="flex gap-3 justify-center">
          <Link href="/auth/signup" className="btn-primary text-base px-6 py-3">Get started free</Link>
          <Link href="/auth/login" className="btn-secondary text-base px-6 py-3">Sign in</Link>
        </div>
        <div className="mt-16 grid grid-cols-3 gap-6 text-left">
          {[
            { icon: '🔍', title: '6 job portals', body: 'LinkedIn, Indeed, Glassdoor, Dice, Jobright, and more' },
            { icon: '✍️', title: 'Tailored per job', body: 'Resume and cover letter rewritten to match each JD' },
            { icon: '📊', title: 'Live tracker', body: 'Watch applications roll in with real-time status updates' },
          ].map(f => (
            <div key={f.title} className="card p-5">
              <div className="text-2xl mb-2">{f.icon}</div>
              <div className="font-semibold text-gray-900 mb-1">{f.title}</div>
              <div className="text-sm text-gray-500">{f.body}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
