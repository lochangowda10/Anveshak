# ANVESHAK — Project Setup Guide

> From zero to running in 10 minutes.

---

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** and **pnpm**
- **Docker** and **Docker Compose**
- **Git**

---

## 1. Clone & Branch

```bash
git clone <repo-url> anveshak
cd anveshak
git checkout -b dev
git checkout -b feat/<your-module>
```

---

## 2. Environment Variables

```bash
cp .env.example .env
# Edit .env and fill in:
#   TRONGRID_API_KEY=<your-key>
#   DATABASE_URL=postgresql+asyncpg://anveshak:anveshak@localhost:5432/anveshak
#   SECRET_KEY=<random-string>
```

---

## 3. Start Infrastructure

```bash
docker compose up -d postgres
```

---

## 4. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

**Verify:** http://localhost:8000/docs shows the OpenAPI UI.

---

## 5. Frontend Setup

```bash
cd frontend
pnpm install
pnpm dev
```

**Verify:** http://localhost:5173 shows the app.

---

## 6. Run Tests

```bash
# Backend
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend
cd frontend
pnpm test
```

---

## 7. Lint & Format

```bash
# Backend
ruff check .
black --check .

# Frontend
pnpm lint
pnpm format:check
```

---

## Docker Compose (Full Stack)

```bash
docker compose up --build
```

This starts:
- PostgreSQL on port 5432
- FastAPI backend on port 8000
- React frontend on port 5173

---

## Project Structure Quick Reference

```
anveshak/
├── CONTEXT.md              ← What is this project?
├── CONTRIBUTING.md          ← How to write code
├── OWNERSHIP.md             ← Who owns what module
├── .env.example             ← Environment variable template
├── docker-compose.yml       ← Full stack orchestration
├── backend/
│   ├── pyproject.toml       ← Python deps + tool config
│   ├── alembic.ini          ← Migration config
│   ├── alembic/             ← DB migrations
│   ├── app/
│   │   ├── main.py          ← FastAPI app entry
│   │   ├── core/            ← Config, deps, utils
│   │   ├── api/             ← Route handlers
│   │   ├── models/          ← DB + Pydantic models
│   │   ├── services/        ← Business logic modules
│   │   └── db/              ← Database session, engine
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   └── graph/           ← Cytoscape config
│   └── tests/
├── docs/
│   ├── ADR.md               ← Architecture decisions
│   ├── API_CONTRACT.md      ← Interface specifications
│   ├── SPRINT_PLAN.md       ← Sprint tasks & timeline
│   └── AGENT_GUIDE.md       ← AI coding agent rules
├── infra/
│   └── Dockerfile
└── scripts/
    └── seed_labels.py       ← Seed VASP label data
```
