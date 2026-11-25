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

## Current Team Setup (5-Developer Active Sprint)

> **Team Lead & Final PR Reviewer:** **Lochan** (reviews all PRs, enforces `CONTRIBUTING.md` + CI gates, and merges into `main`).
> **5 developers** are actively driving implementation across 5 non-overlapping tracks.
> Tasks are claimed asynchronously using the **Claim ➔ Working ➔ Finished** protocol in `docs/SPRINT_PLAN.md`.

### Primary Domain Split (5 Tracks)

| Track | Lead | Backup / Reviewer | Owned Modules & Scope | Milestones |
|---|---|---|---|---|
| **Track 1: DB Schema & Case Intake** | **Lochan** | Hanamaraddi | `backend/app/models/case.py`, `backend/alembic/`, `backend/app/api/schemas/case.py`, `backend/app/api/routes/cases.py` | **M1** |
| **Track 2: TRON Adapter & Graph Engine** | **Hanamaraddi** | Lochan | `backend/app/services/chain/`, `backend/app/models/transaction.py`, `backend/app/services/graph/`, `backend/app/models/trace.py`, `backend/app/api/routes/trace.py` | **M0, M2, M3** |
| **Track 3: VASP Attribution, Ranking & Evidence/PDF** | **Harshitha** | Lochan | `backend/app/services/attribution/`, `backend/app/services/ranking/`, `backend/app/services/evidence/`, `backend/app/models/{label,candidate,action_package}.py`, `backend/app/api/routes/{candidates,labels,evidence}.py`, `backend/app/scripts/seed_labels.py` | **M4, M5** |
| **Track 4: Frontend — Case Management & App Shell** | **Haripriya** | Krishnapriya | `frontend/src/App.tsx`, `frontend/src/components/`, `frontend/src/services/api.ts`, `Dashboard.tsx`, `CaseList.tsx`, `CreateCase.tsx`, `CaseDetail.tsx` | **M6** |
| **Track 5: Frontend — Cytoscape Graph, Evidence UI & E2E QA** | **Krishnapriya** | Hanamaraddi | `frontend/src/graph/CytoscapeGraph.tsx`, `CandidatePanel`, `EvidenceView`, `ActionPackageView`, `backend/tests/e2e/`, `backend/app/scripts/seed_demo.py`, Docker/CI QA | **M7, M8** |

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

