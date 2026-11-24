# ANVESHAK — Ordered Build Milestones

> **Machine-Executable Build Roadmap (Milestones 0 → 8)**
> Each milestone produces a working, testable increment. Follow the Agent Build Protocol below strictly.

---

## Agent Build Protocol

Read these docs before building each milestone:
1. `CONTEXT.md` — project overview & tech stack
2. `docs/PRODUCT_SPEC.md` — functional requirements & validation rules
3. `docs/DATA_MODEL.md` — PostgreSQL schema & indexes
4. `docs/API_CONTRACT.md` — endpoint specs & Python protocols
5. `docs/GRAPH_ENGINE.md` — BFS traversal & 6 pruning filters
6. `docs/VASP_ATTRIBUTION.md` — scoring formula & label matching
7. `docs/UI_SPEC.md` — frontend screens & Cytoscape styling
8. `docs/ACTION_PACKAGE_SPEC.md` — evidence & PDF report spec
9. `docs/ACCEPTANCE_TESTS.md` — synthetic scenarios & pass criteria

**Execution Rules:**
- Build **ONE milestone at a time**.
- Do NOT invent undocumented endpoints, database columns, or UI screens.
- After each milestone: run all tests, run linters, verify the milestone's exit criteria, commit using Conventional Commits, and update `docs/SPRINT_PLAN.md`.
- Do NOT proceed to the next milestone until verification passes.

---

## Milestone 0: Project Scaffold & Infrastructure
**Goal:** Runnable monorepo skeleton with Postgres, FastAPI healthcheck, Vite React shell, and CI.
**Tasks:**
1. Create `backend/` with `pyproject.toml` (`fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic`, `pydantic-settings`, `networkx`, `httpx`, `reportlab`, `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `black`).
2. Create `backend/app/core/config.py` (`pydantic-settings` `Settings` reading `.env`) and `backend/app/core/database.py` (async engine + `async_sessionmaker`).
3. Create `backend/app/main.py` with CORS middleware and `GET /api/v1/health`.
4. Configure `backend/alembic.ini` and `backend/alembic/env.py` for async SQLAlchemy.
5. Create `backend/tests/conftest.py` with async test client + test DB fixtures.
6. Create `frontend/` with Vite + React 18 + TypeScript (strict) + TailwindCSS + `react-router-dom` + `cytoscape` + `cytoscape-dagre` + `vitest`.
7. Create `frontend/src/services/api.ts` base fetch wrapper.
8. Create `docker-compose.yml` (`postgres:16`, `backend`, `frontend`) and `.github/workflows/ci.yml`.
**Verification:** `docker compose up` starts all 3 services; `GET /api/v1/health` returns `200 {"status": "ok", ...}`; `http://localhost:5173` renders without console errors.

---

## Milestone 1: Database Schema & Case Intake API
**Goal:** Persist cases, tags, and seed wallets to PostgreSQL via validated REST endpoints.
**Tasks:**
1. Implement SQLAlchemy models in `backend/app/models/case.py` (`Case`, `CaseTag`, `SeedWallet`) matching `docs/DATA_MODEL.md`.
2. Generate and run Alembic migration `0001_cases_and_wallets.py`.
3. Implement Pydantic schemas in `backend/app/api/schemas/case.py` (including TRON Base58 regex validation).
4. Implement `backend/app/api/routes/cases.py`: `POST /api/v1/cases`, `GET /api/v1/cases` (paginated, filtered, sorted), `GET /api/v1/cases/{case_id}`.
5. Register router in `app/main.py`.
6. Write unit/API tests (`API-01` through `API-05` in `docs/ACCEPTANCE_TESTS.md`).
**Verification:** `pytest` passes; `POST /api/v1/cases` persists to Postgres; invalid TRON address returns `422`.

---

## Milestone 2: TRON Chain Adapter & Transaction Cache
**Goal:** Fetch and normalize TRON TRC-20/TRX transactions from TronGrid with PostgreSQL caching.
**Tasks:**
1. Create `backend/app/services/chain/base.py` implementing `ChainAdapter` Protocol & `TransactionData` dataclass.
2. Create `backend/app/models/transaction.py` (`Transaction` model) + Alembic migration.
3. Create `backend/app/services/chain/cache.py` (24-hour TTL DB cache check & upsert).
4. Create `backend/app/services/chain/tron.py` (`TronAdapter` calling TronGrid `/v1/accounts/{address}/transactions/trc20` & `/transactions`, pagination up to 200/page, 300ms rate limiter, exponential backoff on 429).
5. Write mocked `httpx` tests verifying normalization, pagination, rate-limit retry, and cache hit behavior.
**Verification:** `pytest` passes all mocked TronGrid tests; cache prevents duplicate external requests within 24h.

---

## Milestone 3: Graph Engine (BFS + 6 Pruning Filters)
**Goal:** Execute pruned multi-hop BFS trace as a background task and serve Cytoscape JSON.
**Tasks:**
1. Create `backend/app/models/trace.py` (`TraceNode`, `TraceEdge`) + Alembic migration.
2. Implement `backend/app/services/graph/engine.py` (`GraphEngine`) following `docs/GRAPH_ENGINE.md` (BFS, 6 pruning filters in exact order, path-local cycle detection, error threshold abort).
3. Implement `backend/app/services/graph/serializer.py` (NetworkX / DB records → Cytoscape JSON).
4. Create `backend/app/api/routes/trace.py`: `POST /api/v1/cases/{id}/trace` (`BackgroundTasks`, `202` / `409`) and `GET /api/v1/cases/{id}/graph`.
5. Write unit tests for BFS, all 6 pruning filters, and cycle detection (`docs/ACCEPTANCE_TESTS.md` Section 3).
**Verification:** Triggering trace transitions `PENDING → TRACING → TRACED`; `GET /graph` returns valid Cytoscape JSON.

---

## Milestone 4: VASP Attribution & Ranking Engine
**Goal:** Match traced addresses against VASP labels and heuristics, score, and rank candidates.
**Tasks:**
1. Create `backend/app/models/label.py` (`VASPLabel`) and `backend/app/models/candidate.py` (`VASPCandidate`) + Alembic migrations.
2. Create `backend/app/scripts/seed_labels.py` loading all 20+ known exchange labels from `docs/DATA_MODEL.md` / `docs/VASP_ATTRIBUTION.md`.
3. Implement `backend/app/services/attribution/matcher.py` (exact match, conflict resolution, 3 heuristic detectors).
4. Implement `backend/app/services/ranking/scorer.py` (6-signal weighted formula, tie-breaking, `0.20` min threshold).
5. Create `backend/app/api/routes/candidates.py` (`GET /candidates`, `POST /candidates/{cid}/review`) and `backend/app/api/routes/labels.py` (`GET /labels/search`, `POST /labels`).
6. Wire attribution + ranking into the end of the trace background pipeline (transitioning status to `ANALYZED`).
7. Write unit tests (`docs/ACCEPTANCE_TESTS.md` Section 4).
**Verification:** Seed script populates labels; Scenario A & B traces produce expected ranked VASP candidates.

---

## Milestone 5: Evidence Assembly & Action Package (JSON + PDF)
**Goal:** Assemble provenance-tagged evidence paths and export ReportLab PDF action packages.
**Tasks:**
1. Create `backend/app/models/action_package.py` (`ActionPackage`) + Alembic migration.
2. Implement `backend/app/services/evidence/assembler.py` (path reconstruction, flow retention %).
3. Implement `backend/app/services/evidence/action_generator.py` (deterministic CrPC 91 / 102 / IEA 65B recommendations).
4. Implement `backend/app/services/evidence/pdf_generator.py` (ReportLab A4 multi-page PDF matching `docs/ACTION_PACKAGE_SPEC.md`).
5. Create `backend/app/api/routes/evidence.py`: `GET /evidence`, `GET /action-package`, `GET /action-package/export`.
6. Write unit/API tests verifying JSON structure and `%PDF-` binary download.
**Verification:** `GET /evidence` returns full paths; `GET /action-package/export` downloads a valid multi-page PDF.

---

## Milestone 6: Frontend — Case Management UI
**Goal:** Complete Dashboard, Case List, Create Case form, and Case Detail Overview tab.
**Tasks:**
1. Implement App Shell (dark sidebar + main content + toast notifications + `<StatusBadge />`) per `docs/UI_SPEC.md`.
2. Implement `Dashboard.tsx` (KPI cards, status distribution, recent 10 cases).
3. Implement `CaseList.tsx` (search, status/date filters, sorting, 20/page pagination).
4. Implement `CreateCase.tsx` (inline TRON address validation, dynamic seed wallet rows, tags).
5. Implement `CaseDetail.tsx` shell with 5 tabs and Overview tab.
**Verification:** User can create a case in browser, see it in Case List, filter/paginate, and open Case Detail.

---

## Milestone 7: Frontend — Cytoscape Graph, Candidates & Evidence UI
**Goal:** Interactive fund-flow graph, trace polling, candidate review, and PDF export in browser.
**Tasks:**
1. Implement `src/graph/CytoscapeGraph.tsx` (`dagre` layout, node/edge styling per `UI_SPEC.md`, click-to-inspect side drawer, PNG export, layout switcher).
2. Implement 3-second polling loop while `status === "TRACING"`.
3. Implement `CandidatePanel` (ranked list, expandable 6-signal breakdown, Accept/Reject buttons).
4. Implement `EvidenceView` (hop-by-hop timeline with TronScan links) and `ActionPackageView` (preview + PDF/JSON download buttons).
**Verification:** Full UI flow works from `Start Trace` → live graph → inspect node → download PDF.

---

## Milestone 8: E2E Acceptance Testing & Demo Readiness
**Goal:** All acceptance tests pass; demo scenarios seeded and verified.
**Tasks:**
1. Implement E2E tests for Scenario A, B, and C (`docs/ACCEPTANCE_TESTS.md`).
2. Verify all empty states, error states, and loading skeletons in UI.
3. Create `scripts/seed_demo.py` with realistic demo cases ready for SIH presentation.
4. Run full CI check (`ruff`, `black`, `pytest --cov`, `tsc`, `vitest`).
**Verification:** 100% of acceptance tests pass with `>= 80%` backend coverage; clean `docker compose up` demo works end-to-end.
