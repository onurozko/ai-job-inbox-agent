# AI Job Inbox — Demo Frontend

Minimal Next.js UI for demonstrating the backend with a pasted demo JWT. Dark-mode-first layout for portfolio presentations.

## Setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` to your backend API prefix (default `http://localhost:8000/api/v1`).

## Demo flow

See the root [README](../README.md) and [docs/DEMO_SCRIPT.md](../docs/DEMO_SCRIPT.md).

1. Seed backend demo data and create a token.
2. Open http://localhost:3000 and paste the JWT.
3. Explore dashboard, applications, profile, and assistant tools.

## Screenshots

Add captures to [docs/screenshots/](../docs/screenshots/) at the repo root (see that folder's README).

## Notes

- Token storage uses `localStorage` for demo purposes only.
- No Google login or production auth in the frontend yet.
- Manual testing only; no frontend test suite configured.
