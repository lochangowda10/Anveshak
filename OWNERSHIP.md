# ANVESHAK — Module Ownership & Team Allocation

> Each module has **one owner**. The owner is responsible for design decisions,
> code reviews, and ensuring quality. Others may contribute, but the owner has
> final say on their module.

---

## Module Map (Canonical Repository Layout)

```
anveshak/
├── .github/
│   ├── CODEOWNERS            # Track auto-review assignments
│   ├── pull_request_template.md
│   └── workflows/ci.yml      # backend-ci + frontend-ci
├── backend/
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── pyproject.toml        # Python deps, ruff, black, pytest
│   ├── alembic.ini
│   ├── alembic/versions/     # Sequential migrations: 0000 .. 0005
│   ├── app/
│   │   ├── main.py           # FastAPI entry + router mounts (shared line-add)
│   │   ├── core/             # config.py, database.py (M0 — done)
│   │   ├── api/
│   │   │   ├── routes/       # cases.py, trace.py, candidates.py, labels.py, evidence.py
│   │   │   └── schemas/      # Pydantic v2 request/response schemas
│   │   ├── models/           # SQLAlchemy ORM models (__init__.py re-exports all)
│   │   ├── services/
│   │   │   ├── chain/        # ChainAdapter, TronAdapter, 24h DB cache
│   │   │   ├── graph/        # GraphEngine, 6 pruning filters, Cytoscape serializer
│   │   │   ├── attribution/  # Label matcher & 3 heuristic detectors
│   │   │   ├── ranking/      # 6-signal scoring & ranking engine
│   │   │   └── evidence/     # Evidence assembler, action rules, ReportLab PDF
│   │   └── scripts/          # seed_labels.py, seed_demo.py
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.tsx           # Router & App Shell
│       ├── components/       # StatusBadge, Toast, CandidatePanel, EvidenceView, ActionPackageView
│       ├── pages/            # Dashboard.tsx, CaseList.tsx, CreateCase.tsx, CaseDetail.tsx
│       ├── context/          # CaseContext
│       ├── services/         # Typed fetch API client (api.ts)
│       └── graph/            # CytoscapeGraph.tsx
├── docs/                     # Machine-executable specifications & DECISIONS.md
├── docker-compose.yml        # postgres:16 + backend + frontend
├── LICENSE
└── SECURITY.md
```

---

## Shared Integration Files Protocol (Zero Merge Conflicts)

| Shared File | Rule |
|---|---|
| `backend/app/main.py` | Only add your track's router import + `app.include_router(..., prefix="/api/v1")` line. |
| `backend/app/models/__init__.py` | Import and re-export every ORM model you add so Alembic & `tests/conftest.py` auto-discover tables. |
| `backend/alembic/versions/` | Follow sequential IDs (`0001`–`0005` per `docs/DECISIONS.md` §9). Always run `alembic heads` (must be 1 head) after rebasing onto `dev`. |
| `frontend/src/pages/CaseDetail.tsx` | Track 4 (M6) defines clean tab slot containers (`Graph`, `Candidates`, `Evidence`, `Action Package`); Track 5 (M7) plugs components into those slots. |

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
   - Run tests + linters (`ruff check .`, `black --check .`, `pytest`, `pnpm lint`, `tsc --noEmit`, `pnpm test --run`).
   - Rebase onto latest `dev` (`git pull --rebase origin dev`), update the task in `docs/SPRINT_PLAN.md` to `[FINISHED: @Name]`, push your branch, and open a Pull Request targeting `dev` for Team Lead (**Lochan**) / backup review.
   - Ping the teammate: _"Finished task X, merged to dev. You're clear to pull."_

---

## Rules of Ownership

1. **Never start a task without marking it `[WORKING: <Name>]`.**
2. **Never push directly to `main`.** Keep `dev` as the shared sync branch.
3. **Pull before starting new work:** `git pull origin dev` to stay up to date.
4. **Cross-module interfaces are agreed in writing:** Refer to `docs/API_CONTRACT.md`. If changes are needed, both devs agree first.

