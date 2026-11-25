# GRAPH_ENGINE.md — Graph Traversal & Pruning Algorithm Specification

> **Status**: DRAFT v1.0  
> **Last Updated**: 2026-11-24  
> **Owner**: Backend / Graph Engine Team  
> **Audience**: Implementing developer (human or AI agent)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Traversal Algorithm](#2-traversal-algorithm)
3. [Pruning Filters](#3-pruning-filters)
4. [Cycle Detection](#4-cycle-detection)
5. [Caching Strategy](#5-caching-strategy)
6. [Error Handling](#6-error-handling)
7. [Performance Constraints (MVP)](#7-performance-constraints-mvp)
8. [Output Format](#8-output-format)
9. [Pseudocode](#9-pseudocode)
10. [Data Structures Reference](#10-data-structures-reference)
11. [Configuration Reference](#11-configuration-reference)
12. [Appendix: Worked Example](#appendix-worked-example)

---

## 1. Overview

The Graph Engine is the core algorithmic component of ANVESHAK. Given one or more **seed wallets** extracted from a victim's complaint, it traces where the stolen funds went on the **TRON blockchain** by crawling outgoing TRC-20 (USDT) and TRX transactions via the TronGrid API, building a directed graph, and pruning irrelevant branches.

**Pipeline position:**

```
Complaint → Seed Wallet(s) → ★ GRAPH ENGINE ★ → Pruned DiGraph → VASP Ranking → Evidence Package
```

**Key design decisions:**

| Decision | Choice | Rationale |
|---|---|---|
| Graph library | `networkx.DiGraph` | Python-native, adequate for graphs ≤ 500 nodes (MVP scale) |
| Traversal | Breadth-First Search (BFS) | Level-by-level expansion maps naturally to "hops" from seed |
| Direction | OUTGOING only | We trace where money **went**, not where it came from |
| Pruning | Six filters applied **in order** at each hop | Keeps graph small, preserves investigative relevance |
| Blockchain | TRON (TRC-20 USDT + TRX) | Primary chain used in Indian crypto fraud cases |

---

## 2. Traversal Algorithm

### 2.1 Algorithm: Breadth-First Search (BFS)

The engine performs a **level-synchronous BFS** starting from every seed wallet in the case. All seed wallets begin at **hop 0**. The BFS explores OUTGOING transactions only — meaning we follow the `to_address` of each transaction to discover the next level of addresses.

### 2.2 Definitions

| Term | Definition |
|---|---|
| **Seed wallet** | A TRON address (Base58, `T`-prefixed, 34 chars) extracted from the complaint. Hop level = 0. |
| **Hop** | The shortest distance (in transaction edges) from any seed wallet to a given address. Seed = hop 0, first recipients = hop 1, etc. |
| **Frontier** | The set of addresses at the current hop level whose outgoing transactions have not yet been fetched. |
| **Visited (global)** | A `dict[str, int]` mapping `address → first_seen_hop`. An address is added the first time it is encountered. If encountered again at a later hop, it is **not re-processed** (the shorter path wins). |
| **Visited (per-path)** | A separate set used for cycle detection within a single BFS path (see §4). |

### 2.3 BFS Procedure (High Level)

```
1. Initialize frontier = {all seed wallets} at hop = 0
2. Initialize global_visited = {seed_addr: 0 for each seed}
3. For hop = 1 to trace_config.hop_limit (inclusive):
   a. next_frontier = empty set
   b. For each address in frontier:
      i.   Fetch all outgoing TRC-20/TRX transactions for this address (from cache or TronGrid)
      ii.  Apply pruning filters 1–6 (see §3) to each transaction
      iii. For each surviving transaction:
           - Add edge (from_address → to_address) to the DiGraph
           - If to_address not in global_visited:
               • Add to_address to global_visited with current hop
               • Add to_address to next_frontier
   c. frontier = next_frontier
   d. If frontier is empty → stop (no more addresses to explore)
   e. If total nodes in graph > MAX_ADDRESSES_PER_TRACE (500) → stop
   f. If total API calls made > MAX_API_CALLS_PER_TRACE (200) → stop
4. Return the pruned DiGraph + trace metadata
```

### 2.4 Multiple Seed Wallets

A single case may have multiple seed wallets (e.g., victim sent funds to two different scammer addresses). All seeds are placed in the initial frontier together. If the same address is reachable from two different seeds, it appears at the **minimum hop** across all seeds. The BFS does **not** restart for each seed — it is a single unified BFS from all seeds simultaneously.

### 2.5 Node Attributes (stored on DiGraph nodes)

| Attribute | Type | Description | Example |
|---|---|---|---|
| `address` | `str` | TRON Base58 address (34 chars, `T`-prefix) | `"TXrZ9B..."` |
| `hop` | `int` | Shortest hop distance from any seed | `2` |
| `node_type` | `str` enum | One of: `"seed"`, `"intermediate"`, `"vasp_candidate"`, `"fetch_failed"` | `"intermediate"` |
| `vasp_label` | `str \| None` | Matched VASP name if identified, else `None` | `"Binance"` |
| `in_degree` | `int` | Number of incoming edges in the pruned graph | `3` |
| `out_degree` | `int` | Number of outgoing edges in the pruned graph | `7` |
| `total_inflow` | `Decimal` | Sum of amounts on incoming edges (USDT equivalent) | `15000.00` |
| `total_outflow` | `Decimal` | Sum of amounts on outgoing edges (USDT equivalent) | `14800.00` |
| `first_seen_at` | `datetime` | Timestamp of the earliest transaction involving this address in the graph | `2026-10-15T08:30:00Z` |
| `degree_capped` | `bool` | `True` if this address was skipped due to degree cap filter | `False` |

### 2.6 Edge Attributes (stored on DiGraph edges)

| Attribute | Type | Description | Example |
|---|---|---|---|
| `tx_hash` | `str` | Transaction hash (64 hex chars) | `"a1b2c3..."` |
| `from_address` | `str` | Sender TRON address | `"TXrZ9B..."` |
| `to_address` | `str` | Receiver TRON address | `"TAbC12..."` |
| `amount` | `Decimal` | Transaction amount in token's native unit | `5000.000000` |
| `token` | `str` | Token symbol | `"USDT"` |
| `token_contract` | `str` | TRC-20 contract address (for USDT: `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`) | `"TR7NHq..."` |
| `timestamp` | `datetime` (UTC) | Block timestamp of the transaction | `2026-10-16T14:22:00Z` |
| `block_number` | `int` | TRON block number | `58123456` |
| `hop` | `int` | The hop level at which this edge was discovered (= source node's hop + 1) | `2` |
| `pruned` | `bool` | `True` if this edge was dropped by a filter | `False` |
| `prune_reason` | `str \| None` | Filter that dropped it, or `None` | `"amount_below_threshold"` |
| `cycle_detected` | `bool` | `True` if traversal was stopped here due to cycle | `False` |
| `incoming_tx_hash` | `str \| None` | The tx_hash of the incoming transaction that brought funds to `from_address` (for path continuity check). `None` for hop 1 edges (seed outgoing). | `"d4e5f6..."` |

---

## 3. Pruning Filters

Filters are applied **in the specified order** at each hop level for every candidate transaction. A transaction that fails **any** filter is marked `pruned=TRUE` with the corresponding `prune_reason` and is **not traversed further** (its `to_address` is not added to the next frontier). However, the pruned edge **is still stored** in the database for auditability.

### 3.1 Filter Ordering

```
Filter 1: Hop Limit          → structural limit
Filter 2: Amount Relevance   → value-based relevance
Filter 3: Time Window        → temporal relevance
Filter 4: Degree Cap         → fan-out heuristic (exchange detection)
Filter 5: Path Continuity    → causal flow integrity
Filter 6: Duplicate Removal  → graph deduplication
```

> [!IMPORTANT]
> Filters are applied in this exact sequence. A transaction dropped by Filter 2 is never evaluated against Filters 3–6. The `prune_reason` records the **first** filter that rejected the transaction.

---

### 3.2 Filter 1: Hop Limit

**Purpose:** Prevent unbounded graph expansion.

**Parameters:**

| Parameter | Type | Default | Min | Max | Source |
|---|---|---|---|---|---|
| `trace_config.hop_limit` | `int` | `3` | `1` | `5` | Per-case configuration |

**Rule:**

```python
if current_hop > trace_config.hop_limit:
    skip address entirely (do not fetch its outgoing transactions)
```

**Behavior:**
- Seed wallets are at `hop = 0`.
- At `hop = 1`, we fetch outgoing transactions of seed wallets. Recipients are at `hop = 1`.
- BFS loop runs from `hop = 1` to `hop = hop_limit` inclusive.
- An address at `hop = hop_limit` has its outgoing transactions fetched and edges recorded, but the **recipients** (at `hop = hop_limit + 1`) are NOT added to the frontier.

**`prune_reason` value:** `"hop_limit"`

---

### 3.3 Filter 2: Amount Relevance

**Purpose:** Drop micro-transactions that are not investigatively relevant.

**Parameters:**

| Parameter | Type | Default | Source |
|---|---|---|---|
| `seed_reported_amount` | `Decimal` | Extracted from `seed_wallets.reported_amount` | Complaint record |
| Relative threshold | `Decimal` | `0.01` (1%) | Hardcoded constant |
| Absolute minimum | `Decimal` | `10.0` USDT | Hardcoded constant |

**Rule:**

```python
# Compute effective threshold
if seed_reported_amount is not None and seed_reported_amount > 0:
    threshold = max(seed_reported_amount * Decimal("0.01"), Decimal("10.0"))
else:
    threshold = Decimal("10.0")

# Apply
if tx.amount < threshold:
    mark pruned, reason = "amount_below_threshold"
```

**Token normalization:**
- USDT (TRC-20): 6 decimal places. Raw amount from TronGrid is in **sun** (1 USDT = 1,000,000 sun). Divide by `10^6`.
- TRX: 6 decimal places. Raw amount from TronGrid is in **sun** (1 TRX = 1,000,000 sun). Divide by `10^6`.
- For TRX transactions, convert to USDT-equivalent using a cached exchange rate (fetched once per trace run, stored in `trace_metadata.trx_usdt_rate`). If rate fetch fails, use hardcoded fallback rate of `0.10` USD/TRX.

**Example:**
```
seed_reported_amount = 50000.0 USDT
threshold = max(50000.0 * 0.01, 10.0) = max(500.0, 10.0) = 500.0 USDT
tx.amount = 200.0 USDT → PRUNED (200 < 500)
tx.amount = 600.0 USDT → KEPT
```

**`prune_reason` value:** `"amount_below_threshold"`

---

### 3.4 Filter 3: Time Window

**Purpose:** Only include transactions temporally related to the reported fraud.

**Parameters:**

| Parameter | Type | Default | Min | Max | Source |
|---|---|---|---|---|---|
| `trace_config.time_window_before_days` | `int` | `30` | `1` | `365` | Per-case config |
| `trace_config.time_window_after_days` | `int` | `7` | `0` | `90` | Per-case config |
| `cases.reported_at` | `datetime` (UTC) | — | — | — | Complaint record |

**Rule:**

```python
window_start = cases.reported_at - timedelta(days=trace_config.time_window_before_days)
window_end   = cases.reported_at + timedelta(days=trace_config.time_window_after_days)

if not (window_start <= tx.timestamp <= window_end):
    mark pruned, reason = "time_window"
```

**Rationale:** In Indian crypto fraud cases, the typical pattern is:
1. Victim sends funds (days to weeks before filing complaint)
2. Scammer launders funds within hours/days
3. Victim files complaint
4. Some movement may happen after complaint filing (up to ~1 week)

**Edge case — missing `reported_at`:**
- If `cases.reported_at` is `NULL`, fall back to `cases.created_at` (the system timestamp when the complaint was entered).
- If both are `NULL`, abort the trace with error code `TRACE_ERR_NO_TIMESTAMP`.

**`prune_reason` value:** `"time_window"`

---

### 3.5 Filter 4: Degree Cap

**Purpose:** Identify and skip high-fan-out addresses (likely exchange hot wallets, mixing services, or automated contract systems) that would explode the graph.

**Parameters:**

| Parameter | Type | Default | Min | Max | Source |
|---|---|---|---|---|---|
| `trace_config.degree_cap` | `int` | `100` | `10` | `1000` | Per-case config |

**Rule:**

```python
# Count outgoing transactions from this address within the time window
outgoing_count = count_outgoing_txs(address, window_start, window_end)

if outgoing_count > trace_config.degree_cap:
    # Do NOT traverse this address's outgoing transactions
    # But DO mark it as a VASP candidate
    node.node_type = "vasp_candidate"
    node.degree_capped = True
    # All outgoing edges from this address: mark pruned
    for tx in outgoing_txs:
        mark pruned, reason = "degree_cap"
```

**Key behavior:**
- The address itself **remains in the graph** as a node (it was already added when discovered as a recipient).
- It is flagged as `node_type = "vasp_candidate"` because high-fan-out addresses are strong VASP indicators.
- Its **incoming** edges (which brought funds to it) are **kept** (they were added in the previous hop).
- Its **outgoing** edges are **all pruned** with `reason = "degree_cap"`.
- The outgoing transaction count is determined **before** fetching all transaction details — use TronGrid's pagination metadata (`total` field) or count the first page results. If the count exceeds the cap, **do not fetch further pages**.

**`prune_reason` value:** `"degree_cap"`

---

### 3.6 Filter 5: Path Continuity

**Purpose:** Ensure causal flow — money must arrive at an address before it can leave. This filters out transactions that are temporally unrelated to the traced funds.

**Parameters:**

| Parameter | Type | Default | Source |
|---|---|---|---|
| Continuity tolerance | `timedelta` | `72 hours` | Hardcoded constant |

**Rule:**

```python
# This filter applies ONLY at hop >= 2
# (At hop 1, the seed wallet's outgoing transactions have no "incoming" to compare against)

if hop == 1:
    skip this filter (all seed outgoing transactions pass)

# For hop >= 2:
# `incoming_tx` = the transaction that brought funds to this address (from the previous hop)
# `outgoing_tx` = the candidate transaction leaving this address (current hop)

if not (incoming_tx.timestamp <= outgoing_tx.timestamp <= incoming_tx.timestamp + timedelta(hours=72)):
    mark pruned, reason = "path_discontinuity"
```

**Multiple incoming transactions:**
- An address may have been reached by **multiple** incoming transactions from the previous hop (e.g., two different senders in the same traced flow).
- An outgoing transaction passes this filter if it satisfies the continuity constraint with **ANY** of the incoming transactions. In other words, we take the **earliest** incoming timestamp and the **latest** incoming timestamp + 72h as the valid window:

```python
earliest_incoming = min(inc.timestamp for inc in incoming_txs_to_this_address)
latest_incoming   = max(inc.timestamp for inc in incoming_txs_to_this_address)
valid_window_start = earliest_incoming
valid_window_end   = latest_incoming + timedelta(hours=72)

if not (valid_window_start <= outgoing_tx.timestamp <= valid_window_end):
    mark pruned, reason = "path_discontinuity"
```

**`prune_reason` value:** `"path_discontinuity"`

---

### 3.7 Filter 6: Duplicate Removal

**Purpose:** Deduplicate edges and paths to keep the graph minimal and unambiguous.

**Two sub-rules:**

#### 6a. Duplicate Transaction Hash

The same `tx_hash` can appear in multiple BFS paths if two paths converge at the same address and then diverge again through the same transaction. In this case:

```python
if tx_hash already exists as a kept (pruned=FALSE) edge in the graph:
    # Keep it in the SHORTEST path (lowest hop level)
    if existing_edge.hop <= current_hop:
        mark current occurrence pruned, reason = "duplicate"
    else:
        # Current path is shorter — swap: prune the old one, keep this one
        mark existing occurrence pruned, reason = "duplicate"
        add current occurrence as kept
```

#### 6b. Duplicate Address via Multiple Paths

If the same `to_address` is reached via multiple paths at the **same** hop level:

```python
if to_address already in global_visited at same hop:
    # Keep the path with the HIGHEST total amount flow from seed to this address
    existing_path_amount = sum of edge amounts along the existing path
    current_path_amount  = sum of edge amounts along the current path
    
    if current_path_amount > existing_path_amount:
        # Replace: prune old path's final edge, keep current
        mark old edge pruned, reason = "duplicate"
        keep current edge
    else:
        mark current edge pruned, reason = "duplicate"
```

**Implementation note:** For MVP, the "total path amount" is approximated by looking only at the **edge amount** arriving at the address (not the full path sum), since tracking full path sums in BFS requires additional bookkeeping. This is acceptable because the highest single-edge amount is a reasonable proxy for the most significant flow.

**`prune_reason` values:** `"duplicate"` or `"duplicate"`

---

## 4. Cycle Detection

### 4.1 Mechanism

Cycles occur when funds flow in a loop (e.g., A → B → C → A). In a BFS, the global visited set prevents re-processing, but we need to **detect and log** cycles explicitly.

**Rule:**

```python
# When processing outgoing transactions of address X at hop H:
for tx in outgoing_txs:
    if tx.to_address in global_visited:
        # This address was already seen at an earlier (or equal) hop
        # This is a cycle (or reconvergence)
        edge.cycle_detected = True
        # Add the edge to the graph (for visualization) but do NOT add to_address to frontier
        # Log the cycle
        trace_metadata.cycles.append({
            "from": tx.from_address,
            "to": tx.to_address,
            "tx_hash": tx.tx_hash,
            "hop": H,
            "target_original_hop": global_visited[tx.to_address]
        })
```

### 4.2 Cycle Edge Behavior

- The edge IS added to the DiGraph (with `cycle_detected = True`).
- The edge is NOT marked as `pruned` — it is a valid transaction that happened, just not traversed further.
- The `to_address` is NOT re-added to the frontier (it was already processed or will be processed at its original hop level).
- Cycles are counted in `trace_metadata.cycles_detected`.

### 4.3 Self-Loops

A transaction where `from_address == to_address` is treated as a self-loop:
- Edge is added with `cycle_detected = True`.
- Not traversed further.
- Logged in cycle metadata.

---

## 5. Caching Strategy

### 5.1 Cache Location

Transactions fetched from TronGrid are stored in the `transactions` table in PostgreSQL. The cache key is `(tx_hash, chain)` where `chain = 'TRON'`.

### 5.2 Cache-Before-Fetch Logic

```python
def get_outgoing_transactions(address: str, window_start: datetime, window_end: datetime) -> list[Transaction]:
    # Step 1: Check DB cache
    cached = db.query(Transaction).filter(
        Transaction.from_address == address,
        Transaction.chain == "TRON",
        Transaction.timestamp >= window_start,
        Transaction.timestamp <= window_end,
        Transaction.fetched_at >= now() - timedelta(hours=24)  # Cache TTL
    ).all()
    
    if cached:
        # Cache hit — check completeness flag
        cache_meta = db.query(AddressFetchLog).filter(
            AddressFetchLog.address == address,
            AddressFetchLog.window_start == window_start,
            AddressFetchLog.window_end == window_end,
            AddressFetchLog.fetched_at >= now() - timedelta(hours=24)
        ).first()
        
        if cache_meta and cache_meta.is_complete:
            return cached
    
    # Step 2: Fetch from TronGrid
    raw_txs = trongrid_client.fetch_outgoing(address, window_start, window_end)
    
    # Step 3: Upsert into DB
    for tx in raw_txs:
        db.upsert(Transaction(
            tx_hash=tx.hash,
            chain="TRON",
            from_address=tx.from_addr,
            to_address=tx.to_addr,
            amount=tx.amount,
            token=tx.token,
            token_contract=tx.contract,
            timestamp=tx.timestamp,
            block_number=tx.block,
            fetched_at=now()
        ))
    
    # Step 4: Mark fetch as complete
    db.upsert(AddressFetchLog(
        address=address,
        window_start=window_start,
        window_end=window_end,
        fetched_at=now(),
        is_complete=True,
        tx_count=len(raw_txs)
    ))
    
    return raw_txs
```

### 5.3 Cache TTL

| Parameter | Value | Rationale |
|---|---|---|
| `CACHE_TTL_HOURS` | `24` | Blockchain data is immutable, but TronGrid indexing may lag. 24h is conservative for MVP. |

### 5.4 `AddressFetchLog` Table Schema

| Column | Type | Description |
|---|---|---|
| `id` | `UUID` PK | Auto-generated |
| `address` | `VARCHAR(34)` | TRON address |
| `window_start` | `TIMESTAMPTZ` | Start of time window queried |
| `window_end` | `TIMESTAMPTZ` | End of time window queried |
| `fetched_at` | `TIMESTAMPTZ` | When the fetch completed |
| `is_complete` | `BOOLEAN` | True if all pages were fetched without error |
| `tx_count` | `INTEGER` | Number of transactions fetched |

**Index:** `UNIQUE(address, window_start, window_end)`

---

## 6. Error Handling

### 6.1 TronGrid API Errors

| Scenario | HTTP Status | Action | Max Retries | Backoff |
|---|---|---|---|---|
| Rate limited | `429` | Exponential backoff | 3 | 1s → 2s → 4s |
| Server error | `5xx` | Retry once | 1 | 2s (fixed) |
| Timeout | N/A (>10s) | Mark failed | 0 | — |
| Client error | `4xx` (not 429) | Mark failed, log error | 0 | — |
| Network error | N/A | Retry once | 1 | 2s (fixed) |

### 6.2 Retry Implementation

```python
async def fetch_with_retry(address: str, window_start: datetime, window_end: datetime) -> FetchResult:
    max_retries = 3
    base_delay = 1.0  # seconds
    
    for attempt in range(max_retries + 1):
        try:
            response = await trongrid_client.get(
                url=f"/v1/accounts/{address}/transactions/trc20",
                params={
                    "min_timestamp": int(window_start.timestamp() * 1000),
                    "max_timestamp": int(window_end.timestamp() * 1000),
                    "limit": 200,
                    "only_from": "true",  # outgoing only
                    "contract_address": USDT_CONTRACT  # filter to USDT
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                return FetchResult(success=True, data=response.json()["data"])
            
            if response.status_code == 429:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
                    await asyncio.sleep(delay)
                    continue
                else:
                    return FetchResult(success=False, error="rate_limited_exhausted")
            
            if response.status_code >= 500:
                if attempt == 0:
                    await asyncio.sleep(2.0)
                    continue
                else:
                    return FetchResult(success=False, error=f"server_error_{response.status_code}")
            
            # 4xx (not 429)
            return FetchResult(success=False, error=f"client_error_{response.status_code}")
        
        except asyncio.TimeoutError:
            return FetchResult(success=False, error="timeout")
        
        except (aiohttp.ClientError, ConnectionError) as e:
            if attempt == 0:
                await asyncio.sleep(2.0)
                continue
            return FetchResult(success=False, error=f"network_error: {str(e)}")
    
    return FetchResult(success=False, error="max_retries_exceeded")
```

### 6.3 Fetch Failure Handling

```python
# After fetching all addresses at a hop level:
failed_count = sum(1 for addr in frontier if addr.fetch_status == "fetch_failed")
total_count = len(frontier)
failure_rate = failed_count / total_count if total_count > 0 else 0.0

if failure_rate > 0.50:
    # >50% failure at this hop level → abort entire trace
    case.status = "TRACE_FAILED"
    trace_metadata.abort_reason = f"fetch_failure_rate={failure_rate:.2%} at hop={current_hop}"
    # Save partial results (all edges fetched so far remain in DB)
    save_partial_results()
    return TraceResult(status="TRACE_FAILED", metadata=trace_metadata)
```

### 6.4 Failed Address Nodes

When an address fetch fails:
- The node is added to the graph with `node_type = "fetch_failed"`.
- No outgoing edges are added from it.
- It appears in the visualization with a distinct style (grey, dashed border).
- `trace_metadata.fetch_failures` is incremented.

### 6.5 Error Codes

| Code | Meaning | Resolution |
|---|---|---|
| `TRACE_ERR_NO_SEED` | No seed wallets in the case | Add seed wallets to complaint |
| `TRACE_ERR_NO_TIMESTAMP` | `cases.reported_at` and `cases.created_at` are both NULL | Update complaint record |
| `TRACE_ERR_INVALID_ADDRESS` | Seed wallet address is not a valid TRON Base58 address | Correct the address |
| `TRACE_ERR_TRONGRID_DOWN` | All TronGrid requests failed at hop 1 | Retry later |
| `TRACE_ERR_FETCH_ABORT` | >50% fetch failure at a hop level | Check TronGrid status, retry |
| `TRACE_ERR_MAX_NODES` | Graph exceeded 500 nodes | Review with higher amount threshold |
| `TRACE_ERR_MAX_API_CALLS` | Exceeded 200 API calls | Reduce hop limit or increase amount threshold |

---

## 7. Performance Constraints (MVP)

### 7.1 Hard Limits

| Constraint | Value | Behavior When Exceeded |
|---|---|---|
| `MAX_ADDRESSES_PER_TRACE` | `500` | Stop BFS. Use partial graph. Set `trace_metadata.truncated = True`. |
| `MAX_API_CALLS_PER_TRACE` | `200` | Stop BFS. Use partial graph. Set `trace_metadata.truncated = True`. |
| `TARGET_TRACE_TIME_SECONDS` | `60` | Soft target. No abort, but log warning if exceeded. |

### 7.2 API Call Counting

One API call = one HTTP request to TronGrid. Paginated fetches count each page as a separate call.

```python
api_call_counter = 0

# Before each TronGrid request:
api_call_counter += 1
if api_call_counter > MAX_API_CALLS_PER_TRACE:
    raise MaxApiCallsExceeded()
```

### 7.3 Concurrency

- Addresses at the same hop level are fetched **concurrently** using `asyncio.gather()`.
- Maximum concurrent requests: `10` (to avoid overwhelming TronGrid).
- Use `asyncio.Semaphore(10)` to throttle.

```python
semaphore = asyncio.Semaphore(10)

async def throttled_fetch(address, window_start, window_end):
    async with semaphore:
        return await fetch_with_retry(address, window_start, window_end)

# Fetch all addresses at this hop concurrently:
results = await asyncio.gather(
    *[throttled_fetch(addr, ws, we) for addr in frontier]
)
```

### 7.4 Background Execution

The trace is executed as a **background async task** via FastAPI's `BackgroundTasks` or a task queue (Celery/ARQ for post-MVP).

```
POST /api/v1/cases/{case_id}/trace  →  returns 202 Accepted + { task_id }
GET  /api/v1/cases/{case_id}/trace/status  →  returns { status, progress, metadata }
```

**Status values:** `PENDING` → `RUNNING` → `COMPLETED` | `TRACE_FAILED`

**Progress reporting:** After each hop level completes, update the trace status with:
```json
{
  "status": "RUNNING",
  "current_hop": 2,
  "total_hops": 3,
  "nodes_found": 47,
  "edges_found": 83,
  "api_calls_made": 52,
  "elapsed_seconds": 12.3
}
```

---

## 8. Output Format

### 8.1 Database Persistence

The trace results are persisted to the canonical tables defined in `docs/DATA_MODEL.md` §3.5–§3.6 (`trace_nodes` and `trace_edges` — **always treat `docs/DATA_MODEL.md` as authoritative for exact SQL types, triggers, and constraints**):

- **`trace_nodes`**: One row per address discovered during the trace (`case_id`, `address`, `chain`, `node_type` IN `('seed','intermediate','vasp_candidate','unknown')`, `hop_depth`, `in_degree`, `out_degree`, `total_received`, `total_sent`, `first_seen`, `last_seen`).
- **`trace_edges`**: One row per transaction (`case_id`, `transaction_id`, `from_address`, `to_address`, `amount`, `token`, `timestamp`, `hop_depth`, `path_id`, `pruned`, `prune_reason`).
- **Source timestamps & amounts**: Load `reported_at` from `cases.reported_at` and seed amounts from `seed_wallets.reported_amount`.

### 8.2 Trace Metadata Object

Returned inside `GET /api/v1/cases/{case_id}/graph` under `"metadata"` (`API_CONTRACT.md` §2.6):

```json
{
  "trace_id": "uuid-string",
  "started_at": "2026-10-20T10:00:00Z",
  "completed_at": "2026-10-20T10:00:45Z",
  "elapsed_seconds": 45.2,
  "status": "COMPLETED",
  "truncated": false,
  "abort_reason": null,
  "seed_wallets": ["TXrZ9B...", "TAbC12..."],
  "hop_limit": 3,
  "amount_threshold": 500.0,
  "time_window": {
    "start": "2026-09-20T00:00:00Z",
    "end": "2026-10-27T00:00:00Z"
  },
  "trx_usdt_rate": 0.112,
  "total_fetched": 312,
  "total_pruned": 229,
  "total_kept": 83,
  "pruning_breakdown": {
    "hop_limit": 0,
    "amount_below_threshold": 87,
    "time_window": 42,
    "degree_cap": 55,
    "path_discontinuity": 31,
    "duplicate": 14
  },
  "nodes_count": 47,
  "edges_count": 83,
  "cycles_detected": 2,
  "cycles": [
    {
      "from": "TAbC12...",
      "to": "TXrZ9B...",
      "tx_hash": "a1b2c3...",
      "hop": 3,
      "target_original_hop": 0
    }
  ],
  "fetch_failures": 3,
  "api_calls_made": 52,
  "degree_capped_addresses": ["THotWallet1...", "THotWallet2..."],
  "vasp_candidates": ["THotWallet1...", "THotWallet2...", "TKnownExch..."]
}
```

### 8.3 Cytoscape JSON Serialization

The graph engine serializes the traced graph into the exact top-level shape specified in `API_CONTRACT.md` §2.6 (`nodes`, `edges`, `metadata`):

```json
{
  "nodes": [
    {
      "data": {
        "id": "TL6NsnvPg3N7QxaLsBvHCEaBiSYrqiDNws",
        "label": "TL6N...DNws",
        "type": "seed",
        "hop_depth": 0,
        "in_degree": 0,
        "out_degree": 3,
        "total_received": 0.0,
        "total_sent": 50000.0,
        "vasp_label": null,
        "vasp_confidence": null
      }
    },
    {
      "data": {
        "id": "TQpoianDcskU3tei8gxhJzJhN1ZKz75SZ1",
        "label": "TQpo...5SZ1",
        "type": "intermediate",
        "hop_depth": 1,
        "in_degree": 1,
        "out_degree": 2,
        "total_received": 20000.0,
        "total_sent": 19500.0,
        "vasp_label": null,
        "vasp_confidence": null
      }
    },
    {
      "data": {
        "id": "TVKGjmUx73nc4EX1pNg8c3AnN8vSZqGgnU",
        "label": "TVKG...GgnU",
        "type": "vasp_candidate",
        "hop_depth": 2,
        "in_degree": 2,
        "out_degree": 0,
        "total_received": 15000.0,
        "total_sent": 0.0,
        "vasp_label": "Binance",
        "vasp_confidence": 0.88
      }
    }
  ],
  "edges": [
    {
      "data": {
        "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "source": "TL6NsnvPg3N7QxaLsBvHCEaBiSYrqiDNws",
        "target": "TQpoianDcskU3tei8gxhJzJhN1ZKz75SZ1",
        "amount": 20000.0,
        "token": "USDT",
        "timestamp": "2026-10-16T14:22:00Z",
        "hop_depth": 1,
        "pruned": false,
        "prune_reason": null
      }
    },
    {
      "data": {
        "id": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
        "source": "TQpoianDcskU3tei8gxhJzJhN1ZKz75SZ1",
        "target": "TVKGjmUx73nc4EX1pNg8c3AnN8vSZqGgnU",
        "amount": 15000.0,
        "token": "USDT",
        "timestamp": "2026-10-16T15:03:00Z",
        "hop_depth": 2,
        "pruned": false,
        "prune_reason": null
      }
    }
  ],
  "metadata": {
    "total_fetched": 48,
    "total_pruned": 25,
    "pruning_breakdown": {
      "hop_limit": 12,
      "amount_below_threshold": 8,
      "time_window": 3,
      "degree_cap": 1,
      "path_discontinuity": 0,
      "duplicate": 1
    },
    "cycles_detected": 0,
    "fetch_failures": 0,
    "elapsed_seconds": 4.21
  }
}
```

**Label generation rule:**
```python
def short_label(address: str) -> str:
    """First 4 chars + '...' + last 4 chars of the address."""
    return f"{address[:4]}...{address[-4:]}"
```

### 8.4 Return Type

```python
@dataclass
class TraceResult:
    status: Literal["COMPLETED", "TRACE_FAILED"]
    trace_nodes: list[GraphNode]       # DB model objects
    trace_edges: list[GraphEdge]       # DB model objects (pruned=FALSE only)
    pruned_edges: list[GraphEdge]      # DB model objects (pruned=TRUE only)
    trace_metadata: dict               # JSON-serializable dict (§8.2)
    cytoscape_json: dict               # Cytoscape-compatible dict (§8.3)
```

---

## 9. Pseudocode

The following is the **complete** BFS + pruning algorithm in Python-like pseudocode. It maps directly to the implementation in `app/services/graph_engine.py`.

```python
# ===========================================================================
# graph_engine.py — Core BFS + Pruning Algorithm
# ===========================================================================

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import networkx as nx

# Constants
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
AMOUNT_RELEVANCE_PERCENT = Decimal("0.01")
AMOUNT_ABSOLUTE_MIN = Decimal("10.0")
PATH_CONTINUITY_HOURS = 72
CACHE_TTL_HOURS = 24
MAX_ADDRESSES = 500
MAX_API_CALLS = 200
MAX_CONCURRENT = 10
TRX_USDT_FALLBACK_RATE = Decimal("0.10")


@dataclass
class TraceConfig:
    hop_limit: int = 3                    # 1–5
    time_window_before_days: int = 30     # 1–365
    time_window_after_days: int = 7       # 0–90
    degree_cap: int = 100                 # 10–1000


@dataclass
class TraceContext:
    case_id: str
    seed_wallets: list[str]
    reported_amount: Optional[Decimal]
    reported_at: datetime
    config: TraceConfig
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    global_visited: dict[str, int] = field(default_factory=dict)       # address → hop
    incoming_txs: dict[str, list] = field(default_factory=dict)        # address → [Transaction]
    api_call_count: int = 0
    fetch_failures: int = 0
    pruning_counts: dict[str, int] = field(default_factory=lambda: {
        "hop_limit": 0, "amount_below_threshold": 0, "time_window": 0,
        "degree_cap": 0, "path_discontinuity": 0, "duplicate": 0
    })
    cycles: list[dict] = field(default_factory=list)
    degree_capped_addrs: list[str] = field(default_factory=list)
    kept_tx_hashes: dict[str, int] = field(default_factory=dict)       # tx_hash → hop
    truncated: bool = False
    abort_reason: Optional[str] = None


async def run_trace(case_id: str, db: Database) -> TraceResult:
    """Main entry point. Fetches case data, runs BFS, returns results."""

    # -----------------------------------------------------------------------
    # STEP 0: Load case and complaint data
    # -----------------------------------------------------------------------
    case = await db.get_case(case_id)
        seed_wallets = await db.get_seed_wallets(case_id)

    if not seed_wallets:
        raise TraceError("TRACE_ERR_NO_SEED")

    reported_at = cases.reported_at or cases.created_at
    if reported_at is None:
        raise TraceError("TRACE_ERR_NO_TIMESTAMP")

    for sw in seed_wallets:
        if not is_valid_tron_address(sw.address):
            raise TraceError("TRACE_ERR_INVALID_ADDRESS", detail=sw.address)

    config = TraceConfig(
        hop_limit=case.trace_config.get("hop_limit", 3),
        time_window_before_days=case.trace_config.get("time_window_before_days", 30),
        time_window_after_days=case.trace_config.get("time_window_after_days", 7),
        degree_cap=case.trace_config.get("degree_cap", 100),
    )

    # Clamp config values
    config.hop_limit = clamp(config.hop_limit, 1, 5)
    config.time_window_before_days = clamp(config.time_window_before_days, 1, 365)
    config.time_window_after_days = clamp(config.time_window_after_days, 0, 90)
    config.degree_cap = clamp(config.degree_cap, 10, 1000)

    # Compute time window
    window_start = reported_at - timedelta(days=config.time_window_before_days)
    window_end = reported_at + timedelta(days=config.time_window_after_days)

    # Compute amount threshold
    reported_amount = sum(sw.reported_amount or Decimal('0') for sw in seed_wallets)  # Decimal or None
    if reported_amount and reported_amount > 0:
        amount_threshold = max(reported_amount * AMOUNT_RELEVANCE_PERCENT, AMOUNT_ABSOLUTE_MIN)
    else:
        amount_threshold = AMOUNT_ABSOLUTE_MIN

    # Fetch TRX/USDT exchange rate
    trx_usdt_rate = await fetch_trx_usdt_rate() or TRX_USDT_FALLBACK_RATE

    # -----------------------------------------------------------------------
    # STEP 1: Initialize BFS
    # -----------------------------------------------------------------------
    ctx = TraceContext(
        case_id=case_id,
        seed_wallets=[sw.address for sw in seed_wallets],
        reported_amount=reported_amount,
        reported_at=reported_at,
        config=config,
    )

    # Add seed nodes
    frontier: list[str] = []
    for sw in seed_wallets:
        addr = sw.address
        ctx.graph.add_node(addr,
            address=addr,
            hop=0,
            node_type="seed",
            vasp_label=None,
            in_degree=0,
            out_degree=0,
            total_inflow=Decimal("0"),
            total_outflow=Decimal("0"),
            first_seen_at=None,
            degree_capped=False,
        )
        ctx.global_visited[addr] = 0
        frontier.append(addr)

    start_time = datetime.utcnow()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # -----------------------------------------------------------------------
    # STEP 2: BFS loop — hop 1 to hop_limit
    # -----------------------------------------------------------------------
    for current_hop in range(1, config.hop_limit + 1):
        if not frontier:
            break  # Nothing left to explore

        # Check node limit
        if ctx.graph.number_of_nodes() >= MAX_ADDRESSES:
            ctx.truncated = True
            ctx.abort_reason = "max_addresses_exceeded"
            break

        # Check API call limit
        if ctx.api_call_count >= MAX_API_CALLS:
            ctx.truncated = True
            ctx.abort_reason = "max_api_calls_exceeded"
            break

        # -------------------------------------------------------------------
        # STEP 2a: Fetch outgoing transactions for all frontier addresses
        # -------------------------------------------------------------------
        async def fetch_one(address: str):
            async with semaphore:
                # Check API call limit inside semaphore
                if ctx.api_call_count >= MAX_API_CALLS:
                    return (address, None, "api_limit")
                
                # Check cache first
                cached = await db.get_cached_transactions(
                    address=address,
                    direction="outgoing",
                    window_start=window_start,
                    window_end=window_end,
                    cache_ttl_hours=CACHE_TTL_HOURS,
                )
                if cached is not None:
                    return (address, cached, None)

                # Fetch from TronGrid
                ctx.api_call_count += 1
                result = await fetch_with_retry(address, window_start, window_end)

                if result.success:
                    await db.cache_transactions(address, result.data, window_start, window_end)
                    return (address, result.data, None)
                else:
                    return (address, None, result.error)

        fetch_results = await asyncio.gather(
            *[fetch_one(addr) for addr in frontier],
            return_exceptions=True,
        )

        # -------------------------------------------------------------------
        # STEP 2b: Handle fetch failures
        # -------------------------------------------------------------------
        hop_total = len(frontier)
        hop_failures = 0
        address_txs: dict[str, list] = {}  # address → [raw transactions]

        for result in fetch_results:
            if isinstance(result, Exception):
                hop_failures += 1
                ctx.fetch_failures += 1
                continue

            address, txs, error = result
            if error:
                hop_failures += 1
                ctx.fetch_failures += 1
                # Mark node as fetch_failed
                if address in ctx.graph:
                    ctx.graph.nodes[address]["node_type"] = "fetch_failed"
                continue

            address_txs[address] = txs

        # Abort if >50% failures
        if hop_total > 0 and (hop_failures / hop_total) > 0.50:
            ctx.abort_reason = f"fetch_failure_rate={hop_failures/hop_total:.2%} at hop={current_hop}"
            await save_partial_results(ctx, db)
            return build_trace_result(ctx, "TRACE_FAILED", start_time)

        # -------------------------------------------------------------------
        # STEP 2c: Apply pruning filters to each transaction
        # -------------------------------------------------------------------
        next_frontier: list[str] = []

        for address in frontier:
            if address not in address_txs:
                continue  # Fetch failed for this address

            outgoing_txs = address_txs[address]

            # --- FILTER 4 CHECK (Degree Cap) ---
            # Check degree BEFORE iterating individual transactions
            if len(outgoing_txs) > config.degree_cap:
                ctx.graph.nodes[address]["node_type"] = "vasp_candidate"
                ctx.graph.nodes[address]["degree_capped"] = True
                ctx.degree_capped_addrs.append(address)
                # Mark ALL outgoing as pruned with reason "degree_cap"
                for tx in outgoing_txs:
                    edge_data = parse_transaction(tx, current_hop, trx_usdt_rate)
                    edge_data["pruned"] = True
                    edge_data["prune_reason"] = "degree_cap"
                    await db.insert_graph_edge(ctx.case_id, edge_data)
                    ctx.pruning_counts["degree_cap"] += 1
                continue  # Skip to next address in frontier

            # --- Process each transaction individually ---
            for tx in outgoing_txs:
                edge_data = parse_transaction(tx, current_hop, trx_usdt_rate)
                pruned = False
                prune_reason = None

                # FILTER 2: Amount Relevance
                if not pruned:
                    usdt_amount = normalize_to_usdt(edge_data["amount"], edge_data["token"], trx_usdt_rate)
                    if usdt_amount < amount_threshold:
                        pruned = True
                        prune_reason = "amount_below_threshold"
                        ctx.pruning_counts["amount_below_threshold"] += 1

                # FILTER 3: Time Window
                if not pruned:
                    tx_ts = edge_data["timestamp"]
                    if not (window_start <= tx_ts <= window_end):
                        pruned = True
                        prune_reason = "time_window"
                        ctx.pruning_counts["time_window"] += 1

                # FILTER 5: Path Continuity (only for hop >= 2)
                if not pruned and current_hop >= 2:
                    incoming_list = ctx.incoming_txs.get(address, [])
                    if incoming_list:
                        earliest_in = min(itx["timestamp"] for itx in incoming_list)
                        latest_in = max(itx["timestamp"] for itx in incoming_list)
                        cont_start = earliest_in
                        cont_end = latest_in + timedelta(hours=PATH_CONTINUITY_HOURS)
                        if not (cont_start <= edge_data["timestamp"] <= cont_end):
                            pruned = True
                            prune_reason = "path_discontinuity"
                            ctx.pruning_counts["path_discontinuity"] += 1

                # FILTER 6: Duplicate Removal
                if not pruned:
                    tx_hash = edge_data["tx_hash"]
                    if tx_hash in ctx.kept_tx_hashes:
                        existing_hop = ctx.kept_tx_hashes[tx_hash]
                        if existing_hop <= current_hop:
                            # Existing is at same or shorter path — prune current
                            pruned = True
                            prune_reason = "duplicate"
                            ctx.pruning_counts["duplicate"] += 1
                        else:
                            # Current path is shorter — prune old, keep new
                            await db.mark_edge_pruned(ctx.case_id, tx_hash, "duplicate")
                            ctx.kept_tx_hashes[tx_hash] = current_hop
                            # (Don't set pruned — this one is kept)

                    # Duplicate path check (same to_address at same hop)
                    if not pruned:
                        to_addr = edge_data["to_address"]
                        if to_addr in ctx.global_visited and ctx.global_visited[to_addr] == current_hop:
                            # Already reached at this hop — compare edge amounts
                            existing_edges = [
                                e for e in ctx.graph.in_edges(to_addr, data=True)
                                if e[2].get("hop") == current_hop and not e[2].get("pruned", False)
                            ]
                            if existing_edges:
                                best_existing_amount = max(e[2]["amount"] for e in existing_edges)
                                if edge_data["amount"] <= best_existing_amount:
                                    pruned = True
                                    prune_reason = "duplicate"
                                    ctx.pruning_counts["duplicate"] += 1
                                else:
                                    # Current edge has higher amount — prune old
                                    for e in existing_edges:
                                        ctx.graph.edges[e[0], e[1]]["pruned"] = True
                                        ctx.graph.edges[e[0], e[1]]["prune_reason"] = "duplicate"
                                        await db.mark_edge_pruned(ctx.case_id, e[2]["tx_hash"], "duplicate")
                                    ctx.pruning_counts["duplicate"] += len(existing_edges)

                # --- Record edge ---
                edge_data["pruned"] = pruned
                edge_data["prune_reason"] = prune_reason

                if pruned:
                    await db.insert_graph_edge(ctx.case_id, edge_data)
                    continue

                # --- Edge is KEPT ---
                to_addr = edge_data["to_address"]
                ctx.kept_tx_hashes[edge_data["tx_hash"]] = current_hop

                # Cycle detection
                if to_addr in ctx.global_visited:
                    edge_data["cycle_detected"] = True
                    ctx.cycles.append({
                        "from": address,
                        "to": to_addr,
                        "tx_hash": edge_data["tx_hash"],
                        "hop": current_hop,
                        "target_original_hop": ctx.global_visited[to_addr],
                    })
                    # Add edge but do NOT add to_addr to next_frontier
                    ctx.graph.add_edge(address, to_addr, **edge_data)
                    await db.insert_graph_edge(ctx.case_id, edge_data)
                    continue

                # Add edge and discover new address
                ctx.graph.add_edge(address, to_addr, **edge_data)
                await db.insert_graph_edge(ctx.case_id, edge_data)

                # Record as incoming tx for the target (for path continuity at next hop)
                if to_addr not in ctx.incoming_txs:
                    ctx.incoming_txs[to_addr] = []
                ctx.incoming_txs[to_addr].append(edge_data)

                # Add new node
                ctx.global_visited[to_addr] = current_hop
                vasp_label = await db.lookup_vasp_label(to_addr)
                ctx.graph.add_node(to_addr,
                    address=to_addr,
                    hop=current_hop,
                    node_type="vasp_candidate" if vasp_label else "intermediate",
                    vasp_label=vasp_label,
                    in_degree=0,
                    out_degree=0,
                    total_inflow=Decimal("0"),
                    total_outflow=Decimal("0"),
                    first_seen_at=edge_data["timestamp"],
                    degree_capped=False,
                )

                # Only add to next frontier if we haven't hit the hop limit
                if current_hop < config.hop_limit:
                    next_frontier.append(to_addr)

                # Node limit check
                if ctx.graph.number_of_nodes() >= MAX_ADDRESSES:
                    ctx.truncated = True
                    ctx.abort_reason = "max_addresses_exceeded"
                    break

            if ctx.truncated:
                break

        frontier = list(set(next_frontier))  # Deduplicate

    # -----------------------------------------------------------------------
    # STEP 3: Post-processing — compute aggregates
    # -----------------------------------------------------------------------
    for node_addr in ctx.graph.nodes():
        node = ctx.graph.nodes[node_addr]
        # In-degree and out-degree (non-pruned edges only)
        in_edges = [
            e for e in ctx.graph.in_edges(node_addr, data=True)
            if not e[2].get("pruned", False)
        ]
        out_edges = [
            e for e in ctx.graph.out_edges(node_addr, data=True)
            if not e[2].get("pruned", False)
        ]
        node["in_degree"] = len(in_edges)
        node["out_degree"] = len(out_edges)
        node["total_inflow"] = sum(e[2]["amount"] for e in in_edges)
        node["total_outflow"] = sum(e[2]["amount"] for e in out_edges)

        # first_seen_at
        all_ts = (
            [e[2]["timestamp"] for e in in_edges] +
            [e[2]["timestamp"] for e in out_edges]
        )
        node["first_seen_at"] = min(all_ts) if all_ts else None

    # -----------------------------------------------------------------------
    # STEP 4: Persist nodes to DB
    # -----------------------------------------------------------------------
    for node_addr in ctx.graph.nodes():
        node_data = ctx.graph.nodes[node_addr]
        await db.insert_graph_node(ctx.case_id, node_data)

    # -----------------------------------------------------------------------
    # STEP 5: Build and return result
    # -----------------------------------------------------------------------
    return build_trace_result(ctx, "COMPLETED", start_time)


def build_trace_result(ctx: TraceContext, status: str, start_time: datetime) -> TraceResult:
    """Assemble the final TraceResult with metadata and Cytoscape JSON."""
    elapsed = (datetime.utcnow() - start_time).total_seconds()

    total_kept = sum(
        1 for _, _, d in ctx.graph.edges(data=True) if not d.get("pruned", False)
    )
    total_pruned = sum(ctx.pruning_counts.values())

    metadata = {
        "trace_id": generate_uuid(),
        "started_at": start_time.isoformat() + "Z",
        "completed_at": datetime.utcnow().isoformat() + "Z",
        "elapsed_seconds": round(elapsed, 2),
        "status": status,
        "truncated": ctx.truncated,
        "abort_reason": ctx.abort_reason,
        "seed_wallets": ctx.seed_wallets,
        "hop_limit": ctx.config.hop_limit,
        "amount_threshold": float(
            max(
                (ctx.reported_amount or Decimal("0")) * AMOUNT_RELEVANCE_PERCENT,
                AMOUNT_ABSOLUTE_MIN,
            )
        ),
        "time_window": {
            "start": (ctx.reported_at - timedelta(days=ctx.config.time_window_before_days)).isoformat() + "Z",
            "end": (ctx.reported_at + timedelta(days=ctx.config.time_window_after_days)).isoformat() + "Z",
        },
        "trx_usdt_rate": None,  # Set by caller
        "total_fetched": total_kept + total_pruned,
        "total_pruned": total_pruned,
        "total_kept": total_kept,
        "pruning_breakdown": dict(ctx.pruning_counts),
        "nodes_count": ctx.graph.number_of_nodes(),
        "edges_count": total_kept,
        "cycles_detected": len(ctx.cycles),
        "cycles": ctx.cycles,
        "fetch_failures": ctx.fetch_failures,
        "api_calls_made": ctx.api_call_count,
        "degree_capped_addresses": ctx.degree_capped_addrs,
        "vasp_candidates": [
            addr for addr, data in ctx.graph.nodes(data=True)
            if data.get("node_type") == "vasp_candidate"
        ],
    }

    cytoscape_json = build_cytoscape_json(ctx.graph)

    return TraceResult(
        status=status,
        trace_nodes=[ctx.graph.nodes[n] for n in ctx.graph.nodes()],
        trace_edges=[
            d for _, _, d in ctx.graph.edges(data=True)
            if not d.get("pruned", False)
        ],
        pruned_edges=[
            d for _, _, d in ctx.graph.edges(data=True)
            if d.get("pruned", False)
        ],
        trace_metadata=metadata,
        cytoscape_json=cytoscape_json,
    )


def build_cytoscape_json(
    graph: nx.DiGraph,
    metadata: dict | None = None,
    include_pruned: bool = False,
) -> dict:
    """Serialize the graph into the API_CONTRACT §2.6 Cytoscape JSON format."""
    nodes = []
    for addr, data in graph.nodes(data=True):
        nodes.append({
            "data": {
                "id": addr,
                "label": short_label(addr),
                "type": data.get("node_type", "intermediate"),
                "hop_depth": data.get("hop", 0),
                "in_degree": data.get("in_degree", 0),
                "out_degree": data.get("out_degree", 0),
                "total_received": float(data.get("total_inflow", 0)),
                "total_sent": float(data.get("total_outflow", 0)),
                "vasp_label": data.get("vasp_label"),
                "vasp_confidence": data.get("vasp_confidence"),
            }
        })

    edges = []
    for src, dst, data in graph.edges(data=True):
        is_pruned = data.get("pruned", False)
        if is_pruned and not include_pruned:
            continue
        edges.append({
            "data": {
                "id": data["tx_hash"],
                "source": src,
                "target": dst,
                "amount": float(data["amount"]),
                "token": data["token"],
                "timestamp": data["timestamp"].isoformat() + "Z" if isinstance(data["timestamp"], datetime) else data["timestamp"],
                "hop_depth": data["hop"],
                "pruned": is_pruned,
                "prune_reason": data.get("prune_reason"),
            }
        })

    return {"nodes": nodes, "edges": edges, "metadata": metadata}


def short_label(address: str) -> str:
    """Generate a short display label: first 4 + '...' + last 4 characters."""
    if len(address) <= 11:
        return address
    return f"{address[:4]}...{address[-4:]}"


def parse_transaction(raw_tx: dict, hop: int, trx_usdt_rate: Decimal) -> dict:
    """Parse a raw TronGrid transaction response into a normalized edge dict."""
    # TRC-20 transfer event structure:
    # {
    #   "transaction_id": "hex_hash",
    #   "token_info": {"symbol": "USDT", "address": "TR7N...", "decimals": 6},
    #   "from": "T...",
    #   "to": "T...",
    #   "value": "1000000",        # Raw integer (sun for USDT = 10^6)
    #   "block_timestamp": 1698765432000,  # Milliseconds
    #   "type": "Transfer"
    # }
    decimals = int(raw_tx.get("token_info", {}).get("decimals", 6))
    raw_value = Decimal(raw_tx.get("value", "0"))
    amount = raw_value / (Decimal(10) ** decimals)

    return {
        "tx_hash": raw_tx["transaction_id"],
        "from_address": raw_tx["from"],
        "to_address": raw_tx["to"],
        "amount": amount,
        "token": raw_tx.get("token_info", {}).get("symbol", "UNKNOWN"),
        "token_contract": raw_tx.get("token_info", {}).get("address", ""),
        "timestamp": datetime.utcfromtimestamp(raw_tx["block_timestamp"] / 1000),
        "block_number": raw_tx.get("block", 0),
        "hop": hop,
        "pruned": False,
        "prune_reason": None,
        "cycle_detected": False,
        "incoming_tx_hash": None,  # Set by caller for path continuity
    }


def normalize_to_usdt(amount: Decimal, token: str, trx_usdt_rate: Decimal) -> Decimal:
    """Convert an amount to USDT equivalent for comparison."""
    if token == "USDT":
        return amount
    elif token == "TRX":
        return amount * trx_usdt_rate
    else:
        # Unknown token — treat as 0 (will be pruned by amount filter)
        return Decimal("0")


def is_valid_tron_address(address: str) -> bool:
    """Validate a TRON Base58 address: starts with 'T', 34 chars, Base58 charset."""
    if not address or len(address) != 34 or not address.startswith("T"):
        return False
    base58_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    return all(c in base58_chars for c in address)


def clamp(value: int, min_val: int, max_val: int) -> int:
    return max(min_val, min(value, max_val))
```

---

## 10. Data Structures Reference

### 10.1 `FetchResult`

```python
@dataclass
class FetchResult:
    success: bool
    data: list[dict] | None = None     # List of raw TronGrid transaction dicts
    error: str | None = None           # Error description if success=False
```

### 10.2 `TraceResult`

```python
@dataclass
class TraceResult:
    status: Literal["COMPLETED", "TRACE_FAILED"]
    trace_nodes: list[dict]            # Node attribute dicts
    trace_edges: list[dict]            # Kept edge attribute dicts
    pruned_edges: list[dict]           # Pruned edge attribute dicts
    trace_metadata: dict               # JSON-serializable metadata (§8.2)
    cytoscape_json: dict               # Cytoscape.js JSON (§8.3)
```

### 10.3 `TraceConfig`

```python
@dataclass
class TraceConfig:
    hop_limit: int             # Range: 1–5, Default: 3
    time_window_before_days: int  # Range: 1–365, Default: 30
    time_window_after_days: int   # Range: 0–90, Default: 7
    degree_cap: int            # Range: 10–1000, Default: 100
```

---

## 11. Configuration Reference

All configuration values in one table for quick reference:

| Parameter | Location | Type | Default | Min | Max | Hardcoded? |
|---|---|---|---|---|---|---|
| `hop_limit` | `trace_config` JSONB | `int` | `3` | `1` | `5` | No |
| `time_window_before_days` | `trace_config` JSONB | `int` | `30` | `1` | `365` | No |
| `time_window_after_days` | `trace_config` JSONB | `int` | `7` | `0` | `90` | No |
| `degree_cap` | `trace_config` JSONB | `int` | `100` | `10` | `1000` | No |
| Amount relevance % | Constant | `Decimal` | `0.01` | — | — | Yes |
| Amount absolute min | Constant | `Decimal` | `10.0` USDT | — | — | Yes |
| Path continuity tolerance | Constant | `int` | `72` hours | — | — | Yes |
| Cache TTL | Constant | `int` | `24` hours | — | — | Yes |
| Max addresses per trace | Constant | `int` | `500` | — | — | Yes |
| Max API calls per trace | Constant | `int` | `200` | — | — | Yes |
| Max concurrent requests | Constant | `int` | `10` | — | — | Yes |
| TRX/USDT fallback rate | Constant | `Decimal` | `0.10` | — | — | Yes |
| Retry base delay | Constant | `float` | `1.0` s | — | — | Yes |
| Retry max (429) | Constant | `int` | `3` | — | — | Yes |
| Retry max (5xx) | Constant | `int` | `1` | — | — | Yes |
| Request timeout | Constant | `float` | `10.0` s | — | — | Yes |
| Fetch failure abort threshold | Constant | `float` | `0.50` (50%) | — | — | Yes |
| USDT contract address | Constant | `str` | `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` | — | — | Yes |

---

## Appendix: Worked Example

### Scenario

- **Complaint:** Victim reports losing **50,000 USDT** to address `TNpS8xYnzLSm1XgKMs5HYv8zFHXPWgGqHF`
- **Reported at:** `2026-10-20T00:00:00Z`
- **Config:** `hop_limit=3`, `degree_cap=100`, defaults for everything else

### Computed Parameters

```
amount_threshold = max(50000 * 0.01, 10.0) = 500.0 USDT
window_start = 2026-10-20 - 30 days = 2026-09-20T00:00:00Z
window_end = 2026-10-20 + 7 days = 2026-10-27T00:00:00Z
```

### BFS Execution

```
HOP 0: Seed = [TSeed...A]

HOP 1: Fetch outgoing for TSeed...A
  Found 5 outgoing transactions:
    tx1: TSeed...A → TAddr...B, 20000 USDT, 2026-10-18T10:00Z  → KEPT (20000 ≥ 500)
    tx2: TSeed...A → TAddr...C, 15000 USDT, 2026-10-18T10:05Z  → KEPT
    tx3: TSeed...A → TAddr...D, 10000 USDT, 2026-10-18T10:10Z  → KEPT
    tx4: TSeed...A → TAddr...E,   200 USDT, 2026-10-18T10:15Z  → PRUNED (amount: 200 < 500)
    tx5: TSeed...A → TAddr...F,  4800 USDT, 2026-10-18T10:20Z  → KEPT
  Frontier for hop 2: [TAddr...B, TAddr...C, TAddr...D, TAddr...F]

HOP 2: Fetch outgoing for each frontier address
  TAddr...B: 3 outgoing transactions
    tx6: TAddr...B → TAddr...G, 19500 USDT, 2026-10-18T12:00Z
         Path continuity: incoming tx1 at 10:00, outgoing at 12:00 → 2h < 72h → KEPT
    tx7: TAddr...B → TAddr...H, 500 USDT, 2026-10-18T12:05Z     → KEPT (500 = 500)

  TAddr...C: 150 outgoing transactions → DEGREE CAPPED (150 > 100)
    TAddr...C marked as vasp_candidate, all 150 edges pruned with reason "degree_cap"

  TAddr...D: 2 outgoing transactions
    tx8: TAddr...D → TAddr...I, 9500 USDT, 2026-10-18T14:00Z    → KEPT
    tx9: TAddr...D → TSeed...A, 500 USDT, 2026-10-18T14:30Z     → KEPT but CYCLE (back to seed)

  TAddr...F: 1 outgoing transaction
    tx10: TAddr...F → TAddr...J, 4000 USDT, 2026-10-25T10:00Z
         Path continuity: incoming tx5 at 10:20 Oct 18, outgoing at 10:00 Oct 25
         Difference = ~6.98 days = 167.7 hours > 72h → PRUNED (path_discontinuity)

  Frontier for hop 3: [TAddr...G, TAddr...H, TAddr...I]

HOP 3: Fetch outgoing (last hop — recipients won't be added to frontier)
  TAddr...G: 1 outgoing
    tx11: TAddr...G → TBinance, 19000 USDT, 2026-10-18T14:00Z   → KEPT
         TBinance matched in VASP DB → vasp_label="Binance", node_type="vasp_candidate"

  TAddr...H: 0 outgoing → no edges

  TAddr...I: 1 outgoing
    tx12: TAddr...I → TAddr...G, 9000 USDT, 2026-10-18T16:00Z
         TAddr...G already visited at hop 2 → CYCLE DETECTED, edge added, not traversed

BFS COMPLETE.
```

### Result Summary

```
Nodes: 10 (1 seed + 7 intermediate + 1 vasp_candidate[degree_capped] + 1 vasp_candidate[Binance])
Kept edges: 8 (tx1, tx2, tx3, tx5, tx6, tx7, tx8, tx11) + 2 cycle edges (tx9, tx12)
Pruned edges: 152 (1 amount + 150 degree_cap + 1 path_discontinuity)
Cycles detected: 2
Fetch failures: 0
```

### Cytoscape Output (abbreviated illustrative excerpt — see `API_CONTRACT.md` §2.6 for full schema)

```json
{
  "nodes": [
    {"data": {"id": "TSeed...A", "label": "TSee...111A", "type": "seed", "hop_depth": 0, "vasp_label": null}},
    {"data": {"id": "TAddr...B", "label": "TAdd...rB", "type": "intermediate", "hop_depth": 1, "vasp_label": null}},
    {"data": {"id": "TAddr...C", "label": "TAdd...rC", "type": "vasp_candidate", "hop_depth": 1, "vasp_label": null}},
    {"data": {"id": "TBinance", "label": "TBin...nce", "type": "vasp_candidate", "hop_depth": 3, "vasp_label": "Binance"}}
  ],
  "edges": [
    {"data": {"id": "tx1", "source": "TSeed...A", "target": "TAddr...B", "amount": 20000.0, "token": "USDT", "timestamp": "2026-10-18T10:00:00Z", "hop_depth": 1, "pruned": false, "prune_reason": null}},
    {"data": {"id": "tx9", "source": "TAddr...D", "target": "TSeed...A", "amount": 500.0, "token": "USDT", "timestamp": "2026-10-18T14:30:00Z", "hop_depth": 2, "pruned": false, "prune_reason": null}}
  ],
  "metadata": {"total_fetched": 160, "total_pruned": 152, "cycles_detected": 2}
}
```

---

> [!NOTE]
> This specification targets MVP (SIH 2026 demo). Post-MVP enhancements include:
> - Multi-chain support (Ethereum, BSC)
> - Heuristic clustering (change-address detection)
> - Weighted BFS (prioritize higher-amount paths)
> - Incremental re-tracing (only fetch new transactions since last trace)
> - Graph diffing (compare two traces of the same case)
