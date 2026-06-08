# Contributing

Thanks for your interest in this project. It is primarily a portfolio/reference implementation, but issues and small improvements are welcome.

## Local setup

### Backend

```bash
cp .env.example .env
docker compose up -d
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend (optional demo UI)

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

See [README.md](README.md) for demo seeding and token generation.

## Code quality

Run these before opening a pull request:

```bash
# Backend
ruff check app tests
ruff format app tests --check
pytest

# Optional
mypy app
pre-commit run --all-files

# Frontend
cd frontend
npm run lint
npm run build
```

## Guidelines

- Keep routes thin; put business logic in services.
- Scope all user-owned queries to `current_user.id`.
- Do not commit secrets, `.env` files, or local credentials.
- Preserve existing API contracts unless fixing an obvious bug.
- Add or update tests for behavior changes.

## Architecture reference

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/API_OVERVIEW.md](docs/API_OVERVIEW.md)
