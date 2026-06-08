# AI Job Inbox Assistant

A full-stack portfolio project for tracking job-search email, building application timelines, and surfacing AI-assisted next steps. The backend syncs Gmail (or demo data), classifies messages, and exposes a REST API. A Next.js demo UI showcases the product without requiring real OAuth or OpenAI keys.

**License:** [MIT](LICENSE)

## Why this project exists

Job applications generate scattered email across many companies and stages. This project demonstrates how to:

- Ingest and classify job-search mail with structured AI output
- Collapse multiple emails into one application timeline per company/role
- Expose dashboard, analytics, and assistant endpoints behind real JWT auth
- Keep architecture maintainable with clear service and integration boundaries

It is designed as an interview-ready reference implementation, not a production SaaS.

## Key features

- **Google login + JWT** — authenticated API access
- **Gmail connect (separate OAuth)** — per-user credential storage for sync
- **Email sync** — manual and optional background sync via APScheduler
- **AI classification** — categories, company/role extraction, deadlines (PydanticAI + OpenAI)
- **Application timeline** — one record per company/role, many events
- **Dashboard & analytics** — pipeline counts, rates, trends, activity
- **Assistant** — next actions, reply drafts, resume-to-job matching
- **Demo mode** — seeded data + JWT script for presentations without Gmail/OpenAI
- **Demo frontend** — dark-mode Next.js UI with pasted token auth

## Tech stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic, PyJWT |
| Database | PostgreSQL, Docker Compose |
| AI | PydanticAI, OpenAI (optional; mock fallbacks when unset) |
| Integrations | Gmail API, Google OAuth |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Quality | pytest, ruff, mypy, pre-commit, GitHub Actions |

## Architecture

```text
Routes → Services → Repositories / Integrations → PostgreSQL
```

- **Routes** — thin HTTP handlers (`app/api/routes/`)
- **Services** — business workflows (`app/services/`)
- **Repositories** — user-scoped queries (`app/db/repositories/`)
- **Integrations** — Gmail, Google OAuth, AI agents (`app/integrations/`)
- **Schemas / models** — API contracts vs persistence (`app/schemas/`, `app/models/`)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for data model, AI flow, background sync, and error handling.

## Screenshots

Capture these locally after running the demo (files not included in the repo until you add them):

| Screen | Path |
|---|---|
| Login | [docs/screenshots/login.png](docs/screenshots/login.png) |
| Dashboard | [docs/screenshots/dashboard.png](docs/screenshots/dashboard.png) |
| Applications | [docs/screenshots/applications.png](docs/screenshots/applications.png) |
| Application detail | [docs/screenshots/application-detail.png](docs/screenshots/application-detail.png) |
| Resume profile | [docs/screenshots/profile.png](docs/screenshots/profile.png) |

## Quick start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Node.js 20+ (for frontend demo)
- Google Cloud OAuth credentials (only for real Gmail/login flows)

### Backend

```bash
cp .env.example .env
docker compose up -d
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend demo UI

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Demo mode (recommended for presentations)

No Gmail or OpenAI required. Full walkthrough: [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

```bash
# After backend setup
python scripts/seed_demo_data.py
python scripts/create_demo_token.py   # paste token in frontend login
```

Set `ENVIRONMENT=development` or `local`. Demo scripts are **blocked** when `ENVIRONMENT=production`.

Seeded data includes fake companies (Stripe, Datadog, Shopify, Meta, Anthropic, Figma) covering confirmation, assessment, interview, rejection, outreach, and offer scenarios. Re-running the seed script is idempotent.

## Auth and Gmail flows

**Login (JWT)**

1. `GET /api/v1/auth/google/login` → Google sign-in
2. `GET /api/v1/auth/google/callback` → JWT issued
3. Protected routes use `Authorization: Bearer <token>`

**Gmail connect (separate from login)**

1. Authenticate with JWT
2. `GET /api/v1/auth/gmail/connect` → Gmail OAuth
3. `GET /api/v1/auth/gmail/callback` → credentials stored
4. `POST /api/v1/emails/sync` or background sync fetches mail

See [docs/API_OVERVIEW.md](docs/API_OVERVIEW.md) for all endpoints.

## AI features

| Feature | Endpoint | Notes |
|---|---|---|
| Email classification | via sync pipeline | Skips irrelevant mail for applications |
| Next actions | `GET /assistant/next-actions` | Prioritized recommendations |
| Reply drafts | `POST /assistant/draft-reply` | Draft only; never sends email |
| Job match | `POST /assistant/match-job` | Requires stored resume profile |

When `OPENAI_API_KEY` is unset, agents use deterministic mock logic for local development.

## Background sync (optional)

```env
ENABLE_BACKGROUND_SYNC=true
BACKGROUND_SYNC_INTERVAL_MINUTES=30
BACKGROUND_SYNC_MAX_RESULTS=25
```

Uses APScheduler in the FastAPI lifespan. Shares the same `EmailSyncService` as manual sync. Only runs for users with Gmail credentials.

## Environment variables

Copy [.env.example](.env.example) to `.env`. Key settings:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing (use 32+ bytes in production) |
| `ENVIRONMENT` | `local` / `development` / `production`; controls demo scripts |
| `DATABASE_URL` | PostgreSQL connection string |
| `GMAIL_CLIENT_ID` / `GMAIL_CLIENT_SECRET` | Google OAuth |
| `OPENAI_API_KEY` | Optional; enables live AI agents |
| `ENABLE_BACKGROUND_SYNC` | Scheduled Gmail sync toggle |

Frontend: [frontend/.env.example](frontend/.env.example) — `NEXT_PUBLIC_API_BASE_URL`.

## Development commands

```bash
# Backend tests
pytest

# Backend lint
ruff check app tests
ruff format app tests

# Optional
mypy app
pre-commit run --all-files

# Frontend
cd frontend && npm run lint && npm run build
```

CI runs backend ruff + pytest and frontend build on push/PR (see [.github/workflows/ci.yml](.github/workflows/ci.yml)).

Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)

## Security and privacy notes

- User-owned resources return **404** for other users (no existence leak).
- API errors avoid exposing tokens, OAuth internals, or stack traces.
- Gmail credentials are stored per user; treat production storage as sensitive (encryption at rest not implemented).
- Demo JWT script and seed data are for local/demo use only.
- Do not commit `.env`, credentials, or real inbox data.

## Limitations and future improvements

Current scope is intentional for a portfolio project:

- No production frontend Google login (demo UI uses pasted JWT)
- Gmail tokens stored without application-level encryption
- No email sending from reply drafts
- No multi-tenant admin or billing
- Mock AI when OpenAI key is absent
- Frontend has no automated test suite

Possible next steps: encrypted credential storage, production auth UI, background job queue, rate limiting, observability, and deployment manifests.

## Project layout

| Path | Description |
|---|---|
| `app/` | FastAPI backend |
| `frontend/` | Next.js demo UI |
| `alembic/` | Database migrations |
| `scripts/` | Demo seed and token helpers |
| `tests/` | Backend pytest suite |
| `docs/` | Architecture, API, demo script |

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API overview](docs/API_OVERVIEW.md)
- [Demo script](docs/DEMO_SCRIPT.md)
- [Frontend README](frontend/README.md)
