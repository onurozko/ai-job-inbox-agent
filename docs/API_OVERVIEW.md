# API Overview

Base URL: `/api/v1`

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs) when running locally.

Authentication: protected routes require `Authorization: Bearer <jwt>` unless noted.

## Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Service and database health check |

## Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/auth/google/login` | No | Redirect to Google sign-in |
| GET | `/auth/google/callback` | No | Google login callback; returns JWT (or redirects) |
| GET | `/auth/me` | Yes | Current user profile |
| POST | `/auth/logout` | Yes | Stateless logout (client deletes token) |
| GET | `/auth/gmail/connect` | Yes | Start Gmail OAuth for current user |
| GET | `/auth/gmail/callback` | No | Gmail OAuth callback; stores credentials |

## Gmail / email sync

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/emails` | Yes | Paginated list of synced emails |
| GET | `/emails/{email_id}` | Yes | Single email details |
| POST | `/emails/sync` | Yes | Manual Gmail sync for current user |
| POST | `/emails/{email_id}/reprocess` | Yes | Re-run classification pipeline on one email |

## Dashboard

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/dashboard/summary` | Yes | Counts, recent events, upcoming deadlines |

## Applications

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/applications` | Yes | Paginated application list |
| GET | `/applications/{application_id}` | Yes | Application detail with events |
| GET | `/applications/{application_id}/timeline` | Yes | Timeline with related emails |
| PATCH | `/applications/{application_id}` | Yes | Update status, summary, action flag |

## Assistant

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/assistant/next-actions` | Yes | AI-recommended next steps |
| POST | `/assistant/draft-reply` | Yes | Generate reply draft for an email |
| POST | `/assistant/match-job` | Yes | Match resume to job application/description |

## Analytics

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/analytics/summary` | Yes | Pipeline metrics, rates, trends, activity counts |

## Profile

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/profile/resume` | Yes | Get stored resume profile |
| PUT | `/profile/resume` | Yes | Create or update resume profile |

## Common response patterns

- `401` — missing or invalid JWT
- `404` — resource not found or not owned by current user
- `400` — bad request (e.g. Gmail not connected)
- `422` — validation error
- `502` — external service failure (generic message; details logged server-side)
