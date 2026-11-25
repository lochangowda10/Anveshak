# ANVESHAK — Canonical Specification Decisions

> **Tie-Breaker & Ambiguity Resolution Document (MVP v1.0.0)**
> Resolves all cross-document edge cases so autonomous coding agents never have to guess or stop on minor discrepancies.

---

## 1. Time-Window Config Bounds (Resolved)
- **Canonical Rule:** `time_window_before_days` accepts `1..365` (default `30`); `time_window_after_days` accepts `0..90` (default `7`).
- Both `docs/API_CONTRACT.md` and `docs/GRAPH_ENGINE.md` follow these exact bounds.

## 2. Canonical `prune_reason` Enum (Resolved)
- **Canonical Values (`trace_edges.prune_reason` and `pruning_breakdown` keys):**
  1. `hop_limit`
  2. `amount_below_threshold`
  3. `time_window`
  4. `degree_cap`
  5. `path_discontinuity`
  6. `duplicate`
- Do NOT use `duplicate_tx`, `duplicate_path`, or `path_continuity` as `prune_reason` strings.

## 3. `seed_tx_ts` Fallback When `seed_wallets.tx_hash` Is Omitted (Resolved)
- Because `seed_wallets.tx_hash` is optional, `time_gap_score` in `docs/VASP_ATTRIBUTION.md` resolves `seed_tx_ts` in this exact order:
  1. Timestamp of `seed_wallets.tx_hash` (if provided and found in `transactions`).
  2. Earliest outgoing transaction timestamp from the seed wallet within the trace window.
  3. `cases.reported_at` (if no outgoing transactions exist).
- If `candidate_first_inbound_ts < seed_tx_ts`, clamp `time_gap_hours = 0.0`.

## 4. Re-Trace Behavior on `POST /api/v1/cases/{id}/trace` (Resolved)
- Trace execution is allowed **only** when `cases.status IN ('PENDING', 'TRACE_FAILED')`.
- Calling `POST /api/v1/cases/{id}/trace` when:
  - `status == 'TRACING'` → returns `409 Conflict` (`"Trace already in progress"`).
  - `status IN ('TRACED', 'ANALYZED', 'EXPORTED', 'CLOSED')` → returns `409 Conflict` (`"Case has already been traced; create a new case to re-run"`).

## 5. Docker Layout & Seed Script Path (Resolved)
- `backend/Dockerfile` (build context `./backend`) and `frontend/Dockerfile` (build context `./frontend`) are the canonical Dockerfiles. There is no `infra/Dockerfile`.
- `seed_labels.py` lives at `backend/app/scripts/seed_labels.py` (inside the `backend/` build context) and is invoked via `python -m app.scripts.seed_labels`.

## 6. Seed VASP Labels Disclaimer (Resolved)
- All 20 seed VASP addresses in `docs/DATA_MODEL.md` and `docs/VASP_ATTRIBUTION.md` are **Base58Check-valid synthetic/placeholder TRON addresses** for MVP development and hackathon demo use.
- Their real-world exchange attribution is unverified. Production deployment requires replacing them with verified agency or licensed intelligence feeds.

## 7. `docs/DATA_MODEL.md` Single Source of Truth (Resolved)
- Section 3 of `docs/DATA_MODEL.md` is the **single authoritative DDL** for all 9 tables. No duplicate DDL appendix exists.

---

## 8. Specification Authority Hierarchy (Resolved)
- If an AI coding agent ever encounters a wording nuance across docs, resolve using this strict precedence order:
  1. `docs/DECISIONS.md` (canonical tie-breakers)
  2. `docs/API_CONTRACT.md` & `docs/DATA_MODEL.md` Section 3 (wire payloads, error formats, status codes, DB column names/types)
  3. Module specs: `docs/GRAPH_ENGINE.md`, `docs/VASP_ATTRIBUTION.md`, `docs/ACTION_PACKAGE_SPEC.md`, `docs/UI_SPEC.md`, `docs/DEPLOYMENT.md`
  4. `docs/PRODUCT_SPEC.md` (functional workflows, roles, non-goals)

## 9. Linear Alembic Migration Chain & Single-Head Rule (Resolved)
- All migrations MUST use sequential 4-digit revision IDs matching `backend/alembic/versions/0000_initial.py`:
  - `0000_initial.py` (`down_revision = None`) — M0 (already merged)
  - `0001_cases_and_wallets.py` (`down_revision = "0000"`) — M1 (`pgcrypto`, `set_updated_at()`, `cases`, `case_tags`, `seed_wallets`)
  - `0002_transactions.py` (`down_revision = "0001"`) — M2 (`transactions`)
  - `0003_trace_tables.py` (`down_revision = "0002"`) — M3 (`trace_edges`, `trace_nodes`)
  - `0004_vasp_tables.py` (`down_revision = "0003"`) — M4 (`vasp_labels`, `vasp_candidates`)
  - `0005_action_packages.py` (`down_revision = "0004"`) — M5 (`action_packages`)
- Generate with explicit IDs (`alembic revision --rev-id 000X -m "..."`) and ensure `backend/alembic/env.py` imports all ORM models before referencing `Base.metadata`.
- Before opening any PR containing a migration, rebase onto `dev` and verify `alembic heads` returns strictly **one** head.

## 10. Shared Integration Files & Parallel Track Rule (Resolved)
- Every backend route module (`cases`, `trace`, `candidates`, `labels`, `evidence`) defines its own `APIRouter` and registers only one `app.include_router(..., prefix="/api/v1")` line in `backend/app/main.py` to avoid merge conflicts.
- `backend/app/models/__init__.py` re-exports ORM models added by each milestone so `alembic/env.py` and `tests/conftest.py` auto-discover tables cleanly.
- On the frontend, Track 4 (`M6`) creates `frontend/src/pages/CaseDetail.tsx` with clean placeholder slots for the Graph, Candidates, Evidence, and Action Package tabs so Track 5 (`M7`) plugs in components with minimal diff.

## 11. Canonical Field & API Enum Names (Resolved)
- **`vasp_labels` columns:** `label`, `label_type`, `source`, `confidence` (NOT `label_name`, `vasp_type`, `confidence_base`).
- **`trace_edges` prune column:** `prune_reason` (NOT `pruned_reason`).
- **Candidate review:** `POST /api/v1/cases/{case_id}/candidates/{candidate_id}/review` with body `{"decision": "accepted" | "rejected" | "pending", "notes": ...}` (`API_CONTRACT.md` §2.8).
- **Manual VASP labels:** `POST /api/v1/labels` and `GET /api/v1/labels/search` (`API_CONTRACT.md` §2.12).
- **Graph JSON payload:** Top-level `{"nodes": [...], "edges": [...], "metadata": {...}}` with node fields `id`, `label`, `type`, `hop_depth`, `in_degree`, `out_degree`, `total_received`, `total_sent`, `vasp_label`, `vasp_confidence` (`API_CONTRACT.md` §2.6).
- **Case status failures (MVP):** Trace and attribution run inside one background task triggered by `POST /api/v1/cases/{case_id}/trace`; any failure sets `TRACE_FAILED`. (`ANALYSIS_FAILED` is kept in the DB CHECK constraint as reserved for future async split.)
- **Error response format:** FastAPI standard `{"detail": "..."}` (and Pydantic 422 `{"detail": [...]}` list) per `API_CONTRACT.md` §1.
