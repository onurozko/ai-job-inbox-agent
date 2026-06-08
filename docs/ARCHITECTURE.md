# Architecture

This document describes how the AI Job Inbox Assistant is structured and how major workflows flow through the system.

## High-level view

```text
Client (curl / Next.js demo UI)
        |
        v
   FastAPI routes  (auth, validation, HTTP)
        |
        v
   Services        (business workflows)
        |
   +----+----+
   |         |
   v         v
Repositories  Integrations (Gmail, Google OAuth, PydanticAI)
   |         |
   +----+----+
        v
   PostgreSQL
```

The backend follows a layered design: routes stay thin, services own workflows, repositories centralize user-scoped database access, and integrations wrap external systems.

## Backend layers

| Layer | Location | Responsibility |
|---|---|---|
| Routes | `app/api/routes/` | HTTP handlers, dependency injection, request/response mapping |
| Dependencies | `app/api/deps.py` | JWT auth, DB session |
| Exception handlers | `app/api/exception_handlers.py` | Map `AppError` to HTTP responses |
| Services | `app/services/` | Business logic (sync, dashboard, assistant, profile, analytics) |
| Repositories | `app/db/repositories/` | Reusable user-scoped queries |
| Integrations | `app/integrations/` | Gmail API, Google login OAuth, PydanticAI agents |
| Schemas | `app/schemas/` | Pydantic request/response models |
| Models | `app/models/` | SQLAlchemy ORM persistence |
| Core | `app/core/` | Config, security, exceptions, logging, scheduler |

## Frontend structure

The demo UI in `frontend/` is a Next.js App Router application:

| Path | Purpose |
|---|---|
| `src/app/` | Pages: login, dashboard, applications, profile |
| `src/lib/api.ts` | Fetch wrapper with JWT from localStorage |
| `src/lib/services.ts` | Typed API calls |
| `src/components/` | Layout shell, dashboard sections, pipeline list, timeline, assistant panels |

The frontend uses a pasted demo JWT only. It does not implement Google login or production auth yet.

## Data model overview

Core entities and relationships:

```text
User
 ├── EmailMessage (synced from Gmail)
 ├── JobApplication (one per user + company + normalized role)
 │    └── ApplicationEvent (timeline entries, linked to emails)
 ├── GmailCredential (separate from login; per-user Gmail OAuth tokens)
 └── UserProfile (resume text, target roles/locations)
```

**Timeline rule:** Multiple job-search emails for the same company/role update one `JobApplication` and append `ApplicationEvent` records. Irrelevant emails are stored but do not create applications.

**Ownership rule:** All user-owned resources are queried with `current_user.id`. Cross-user access returns `404`.

## AI agent flow

AI features live in `app/integrations/ai/` and are invoked from services:

1. **Email classification** — After Gmail sync, emails are classified (category, company, role, deadlines). Irrelevant mail is skipped for application creation.
2. **Next actions** — Recommends follow-ups from active applications and recent events.
3. **Reply drafts** — Generates a draft reply for a specific email without sending mail.
4. **Job match** — Compares stored resume text against an application and/or pasted job description.

When `OPENAI_API_KEY` is unset, agents use deterministic mock logic suitable for local development and demos.

Agents are instructed not to invent credentials or experience not present in source data (especially for reply drafts and job matching).

## Background sync flow

Optional background sync uses APScheduler in the FastAPI lifespan (`app/core/scheduler.py`):

1. Starts only when `ENABLE_BACKGROUND_SYNC=true`.
2. On each interval, `ScheduledEmailSyncService` finds users with `GmailCredential` records.
3. For each user, it calls the same `EmailSyncService` used by manual `POST /api/v1/emails/sync`.
4. Failures for one user do not stop sync for others.

Manual sync and background sync share one workflow; logic is not duplicated.

## Auth vs Gmail separation

Two distinct OAuth flows:

| Flow | Purpose | Endpoints |
|---|---|---|
| Google login | Authenticate the user, issue JWT | `/auth/google/login`, `/auth/google/callback` |
| Gmail connect | Store Gmail API credentials for sync | `/auth/gmail/connect`, `/auth/gmail/callback` |

A user can log in without connecting Gmail. Gmail sync (manual or scheduled) requires stored Gmail credentials.

## Error handling strategy

Application code raises typed exceptions from `app/core/exceptions.py` (e.g. `NotFoundError`, `UnauthorizedError`, `GmailCredentialsMissingError`, `ExternalServiceError`).

Global handlers map these to consistent HTTP status codes and safe messages. Stack traces and secrets are not returned to clients. Validation errors return `422` with structured details.

## Demo utilities

Local demo scripts in `scripts/` and `app/demo/` seed fake data and mint JWTs for `demo@example.com`. They are blocked when `ENVIRONMENT=production`.
