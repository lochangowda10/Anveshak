# ANVESHAK — Agent Coding Guide

> How to use AI coding agents (Antigravity, Copilot, Cursor, etc.) effectively
> as a team without stepping on each other's work.

---

## Golden Rules for AI-Assisted Development

### 1. One Agent, One Module, One Branch

```
❌  "Hey AI, build the entire backend"
✅  "Build the TRON chain adapter in backend/app/services/chain/tron.py
     following the ChainAdapter protocol in docs/API_CONTRACT.md"
```

- Each agent session works on **one module** in **one feature branch**.
- Always tell the agent which files it owns and which files are read-only context.

### 2. Always Feed Context First

Before any coding task, point the agent to these files **in order**:

1. `CONTEXT.md` — What is ANVESHAK?
2. `docs/API_CONTRACT.md` — The interfaces it must conform to
3. `CONTRIBUTING.md` — Code style, commit conventions
4. `OWNERSHIP.md` — Who owns what (so it doesn't touch other modules)

### 3. Prompt Template for Agents

Use this template for every AI coding task:

```markdown
## Task
<One-line description>

## Module
<Which module from OWNERSHIP.md>

## Files to Create/Modify
- `backend/app/services/chain/tron.py` (create)
- `backend/tests/services/chain/test_tron.py` (create)

## Interface to Implement
<Paste the relevant Protocol/Interface from API_CONTRACT.md>

## Constraints
- Follow CONTRIBUTING.md code style (Black, Ruff, type hints, Google docstrings)
- Use async/await for all I/O
- Do NOT modify any files outside the listed paths
- Write pytest tests with ≥80% coverage
- Use `pydantic-settings` for any config/API keys

## Context Files (Read-Only)
- CONTEXT.md
- docs/API_CONTRACT.md
- CONTRIBUTING.md
```

### 4. Never Let Two Agents Touch the Same File

| Scenario | What Happens | Prevention |
|----------|-------------|------------|
| Two agents edit `models.py` | Merge conflict, lost work | OWNERSHIP.md — one owner per file |
| Agent A creates interface, Agent B uses it | Type mismatch | Define interface in API_CONTRACT.md first |
| Agent generates DB migration | Conflicts with another migration | Only DB owner runs `alembic revision` |

### 5. Review Checklist for AI-Generated Code

Before committing any AI output:

- [ ] **Read every line.** Don't trust blindly.
- [ ] **Run the tests.** AI often writes tests that pass trivially.
- [ ] **Check for hallucinated imports** — packages that don't exist.
- [ ] **Check for hardcoded values** — API keys, addresses, URLs.
- [ ] **Verify async correctness** — missing `await`, blocking calls in async.
- [ ] **Check error handling** — bare `except:`, swallowed exceptions.
- [ ] **Verify the interface match** — does it actually implement the Protocol?
- [ ] **Run linters** — `ruff check .` and `black --check .`

### 6. Agent Session Boundaries

| ✅ Good Agent Tasks | ❌ Bad Agent Tasks |
|---------------------|-------------------|
| Implement one adapter | "Build the whole backend" |
| Write tests for one module | "Write all tests" |
| Add one API endpoint | "Design the database" (needs human design) |
| Refactor one function | "Refactor everything" |
| Generate Alembic migration | "Set up the entire project" |
| Write docstrings | "Review and merge PRs" |

---

## Parallel Agent Workflow (Team of 5)

```
┌─────────────────────────────────────────────────────────────────┐
│                        SHARED (Read-Only for Agents)            │
│  CONTEXT.md · API_CONTRACT.md · DATA_MODEL.md · OWNERSHIP.md    │
└──────────────┬──────────────────────────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼          ▼
  Lochan   Hanamaraddi Harshitha Haripriya Krishnapriya
  intake/   chain/     attrib/    ui-cases/  ui-graph/
  db-cases  graph/     evidence/  app-shell  e2e-qa/
    │          │          │          │          │
    ▼          ▼          ▼          ▼          ▼
  feat/      feat/      feat/      feat/      feat/
  intake     tron-graph attrib-pdf ui-cases   ui-graph-e2e
    │          │          │          │          │
    └──────────┴──────────┴──────────┴──────────┘
                              │
                           dev branch
                              │
                           main (release)
```

### How This Prevents Duplicate Work

1. **Module isolation** — each agent only touches its owned files
2. **Interface contracts** — API_CONTRACT.md defines the handshake points
3. **Branch isolation** — each agent works on a separate feature branch
4. **Review gate** — module owner must approve before merge

---

## Quick Reference: Agent Commands

### Starting a session
```
1. Read CONTEXT.md
2. Read docs/API_CONTRACT.md  
3. Read CONTRIBUTING.md
4. Read OWNERSHIP.md
5. Start coding task (use prompt template above)
```

### After agent finishes
```
1. Review generated code
2. Run: ruff check .
3. Run: black --check .
4. Run: pytest tests/ -v --cov
5. Git add + conventional commit
6. Push feature branch
7. Open PR → tag module owner for review
```
