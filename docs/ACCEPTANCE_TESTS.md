# ANVESHAK — Acceptance Tests & Verification Suite

> **Machine-Executable Acceptance Criteria (MVP v1.0.0)**
> All unit, integration, and end-to-end tests MUST validate against these exact scenarios and pass/fail thresholds.

---

## 1. Synthetic Test Scenarios (Seed Data)

All TX hashes below are 64-char hex strings; all TRON addresses are valid 34-char Base58 strings starting with `T`.

### Scenario A: Simple 2-Hop (Happy Path)
- **Seed Wallet:** `TFNyk1vSQ82XBvvboW7mLBtneeDToVt1KW` (`reported_amount: 50000.00`, `token: USDT`)
- **Reported At:** `2026-11-20T14:30:00Z`
- **Mocked TronGrid Transactions:**
  1. Hop 1: `TFNyk1vSQ82XBvvboW7mLBtneeDToVt1KW` → `TNMKZSJx7g5Ryv91BXgv2q56VRQwi1ozue` | `49500.00 USDT` | `2026-11-20T15:10:00Z` | `tx_hash: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
  2. Hop 2: `TNMKZSJx7g5Ryv91BXgv2q56VRQwi1ozue` → `TNgEDH3RhWAWm7yBDmJgwWBZiGkjEnFaK7` | `48000.00 USDT` | `2026-11-20T16:45:00Z` | `tx_hash: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`
- **Seed Label Match:** `TNgEDH3RhWAWm7yBDmJgwWBZiGkjEnFaK7` → `"WazirX"` (`source: "public"`, `confidence: 0.60`)
- **Expected Result:**
  - `nodes`: 3 (`seed`, `intermediate`, `vasp_candidate`)
  - `edges`: 2 (`pruned=False`)
  - `vasp_candidates`: 1 candidate (`WazirX`, `rank=1`, `confidence >= 0.80`)
  - `recommended_actions`: Includes `"Issue Section 91 CrPC notice to WazirX"` and `"freeze"` (`HIGH` urgency)

### Scenario B: 3-Hop with Branching & Dust (Pruning Test)
- **Seed Wallet:** `TC2JpJStJPhCiJg8GDGutbHoU7zBXrazYK` (`reported_amount: 100000.00`, `token: USDT`)
- **Reported At:** `2026-11-20T10:00:00Z`
- **Mocked TronGrid Transactions:**
  1. Hop 1: Seed → `TT1XyC9pzGn4CTyBNMj1HELebeEW3zLgcZ` (`60000.00 USDT`, `2026-11-20T11:00:00Z`)
  2. Hop 1: Seed → `TTLSrQgGLmAPK8VPXCbLf7gk7x6TLzNrn7` (`35000.00 USDT`, `2026-11-20T11:05:00Z`)
  3. Hop 1: Seed → `TMKNKso568TSB9c8yZjbF3CxTLCeJTQV3j` (`500.00 USDT`, `2026-11-20T11:10:00Z`) — **MUST BE PRUNED** (`500 < 100000 * 0.01 = 1000`)
  4. Hop 2: `TT1XyC9pzGn4CTyBNMj1HELebeEW3zLgcZ` → `TAtcptJtpKLMEuKxUL9YeGPzrwQwxqPEJ8` (`58000.00 USDT`, `2026-11-20T12:00:00Z`) — Label: `"Binance"`
  5. Hop 2: `TTLSrQgGLmAPK8VPXCbLf7gk7x6TLzNrn7` → `TN1dTU526TCojBcifuykevpRZW98wzUJ1X` (`34000.00 USDT`, `2026-11-20T12:30:00Z`)
  6. Hop 3: `TN1dTU526TCojBcifuykevpRZW98wzUJ1X` → `TQRjK5QVnhjD8h17KJDXJa3nf2UWnpUupN` (`33000.00 USDT`, `2026-11-20T13:00:00Z`) — Label: `"KuCoin"`
- **Expected Result:**
  - `TMKNKso568TSB9c8yZjbF3CxTLCeJTQV3j` edge has `pruned=True`, `prune_reason="amount_below_threshold"`
  - Kept edges: 5, Kept nodes: 6
  - `vasp_candidates`: 2 candidates — **Rank 1: Binance**, **Rank 2: KuCoin** (Binance ranks higher due to hop 2 vs hop 3 + higher amount)

### Scenario C: Zero Transactions (Empty Graph Edge Case)
- **Seed Wallet:** `TS2sdoZQW7SjMgbUYzSc2yjsm4SJNweJRL` (`reported_amount: 10000.00`, `token: USDT`)
- **Mocked TronGrid Transactions:** `[]` (0 outgoing transactions)
- **Expected Result:**
  - Case status transitions `PENDING` → `TRACING` → `ANALYZED` (or `TRACED`)
  - `nodes`: 1 (seed node only), `edges`: `[]`
  - `vasp_candidates`: `[]`
  - `action_package.recommended_actions`: Contains `"No VASP endpoints identified"`

---

## 2. API Test Cases

```
TEST: API-01 Create Case (Valid)
ENDPOINT: POST /api/v1/cases
INPUT: Valid Scenario A payload
EXPECTED STATUS: 201
EXPECTED RESPONSE: id (UUID), status == "PENDING", len(seed_wallets) == 1

TEST: API-02 Create Case (Invalid TRON Address)
ENDPOINT: POST /api/v1/cases
INPUT: seed_wallets[0].address = "0x1234567890abcdef"
EXPECTED STATUS: 422
EXPECTED RESPONSE: detail[0].loc includes "address"

TEST: API-03 Create Case (Too Many Tags)
ENDPOINT: POST /api/v1/cases
INPUT: tags = ["t1","t2","t3","t4","t5","t6","t7","t8","t9","t10","t11"]
EXPECTED STATUS: 422

TEST: API-04 List Cases (Pagination & Status Filter)
ENDPOINT: GET /api/v1/cases?page=1&page_size=10&status=PENDING
EXPECTED STATUS: 200
EXPECTED RESPONSE: items (list, len <= 10), total (int), page == 1, page_size == 10

TEST: API-05 Get Case (Not Found)
ENDPOINT: GET /api/v1/cases/00000000-0000-0000-0000-000000000000
EXPECTED STATUS: 404
EXPECTED RESPONSE: {"detail": "Case not found"}

TEST: API-06 Trigger Trace (Valid)
ENDPOINT: POST /api/v1/cases/{case_id}/trace
INPUT: {}
EXPECTED STATUS: 202
EXPECTED RESPONSE: status == "TRACING"

TEST: API-07 Trigger Trace (Already Tracing)
ENDPOINT: POST /api/v1/cases/{case_id}/trace (when status == "TRACING")
EXPECTED STATUS: 409
EXPECTED RESPONSE: {"detail": "Trace already in progress"}

TEST: API-08 Get Graph (Before Trace)
ENDPOINT: GET /api/v1/cases/{case_id}/graph
EXPECTED STATUS: 200
EXPECTED RESPONSE: {"nodes": [], "edges": [], "metadata": null}

TEST: API-09 Get Candidates (After Trace)
ENDPOINT: GET /api/v1/cases/{case_id}/candidates
EXPECTED STATUS: 200
EXPECTED RESPONSE: candidates sorted by rank ASC, confidence in [0.0, 1.0]

TEST: API-10 Export Action Package PDF
ENDPOINT: GET /api/v1/cases/{case_id}/action-package/export
EXPECTED STATUS: 200
EXPECTED RESPONSE: Content-Type == "application/pdf", len(content) > 1000 bytes, starts with "%PDF-"

TEST: API-11 Health Check
ENDPOINT: GET /api/v1/health
EXPECTED STATUS: 200
EXPECTED RESPONSE: {"status": "ok", "version": "1.0.0", "database": "connected"}
```

---

## 3. Graph Engine Unit Test Cases

1. **`test_bfs_hop_depths`**: Verify seed is hop 0, direct recipients are hop 1, second layer is hop 2.
2. **`test_filter_hop_limit`**: With `hop_limit=2`, hop 3 transactions are marked `pruned=True, prune_reason="hop_limit"`.
3. **`test_filter_amount_relevance`**: Amount `< max(seed_amount * 0.01, 10.0)` is marked `pruned=True, prune_reason="amount_below_threshold"`.
4. **`test_filter_time_window`**: Transaction outside `[reported_at - 30d, reported_at + 7d]` is marked `pruned=True, prune_reason="time_window"`.
5. **`test_filter_degree_cap`**: Address with `> 100` outgoing txns is NOT expanded further and is flagged as potential VASP candidate.
6. **`test_filter_path_continuity`**: Hop 2 outgoing txn occurring *before* incoming txn or `> 72h` after incoming txn is marked `pruned=True, prune_reason="path_discontinuity"`.
7. **`test_filter_duplicate`**: Same `tx_hash` reached via two paths is kept only on shortest/highest-flow path.
8. **`test_cycle_detection`**: `A -> B -> C -> A` terminates cleanly without infinite loop and logs `cycles_detected >= 1`.

---

## 4. Ranking & Attribution Unit Test Cases

1. **`test_exact_label_match_ranks_highest`**: Known VASP address scores `label_match_score == 1.0` and outranks unknown addresses.
2. **`test_hop_depth_decay`**: Hop 1 (`1.0`) > Hop 2 (`0.75`) > Hop 3 (`0.50`).
3. **`test_confidence_threshold`**: Address with composite score `< 0.20` is excluded from `vasp_candidates`.
4. **`test_tie_breaking_by_amount`**: Equal confidence candidates sort by `total_received` DESC.
5. **`test_conflict_resolution`**: Address with both `agency` (0.95) and `public` (0.60) labels surfaces `agency` label and lists `public` in `alternative_labels`.

---

## 5. End-to-End (E2E) Test

- **`test_e2e_scenario_a_full_pipeline`**:
  1. `POST /api/v1/cases` with Scenario A seed wallet → `201`
  2. `POST /api/v1/cases/{id}/trace` (with mocked `TronAdapter`) → `202`
  3. Poll `GET /api/v1/cases/{id}` until `status == "ANALYZED"`
  4. `GET /api/v1/cases/{id}/graph` → `3` nodes, `2` edges
  5. `GET /api/v1/cases/{id}/candidates` → Rank 1 is `WazirX`
  6. `GET /api/v1/cases/{id}/evidence` → Contains `path-001` with 2 hops
  7. `GET /api/v1/cases/{id}/action-package/export` → Valid PDF bytes (`%PDF-`)

---

## 6. Pass/Fail Criteria

- **Unit & Integration Coverage:** `>= 80%` across `backend/app/services/`.
- **API Contracts:** 100% of API-01 through API-11 pass with exact HTTP status codes and schema validation.
- **Linter/Formatter:** `ruff check .` and `black --check .` exit `0`; `tsc --noEmit` exits `0`.
