# ANVESHAK — Deployment, Docker & CI/CD Specification

> **Infrastructure & Operations Specification (MVP v1.0.0)**
> Defines exact container configurations, database provisioning, secrets handling, and CI/CD pipelines.

---

## 1. Docker Compose Architecture (`docker-compose.yml`)

All 3 services run on a shared bridge network `anveshak-net`:

| Service | Image / Build | Port | Healthcheck | Volumes |
|---|---|---|---|---|
| `postgres` | `postgres:16-alpine` | `5432:5432` | `pg_isready -U anveshak -d anveshak` | `pgdata:/var/lib/postgresql/data` |
| `backend` | `./backend/Dockerfile` | `8000:8000` | `curl -f http://localhost:8000/api/v1/health` | `./backend/storage:/app/storage` |
| `frontend` | `./frontend/Dockerfile` | `5173:5173` | `curl -f http://localhost:5173` | — |

### Default Local Credentials (`.env`)
- `POSTGRES_USER`: `anveshak`
- `POSTGRES_PASSWORD`: `anveshak`
- `POSTGRES_DB`: `anveshak`
- `DATABASE_URL`: `postgresql+asyncpg://anveshak:anveshak@postgres:5432/anveshak` (inside Docker) or `@localhost:5432/anveshak` (host dev)

---

## 2. Database Provisioning & Startup Order

1. `backend` depends on `postgres` with `condition: service_healthy`.
2. On container startup, `backend` entrypoint runs:
   ```bash
   alembic upgrade head
   python -m app.scripts.seed_labels
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
3. `backend/app/scripts/seed_labels.py` MUST be idempotent (`ON CONFLICT (address, chain, source) DO NOTHING`).

---

## 3. Secrets & Environment Management

- **Never commit `.env`.** Only `.env.example` is tracked in Git.
- Required secrets in production / CI:
  - `TRONGRID_API_KEY` — TronGrid Pro / Free tier key (`TRON-PRO-API-KEY` header)
  - `SECRET_KEY` — 32+ byte random string for future JWT/encryption
  - `DATABASE_URL` — Managed PostgreSQL connection string
- In GitHub Actions CI, use repository Secrets or dummy test values (`TRONGRID_API_KEY=test-key`) since all unit/API tests mock TronGrid via `httpx`.

---

## 4. CI/CD Pipeline (`.github/workflows/ci.yml`)

Triggered on `push` to `dev` / `main` and all `pull_request` events:

### Job 1: `backend-ci`
- Python `3.11`
- PostgreSQL `16` service container for integration tests
- Steps:
  1. `pip install -e ".[dev]"`
  2. `ruff check .`
  3. `black --check .`
  4. `alembic upgrade head`
  5. `pytest tests/ -v --cov=app --cov-fail-under=80`

### Job 2: `frontend-ci`
- Node.js `20` + `pnpm`
- Steps:
  1. `pnpm install --frozen-lockfile`
  2. `pnpm lint`
  3. `npx tsc --noEmit`
  4. `pnpm test --run`
  5. `pnpm build`

---

## 5. Production Hosting (SIH Demo / Cloud)

- **Recommended MVP Hosting:** Single VM (Ubuntu 24.04, 2 vCPU, 4 GB RAM) running Docker Compose behind Caddy/Nginx reverse proxy with HTTPS, OR Render/Railway (Postgres + FastAPI) + Vercel (Vite React).
- **Storage Persistence:** Mount `storage/action_packages/` to a persistent volume so generated PDFs survive container restarts.
