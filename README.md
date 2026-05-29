# JobApply — AI-powered job application platform

Automated job applications across LinkedIn, Indeed, Glassdoor, Dice, and Jobright.
AI tailors your resume and cover letter for every job. Applies automatically.

## Stack
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python + LangGraph
- **Browser automation**: Playwright (headless Chromium)
- **Queue**: Celery + Redis
- **LLM**: Gemini Flash 1.5 (free) + Groq (free)

## Quick start

```bash
cp .env.example .env   # fill in your API keys
docker-compose up      # starts redis + backend + worker + frontend
```

Open http://localhost:3000

## Project structure
```
jobapply/
├── backend/
│   ├── app/
│   │   ├── agents/          # orchestrator + search + scoring + tailoring + application
│   │   ├── api/routes/      # FastAPI route handlers
│   │   ├── models/          # Pydantic schemas
│   │   ├── services/        # LLM, browser, email
│   │   └── workers/         # Celery tasks
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    └── src/app/
        ├── dashboard/       # live run dashboard
        ├── tracker/         # application tracker table
        ├── queue/           # human review queue
        ├── settings/        # saved fields + preferences
        └── onboarding/      # multi-step setup wizard
```
