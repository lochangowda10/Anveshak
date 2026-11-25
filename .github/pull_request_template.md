## Summary

<!-- Briefly describe what this PR implements and link the milestone/task in docs/SPRINT_PLAN.md -->

- **Track:** Track 1 (M1) / Track 2 (M2–M3) / Track 3 (M4–M5) / Track 4 (M6) / Track 5 (M7–M8)
- **Milestone / Task:**
- **Developer:**

---

## Specification Alignment

- [ ] Matches `docs/DECISIONS.md` and `OWNERSHIP.md` boundaries (did NOT modify files outside my track except registered shared lines)
- [ ] Matches `docs/API_CONTRACT.md`, `docs/DATA_MODEL.md`, and module specs with zero undocumented fields/endpoints
- [ ] `docs/SPRINT_PLAN.md` updated to `[FINISHED: <YourName>]`

---

## Database & Migration Checklist (if applicable)

- [ ] Sequential revision ID (`0001`–`0005`) matches `docs/DECISIONS.md` §9
- [ ] Rebased on latest `dev`; `alembic heads` returns strictly **1** head
- [ ] ORM models re-exported from `backend/app/models/__init__.py`

---

## Verification & Code Quality Checklist (`CONTRIBUTING.md`)

- [ ] Conventional commit messages used (`feat(scope): ...`, `fix(scope): ...`)
- [ ] No secrets, `.env`, or unapproved hardcoded addresses/URLs
- [ ] Type hints & docstrings added on public functions; no bare `except:` or `print()`
- [ ] Backend checks passed locally (if touched): `ruff check .`, `black --check .`, `pytest tests/ -v --cov=app --cov-fail-under=80`
- [ ] Frontend checks passed locally (if touched): `pnpm lint`, `npx tsc --noEmit`, `pnpm format:check`, `pnpm test --run`, `pnpm build`
