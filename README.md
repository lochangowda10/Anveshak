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

## 👥 2-Developer Pair Workflow

We are operating an active **2-developer pair model** to ensure zero duplication of work and rapid delivery:

### 1. Domain Split

| Track | Lead | Modules Covered |
|---|---|---|
| **Track A** | **Lochan** | Case Intake, TRON Chain Adapter (TronGrid), DB Schema/Models, NetworkX Graph Engine & Pruning filters |
| **Track B** | **Teammate** | VASP Ranking & Scoring Engine, Attribution Label Store, Evidence & Action Package (PDF), Frontend (React + Cytoscape) |

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

Give this exact prompt to your AI coding agent when starting work:

> Read `README.md`, `CONTEXT.md`, `docs/`, and all existing code. Build only the next milestone from `docs/MILESTONES.md`. Follow `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, and `docs/GRAPH_ENGINE.md` exactly. Do not invent undocumented features, APIs, database fields, or UI behavior. If requirements conflict or are missing, stop and ask. After each milestone, add tests, update documentation, and provide run instructions.

## License

Internal — SIH 2026 Submission
