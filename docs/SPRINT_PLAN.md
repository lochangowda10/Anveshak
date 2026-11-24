# ANVESHAK — Sprint Plan (MVP)

> Active Sprint: 2-Developer Pair Workflow · ~4 weeks to SIH demo · 2-week sprints

### Task Status Protocol

When taking on a task:
- Change status from `[TODO]` to `[WORKING: @YourName]` and commit/push to `dev`.
- When done and tested, change status to `[FINISHED: @YourName]`.
- This ensures neither developer ever duplicates effort.

---

## Sprint 0 — Setup (Days 1–2)

**Goal:** Everyone can run the project locally.

| Task                                        | Owner          | Status |
|---------------------------------------------|----------------|--------|
| Initialize monorepo structure               | Lochan         | [TODO] |
| Set up `pyproject.toml` + Ruff + Black      | Lochan         | [TODO] |
| Set up React + Vite + TypeScript + ESLint   | Dev 2          | [TODO] |
| Create `docker-compose.yml` (Postgres + API)| Lochan         | [TODO] |
| Create `.env.example`                       | Lochan         | [FINISHED: Lochan] |
| Set up CI (GitHub Actions: lint + test)     | Dev 2          | [TODO] |
| Everyone clones, runs `docker compose up`   | Both           | [TODO] |
| Create initial Alembic migration (empty)    | Lochan         | [TODO] |

**Exit Criteria:** `docker compose up` starts Postgres + FastAPI + React on
every team member's machine.

---

## Sprint 1 — Core Pipeline (Days 3–9)

**Goal:** Seed wallet → transaction fetching → graph building (no pruning yet).

| Task                                            | Owner          | Depends On     | Status |
|-------------------------------------------------|----------------|----------------|--------|
| Design DB schema (cases, transactions, labels)  | DB Owner       | —              | ☐      |
| Alembic migration for schema                    | DB Owner       | Schema design  | ☐      |
| `POST /api/v1/cases` endpoint                   | Intake Owner   | DB schema      | ☐      |
| `GET /api/v1/cases` + `GET /cases/{id}`         | Intake Owner   | DB schema      | ☐      |
| TRON adapter: fetch TRC-20 transfers            | Chain Owner    | —              | ☐      |
| TRON adapter: fetch normal TRX transfers        | Chain Owner    | —              | ☐      |
| Transaction normalizer (→ canonical schema)     | Chain Owner    | DB schema      | ☐      |
| Graph builder: BFS from seed wallet (no prune)  | Graph Owner    | Chain adapter  | ☐      |
| Graph serializer: NetworkX → Cytoscape JSON     | Graph Owner    | Graph builder  | ☐      |
| Frontend: Case list page                        | Frontend Owner | Cases API      | ☐      |
| Frontend: Case detail page (empty graph area)   | Frontend Owner | Cases API      | ☐      |
| Unit tests: chain adapter (mocked API)          | Chain Owner    | Chain adapter  | ☐      |
| Unit tests: graph builder                       | Graph Owner    | Graph builder  | ☐      |

**Exit Criteria:** Submit a wallet → see raw (unpruned) graph in the UI.

---

## Sprint 2 — Intelligence Layer (Days 10–16)

**Goal:** Pruning + VASP ranking + evidence display.

| Task                                            | Owner            | Depends On       | Status |
|-------------------------------------------------|------------------|------------------|--------|
| Pruning filters: hop limit, amount threshold    | Graph Owner      | Graph builder    | ☐      |
| Pruning filters: time window, degree cap        | Graph Owner      | Graph builder    | ☐      |
| Pruning filters: path continuity, dedup         | Graph Owner      | Graph builder    | ☐      |
| VASP label store (seed data: known exchanges)   | Attribution Owner| DB schema        | ☐      |
| Label matching: address → known VASP lookup     | Attribution Owner| Label store      | ☐      |
| Ranking signals: implement scoring formula      | Ranking Owner    | Graph + labels   | ☐      |
| `GET /cases/{id}/candidates` endpoint           | Ranking Owner    | Scoring          | ☐      |
| Frontend: Cytoscape graph — interactive view    | Frontend Owner   | Graph serializer | ☐      |
| Frontend: Candidate VASP panel (ranked list)    | Frontend Owner   | Candidates API   | ☐      |
| Frontend: Click node → show address details     | Frontend Owner   | Graph view       | ☐      |
| Integration test: full pipeline seed → rank     | All              | All above        | ☐      |

**Exit Criteria:** Submit wallet → see pruned graph + ranked VASP candidates.

---

## Sprint 3 — Evidence & Polish (Days 17–23)

**Goal:** Action package generation + demo readiness.

| Task                                            | Owner            | Depends On       | Status |
|-------------------------------------------------|------------------|------------------|--------|
| Evidence assembler: collect paths per candidate | Evidence Owner   | Ranking          | ☐      |
| Action package generator (JSON output)          | Evidence Owner   | Evidence         | ☐      |
| PDF export of action package                    | Evidence Owner   | Action package   | ☐      |
| `GET /cases/{id}/evidence` endpoint             | Evidence Owner   | Evidence logic   | ☐      |
| `GET /cases/{id}/action-package/export`         | Evidence Owner   | PDF generator    | ☐      |
| Frontend: Evidence view (paths, provenance)     | Frontend Owner   | Evidence API     | ☐      |
| Frontend: Action package download button        | Frontend Owner   | Export API       | ☐      |
| Frontend: Dashboard / stats page                | Frontend Owner   | Cases API        | ☐      |
| End-to-end test: complaint → action package     | All              | All above        | ☐      |
| Load test with real TRON data (10 cases)        | Chain Owner      | Full pipeline    | ☐      |
| Security review: no exposed secrets, CORS, etc. | Infra Owner      | All              | ☐      |
| README.md + demo script                         | All              | All              | ☐      |

**Exit Criteria:** Live demo: enter complaint → automated trace → pruned graph →
ranked VASP → download action package PDF.

---

## Sprint 4 — Demo Week (Days 24–28)

| Task                                   | Owner | Status |
|----------------------------------------|-------|--------|
| Rehearse demo flow (3× minimum)        | All   | ☐      |
| Fix demo-blocking bugs only            | All   | ☐      |
| Prepare seed data for live demo        | All   | ☐      |
| Record backup video demo               | All   | ☐      |
| Prepare Q&A answers (risks, roadmap)   | All   | ☐      |

---

## Daily Standup Template

Each team member answers (async or in-person):

1. **Yesterday:** What did I finish?
2. **Today:** What am I working on?
3. **Blocked:** Am I stuck on anything?
4. **Cross-module:** Do I need anything from another module?
