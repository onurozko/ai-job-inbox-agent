# Demo Script (3–5 minutes)

Use this walkthrough for portfolio presentations or interview demos. No real Gmail or OpenAI key required.

## Before you start

```bash
# Terminal 1 — backend
cp .env.example .env
docker compose up -d
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed_demo_data.py
python scripts/create_demo_token.py   # copy the token
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Ensure `ENVIRONMENT=development` (or `local`) in `.env`.

## 1. Intro (30 seconds)

> This is an AI-assisted job search inbox backend. It syncs job-related Gmail, classifies messages, builds an application timeline, and exposes dashboard, analytics, and assistant endpoints. There is a demo UI that uses seeded data and a local JWT—no Google login required for the demo.

## 2. Login (30 seconds)

1. Open [http://localhost:3000](http://localhost:3000).
2. Paste the token from `create_demo_token.py`.
3. Continue to the dashboard.

Mention: production auth is JWT after Google login; the demo uses a script-generated token stored in localStorage.

## 3. Dashboard (45 seconds)

Highlight:

- **Overview** — total/active applications, interviews, offers
- **Next actions** — AI-style recommendations (mock when no OpenAI key)
- **Upcoming deadlines** — assessment/interview dates from seeded data
- **Recent activity** — timeline events from fake companies
- **Analytics** — response, interview, and offer rates

## 4. Applications pipeline (45 seconds)

1. Go to **Applications**.
2. Point out company, role, status badges, and last updated.
3. Open one application (e.g. Shopify or Datadog).

On the detail page:

- Walk through the **timeline** (confirmation → assessment → interview, etc. across seeded companies).
- Show **related emails** tied to events.

## 5. Assistant tools (60 seconds)

On an application detail page:

1. **Reply draft** — click “Draft reply” on an email; show generated text and copy button. Note drafts are never sent automatically.
2. **Job match** — optionally paste a short job description; run match; explain score, verdict, matched/missing skills. Mention resume comes from the profile page.

## 6. Profile and analytics (30 seconds)

1. Open **Resume** — show stored resume and target roles/locations used for matching.
2. Optionally return to dashboard **Analytics** section or call `GET /api/v1/analytics/summary` in Swagger.

## 7. Close (30 seconds)

Summarize architecture briefly:

- FastAPI + PostgreSQL backend with layered services
- Gmail OAuth separate from login; optional background sync
- PydanticAI agents with mock fallbacks for demos
- Next.js demo frontend for portfolio viewing

Point reviewers to `docs/ARCHITECTURE.md` and the GitHub repo README.

## Troubleshooting

| Issue | Fix |
|---|---|
| 401 on API calls | Re-paste token; check `NEXT_PUBLIC_API_BASE_URL` |
| Empty dashboard | Run `python scripts/seed_demo_data.py` again |
| Demo scripts blocked | Set `ENVIRONMENT=development`, not `production` |
| CORS errors | Backend `CORS_ORIGINS=*` or include `http://localhost:3000` |
