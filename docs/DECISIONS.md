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
