# ANVESHAK — Sprint Plan (MVP)

> Active Sprint: 5-Developer Track Workflow · **Team Lead & Final PR Reviewer: Lochan** · Team: Hanamaraddi, Harshitha, Haripriya, Krishnapriya · ~4 weeks to SIH demo

### Task Status Protocol

When taking on a task:
- Change status from `[TODO]` to `[WORKING: @YourName]` and commit/push to `dev`.
- When done and tested, change status to `[FINISHED: @YourName]`.
- This ensures no two developers ever duplicate effort.

---

## Sprint 0 — Setup (Milestone 0 — Completed)

**Goal:** Everyone can run the project locally.

| Task                                        | Owner          | Status |
|---------------------------------------------|----------------|--------|
| Initialize monorepo structure               | Hanamaraddi    | [FINISHED: OpenCode] |
| Set up `pyproject.toml` + Ruff + Black      | Hanamaraddi    | [FINISHED: OpenCode] |
| Set up React + Vite + TypeScript + ESLint   | Hanamaraddi    | [FINISHED: OpenCode] |
| Create `docker-compose.yml` (Postgres + API)| Hanamaraddi    | [FINISHED: OpenCode] |
| Create `.env.example`                       | Lochan         | [FINISHED: Lochan] |
| Set up CI (GitHub Actions: lint + test)     | Hanamaraddi    | [FINISHED: OpenCode] |
| Everyone clones, runs `docker compose up`   | All (5)        | [FINISHED: OpenCode] |
| Create initial Alembic migration (empty)    | Hanamaraddi    | [FINISHED: OpenCode] |

**Exit Criteria:** `docker compose up` starts Postgres + FastAPI + React on
every team member's machine.

---

## Sprint 1 — Core Pipeline (Milestones 1, 2, 6)

**Goal:** Case intake + TRON transaction fetching + raw graph + Case Management UI.

| Task                                            | Owner          | Depends On     | Status |
|-------------------------------------------------|----------------|----------------|--------|
| Case/Tag/SeedWallet SQLAlchemy models (M1)      | Lochan         | —              | [TODO] |
| Alembic migration `0001_cases_and_wallets` (M1) | Lochan         | Case models    | [TODO] |
| `POST /api/v1/cases` endpoint + validation (M1) | Lochan         | Migration 0001 | [TODO] |
| `GET /api/v1/cases` + `GET /cases/{id}` (M1)    | Lochan         | Migration 0001 | [TODO] |
| Unit/API tests for Cases endpoints (M1)         | Lochan         | Cases routes   | [TODO] |
| `ChainAdapter` protocol + `Transaction` model (M2)| Hanamaraddi  | —              | [TODO] |
| TRON adapter: fetch TRC-20 & TRX transfers (M2) | Hanamaraddi    | ChainAdapter   | [TODO] |
| Transaction DB cache (24h TTL) (M2)             | Hanamaraddi    | Tx model       | [TODO] |
| Unit tests: TRON adapter (mocked httpx) (M2)    | Hanamaraddi    | TRON adapter   | [TODO] |
| Frontend: App Shell, Dashboard, Case List (M6)  | Haripriya      | —              | [TODO] |
| Frontend: Create Case form + Case Detail shell (M6)| Haripriya   | —              | [TODO] |

**Exit Criteria:** Create a case in UI → persisted in Postgres → TRON adapter fetches mocked/live transfers.

---

## Sprint 2 — Intelligence Layer (Milestones 3, 4, 7)

**Goal:** Pruned BFS graph + VASP attribution & ranking + Cytoscape graph UI.

| Task                                            | Owner          | Depends On       | Status |
|-------------------------------------------------|----------------|------------------|--------|
| `TraceNode` & `TraceEdge` models + migration (M3)| Hanamaraddi   | M2               | [TODO] |
| GraphEngine: BFS + 6 pruning filters + cycles (M3)| Hanamaraddi  | M2               | [TODO] |
| Cytoscape JSON serializer + `/trace` & `/graph` (M3)| Hanamaraddi| GraphEngine      | [TODO] |
| Unit tests: BFS, all 6 pruning filters, cycles (M3)| Hanamaraddi | GraphEngine      | [TODO] |
| `VASPLabel` & `VASPCandidate` models + migrations (M4)| Harshitha| —                | [TODO] |
| Seed labels script (`app/scripts/seed_labels.py`) (M4)| Harshitha| Label model      | [TODO] |
| Label matcher + 3 heuristic detectors (M4)      | Harshitha      | Seed labels      | [TODO] |
| 6-signal scoring & ranking engine (M4)          | Harshitha      | Label matcher    | [TODO] |
| `/candidates`, `/review`, `/labels` endpoints (M4)| Harshitha    | Ranking engine   | [TODO] |
| Unit tests: matching, scoring, conflict res (M4)| Harshitha      | Ranking engine   | [TODO] |
| Frontend: `CytoscapeGraph.tsx` + 3s polling (M7)| Krishnapriya   | M6               | [TODO] |

**Exit Criteria:** Submit wallet → pruned graph rendered in Cytoscape + ranked VASP candidates.

---

## Sprint 3 — Evidence, Action Package & QA (Milestones 5, 7, 8)

**Goal:** Action package PDF/JSON + Evidence UI + E2E acceptance suite.

| Task                                            | Owner          | Depends On       | Status |
|-------------------------------------------------|----------------|------------------|--------|
| `ActionPackage` model + migration (M5)          | Harshitha      | M4               | [TODO] |
| Evidence assembler + deterministic action rules (M5)| Harshitha  | M4               | [TODO] |
| ReportLab PDF generator (`ACTION_PACKAGE_SPEC`) (M5)| Harshitha  | Assembler        | [TODO] |
| `/evidence`, `/action-package`, `/export` routes (M5)| Harshitha | PDF generator    | [TODO] |
| Unit tests: evidence, actions, PDF bytes (M5)   | Harshitha      | M5 routes        | [TODO] |
| Frontend: `CandidatePanel`, `EvidenceView`, `ActionPackageView` (M7)| Krishnapriya| M6 | [TODO] |
| E2E integration tests: Scenarios A, B, C (M8)   | Krishnapriya   | M1–M5            | [TODO] |
| Demo seed script (`app/scripts/seed_demo.py`) (M8)| Krishnapriya | M1–M5            | [TODO] |
| Full CI & Docker Compose verification (M8)      | All (5)        | All above        | [TODO] |

**Exit Criteria:** Live demo: enter complaint → automated trace → pruned graph → ranked VASP → download action package PDF.

---

## Sprint 4 — Demo Week (Days 24–28)

| Task                                   | Owner   | Status |
|----------------------------------------|---------|--------|
| Rehearse demo flow (3× minimum)        | All (5) | [TODO] |
| Fix demo-blocking bugs only            | All (5) | [TODO] |
| Prepare seed data for live demo        | All (5) | [TODO] |
| Record backup video demo               | All (5) | [TODO] |
| Prepare Q&A answers (risks, roadmap)   | All (5) | [TODO] |

---

## Daily Standup Template

Each team member answers (async or in-person):

1. **Yesterday:** What did I finish?
2. **Today:** What am I working on?
3. **Blocked:** Am I stuck on anything?
4. **Cross-module:** Do I need anything from another module?
