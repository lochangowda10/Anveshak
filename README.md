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

| Document | Purpose |
|----------|---------|
| [CONTEXT.md](./CONTEXT.md) | Project overview, stack, roadmap |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Git workflow, commit conventions, code standards |
| [OWNERSHIP.md](./OWNERSHIP.md) | Module ownership & team allocation |
| [docs/API_CONTRACT.md](./docs/API_CONTRACT.md) | Interface specifications between modules |
| [docs/ADR.md](./docs/ADR.md) | Architecture Decision Records |
| [docs/SPRINT_PLAN.md](./docs/SPRINT_PLAN.md) | Active sprint plan & live task status tracker |
| [docs/AGENT_GUIDE.md](./docs/AGENT_GUIDE.md) | AI coding agent best practices |
| [docs/SETUP.md](./docs/SETUP.md) | Detailed setup instructions |

## License

Internal — SIH 2026 Submission
