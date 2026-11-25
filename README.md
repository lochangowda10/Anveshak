# ANVESHAK — Complaint-to-Action Crypto Investigation Workflow

> Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges from
> Victim-Reported Suspect Wallet Addresses through Automated Blockchain Analytics

**SIH 2026 · PS ID: SIH26183 · Team PHANTOMS**

---

## Quick Start

```bash
# 1. Clone
git clone <repo-url> anveshak && cd anveshak

# 2. Configure
cp .env.example .env   # Fill in your API keys

# 3. Run
docker compose up --build

# 4. Open
# Backend API docs: http://localhost:8000/docs
# Frontend:         http://localhost:5173
```

## 👥 5-Developer Team Workflow

We are operating an active **5-developer track model** to ensure zero duplication of work and rapid parallel delivery:

### 1. Domain Split

| Track | Lead | Modules Covered | Milestones |
|---|---|---|---|
| **Track 1** | **Lochan** | Case Intake API, DB Schema & Migrations | M1 |
| **Track 2** | **Hanamaraddi** | Project Scaffold, TRON Adapter (TronGrid + Cache), NetworkX Graph Engine & Pruning | M0, M2, M3 |
| **Track 3** | **Harshitha** | VASP Attribution & Label Store, 6-Signal Ranking Engine, Evidence & Action Package (JSON + PDF) | M4, M5 |
| **Track 4** | **Haripriya** | Frontend App Shell, Dashboard, Case List, Create Case, Case Detail Overview | M6 |
| **Track 5** | **Krishnapriya** | Frontend Cytoscape.js Graph, Candidate/Evidence/Action Views, E2E Acceptance Tests & Demo Seed | M7, M8 |

### 2. The Live "Claim ➔ Working ➔ Finished" Flow

Whenever either developer starts or completes a task:

1. **Pull latest `dev`:**
   ```bash
   git checkout dev && git pull origin dev
   ```
2. **Claim task in [docs/SPRINT_PLAN.md](./docs/SPRINT_PLAN.md):**
   Change the task's status from `[TODO]` to `[WORKING: Lochan]` (or `[WORKING: Teammate]`), commit, and push to `dev`. Now the other person immediately sees you own that task.
   ```bash
   git commit -am "chore(sprint): claim task <task-name>"
   git push origin dev
   ```
3. **Work on your feature branch:**
   ```bash
   git checkout -b feat/<task-name>
   ```
4. **Finish, test, and merge:**
   - Run tests & linters (`pytest`, `ruff`, `pnpm test`).
   - Merge `feat/<task-name>` into `dev` (or open PR).
   - In [docs/SPRINT_PLAN.md](./docs/SPRINT_PLAN.md), mark it `[FINISHED: Lochan]`.
   - Push to `dev`:
   ```bash
   git commit -am "chore(sprint): finish task <task-name>"
   git push origin dev
   ```

---

## Documentation

### Governance & Workflow
| Document | Purpose |
|----------|---------|
| [CONTEXT.md](./CONTEXT.md) | Project overview, stack, roadmap |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Git workflow, commit conventions, code standards |
| [OWNERSHIP.md](./OWNERSHIP.md) | Module ownership & 2-dev collaboration rules |
| [docs/ADR.md](./docs/ADR.md) | Architecture Decision Records |
| [docs/SPRINT_PLAN.md](./docs/SPRINT_PLAN.md) | Active sprint plan & live task status tracker |
| [docs/AGENT_GUIDE.md](./docs/AGENT_GUIDE.md) | AI coding agent best practices |
| [docs/SETUP.md](./docs/SETUP.md) | Detailed setup instructions |

### Machine-Executable Specifications
| Document | Purpose |
|----------|---------|
| [docs/PRODUCT_SPEC.md](./docs/PRODUCT_SPEC.md) | Exact features, user roles, workflows, validation rules, edge cases |
| [docs/DATA_MODEL.md](./docs/DATA_MODEL.md) | PostgreSQL schema (9 tables), indexes, triggers, ER diagram, seed SQL |
| [docs/API_CONTRACT.md](./docs/API_CONTRACT.md) | Every REST endpoint, payloads, error codes, Python Protocols |
| [docs/GRAPH_ENGINE.md](./docs/GRAPH_ENGINE.md) | BFS traversal, 6 pruning filters, cycle detection, caching, pseudocode |
| [docs/VASP_ATTRIBUTION.md](./docs/VASP_ATTRIBUTION.md) | Label sources, matching rules, scoring formula, conflict resolution |
| [docs/UI_SPEC.md](./docs/UI_SPEC.md) | All 6 screens, components, Cytoscape styling, polling, states |
| [docs/ACTION_PACKAGE_SPEC.md](./docs/ACTION_PACKAGE_SPEC.md) | JSON & ReportLab PDF structure, Indian legal mappings, action rules |
| [docs/ACCEPTANCE_TESTS.md](./docs/ACCEPTANCE_TESTS.md) | Synthetic test scenarios (A/B/C), API/unit/E2E tests, pass criteria |
| [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) | Docker Compose, Postgres provisioning, secrets, GitHub Actions CI/CD |
| [docs/DECISIONS.md](./docs/DECISIONS.md) | Canonical tie-breaker decisions resolving all cross-doc edge cases |
| [docs/MILESTONES.md](./docs/MILESTONES.md) | Ordered build plan (Milestones 0 → 8) with verification gates |

## 🤖 Prompt for AI Coding Agents

Replace `<YourName>` (`Hanamaraddi`, `Harshitha`, `Haripriya`, or `Krishnapriya`) and paste this exact prompt into your AI coding agent:

```text
First run `git checkout dev && git pull origin dev` to get the latest code and specifications.

Read `README.md`, `CONTEXT.md`, `OWNERSHIP.md`, `CONTRIBUTING.md`, `docs/DECISIONS.md`, and all files in `docs/`.

You are working for `<YourName>`. Check your assigned Track in `OWNERSHIP.md` and your tasks in `docs/SPRINT_PLAN.md` and `docs/MILESTONES.md`.

Rules:
1. Do NOT touch files outside your assigned Track in `OWNERSHIP.md`.
2. Before writing any code, mark your current task `[WORKING: <YourName>]` in `docs/SPRINT_PLAN.md`, commit, and push to `dev`.
3. Create a feature branch (`feat/<task-name>`) off `dev` and build ONLY one milestone/task at a time.
4. Follow `docs/DECISIONS.md`, `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, `docs/GRAPH_ENGINE.md`, `docs/VASP_ATTRIBUTION.md`, `docs/UI_SPEC.md`, `docs/ACTION_PACKAGE_SPEC.md`, and `docs/DEPLOYMENT.md` exactly. Do not invent undocumented APIs, DB columns, or UI behavior.
5. Write tests matching `docs/ACCEPTANCE_TESTS.md`, run all linters and tests (`ruff check .`, `black --check .`, `pytest`, or `tsc --noEmit` / `pnpm test`), mark your task `[FINISHED: <YourName>]` in `docs/SPRINT_PLAN.md`, push your branch, and open a PR for Team Lead (Lochan) review before merging to `main`.

If any requirement conflicts or is missing, stop and ask before guessing.
```

> **Release Gate:** **Lochan (Team Lead)** reviews all PRs and merges verified milestones into `main`.

## License

Internal — SIH 2026 Submission
