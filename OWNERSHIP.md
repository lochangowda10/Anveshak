# ANVESHAK — Module Ownership & Team Allocation

> Each module has **one owner**. The owner is responsible for design decisions,
> code reviews, and ensuring quality. Others may contribute, but the owner has
> final say on their module.

---

## Module Map

```
anveshak/
├── backend/
│   ├── app/
│   │   ├── api/              # REST endpoints (FastAPI)
│   │   ├── core/             # Config, security, shared utilities
│   │   ├── models/           # SQLAlchemy / Pydantic models
│   │   ├── services/
│   │   │   ├── intake/       # Case intake & validation
│   │   │   ├── chain/        # Blockchain adapters (TRON, EVM)
│   │   │   ├── graph/        # Graph engine & pruning
│   │   │   ├── ranking/      # VASP ranking signals
│   │   │   ├── attribution/  # Endpoint identification
│   │   │   └── evidence/     # Evidence packaging & action gen
│   │   └── db/               # Database, migrations
│   ├── tests/
│   └── alembic/
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Route-level pages
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API client layer
│   │   ├── store/            # State management
│   │   └── graph/            # Cytoscape graph config & rendering
│   └── tests/
├── infra/                    # Docker, docker-compose, CI
├── docs/                     # Architecture docs, API docs
└── scripts/                  # Dev utilities, seed data
```

---

## Current Team Setup (2-Person Active Sprint)

> As of now, **2 core developers** are actively driving implementation.
> Tasks are claimed asynchronously using the **Claim-Work-Finish** protocol.

### Primary Domain Split

| Domain / Pipeline Half | Primary Lead | Backup / Reviewer | Scope |
|------------------------|--------------|-------------------|-------|
| **Track A: Ingestion, Chain & Graph Core** | **Developer 1 (Lochan)** | Developer 2 | TRON adapter, TronGrid, Canonical Schema, DB Models, NetworkX traversal & pruning |
| **Track B: Intelligence, Action Pkg & UI** | **Developer 2** | Developer 1 (Lochan) | Scoring & ranking, VASP attribution store, Evidence & PDF generator, React Cytoscape UI |

---

## The "Claim ➔ Working ➔ Finished" Protocol

To ensure nobody works on the same task at the same time:

1. **Before starting a task:**
   - Check `docs/SPRINT_PLAN.md`.
   - Update the task status to `[WORKING: @Name]` in the sprint board / PR issue.
   - Create a feature branch: `feat/<task-name>`.

2. **While working:**
   - Commit often with conventional commits (`feat(...)`, `test(...)`).
   - If blocked or modifying shared interface contracts (`docs/API_CONTRACT.md`), sync immediately with the other dev.

3. **When finished:**
   - Run tests + linter (`pytest`, `ruff`, `pnpm test`).
   - Open PR targeting `dev` (or merge directly if pairing).
   - Update the task in `docs/SPRINT_PLAN.md` to `[FINISHED: @Name]` (or check the box `[x]`).
   - Ping the teammate: _"Finished task X, merged to dev. You're clear to pull."_

---

## Rules of Ownership

1. **Never start a task without marking it `[WORKING: <Name>]`.**
2. **Never push directly to `main`.** Keep `dev` as the shared sync branch.
3. **Pull before starting new work:** `git pull origin dev` to stay up to date.
4. **Cross-module interfaces are agreed in writing:** Refer to `docs/API_CONTRACT.md`. If changes are needed, both devs agree first.

