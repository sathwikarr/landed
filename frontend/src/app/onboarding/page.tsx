'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

const PLATFORMS = ['linkedin','indeed','glassdoor','dice','jobright']
const EXP_LEVELS = ['intern','junior','mid','senior','staff','principal']
const REMOTE_OPTS = ['remote','hybrid','on_site','any']

export default function Onboarding() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [prefs, setPrefs] = useState({
    target_roles: '',
    locations: '',
    remote_pref: 'remote',
    salary_min: '',
    salary_max: '',
    experience_level: 'mid',
    years_of_experience: '',
    preferred_companies: '',
    excluded_companies: '',
    platforms: PLATFORMS,
    max_apps_per_day: '10',
    generate_cover_letter: true,
    send_hiring_message: false,
  })

  const set = (k: string, v: unknown) => setPrefs(p => ({...p, [k]: v}))

  const handleFinish = async () => {
    // Save to localStorage for now (replace with API call)
    localStorage.setItem('prefs', JSON.stringify(prefs))
    if (resumeFile) {
      const formData = new FormData()
      formData.append('file', resumeFile)
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/resume/upload`, { method: 'POST', body: formData })
    }
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="card p-8 w-full max-w-lg">
        {/* Progress */}
        <div className="flex gap-1 mb-6">
          {[1,2,3].map(s => (
            <div key={s} className={`h-1.5 flex-1 rounded-full transition-colors ${s <= step ? 'bg-blue-600' : 'bg-gray-200'}`} />
          ))}
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Upload your resume</h2>
            <p className="text-sm text-gray-500">We parse it to build your candidate profile.</p>
            <label className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl p-8 cursor-pointer hover:border-blue-400 transition-colors">
              <span className="text-3xl mb-2">📄</span>
              <span className="text-sm text-gray-500">{resumeFile ? resumeFile.name : 'Click to upload PDF or DOCX'}</span>
              <input type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={e => setResumeFile(e.target.files?.[0] || null)} />
            </label>
            <button className="btn-primary w-full" onClick={() => setStep(2)} disabled={!resumeFile}>Continue</button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Job preferences</h2>
            <div>
              <label className="label">Target roles <span className="text-red-500">*</span></label>
              <input className="input" placeholder="e.g. Software Engineer, Product Manager" value={prefs.target_roles} onChange={e => set('target_roles', e.target.value)} />
            </div>
            <div>
              <label className="label">Locations</label>
              <input className="input" placeholder="e.g. Austin TX, Remote" value={prefs.locations} onChange={e => set('locations', e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Salary min ($)</label>
                <input className="input" type="number" placeholder="80000" value={prefs.salary_min} onChange={e => set('salary_min', e.target.value)} />
              </div>
              <div>
                <label className="label">Salary max ($)</label>
                <input className="input" type="number" placeholder="160000" value={prefs.salary_max} onChange={e => set('salary_max', e.target.value)} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Experience level</label>
                <select className="input" value={prefs.experience_level} onChange={e => set('experience_level', e.target.value)}>
                  {EXP_LEVELS.map(l => <option key={l}>{l}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Remote preference</label>
                <select className="input" value={prefs.remote_pref} onChange={e => set('remote_pref', e.target.value)}>
                  {REMOTE_OPTS.map(r => <option key={r}>{r}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="label">Preferred companies (optional)</label>
              <input className="input" placeholder="Stripe, Figma, Notion" value={prefs.preferred_companies} onChange={e => set('preferred_companies', e.target.value)} />
            </div>
            <div>
              <label className="label">Excluded companies (optional)</label>
              <input className="input" placeholder="Companies to never apply to" value={prefs.excluded_companies} onChange={e => set('excluded_companies', e.target.value)} />
            </div>
            <div className="flex gap-3">
              <button className="btn-secondary flex-1" onClick={() => setStep(1)}>Back</button>
              <button className="btn-primary flex-1" onClick={() => setStep(3)}>Continue</button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold">Application settings</h2>
            <div>
              <label className="label">Max applications per day</label>
              <input className="input" type="number" min="1" max="50" value={prefs.max_apps_per_day} onChange={e => set('max_apps_per_day', e.target.value)} />
            </div>
            <div>
              <label className="label">Platforms to search</label>
              <div className="flex flex-wrap gap-2 mt-1">
                {PLATFORMS.map(p => (
                  <button key={p} type="button"
                    onClick={() => set('platforms', prefs.platforms.includes(p) ? prefs.platforms.filter(x => x !== p) : [...prefs.platforms, p])}
                    className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${prefs.platforms.includes(p) ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-300'}`}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium text-sm">Generate cover letters</div>
                <div className="text-xs text-gray-500">AI-written, tailored per job</div>
              </div>
              <button onClick={() => set('generate_cover_letter', !prefs.generate_cover_letter)}
                className={`w-11 h-6 rounded-full transition-colors relative ${prefs.generate_cover_letter ? 'bg-blue-600' : 'bg-gray-300'}`}>
                <span className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${prefs.generate_cover_letter ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </button>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium text-sm">Send hiring team message</div>
                <div className="text-xs text-gray-500">Short personalised note after applying</div>
              </div>
              <button onClick={() => set('send_hiring_message', !prefs.send_hiring_message)}
                className={`w-11 h-6 rounded-full transition-colors relative ${prefs.send_hiring_message ? 'bg-blue-600' : 'bg-gray-300'}`}>
                <span className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${prefs.send_hiring_message ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </button>
            </div>
            <div className="flex gap-3">
              <button className="btn-secondary flex-1" onClick={() => setStep(2)}>Back</button>
              <button className="btn-primary flex-1" onClick={handleFinish}>Start applying 🚀</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
