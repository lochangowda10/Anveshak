# Contributing to ANVESHAK

> Industry-standard practices for the team. Read this before writing any code.

---

## 1. Git Workflow — Trunk-Based with Feature Branches

```
main (protected — release baseline)
  └── dev (integration branch — team syncs here)
       ├── feat/case-intake-api
       ├── feat/tron-adapter
       ├── feat/graph-engine
       ├── fix/pruning-threshold
       └── docs/api-reference
```

### The 5-Developer Sync Protocol

To avoid overlapping work across the five active developers (**Lochan [Team Lead]**, **Hanamaraddi**, **Harshitha**, **Haripriya**, **Krishnapriya**):
1. **Always sync before starting:** `git checkout dev && git pull origin dev`.
2. **Claim task:** Mark task as `[WORKING: <Name>]` in `docs/SPRINT_PLAN.md`, commit, and push to `dev` (the only exception allowed for direct pushes to `dev` — no application code).
3. **Branch:** Create `feat/<task-name>` off `dev`.
4. **Open PR to `dev`:** Rebase on latest `dev`, ensure CI passes locally (`ruff`, `black`, `pytest`, `pnpm lint`, `tsc --noEmit`, `pnpm test --run`), update `docs/SPRINT_PLAN.md` to `[FINISHED: <Name>]` on your branch, push your feature branch, and open a Pull Request into `dev` using `.github/pull_request_template.md`.
5. **Review & Merge Gate:** Module backup or **Lochan (Team Lead)** reviews and merges into `dev`. Only **Lochan** merges verified milestones from `dev` into `main`.

### Branch Naming Convention

| Prefix     | Use Case                        | Example                        |
|------------|----------------------------------|-------------------------------|
| `feat/`    | New feature                      | `feat/vasp-ranking-engine`    |
| `fix/`     | Bug fix                          | `fix/hop-limit-off-by-one`    |
| `refactor/`| Code restructure, no behavior Δ  | `refactor/adapter-interface`  |
| `docs/`    | Documentation only               | `docs/api-endpoints`          |
| `test/`    | Test additions / changes         | `test/graph-pruning-unit`     |
| `chore/`   | Tooling, CI, deps                | `chore/docker-compose`        |

### Rules

1. **Never push application code directly to `main` or `dev`.** Only lightweight `[WORKING]` claim updates to `docs/SPRINT_PLAN.md` may push directly to `dev`; all code changes enter `dev` via Pull Request, and only Team Lead (Lochan) merges `dev → main`.
2. **One feature per branch.** Keep PRs focused on one milestone/task.
3. **Rebase on `dev` before opening a PR.** Resolve conflicts and keep Alembic migrations strictly linear (`alembic heads` MUST show 1 head).
4. **Delete feature branch after merge.**
5. **Use conventional commits** (see below).

---

## 2. Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Types

| Type       | When                                              |
|------------|---------------------------------------------------|
| `feat`     | A new feature                                     |
| `fix`      | A bug fix                                         |
| `docs`     | Documentation only changes                        |
| `style`    | Formatting, semicolons, etc. (no logic change)    |
| `refactor` | Code change that neither fixes a bug nor adds feat|
| `test`     | Adding or updating tests                          |
| `chore`    | Build process, CI, dependencies                   |
| `perf`     | Performance improvement                           |

### Scopes (map to modules)

`intake` · `tron` · `graph` · `ranking` · `attribution` · `evidence` · `ui` ·
`db` · `api` · `docker` · `ci`

### Examples

```
feat(tron): add TRC-20 transfer parsing for USDT
fix(graph): prevent infinite loop on cyclic fund flows
docs(api): add OpenAPI schema for case-intake endpoint
test(ranking): add unit tests for hop-depth scoring
chore(docker): add multi-stage build for backend
```

---

## 3. Code Style & Standards

### Python (Backend)

| Rule                       | Standard                                      |
|----------------------------|-----------------------------------------------|
| Formatter                  | **Black** (line-length 88)                    |
| Linter                     | **Ruff** (replaces flake8 + isort + pyflakes) |
| Type Hints                 | **Required** on all public functions           |
| Docstrings                 | **Google style** on all public functions       |
| Import Order               | stdlib → third-party → local (Ruff enforced)  |
| Test Framework             | **pytest**                                     |
| Minimum Test Coverage      | **80%** per module                             |

### TypeScript / React (Frontend)

| Rule                       | Standard                                      |
|----------------------------|-----------------------------------------------|
| Formatter                  | **Prettier**                                  |
| Linter                     | **ESLint** (strict + React hooks rules)       |
| Type Safety                | **TypeScript strict mode** — no `any`         |
| Component Pattern          | Functional components + hooks only            |
| State Management           | **Zustand** or React Context (decided per PR) |
| Test Framework             | **Vitest** + React Testing Library             |

### SQL / Database

| Rule                       | Standard                                      |
|----------------------------|-----------------------------------------------|
| Migrations                 | **Alembic** — never raw DDL in production     |
| Naming                     | `snake_case` for tables and columns           |
| Soft Deletes               | Use `deleted_at` timestamp, never hard delete |
| Indexing                   | Every foreign key must be indexed              |

---

## 4. Code Review Checklist

Every PR reviewer must verify:

- [ ] Follows branch naming and commit conventions
- [ ] No secrets, keys, or credentials in code
- [ ] Type hints on all new public functions (Python)
- [ ] Tests added for new logic (≥ 80% coverage)
- [ ] No `TODO` without a linked issue number
- [ ] API changes have updated OpenAPI docs
- [ ] DB changes have an Alembic migration
- [ ] No hardcoded blockchain addresses or API URLs
- [ ] Error handling — no bare `except:` blocks
- [ ] Logging — structured logs, no `print()` in production code

---

## 5. Environment & Secrets

- **Never commit `.env` files.** Use `.env.example` as a template.
- All secrets go into environment variables.
- API keys (TronGrid, etc.) must be loaded via `pydantic-settings`.
- For local dev, copy `.env.example` → `.env` and fill in your keys.

---

## 6. Definition of Done

A feature is "done" when:

1. ✅ Code is merged into `dev`
2. ✅ All CI checks pass (lint, type-check, tests)
3. ✅ Code reviewed and approved by ≥ 1 teammate
4. ✅ API docs updated (if applicable)
5. ✅ Database migrations included (if applicable)
6. ✅ Manual smoke test on local Docker environment
7. ✅ No regressions in existing tests

---

## 7. AI-Assisted Development Rules

When using AI coding agents (Antigravity, Copilot, etc.):

1. **Always provide CONTEXT.md** — point the agent to this file first.
2. **Scope the task** — one module at a time, never "build everything."
3. **Review AI output** — treat it as a junior dev's PR; review carefully.
4. **Don't commit AI-generated code without tests.**
5. **Follow the same PR process** — AI code goes through the same review.
6. **Reference the module owner** — check OWNERSHIP.md before assigning.
