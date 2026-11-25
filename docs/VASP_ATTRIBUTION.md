# ANVESHAK — VASP Attribution & Ranking Specification

> **Module:** `ranking_engine` \
> **Owner:** Graph & Attribution Team \
> **Status:** Approved for MVP \
> **Last Updated:** 2026-11-24 \
> **Dependencies:** `graph_engine`, `chain_adapter`, PostgreSQL `vasp_labels` table

This document specifies how ANVESHAK identifies, scores, and ranks Virtual Asset
Service Provider (VASP) candidates from the traced transaction graph. It is the
authoritative reference for the ranking engine implementation.

---

## 1. Label Data Sources (Priority Order)

VASP labels come from four source tiers. Each tier has a fixed **confidence
base** that acts as the ceiling for `label_match_score` when matching addresses.

| Priority | `source` Value | Type | Default `confidence` | Description | MVP Status |
|----------|---------------|------|-------------------|-------------|------------|
| 1 | `agency` | Internal | `0.95` | Law enforcement intelligence feeds; manually verified by investigating officers. | ⚠️ Manual-entry only (via Human Review) |
| 2 | `licensed` | Commercial | `0.85` | Licensed commercial data (e.g., Chainalysis Reactor, Elliptic Lens feed). | ❌ Phase 2 |
| 3 | `public` | Community | `0.60` | Public tag databases, community-sourced labels (e.g., TRONSCAN tags, abuse DBs). | ✅ **Implemented — seed data below** |
| 4 | `heuristic` | Algorithmic | `0.40` | Pattern-based detection: sweep behavior, deposit-to-hot-wallet patterns. | ✅ **Implemented** |

> [!IMPORTANT]
> For MVP, only `public` and `heuristic` sources are active. The label store is
> seeded with known Indian and global exchange addresses (Section 7). Officers
> can add `agency`-tier labels via the Human Review flow (Section 6).

---

## 2. Label Matching Rules

When the graph engine identifies a **terminal node** (address with high fan-in,
high total received, or matching a known label), the attribution engine applies
the following matching rules **in order**. The first match that succeeds is used.

### 2.1 Exact Match (MVP)

```
1. Query: SELECT * FROM vasp_labels WHERE address = :address AND chain = :chain ORDER BY confidence DESC, updated_at DESC LIMIT 1
2. If row found → label_match_score = 1.0
3. Use row.label, row.label_type, row.source, row.confidence
```

**Table:** `vasp_labels` (see `docs/DATA_MODEL.md` §3.7) \
**Lookup Key:** `(address, chain)` (case-sensitive, TRON base58 format) \
**Tie-break:** Highest `confidence` first, then most recent `updated_at`.

### 2.2 Cluster Match (Phase 2 — Not in MVP)

```
1. Query: SELECT cluster_id FROM vasp_clusters WHERE address = :address
2. If cluster found → lookup cluster_id in vasp_labels
3. label_match_score = 0.8 (reduced from 1.0 because match is indirect)
```

> [!NOTE]
> Cluster detection (common-input-ownership heuristic) is deferred to Phase 2.
> The `vasp_clusters` table schema is reserved but not populated in MVP.

### 2.3 Heuristic Detection (MVP)

If no exact match or cluster match is found, apply behavioral heuristics against
the node's on-chain metrics. Heuristics are evaluated **independently**; if
multiple match, the one with the **highest confidence** is used.

#### 2.3.1 Sweep Pattern

| Field | Value |
|-------|-------|
| **ID** | `HEUR_SWEEP` |
| **Condition** | Address receives ≥ 10 inbound TRC-20 transfers from ≥ 5 distinct senders within a 24-hour rolling window, AND sends ≥ 1 outbound transfer where `amount_out ≥ 0.80 * sum(amounts_in)` within 6 hours of the last inbound |
| **Interpretation** | Likely exchange deposit aggregation (sweep to hot wallet) |
| **`label_match_score`** | `0.60` |
| **`heuristic_confidence`** | `0.40` |
| **Generated label** | `"Suspected Exchange (Sweep Pattern)"` |

#### 2.3.2 High Fan-In

| Field | Value |
|-------|-------|
| **ID** | `HEUR_FANIN` |
| **Condition** | Address has `in_degree > 50` within the trace window |
| **Interpretation** | Possible exchange hot wallet or mixer output |
| **`label_match_score`** | `0.60` |
| **`heuristic_confidence`** | `0.35` |
| **Generated label** | `"Suspected Exchange (High Fan-In)"` |

#### 2.3.3 Deposit-to-Hot-Wallet Forwarding

| Field | Value |
|-------|-------|
| **ID** | `HEUR_DEPOSIT_FWD` |
| **Condition** | Address receives funds AND forwards ≥ 95% of `total_received` to a **single** destination address within 1 hour (`3600 seconds`) of receipt |
| **Interpretation** | Likely intermediate deposit address controlled by an exchange |
| **`label_match_score`** | `0.60` |
| **`heuristic_confidence`** | `0.30` |
| **Generated label** | `"Suspected Deposit Address (Forward Pattern)"` |

**Heuristic output data structure:**

```python
@dataclass
class HeuristicMatch:
    heuristic_id: str          # "HEUR_SWEEP" | "HEUR_FANIN" | "HEUR_DEPOSIT_FWD"
    address: str               # The matched address
    generated_label: str       # Human-readable label
    label_match_score: float   # Always 0.60 for heuristic matches
    heuristic_confidence: float  # 0.40 | 0.35 | 0.30
    evidence: dict             # Supporting metrics, e.g.:
    # {
    #   "in_degree": 73,
    #   "distinct_senders_24h": 12,
    #   "forward_pct": 0.97,
    #   "forward_destination": "T...",
    #   "time_to_forward_seconds": 1842
    # }
```

> [!TIP]
> When a heuristic identifies a forwarding destination (e.g., in
> `HEUR_DEPOSIT_FWD`), the destination address should also be queried against
> `vasp_labels` for a potential exact match, which may upgrade the candidate's
> confidence.

---

## 3. Confidence Scoring Formula

Each VASP candidate receives a **composite confidence score** in the range
`[0.0, 1.0]`. The score is a weighted linear combination of six component scores.

### 3.1 Formula

```
confidence = (
    w1 * label_match_score +
    w2 * hop_depth_score +
    w3 * amount_relevance_score +
    w4 * time_gap_score +
    w5 * path_continuity_score +
    w6 * degree_fanout_score
)
```

### 3.2 Weights

| Symbol | Component | Weight | Rationale |
|--------|-----------|--------|-----------|
| `w1` | `label_match_score` | **0.35** | A known label is the strongest signal |
| `w2` | `hop_depth_score` | **0.15** | Closer hops → higher attribution confidence |
| `w3` | `amount_relevance_score` | **0.20** | More money flowing → more investigative relevance |
| `w4` | `time_gap_score` | **0.10** | Tighter timing → more likely automated laundering |
| `w5` | `path_continuity_score` | **0.10** | Unbroken fund flow → stronger evidence chain |
| `w6` | `degree_fanout_score` | **0.10** | High fan-in → more VASP-like behavior |
| | **Total** | **1.00** | Weights MUST sum to exactly 1.0 |

> [!IMPORTANT]
> These weights are defined as a configuration constant. They are NOT
> user-configurable in MVP but MAY be tuned in Phase 2 via an admin panel.
>
> ```python
> VASP_SCORING_WEIGHTS: dict[str, float] = {
>     "label_match":      0.35,
>     "hop_depth":        0.15,
>     "amount_relevance": 0.20,
>     "time_gap":         0.10,
>     "path_continuity":  0.10,
>     "degree_fanout":    0.10,
> }
> ```

### 3.3 Individual Score Calculations

#### 3.3.1 `label_match_score`

| Condition | Score | Example |
|-----------|-------|---------|
| Exact match found in `vasp_labels` | `1.0` | Address maps to "WazirX Hot Wallet" |
| Heuristic match (any `HEUR_*` rule fires) | `0.6` | Sweep pattern detected |
| No match — address is unknown | `0.0` | No label, no heuristic match |

**Type:** `float` \
**Range:** `{0.0, 0.6, 1.0}` (discrete values in MVP)

#### 3.3.2 `hop_depth_score`

```python
def hop_depth_score(hop_depth: int) -> float:
    """
    Hop depth from seed wallet. hop_depth >= 1 (direct recipient = hop 1).
    Score decreases by 0.25 per additional hop. Clamped to [0.0, 1.0].
    """
    score = 1.0 - (hop_depth - 1) * 0.25
    return max(0.0, min(1.0, score))
```

| `hop_depth` | Score |
|-------------|-------|
| 1 | `1.00` |
| 2 | `0.75` |
| 3 | `0.50` |
| 4 | `0.25` |
| 5+ | `0.00` |

**Type:** `float` \
**Range:** `[0.0, 1.0]` \
**Input:** Minimum hop depth from any seed wallet to this candidate across all traced paths.

#### 3.3.3 `amount_relevance_score`

```python
def amount_relevance_score(amount_received: float, seed_reported_amount: float) -> float:
    """
    Ratio of funds received by this candidate vs. the total amount the
    victim reported losing. Capped at 1.0.
    If seed_reported_amount is 0 or None, return 0.5 (neutral score).
    """
    if not seed_reported_amount or seed_reported_amount <= 0:
        return 0.5
    return min(1.0, amount_received / seed_reported_amount)
```

| `amount_received` | `seed_reported_amount` | Score |
|--------------------|----------------------|-------|
| 50,000 USDT | 50,000 USDT | `1.00` |
| 30,000 USDT | 50,000 USDT | `0.60` |
| 80,000 USDT | 50,000 USDT | `1.00` (capped) |
| 1,000 USDT | 50,000 USDT | `0.02` |
| Any | 0 or None | `0.50` (neutral) |

**Type:** `float` \
**Range:** `[0.0, 1.0]` \
**Units:** Both amounts in the same token denomination (USDT for MVP).

#### 3.3.4 `time_gap_score`

```python
def time_gap_score(time_gap_hours: float) -> float:
    """
    Time between the seed transaction and the candidate's first inbound
    transaction on the traced path. Shorter = more suspicious.
    Decay window: 720 hours (30 days). Beyond 30 days → 0.0.
    """
    return max(0.0, 1.0 - time_gap_hours / 720.0)
```

| `time_gap_hours` | Score | Interpretation |
|-------------------|-------|----------------|
| 0.5 (30 min) | `0.999` | Immediate forwarding — highly suspicious |
| 6.0 | `0.992` | Same-day, automated |
| 24.0 (1 day) | `0.967` | Within a day |
| 168.0 (7 days) | `0.767` | Week later |
| 360.0 (15 days) | `0.500` | Two weeks |
| 720.0 (30 days) | `0.000` | At decay horizon |
| 1000.0 | `0.000` | Beyond horizon |

**Type:** `float` \
**Range:** `[0.0, 1.0]` \
**Input:** `time_gap_hours` = `(candidate_first_inbound_ts - seed_tx_ts).total_seconds() / 3600.0`

**`seed_tx_ts` Fallback Rule (when `seed_wallets.tx_hash` is `NULL`):**
1. If `seed_wallets.tx_hash` is provided and found in `transactions`, use that transaction's `timestamp`.
2. Otherwise, use the **earliest outgoing transaction timestamp** from the seed wallet within the trace window.
3. If the seed wallet has no outgoing transactions, fall back to `cases.reported_at`.
If `time_gap_hours < 0` (edge timestamp precedes fallback timestamp), clamp `time_gap_hours = 0.0`.

#### 3.3.5 `path_continuity_score`

```python
def path_continuity_score(continuous_edges: int, total_edges: int) -> float:
    """
    Fraction of edges in the traced path that meet the 72-hour continuity
    rule. An edge is 'continuous' if the outbound transaction from a node
    occurs within 72 hours of the inbound transaction to that node.
    """
    if total_edges <= 0:
        return 0.0
    return continuous_edges / total_edges
```

| `continuous_edges` | `total_edges` | Score |
|--------------------|---------------|-------|
| 3 | 3 | `1.00` — Perfect chain |
| 2 | 3 | `0.67` — One break |
| 1 | 4 | `0.25` — Mostly broken |
| 0 | 2 | `0.00` — No continuity |

**Type:** `float` \
**Range:** `[0.0, 1.0]` \
**Continuity Rule:** An edge `(A → B)` at timestamp `t1` is continuous with
edge `(B → C)` at timestamp `t2` if `0 < (t2 - t1) ≤ 72 hours (259,200 seconds)`.

#### 3.3.6 `degree_fanout_score`

```python
def degree_fanout_score(in_degree: int) -> float:
    """
    Normalized in-degree of the candidate address within the trace window.
    More incoming transactions → more VASP-like. Capped at in_degree = 50.
    """
    return min(1.0, in_degree / 50.0)
```

| `in_degree` | Score |
|-------------|-------|
| 1 | `0.02` |
| 10 | `0.20` |
| 25 | `0.50` |
| 50 | `1.00` |
| 100 | `1.00` (capped) |

**Type:** `float` \
**Range:** `[0.0, 1.0]`

### 3.4 Worked Example

**Scenario:** Victim reports loss of 50,000 USDT. Trace finds address
`THb8E3EMsC9xU6bMNWQsr83dFfBEDSfXGg` at hop 2, which received 35,000 USDT,
has an exact label match for "WazirX", time gap of 4 hours, 3/3 continuous
edges, and in-degree of 60.

```
label_match_score      = 1.0   (exact match)
hop_depth_score        = 0.75  (hop 2: 1.0 - (2-1)*0.25)
amount_relevance_score = 0.70  (35000 / 50000)
time_gap_score         = 0.994 (1.0 - 4/720)
path_continuity_score  = 1.0   (3/3)
degree_fanout_score    = 1.0   (min(1.0, 60/50))

confidence = (0.35 * 1.0) + (0.15 * 0.75) + (0.20 * 0.70) +
             (0.10 * 0.994) + (0.10 * 1.0) + (0.10 * 1.0)
           = 0.350 + 0.1125 + 0.140 + 0.0994 + 0.100 + 0.100
           = 0.9019

Final confidence: 0.90 (rounded to 2 decimal places for display)
```

---

## 4. Ranking

### 4.1 Ranking Rules

| Rule | Value | Notes |
|------|-------|-------|
| **Sort order** | `confidence DESC` | Highest confidence = rank 1 |
| **Tie-break** | `amount_received DESC` | Higher received amount wins |
| **Secondary tie-break** | `hop_depth ASC` | Closer to seed wins |
| **Final tie-break** | `address ASC` | Deterministic lexicographic order |
| **Maximum candidates** | `10` | Configurable via `MAX_VASP_CANDIDATES` env var (int, default 10) |
| **Minimum confidence** | `0.20` | Addresses scoring below this are classified as `"unknown"` and excluded from the candidates list |
| **Rank assignment** | Dense ranking (1, 2, 3...) | No gaps; each candidate gets a unique rank |

### 4.2 Configuration Constants

```python
# config/ranking.py

MAX_VASP_CANDIDATES: int = 10          # Maximum candidates returned per case
MIN_CONFIDENCE_THRESHOLD: float = 0.20 # Below this → "unknown", not a candidate
CONFIDENCE_DISPLAY_PRECISION: int = 2  # Round to 2 decimal places for display
HOP_DEPTH_DECAY: float = 0.25         # Score decay per hop
TIME_GAP_HORIZON_HOURS: float = 720.0 # 30-day decay window
CONTINUITY_WINDOW_HOURS: float = 72.0 # Edge continuity threshold
FANIN_CAP: int = 50                    # In-degree normalization cap
```

### 4.3 Output Schema

The ranking engine produces a list of `VASPCandidate` objects:

```python
@dataclass
class VASPCandidate:
    address: str                     # TRON base58 address (34 chars)
    chain: str                       # "TRON" (MVP)
    label: str | None                # Best label or generated heuristic label
    label_source: str | None         # "agency" | "licensed" | "public" | "heuristic" | None
    confidence: float                # Composite score, 0.0 – 1.0
    rank: int                        # 1-based dense rank
    hop_depth: int                   # Minimum hops from seed
    amount_received: float           # Total funds received in trace window (USDT)
    scoring_breakdown: ScoringBreakdown
    alternative_labels: list[AlternativeLabel]  # Other labels if conflict (Section 5)
    evidence_paths: list[str]        # List of path_ids supporting this candidate
    review_status: str               # "pending" | "accepted" | "rejected"
    reviewed_by: str | None          # Officer ID who reviewed (None if pending)
    reviewed_at: str | None          # ISO 8601 timestamp of review

@dataclass
class ScoringBreakdown:
    label_match_score: float         # 0.0 | 0.6 | 1.0
    hop_depth_score: float           # [0.0, 1.0]
    amount_relevance_score: float    # [0.0, 1.0]
    time_gap_score: float            # [0.0, 1.0]
    path_continuity_score: float     # [0.0, 1.0]
    degree_fanout_score: float       # [0.0, 1.0]
    # Weighted contributions (for transparency / debugging)
    label_match_weighted: float      # w1 * label_match_score
    hop_depth_weighted: float        # w2 * hop_depth_score
    amount_relevance_weighted: float # w3 * amount_relevance_score
    time_gap_weighted: float         # w4 * time_gap_score
    path_continuity_weighted: float  # w5 * path_continuity_score
    degree_fanout_weighted: float    # w6 * degree_fanout_score
```

### 4.4 API Response Format

> **Authoritative Wire Schema:** Conform strictly to `docs/API_CONTRACT.md` §2.7 (`GET /api/v1/cases/{case_id}/candidates`, returning `case_id`, `candidates` list, and `total`), with `scoring_breakdown` containing the 6 float scores: `label_match_score`, `hop_depth_score`, `amount_relevance_score`, `time_gap_score`, `path_continuity_score`, `degree_fanout_score`, plus `evidence_path_ids` and `alternative_labels`.

---

## 5. Conflict Resolution

When an address has **multiple labels** from different sources, apply the
following resolution rules:

### 5.1 Resolution Priority

```
Step 1: Group all labels for the address from vasp_labels table.
Step 2: Sort by confidence DESC.
Step 3: If tie on confidence → sort by updated_at DESC (most recent wins).
Step 4: The top-sorted label becomes the PRIMARY label (used for display, scoring).
Step 5: All remaining labels are stored in alternative_labels array.
```

### 5.2 Source Priority Table

| Priority | Source | `confidence` Base | Wins over |
|----------|--------|-------------------|-----------|
| 1 | `agency` | `0.95` | All others |
| 2 | `licensed` | `0.85` | `public`, `heuristic` |
| 3 | `public` | `0.60` | `heuristic` |
| 4 | `heuristic` | `0.40` | Nothing |

### 5.3 Alternative Labels Schema

```python
@dataclass
class AlternativeLabel:
    label: str               # e.g., "Binance" or "Suspected Exchange (Sweep)"
    source: str              # "agency" | "licensed" | "public" | "heuristic"
    confidence: float        # 0.95 | 0.85 | 0.60 | 0.40
    updated_at: str          # ISO 8601
```

### 5.4 Example

Address `TFNyk1vSQ82XBvvboW7mLBtneeDToVt1KW` has three labels:

| Label | Source | `confidence` | `updated_at` |
|-------|--------|--------------|-------------|
| "WazirX Hot Wallet" | `public` | `0.60` | 2026-10-01T00:00:00Z |
| "Suspected Exchange" | `heuristic` | `0.40` | 2026-11-20T12:00:00Z |
| "WazirX Deposit" | `agency` | `0.95` | 2026-11-22T14:30:00Z |

**Result:**
- Primary label: `"WazirX Deposit"` (`source="agency"`, `confidence=0.95`)
- `label_match_score`: `1.0` (exact match)
- `alternative_labels`: `[{"label": "WazirX Hot Wallet", "source": "public", "confidence": 0.60}, ...]`

---

## 6. Human Review Flow (MVP)

### 6.1 Review Actions & Manual Labels

Investigating officers review candidates via `API_CONTRACT.md` §2.8 and add manual intelligence labels via `API_CONTRACT.md` §2.12:

| Action | API Endpoint | Effect |
|--------|--------------|--------|
| **Accept Candidate** | `POST /api/v1/cases/{case_id}/candidates/{candidate_id}/review` | Sets `review_status = "accepted"`, saves `review_notes`. Candidate is included in Action Package export. |
| **Reject Candidate** | `POST /api/v1/cases/{case_id}/candidates/{candidate_id}/review` | Sets `review_status = "rejected"`, saves `review_notes`. Candidate is excluded from default Action Package export. |
| **Reset to Pending** | `POST /api/v1/cases/{case_id}/candidates/{candidate_id}/review` | Sets `review_status = "pending"`. |
| **Add Manual Agency Label** | `POST /api/v1/labels` | Inserts a row into `vasp_labels` (e.g., `source="agency"`, `confidence=0.95`). |

### 6.2 Review Request & Response (`API_CONTRACT.md` §2.8)

**Endpoint:** `POST /api/v1/cases/{case_id}/candidates/{candidate_id}/review`

**Request Body:**
```json
{
  "decision": "accepted",
  "notes": "Confirmed WazirX hot wallet deposit address."
}
```
- `decision`: `"accepted" | "rejected" | "pending"` (required)
- `notes`: `string | null` (optional, max 2000 chars, persisted to `vasp_candidates.review_notes`)

**Response (`200 OK`):** Updated candidate object (`rank`, `address`, `chain`, `label`, `label_source`, `confidence`, `review_status`, `scoring_breakdown`, `evidence_path_ids`).

**Error Responses:**
- `404 Not Found`: `{"detail": "Candidate not found"}` (or `"Case not found"`)
- `422 Unprocessable Entity`: Invalid `decision` value.

### 6.3 MVP Behavior

- Accept/reject updates `vasp_candidates.review_status` and `review_notes` in PostgreSQL.
- All candidates (including rejected) remain visible in the Candidates tab.
- Action package generation (`ACTION_PACKAGE_SPEC.md` §3) filters out `review_status == "rejected"` candidates by default.
- Re-review is allowed: calling `POST .../review` again overwrites `review_status` and `review_notes`.

---

## 7. Authoritative Schema & Seed Data

> [!IMPORTANT]
> **Single Source of Truth:** `docs/DATA_MODEL.md` (§3.7 `vasp_labels`, §3.8 `vasp_candidates`, and §7 Seed Data) is the authoritative SQL schema and 20-row seed label dataset. Do NOT create separate tables such as `review_audit_log` or duplicate DDL columns like `label_name`/`vasp_type`/`confidence_base`.

- **Seed Loader:** Implemented at `backend/app/scripts/seed_labels.py` (invoked via `python -m app.scripts.seed_labels` in `backend/docker-entrypoint.sh`).
- **Idempotency:** Upserts / skips conflicts on `(address, chain, source)` (`ON CONFLICT (address, chain, source) DO NOTHING`).
- **Disclaimer:** All 20 seeded VASP addresses are Base58Check-valid synthetic/placeholder TRON addresses for hackathon MVP testing only (`docs/DECISIONS.md` §6).

---

## 8. Implementation Checklist (Track 3 — Milestone 4)

| # | Task | File | Depends On |
|---|---|---|---|
| 1 | `VASPLabel` and `VASPCandidate` ORM models | `backend/app/models/label.py`, `backend/app/models/candidate.py` | — |
| 2 | Alembic migration `0004_vasp_tables.py` (`down_revision = "0003"`) | `backend/alembic/versions/0004_vasp_tables.py` | #1 |
| 3 | Idempotent seed loader (20+ labels from `DATA_MODEL.md` §7) | `backend/app/scripts/seed_labels.py` | #2 |
| 4 | Exact label matcher, conflict resolver & 3 heuristic detectors | `backend/app/services/attribution/matcher.py` | #1, #3 |
| 5 | 6-signal scoring & dense ranking engine (`min_confidence = 0.20`) | `backend/app/services/ranking/scorer.py` | #4 |
| 6 | Candidates, Review & Labels API routes | `backend/app/api/routes/candidates.py`, `backend/app/api/routes/labels.py` | #5 |
| 7 | Register routers in `main.py` & wire end of trace background task | `backend/app/main.py`, `backend/app/services/graph/engine.py` | #6 |
| 8 | Unit & API tests (`ACCEPTANCE_TESTS.md` §4) | `backend/tests/services/test_ranking.py`, `backend/tests/api/test_candidates.py` | #6 |

---

*End of specification.*
