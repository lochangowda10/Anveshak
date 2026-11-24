# ANVESHAK — Product Specification

> **Version**: 1.0.0-MVP  
> **Last Updated**: 2026-11-24  
> **Status**: APPROVED  
> **Audience**: AI implementation agents, human reviewers  

---

## 1. Product Overview

ANVESHAK is a complaint-to-action crypto investigation workflow for Indian law enforcement, built for SIH 2026. It transforms a victim's complaint and seed wallet address into a court-ready action package by tracing TRON blockchain fund flows, pruning the transaction graph, ranking VASP endpoints, assembling evidence, and exporting PDF/JSON bundles.

### 1.1 Pipeline Summary

```
Victim Complaint → Seed Wallet → TRON Blockchain Tracing → Raw Graph
→ Pruned Graph (6 filters) → VASP Ranking → Evidence Assembly → Action Package (PDF + JSON)
```

### 1.2 Tech Stack

| Layer | Technology | Version (minimum) |
|---|---|---|
| Backend API | FastAPI (Python) | 0.104+ |
| Database | PostgreSQL | 15+ |
| Migrations | Alembic | 1.12+ |
| Graph Engine | NetworkX | 3.2+ |
| Blockchain API | TronGrid REST API | v1 |
| Frontend | React | 18+ |
| Graph Visualization | Cytoscape.js | 3.28+ |
| Containerization | Docker + Docker Compose | 24+ / 2.23+ |
| PDF Generation | ReportLab or WeasyPrint | latest |

---

## 2. User Roles

### 2.1 Role Definitions

| Role | Slug | Description |
|---|---|---|
| Investigating Officer | `investigating_officer` | Creates cases, initiates traces, reviews evidence, approves/rejects VASP candidates, downloads action packages. Primary user. |
| Administrator | `admin` | Manages VASP label store (CRUD on known VASP addresses), configures system settings (hop limits, API keys), manages user accounts. |
| Viewer | `viewer` | Read-only access to all cases and evidence. Intended for supervisors and oversight roles. Cannot create, modify, or export. |

### 2.2 Permission Matrix

| Action | `investigating_officer` | `admin` | `viewer` |
|---|---|---|---|
| List cases | ✅ | ✅ | ✅ |
| View case detail | ✅ | ✅ | ✅ |
| Create case | ✅ | ✅ | ❌ |
| Update case metadata | ✅ | ✅ | ❌ |
| Initiate trace | ✅ | ✅ | ❌ |
| View graph | ✅ | ✅ | ✅ |
| Approve/reject VASP candidate | ✅ | ✅ | ❌ |
| Export action package | ✅ | ✅ | ❌ |
| Close case | ✅ | ✅ | ❌ |
| Manage VASP label store | ❌ | ✅ | ❌ |
| Manage system settings | ❌ | ✅ | ❌ |
| Manage users | ❌ | ✅ | ❌ |

### 2.3 MVP Authentication Strategy

> [!IMPORTANT]
> **For MVP, there is NO authentication or authorization.** All API endpoints are unprotected. Every request is treated as if made by a user with the `investigating_officer` role. The permission matrix above is documented for Phase 2 implementation. No login screen, no JWT, no session management in MVP.

**Phase 2 additions** (out of scope for MVP):
- JWT-based authentication with refresh tokens
- Role-based access control middleware
- User management CRUD endpoints (admin only)
- Audit log of user actions

---

## 3. Features (MVP Scope)

### 3.1 Case Management

#### 3.1.1 Case Creation

- **What**: Create a new investigation case by entering victim complaint details and one or more seed wallet addresses.
- **Inputs**: victim name, complaint ID, description, seed wallets (1–10), optional tags.
- **Output**: A `Case` record in state `PENDING`.
- **API**: `POST /api/v1/cases`

#### 3.1.2 Case Listing

- **What**: Paginated list of all cases with filters.
- **Filters**: `status` (enum), `created_after` (ISO 8601 datetime), `created_before` (ISO 8601 datetime), `search` (free-text search over `complaint_id`, `victim_name`, `description`).
- **Sort**: `created_at` DESC (default), `updated_at`, `victim_name`.
- **Pagination**: cursor-based using `case_id`. Query params: `limit` (int, default 20, max 100), `cursor` (UUID, optional).
- **API**: `GET /api/v1/cases`

#### 3.1.3 Case Detail View

- **What**: Full case record including associated trace results, graph summary stats, and VASP candidates.
- **API**: `GET /api/v1/cases/{case_id}`

#### 3.1.4 Case Status Update

- **What**: Transition case status per the state machine (§6).
- **API**: `PATCH /api/v1/cases/{case_id}/status`
- **Body**: `{ "status": "<new_status>" }`

### 3.2 Blockchain Tracing

#### 3.2.1 Initiate Trace

- **What**: For a given case, crawl the TRON blockchain starting from each seed wallet up to N hops (configurable, default 3, max 5).
- **Trigger**: `POST /api/v1/cases/{case_id}/trace`
- **Body**: `{ "max_hops": 3 }` (optional override; default from system settings)
- **Precondition**: Case status must be `PENDING` or `TRACED` (re-trace allowed). Transitions to `TRACING`.
- **Process**:
  1. For each seed wallet, fetch all TRC-20 (USDT primarily) and TRX transfer transactions via TronGrid API.
  2. For each counterparty address discovered, recursively fetch transactions up to `max_hops`.
  3. Build a directed graph: nodes = addresses, edges = transactions.
  4. Store raw graph data (nodes, edges) in PostgreSQL.
  5. On success, transition case status to `TRACED`.
  6. On failure (API error, timeout), transition to `TRACE_FAILED` with error details.
- **Concurrency**: Only one active trace per case at a time. If a trace is already running (`status == TRACING`), return HTTP 409.
- **Background execution**: Tracing runs as a background task (FastAPI `BackgroundTasks` or Celery). The endpoint returns HTTP 202 immediately with a `trace_id`.

#### 3.2.2 Trace Status Polling

- **What**: Check progress of an active or completed trace.
- **API**: `GET /api/v1/cases/{case_id}/trace`
- **Response fields**: `trace_id`, `status` (RUNNING | COMPLETED | FAILED), `started_at`, `completed_at`, `hops_completed`, `total_nodes`, `total_edges`, `error_message` (nullable).

### 3.3 Graph Visualization

#### 3.3.1 Get Graph Data

- **What**: Return the pruned graph for frontend rendering.
- **API**: `GET /api/v1/cases/{case_id}/graph`
- **Query params**: All 6 pruning filter parameters (see §3.4). If omitted, system defaults apply.
- **Response**: JSON object with `nodes` array and `edges` array in Cytoscape.js-compatible format.

```json
{
  "case_id": "uuid",
  "filter_params": { ... },
  "stats": {
    "total_nodes": 142,
    "total_edges": 387,
    "pruned_nodes": 28,
    "pruned_edges": 45
  },
  "nodes": [
    {
      "data": {
        "id": "TXyz...abc",
        "label": "TXyz...abc",
        "type": "address",
        "is_seed": true,
        "is_vasp": false,
        "vasp_label": null,
        "hop_distance": 0,
        "total_inflow_sun": 150000000000,
        "total_outflow_sun": 148500000000,
        "tx_count": 23,
        "first_seen": "2026-01-15T08:30:00Z",
        "last_seen": "2026-03-20T14:22:00Z"
      }
    }
  ],
  "edges": [
    {
      "data": {
        "id": "edge_<tx_hash>",
        "source": "TXyz...abc",
        "target": "TAbc...xyz",
        "tx_hash": "a1b2c3...64hex",
        "amount_sun": 50000000,
        "amount_display": "50.000000",
        "token": "TRX",
        "contract_address": null,
        "timestamp": "2026-02-10T12:00:00Z",
        "block_number": 58234567,
        "hop_number": 1
      }
    }
  ]
}
```

> [!NOTE]
> All amounts are stored internally in **SUN** (1 TRX = 1,000,000 SUN; 1 USDT on TRON = 1,000,000 SUN equivalent based on token decimals). The `amount_display` field is the human-readable decimal string.

### 3.4 Graph Pruning

The raw transaction graph can be enormous. Six filters are applied server-side before returning the graph. Each filter can be independently enabled/disabled and parameterized.

#### 3.4.1 Filter Definitions

| # | Filter Name | Slug | Parameter(s) | Type | Default | Description |
|---|---|---|---|---|---|---|
| 1 | Hop Limit | `hop_limit` | `max_hops` | int | 3 | Remove all nodes/edges beyond this many hops from any seed wallet. Range: 1–5. |
| 2 | Amount Relevance | `amount_relevance` | `min_amount_sun` | int | 1000000 (1 TRX) | Remove edges where `amount_sun < min_amount_sun`. Eliminates dust transactions. |
| 3 | Time Window | `time_window` | `start_time`, `end_time` | ISO 8601 strings | null (no filter) | Keep only edges with `timestamp` within `[start_time, end_time]`. Both bounds inclusive. |
| 4 | Degree Cap | `degree_cap` | `max_degree` | int | 50 | Remove nodes with in-degree + out-degree > `max_degree`. Eliminates exchange hot wallets and high-volume relay addresses. |
| 5 | Path Continuity | `path_continuity` | `enabled` | bool | true | Remove nodes that are NOT on any path from a seed wallet to a leaf (terminal) node. Ensures all displayed nodes participate in a fund-flow path. |
| 6 | Deduplication | `dedup` | `enabled` | bool | true | Collapse multiple edges between the same (source, target) pair within the same 1-hour window into a single edge with `amount_sun` = sum, `tx_count` = count, `tx_hashes` = list. |

#### 3.4.2 Filter Application Order

Filters MUST be applied in the following strict order:

1. **Hop Limit** — reduces breadth
2. **Time Window** — reduces temporal scope
3. **Amount Relevance** — removes dust
4. **Degree Cap** — removes hub nodes
5. **Path Continuity** — removes orphaned subgraphs
6. **Deduplication** — compresses multi-edges

#### 3.4.3 Filter API Contract

Filters are passed as query parameters on `GET /api/v1/cases/{case_id}/graph`:

```
GET /api/v1/cases/{case_id}/graph?max_hops=3&min_amount_sun=1000000&start_time=2026-01-01T00:00:00Z&end_time=2026-06-01T00:00:00Z&max_degree=50&path_continuity=true&dedup=true
```

All parameters are optional. Omitted parameters use defaults.

### 3.5 VASP Endpoint Ranking

#### 3.5.1 Definition

A **VASP candidate** is any leaf node (terminal address) in the pruned graph that either:
- (a) Matches a known VASP address in the VASP label store, OR
- (b) Has characteristics suggesting it is a custodial endpoint (high in-degree from many unique sources, large aggregate inflow).

#### 3.5.2 Scoring Formula

Each VASP candidate receives a **confidence score** in range `[0.0, 1.0]` computed as:

```
confidence = (w1 * label_match) + (w2 * norm_amount) + (w3 * norm_path_count) + (w4 * norm_in_degree) + (w5 * recency_score)
```

| Factor | Variable | Weight | Type | Computation |
|---|---|---|---|---|
| Known VASP Label Match | `label_match` | `w1 = 0.35` | float {0.0, 1.0} | 1.0 if address exists in VASP label store, else 0.0 |
| Normalized Amount | `norm_amount` | `w2 = 0.25` | float [0.0, 1.0] | `total_inflow_sun / max_inflow_sun_across_all_candidates` |
| Normalized Path Count | `norm_path_count` | `w3 = 0.20` | float [0.0, 1.0] | `paths_from_seeds / max_paths_across_all_candidates` |
| Normalized In-Degree | `norm_in_degree` | `w4 = 0.10` | float [0.0, 1.0] | `in_degree / max_in_degree_across_all_candidates` |
| Recency Score | `recency_score` | `w5 = 0.10` | float [0.0, 1.0] | `1.0 - (days_since_last_tx / max_days_across_all_candidates)`, clamped to [0.0, 1.0] |

> [!IMPORTANT]
> If only one candidate exists, all normalized values that would result in `0/0` are set to `1.0`. If zero candidates exist, the VASP ranking result is an empty list and the case transitions to `ANALYZED` with a warning flag `no_vasp_candidates = true`.

#### 3.5.3 Trigger VASP Analysis

- **API**: `POST /api/v1/cases/{case_id}/analyze`
- **Precondition**: Case status must be `TRACED`.
- **Process**: Runs pruning (with current/default filter params) → identifies leaf nodes → scores each → stores ranked list → transitions status to `ANALYZED`.
- **On failure**: Transitions to `ANALYSIS_FAILED`.

#### 3.5.4 Get VASP Candidates

- **API**: `GET /api/v1/cases/{case_id}/candidates`
- **Response**:

```json
{
  "case_id": "uuid",
  "candidates": [
    {
      "candidate_id": "uuid",
      "address": "TVasp...xyz",
      "vasp_label": "WazirX",
      "confidence_score": 0.87,
      "score_breakdown": {
        "label_match": 1.0,
        "norm_amount": 0.72,
        "norm_path_count": 0.65,
        "norm_in_degree": 0.40,
        "recency_score": 0.90
      },
      "total_inflow_sun": 95000000000,
      "total_inflow_display": "95000.000000",
      "path_count": 5,
      "in_degree": 12,
      "last_tx_time": "2026-03-18T09:15:00Z",
      "status": "pending",
      "officer_notes": null
    }
  ],
  "warnings": {
    "no_vasp_candidates": false
  }
}
```

#### 3.5.5 Approve/Reject Candidate

- **API**: `PATCH /api/v1/cases/{case_id}/candidates/{candidate_id}`
- **Body**: `{ "status": "approved" | "rejected", "officer_notes": "string (max 2000 chars)" }`
- **Constraint**: Only candidates in status `pending` can be transitioned. Valid transitions: `pending → approved`, `pending → rejected`.

### 3.6 Evidence Assembly

#### 3.6.1 Evidence Trail per Candidate

For each approved VASP candidate, the system assembles an evidence record containing:

| Field | Type | Description |
|---|---|---|
| `candidate_id` | UUID | Reference to the VASP candidate |
| `address` | string | The VASP candidate address |
| `vasp_label` | string \| null | Known VASP label if matched |
| `seed_wallets` | string[] | List of seed wallets that have paths to this candidate |
| `paths` | Path[] | Ordered list of fund-flow paths from seed to candidate |
| `total_amount_sun` | int | Sum of all transaction amounts across all paths |
| `total_amount_display` | string | Human-readable decimal |
| `first_tx_time` | ISO 8601 | Earliest transaction timestamp in any path |
| `last_tx_time` | ISO 8601 | Latest transaction timestamp in any path |
| `confidence_score` | float | VASP confidence score |
| `provenance` | Provenance | Data source and retrieval metadata |

**Path** object:

```json
{
  "path_index": 0,
  "hops": [
    {
      "from_address": "TSeed...abc",
      "to_address": "TInter...def",
      "tx_hash": "aabb...64hex",
      "amount_sun": 50000000,
      "amount_display": "50.000000",
      "token": "USDT",
      "timestamp": "2026-02-10T12:00:00Z",
      "block_number": 58234567
    }
  ],
  "total_amount_sun": 50000000,
  "hop_count": 3
}
```

**Provenance** object:

```json
{
  "data_source": "TronGrid API v1",
  "trace_id": "uuid",
  "trace_started_at": "2026-03-20T10:00:00Z",
  "trace_completed_at": "2026-03-20T10:05:32Z",
  "api_calls_made": 142,
  "blocks_range": [58200000, 58300000],
  "filters_applied": {
    "max_hops": 3,
    "min_amount_sun": 1000000,
    "start_time": null,
    "end_time": null,
    "max_degree": 50,
    "path_continuity": true,
    "dedup": true
  }
}
```

### 3.7 Action Package Export

#### 3.7.1 Generate Action Package

- **API**: `POST /api/v1/cases/{case_id}/export`
- **Precondition**: Case status must be `ANALYZED`. At least one candidate must be `approved`.
- **Output**: Generates two files stored on disk and referenced in DB:
  1. **JSON file**: Machine-readable complete evidence bundle.
  2. **PDF file**: Human-readable report formatted for law enforcement.
- **On success**: Transitions case status to `EXPORTED`.

#### 3.7.2 Download Action Package

- **API**: `GET /api/v1/cases/{case_id}/export?format=json|pdf`
- **Response**: Binary file download with appropriate `Content-Type` and `Content-Disposition` headers.
  - JSON: `application/json`, filename `ANVESHAK_{case_id}_{date}.json`
  - PDF: `application/pdf`, filename `ANVESHAK_{case_id}_{date}.pdf`

#### 3.7.3 JSON Action Package Schema

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-03-21T14:00:00Z",
  "generator": "ANVESHAK v1.0.0-MVP",
  "case": {
    "case_id": "uuid",
    "complaint_id": "CMP2026001234",
    "victim_name": "Ramesh Kumar",
    "description": "...",
    "seed_wallets": ["TSeed...abc"],
    "created_at": "2026-03-19T08:00:00Z",
    "status": "EXPORTED",
    "tags": ["phishing", "usdt"]
  },
  "trace_summary": {
    "trace_id": "uuid",
    "max_hops": 3,
    "total_nodes_raw": 142,
    "total_edges_raw": 387,
    "total_nodes_pruned": 28,
    "total_edges_pruned": 45,
    "filters_applied": { ... }
  },
  "approved_candidates": [
    {
      "candidate_id": "uuid",
      "address": "TVasp...xyz",
      "vasp_label": "WazirX",
      "confidence_score": 0.87,
      "score_breakdown": { ... },
      "evidence": {
        "paths": [ ... ],
        "total_amount_sun": 95000000000,
        "total_amount_display": "95000.000000",
        "first_tx_time": "...",
        "last_tx_time": "..."
      },
      "officer_notes": "Confirmed with exchange records",
      "provenance": { ... }
    }
  ],
  "rejected_candidates": [
    {
      "candidate_id": "uuid",
      "address": "TOther...xyz",
      "confidence_score": 0.32,
      "rejection_reason": "Not relevant to this case"
    }
  ],
  "graph_snapshot": {
    "nodes": [ ... ],
    "edges": [ ... ]
  }
}
```

#### 3.7.4 PDF Report Structure

The PDF report MUST contain the following sections in order:

1. **Cover Page**: "ANVESHAK Investigation Report", case ID, complaint ID, generated date, "CONFIDENTIAL" watermark.
2. **Case Summary**: Victim name, complaint ID, description, seed wallets, case timeline.
3. **Trace Summary**: Hops, node/edge counts (raw and pruned), filters applied.
4. **Fund Flow Diagram**: Static rendered image of the pruned graph (PNG embedded).
5. **VASP Candidates — Approved**: Table with address, VASP label, confidence score, total amount, path count. One sub-section per candidate with detailed path table.
6. **VASP Candidates — Rejected**: Table with address, confidence score, rejection reason.
7. **Evidence Paths**: For each approved candidate, a detailed table of every hop in every path: from, to, tx hash, amount, token, timestamp.
8. **Provenance**: Data source, trace timestamps, API call count, block range, filters.
9. **Disclaimer**: "This report is generated by automated blockchain analysis tools. Findings should be corroborated with additional investigation."

---

## 4. Non-Goals (MVP)

The following are explicitly **out of scope** for the MVP release. Do not implement these.

| # | Non-Goal | Rationale |
|---|---|---|
| 1 | User authentication / authorization | Deferred to Phase 2. All users operate as `investigating_officer`. |
| 2 | EVM (Ethereum, Polygon, BSC) chain support | MVP is TRON-only. Multi-chain is Phase 3. |
| 3 | Bitcoin chain support | MVP is TRON-only. |
| 4 | Real-time streaming / WebSockets | Polling-based trace status is sufficient for MVP. |
| 5 | Multi-tenancy | Single deployment, single org. |
| 6 | Bridge / mixer tracing | Requires specialized heuristics beyond MVP scope. |
| 7 | Integration with I4C / NCRP complaint systems | No external system integrations in MVP. |
| 8 | Mobile application | Web-only. Responsive design is nice-to-have but not required. |
| 9 | Automated alert / notification system | No email, SMS, or push notifications. |
| 10 | Historical case analytics / dashboards | No aggregate statistics or trend analysis. |

---

## 5. User Workflows

### 5.1 Workflow 1: Create Case

```
Step 1: Officer navigates to "New Case" page.
Step 2: Officer fills in form:
        - Victim Name (required, text, max 200 chars)
        - Complaint ID (required, alphanumeric, max 50 chars)
        - Description (required, text, max 5000 chars)
        - Seed Wallet(s) (required, 1–10 TRON addresses, each validated per §5.6)
        - Tags (optional, 0–10 tags, each max 50 chars)
Step 3: Officer clicks "Create Case".
Step 4: Frontend sends POST /api/v1/cases.
Step 5: Backend validates all inputs (see §5.6).
        - On validation failure: return 422 with field-level errors. Frontend shows inline errors.
        - On success: create Case record with status=PENDING, return 201 with case_id.
Step 6: Frontend redirects to Case Detail page.
```

### 5.2 Workflow 2: Initiate Trace

```
Step 1:  Officer navigates to Case Detail page (case must be in PENDING or TRACED status).
Step 2:  Officer optionally adjusts max_hops (dropdown: 1, 2, 3, 4, 5; default 3).
Step 3:  Officer clicks "Start Trace".
Step 4:  Frontend sends POST /api/v1/cases/{case_id}/trace with { "max_hops": N }.
Step 5:  Backend validates preconditions:
         - Case exists → else 404.
         - Case status is PENDING or TRACED → else 409 with error code INVALID_STATUS_TRANSITION.
         - No other trace is currently running → else 409 with error code TRACE_ALREADY_RUNNING.
Step 6:  Backend creates trace record, sets case status to TRACING, returns 202 with trace_id.
Step 7:  Frontend begins polling GET /api/v1/cases/{case_id}/trace every 5 seconds.
Step 8:  Backend trace worker:
         a. For each seed wallet, call TronGrid API to fetch transactions.
         b. For each discovered counterparty, recursively fetch up to max_hops.
         c. Build NetworkX directed multigraph.
         d. Store nodes and edges in PostgreSQL.
         e. On completion: set trace status=COMPLETED, case status=TRACED.
         f. On failure: set trace status=FAILED, case status=TRACE_FAILED, store error_message.
Step 9:  Frontend detects trace completion via poll response.
         - On COMPLETED: load and render the pruned graph (auto-applies default filters).
         - On FAILED: show error message with "Retry" button.
Step 10: Officer views the interactive graph (Cytoscape.js). Can pan, zoom, click nodes for details.
Step 11: Officer adjusts pruning filters via sidebar controls. Each change triggers
         GET /api/v1/cases/{case_id}/graph?... to re-fetch the pruned graph.
```

### 5.3 Workflow 3: Review VASP Candidates

```
Step 1: Officer clicks "Analyze" button on Case Detail page (case must be in TRACED status).
Step 2: Frontend sends POST /api/v1/cases/{case_id}/analyze.
Step 3: Backend runs VASP analysis:
        a. Apply pruning filters to get the pruned graph.
        b. Identify leaf nodes (out-degree = 0 in pruned graph).
        c. Match leaf nodes against VASP label store.
        d. Compute confidence scores per §3.5.2.
        e. Store ranked candidate list.
        f. Set case status to ANALYZED.
Step 4: Frontend loads candidate list via GET /api/v1/cases/{case_id}/candidates.
Step 5: Officer sees a ranked table:
        - Columns: Rank, Address (truncated), VASP Label, Confidence Score, Total Amount, Paths, Actions.
        - Sorted by confidence_score DESC.
Step 6: Officer clicks a candidate row to expand details:
        - Full address
        - Score breakdown (5 factors with individual values)
        - List of fund-flow paths from seed(s) to this candidate
        - Each path shown as a step-by-step table (from → to, tx hash, amount, time)
Step 7: Officer clicks "Approve" or "Reject" for each candidate.
        - On Approve: optionally enters officer notes (max 2000 chars).
        - Frontend sends PATCH /api/v1/cases/{case_id}/candidates/{candidate_id}
          with { "status": "approved", "officer_notes": "..." }.
        - On Reject: optionally enters rejection reason (max 2000 chars).
        - Frontend sends PATCH with { "status": "rejected", "officer_notes": "reason" }.
Step 8: Candidate status updates in real-time in the table (approved = green, rejected = red).
```

### 5.4 Workflow 4: Export Action Package

```
Step 1: Officer navigates to Case Detail page (case must be in ANALYZED status).
Step 2: Officer verifies at least one candidate is approved.
        - If no candidates approved: "Export" button is disabled with tooltip "Approve at least one candidate".
Step 3: Officer clicks "Export Action Package".
Step 4: Frontend sends POST /api/v1/cases/{case_id}/export.
Step 5: Backend:
        a. Validates preconditions (status = ANALYZED, ≥1 approved candidate).
        b. Assembles evidence for all approved candidates.
        c. Generates JSON action package.
        d. Renders PDF report (with static graph image).
        e. Stores both files on disk at: /data/exports/{case_id}/
        f. Sets case status to EXPORTED.
        g. Returns 200 with download URLs.
Step 6: Frontend shows download links for JSON and PDF.
Step 7: Officer clicks "Download PDF" → browser downloads PDF file.
Step 8: Officer clicks "Download JSON" → browser downloads JSON file.
```

---

## 6. Case Status Machine

### 6.1 State Diagram

```mermaid
stateDiagram-v2
    [*] --> PENDING : Case created
    PENDING --> TRACING : Trace initiated
    TRACING --> TRACED : Trace completed
    TRACING --> TRACE_FAILED : Trace error
    TRACE_FAILED --> TRACING : Retry trace
    TRACED --> TRACING : Re-trace
    TRACED --> ANALYZED : Analysis completed
    TRACED --> ANALYSIS_FAILED : Analysis error
    ANALYSIS_FAILED --> TRACED : Reset (retry analysis)
    ANALYZED --> EXPORTED : Export generated
    EXPORTED --> CLOSED : Officer closes case
    ANALYZED --> CLOSED : Officer closes case
    EXPORTED --> ANALYZED : Re-analyze
    CLOSED --> [*]
```

### 6.2 Valid Transitions

| From | To | Trigger | Notes |
|---|---|---|---|
| `PENDING` | `TRACING` | `POST .../trace` | Initial trace |
| `TRACING` | `TRACED` | Trace worker completes | Automatic |
| `TRACING` | `TRACE_FAILED` | Trace worker fails | Automatic, stores `error_message` |
| `TRACE_FAILED` | `TRACING` | `POST .../trace` | Retry |
| `TRACED` | `TRACING` | `POST .../trace` | Re-trace (clears old graph data) |
| `TRACED` | `ANALYZED` | `POST .../analyze` | VASP analysis completed |
| `TRACED` | `ANALYSIS_FAILED` | Analysis worker fails | Automatic |
| `ANALYSIS_FAILED` | `TRACED` | `PATCH .../status` body `{"status":"TRACED"}` | Reset for retry |
| `ANALYZED` | `EXPORTED` | `POST .../export` | Action package generated |
| `ANALYZED` | `CLOSED` | `PATCH .../status` body `{"status":"CLOSED"}` | Close without export |
| `EXPORTED` | `CLOSED` | `PATCH .../status` body `{"status":"CLOSED"}` | Normal close |
| `EXPORTED` | `ANALYZED` | `PATCH .../status` body `{"status":"ANALYZED"}` | Re-analyze (e.g., different filter params) |

### 6.3 Invalid Transitions

Any transition not listed in §6.2 MUST return HTTP 409 with error code `INVALID_STATUS_TRANSITION` and body:

```json
{
  "error_code": "INVALID_STATUS_TRANSITION",
  "message": "Cannot transition from {current_status} to {requested_status}",
  "current_status": "PENDING",
  "requested_status": "ANALYZED"
}
```

### 6.4 Status Enum Values

```python
class CaseStatus(str, Enum):
    PENDING = "PENDING"
    TRACING = "TRACING"
    TRACED = "TRACED"
    TRACE_FAILED = "TRACE_FAILED"
    ANALYZED = "ANALYZED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    EXPORTED = "EXPORTED"
    CLOSED = "CLOSED"
```

---

## 7. Input Validation Rules

### 7.1 TRON Address

| Rule | Detail |
|---|---|
| Prefix | Must start with `T` |
| Encoding | Base58Check (characters: `123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz`) |
| Length | Exactly 34 characters |
| Regex | `^T[1-9A-HJ-NP-Za-km-z]{33}$` |
| Example valid | `TN7YwDd4u5kJqTKxoXfJgqUYTZmGCzKJvT` |
| Example invalid | `0xdAC17F958D2ee523a2206206994597C13D831ec7` (Ethereum), `T123` (too short) |
| Error code | `INVALID_TRON_ADDRESS` |
| Error message | `"Invalid TRON address: must start with 'T', be 34 characters, and be base58 encoded"` |

### 7.2 Transaction Hash

| Rule | Detail |
|---|---|
| Encoding | Hexadecimal (case-insensitive) |
| Length | Exactly 64 characters |
| Regex | `^[0-9a-fA-F]{64}$` |
| Example valid | `a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2` |
| Error code | `INVALID_TX_HASH` |
| Error message | `"Invalid transaction hash: must be exactly 64 hexadecimal characters"` |

### 7.3 Amount

| Rule | Detail |
|---|---|
| Type | Numeric (float or int) |
| Minimum | > 0 (strictly positive) |
| Maximum decimal places | 2 for display inputs; internal SUN values are always integers |
| Regex (display input) | `^(?!0$)\d+(\.\d{1,2})?$` |
| Error code | `INVALID_AMOUNT` |
| Error message | `"Amount must be a positive number with at most 2 decimal places"` |

### 7.4 Complaint ID

| Rule | Detail |
|---|---|
| Characters | Alphanumeric plus hyphens and underscores: `[A-Za-z0-9_-]` |
| Length | 1–50 characters |
| Regex | `^[A-Za-z0-9_-]{1,50}$` |
| Uniqueness | Must be unique across all cases. Attempting to create a case with a duplicate complaint_id returns HTTP 409. |
| Error code | `INVALID_COMPLAINT_ID` or `DUPLICATE_COMPLAINT_ID` |

### 7.5 Description

| Rule | Detail |
|---|---|
| Type | Free-text string |
| Min length | 1 character (required) |
| Max length | 5000 characters |
| Error code | `INVALID_DESCRIPTION` |

### 7.6 Tags

| Rule | Detail |
|---|---|
| Type | Array of strings |
| Max tags | 10 |
| Each tag max length | 50 characters |
| Allowed tag characters | Alphanumeric, hyphens, underscores: `[A-Za-z0-9_-]` |
| Duplicate handling | Silently deduplicated (case-insensitive) |
| Error code | `INVALID_TAGS` |

### 7.7 Victim Name

| Rule | Detail |
|---|---|
| Type | String |
| Min length | 1 character (required) |
| Max length | 200 characters |
| Error code | `INVALID_VICTIM_NAME` |

### 7.8 Officer Notes

| Rule | Detail |
|---|---|
| Type | String |
| Required | No (nullable) |
| Max length | 2000 characters |
| Error code | `INVALID_OFFICER_NOTES` |

### 7.9 Max Hops

| Rule | Detail |
|---|---|
| Type | Integer |
| Range | 1–5 (inclusive) |
| Default | 3 |
| Error code | `INVALID_MAX_HOPS` |

---

## 8. Error Handling

### 8.1 Standard Error Response Format

All API errors MUST return a JSON body with this structure:

```json
{
  "error_code": "DESCRIPTIVE_ERROR_CODE",
  "message": "Human-readable description of what went wrong",
  "details": {}
}
```

- `error_code`: UPPER_SNAKE_CASE string. Stable across versions. Clients key on this.
- `message`: English sentence. May change between versions. For human consumption only.
- `details`: Optional object with field-level validation errors or additional context.

### 8.2 Error Code Registry

| HTTP Status | Error Code | Description |
|---|---|---|
| 400 | `INVALID_REQUEST_BODY` | Request body is not valid JSON or is missing required fields |
| 404 | `CASE_NOT_FOUND` | No case with the given `case_id` exists |
| 404 | `CANDIDATE_NOT_FOUND` | No candidate with the given `candidate_id` exists in the case |
| 404 | `EXPORT_NOT_FOUND` | No export has been generated for this case |
| 409 | `INVALID_STATUS_TRANSITION` | Requested status transition is not allowed |
| 409 | `TRACE_ALREADY_RUNNING` | A trace is already in progress for this case |
| 409 | `DUPLICATE_COMPLAINT_ID` | A case with this complaint_id already exists |
| 409 | `NO_APPROVED_CANDIDATES` | Cannot export: no candidates have been approved |
| 422 | `VALIDATION_ERROR` | One or more input fields failed validation |
| 422 | `INVALID_TRON_ADDRESS` | TRON address format validation failed |
| 422 | `INVALID_TX_HASH` | Transaction hash format validation failed |
| 422 | `INVALID_AMOUNT` | Amount validation failed |
| 422 | `INVALID_COMPLAINT_ID` | Complaint ID format validation failed |
| 422 | `INVALID_DESCRIPTION` | Description validation failed |
| 422 | `INVALID_VICTIM_NAME` | Victim name validation failed |
| 422 | `INVALID_TAGS` | Tags validation failed |
| 422 | `INVALID_OFFICER_NOTES` | Officer notes validation failed |
| 422 | `INVALID_MAX_HOPS` | Max hops value out of range |
| 429 | `TRONGRID_RATE_LIMITED` | TronGrid API rate limit hit. Includes `retry_after_seconds` in details. |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 502 | `TRONGRID_API_ERROR` | TronGrid API returned an error or is unreachable |
| 504 | `TRONGRID_TIMEOUT` | TronGrid API request timed out |

### 8.3 Validation Error Detail Format

For HTTP 422 errors, the `details` field contains field-level errors:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Input validation failed",
  "details": {
    "fields": {
      "victim_name": {
        "error_code": "INVALID_VICTIM_NAME",
        "message": "Victim name must be between 1 and 200 characters"
      },
      "seed_wallets[2]": {
        "error_code": "INVALID_TRON_ADDRESS",
        "message": "Invalid TRON address: must start with 'T', be 34 characters, and be base58 encoded"
      }
    }
  }
}
```

---

## 9. Edge Cases

### 9.1 Seed Wallet Has Zero Transactions

- **Detection**: TronGrid API returns empty transaction list for the seed address.
- **Behavior**: Trace completes successfully. Case transitions to `TRACED`. The graph will have exactly N nodes (seed wallets only) and 0 edges.
- **UI**: Graph shows seed wallet node(s) with no connections. Info banner: "No transactions found for seed wallet(s). The address may be unused or transactions may predate the trace window."
- **VASP analysis**: Produces 0 candidates. `no_vasp_candidates = true` warning flag set.

### 9.2 All Paths Pruned (Empty Graph After Filtering)

- **Detection**: After applying all 6 pruning filters, the resulting graph has 0 edges (or only isolated seed nodes).
- **Behavior**: The graph endpoint returns a valid response with `pruned_nodes = N_seeds`, `pruned_edges = 0`.
- **UI**: Graph area shows seed node(s) only. Warning banner: "All transaction paths were removed by the current filters. Try relaxing filter parameters."
- **API response includes**: `"warnings": ["ALL_PATHS_PRUNED"]`
- **VASP analysis on empty graph**: Produces 0 candidates with warning.

### 9.3 TronGrid API Rate Limit Hit

- **Detection**: TronGrid returns HTTP 429 or equivalent rate-limit response.
- **Behavior**:
  1. Trace worker implements exponential backoff: initial delay 2s, multiplier 2×, max delay 60s, max retries 5.
  2. If all retries exhausted, trace transitions to `TRACE_FAILED` with `error_message = "TronGrid API rate limit exceeded after 5 retries"`.
  3. Partial data collected before the rate limit is **discarded** (atomic: all-or-nothing per seed wallet).
- **Retry strategy per seed wallet**: If the trace has multiple seed wallets and one fails, the entire trace fails. Partial results from other seeds are stored but case still goes to `TRACE_FAILED`.
- **Config values** (system settings):

| Setting | Key | Type | Default |
|---|---|---|---|
| Initial retry delay | `trongrid_retry_initial_delay_s` | float | 2.0 |
| Retry multiplier | `trongrid_retry_multiplier` | float | 2.0 |
| Max retry delay | `trongrid_retry_max_delay_s` | float | 60.0 |
| Max retries | `trongrid_retry_max_attempts` | int | 5 |
| Request timeout | `trongrid_request_timeout_s` | float | 30.0 |

### 9.4 Circular Fund Flow (A → B → C → A)

- **Detection**: The trace walker encounters an address it has already visited in the current BFS traversal.
- **Behavior**:
  1. The graph is a directed multigraph. Cycles are allowed and recorded as edges.
  2. The BFS traversal uses a **visited set per hop level**: an address is only expanded once at its minimum hop distance from a seed. If encountered again at a greater hop distance, the edge is recorded but the address is NOT re-expanded.
  3. Circular flows are displayed in the graph visualization as cycles.
  4. Path continuity filter (§3.4.1 #5) does NOT remove nodes that are part of cycles, since they are on a path from a seed.
- **Example**: Seed → A → B → C → A. All 4 addresses appear in the graph. The edge C → A is recorded. A is at hop 1, so B (hop 2) and C (hop 3) are expanded, but A is not re-expanded at hop 4.

### 9.5 Same Address Appears in Multiple Cases

- **Behavior**: This is expected and allowed. Each case maintains its own independent graph, trace data, and candidate records. There is no cross-case deduplication or linking in MVP.
- **Database design**: The `addresses` table (if used as a cache) may have a single row per unique address, but `graph_nodes`, `graph_edges`, and `candidates` tables are always scoped to a `case_id`.
- **VASP label store**: The VASP label store is global (not case-scoped). If an address is labeled as a VASP, it will be recognized in every case that encounters it.
- **Future consideration** (Phase 2): Cross-case link analysis to detect related fraud rings.

### 9.6 Very Large Graphs

- **Detection**: Pruned graph exceeds 500 nodes or 2000 edges.
- **Behavior**: The graph endpoint returns the full data but includes a warning:
  - `"warnings": ["LARGE_GRAPH"]`
  - Frontend may degrade rendering performance. No server-side truncation.
- **Mitigation**: Officer should tighten pruning filters (reduce hops, increase min_amount, narrow time window, lower degree cap).

### 9.7 Duplicate Seed Wallets in Case Creation

- **Detection**: The `seed_wallets` array in the create case request contains duplicate addresses.
- **Behavior**: Silently deduplicated. If `["TAddr1", "TAddr2", "TAddr1"]` is submitted, only `["TAddr1", "TAddr2"]` is stored. No error.

### 9.8 TronGrid API Unavailable (Non-Rate-Limit)

- **Detection**: TronGrid returns HTTP 5xx, connection refused, DNS failure, or request timeout.
- **Behavior**: Same retry strategy as §9.3. After max retries, trace fails with appropriate `error_message`.
- **Error code in API**: `TRONGRID_API_ERROR` (5xx) or `TRONGRID_TIMEOUT` (timeout).

---

## 10. VASP Label Store

### 10.1 Definition

The VASP Label Store is a system-wide lookup table mapping known TRON addresses to Virtual Asset Service Provider identities. It is managed by `admin` users (Phase 2) and seeded with known exchange addresses.

### 10.2 Data Model

| Field | Type | Constraints | Description |
|---|---|---|---|
| `vasp_id` | UUID | PK, auto-generated | Unique identifier |
| `address` | VARCHAR(34) | UNIQUE, NOT NULL, validated per §7.1 | TRON address |
| `label` | VARCHAR(200) | NOT NULL | Display name (e.g., "WazirX", "Binance", "CoinDCX") |
| `category` | VARCHAR(50) | NOT NULL | One of: `exchange`, `payment_processor`, `defi_protocol`, `gambling`, `mixer`, `unknown` |
| `confidence` | VARCHAR(20) | NOT NULL, default `confirmed` | One of: `confirmed`, `suspected`, `community_reported` |
| `source` | VARCHAR(200) | nullable | Where this label came from (e.g., "VASP registry", "manual entry", "MistTrack") |
| `notes` | TEXT | nullable | Free-text notes |
| `created_at` | TIMESTAMPTZ | NOT NULL, auto-set | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, auto-updated | Last modification timestamp |

### 10.3 MVP API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/vasps` | List all VASP labels (paginated) |
| `GET` | `/api/v1/vasps/{vasp_id}` | Get single VASP label |
| `POST` | `/api/v1/vasps` | Create new VASP label |
| `PUT` | `/api/v1/vasps/{vasp_id}` | Update VASP label |
| `DELETE` | `/api/v1/vasps/{vasp_id}` | Delete VASP label |
| `GET` | `/api/v1/vasps/lookup/{address}` | Lookup by TRON address (returns label or 404) |

> [!NOTE]
> In MVP (no auth), all VASP endpoints are accessible to everyone. In Phase 2, `POST`, `PUT`, `DELETE` are restricted to `admin` role.

### 10.4 Seed Data

The system ships with an initial set of known Indian exchange VASP addresses. These are loaded via Alembic data migration. Minimum seed set:

| Label | Category | Confidence |
|---|---|---|
| WazirX | exchange | confirmed |
| CoinDCX | exchange | confirmed |
| CoinSwitch | exchange | confirmed |
| ZebPay | exchange | confirmed |
| Binance | exchange | confirmed |
| Kucoin | exchange | confirmed |
| Huobi (HTX) | exchange | confirmed |
| OKX | exchange | confirmed |

Actual addresses are populated from public VASP address databases or manually entered by admin.

---

## 11. System Configuration

### 11.1 Configuration Parameters

All configuration is via environment variables with sensible defaults:

| Variable | Type | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | string | `postgresql://anveshak:anveshak@localhost:5432/anveshak` | PostgreSQL connection string |
| `TRONGRID_API_URL` | string | `https://api.trongrid.io` | TronGrid API base URL |
| `TRONGRID_API_KEY` | string | (required) | TronGrid API key for higher rate limits |
| `DEFAULT_MAX_HOPS` | int | `3` | Default trace hop depth |
| `MAX_ALLOWED_HOPS` | int | `5` | Maximum configurable hop depth |
| `DEFAULT_MIN_AMOUNT_SUN` | int | `1000000` | Default dust filter threshold (1 TRX) |
| `DEFAULT_MAX_DEGREE` | int | `50` | Default degree cap filter |
| `MAX_SEED_WALLETS_PER_CASE` | int | `10` | Maximum seed wallets in a single case |
| `EXPORT_DIR` | string | `/data/exports` | Directory for generated export files |
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CORS_ORIGINS` | string | `http://localhost:3000` | Comma-separated allowed CORS origins |
| `TRONGRID_RETRY_INITIAL_DELAY_S` | float | `2.0` | Initial backoff delay for TronGrid retries |
| `TRONGRID_RETRY_MULTIPLIER` | float | `2.0` | Backoff multiplier |
| `TRONGRID_RETRY_MAX_DELAY_S` | float | `60.0` | Maximum backoff delay |
| `TRONGRID_RETRY_MAX_ATTEMPTS` | int | `5` | Maximum retry attempts |
| `TRONGRID_REQUEST_TIMEOUT_S` | float | `30.0` | Per-request timeout |

---

## 12. API Summary

### 12.1 Complete Endpoint List

| Method | Path | Description | Request Body | Success Status |
|---|---|---|---|---|
| `POST` | `/api/v1/cases` | Create a new case | CreateCaseRequest | 201 |
| `GET` | `/api/v1/cases` | List cases (paginated, filtered) | — | 200 |
| `GET` | `/api/v1/cases/{case_id}` | Get case detail | — | 200 |
| `PATCH` | `/api/v1/cases/{case_id}/status` | Update case status | StatusUpdateRequest | 200 |
| `POST` | `/api/v1/cases/{case_id}/trace` | Initiate blockchain trace | TraceRequest | 202 |
| `GET` | `/api/v1/cases/{case_id}/trace` | Get trace status | — | 200 |
| `GET` | `/api/v1/cases/{case_id}/graph` | Get pruned graph data | — (query params) | 200 |
| `POST` | `/api/v1/cases/{case_id}/analyze` | Run VASP analysis | — | 200 |
| `GET` | `/api/v1/cases/{case_id}/candidates` | Get ranked VASP candidates | — | 200 |
| `PATCH` | `/api/v1/cases/{case_id}/candidates/{candidate_id}` | Approve/reject candidate | CandidateUpdateRequest | 200 |
| `POST` | `/api/v1/cases/{case_id}/export` | Generate action package | — | 200 |
| `GET` | `/api/v1/cases/{case_id}/export` | Download action package | — (query: format) | 200 |
| `GET` | `/api/v1/vasps` | List VASP labels | — | 200 |
| `GET` | `/api/v1/vasps/{vasp_id}` | Get VASP label | — | 200 |
| `POST` | `/api/v1/vasps` | Create VASP label | CreateVASPRequest | 201 |
| `PUT` | `/api/v1/vasps/{vasp_id}` | Update VASP label | UpdateVASPRequest | 200 |
| `DELETE` | `/api/v1/vasps/{vasp_id}` | Delete VASP label | — | 204 |
| `GET` | `/api/v1/vasps/lookup/{address}` | Lookup VASP by address | — | 200 |
| `GET` | `/api/v1/health` | Health check | — | 200 |

### 12.2 Health Check Response

```json
{
  "status": "healthy",
  "version": "1.0.0-MVP",
  "database": "connected",
  "trongrid": "reachable",
  "timestamp": "2026-03-21T14:00:00Z"
}
```

If database or TronGrid is unreachable, return HTTP 200 but set respective field to `"unreachable"` and `status` to `"degraded"`.

---

## 13. Data Models (Request/Response Schemas)

### 13.1 CreateCaseRequest

```json
{
  "victim_name": "string, required, 1-200 chars",
  "complaint_id": "string, required, 1-50 chars, alphanumeric+hyphens+underscores, unique",
  "description": "string, required, 1-5000 chars",
  "seed_wallets": ["string, required, 1-10 items, each valid TRON address"],
  "tags": ["string, optional, 0-10 items, each 1-50 chars alphanumeric+hyphens+underscores"]
}
```

### 13.2 CreateCaseResponse

```json
{
  "case_id": "uuid",
  "complaint_id": "CMP2026001234",
  "victim_name": "Ramesh Kumar",
  "description": "Victim lost 50,000 USDT in a phishing scam...",
  "seed_wallets": ["TSeed...abc"],
  "tags": ["phishing", "usdt"],
  "status": "PENDING",
  "created_at": "2026-03-19T08:00:00Z",
  "updated_at": "2026-03-19T08:00:00Z"
}
```

### 13.3 TraceRequest

```json
{
  "max_hops": 3
}
```

All fields optional. `max_hops` defaults to system setting `DEFAULT_MAX_HOPS`.

### 13.4 StatusUpdateRequest

```json
{
  "status": "CLOSED"
}
```

### 13.5 CandidateUpdateRequest

```json
{
  "status": "approved",
  "officer_notes": "Confirmed through exchange KYC records"
}
```

`status` must be `"approved"` or `"rejected"`. `officer_notes` is optional, max 2000 chars.

---

## 14. Performance Requirements (MVP)

| Metric | Target |
|---|---|
| Case creation response time | < 500ms |
| Trace initiation (202 response) | < 1s |
| Trace completion (3 hops, 1 seed, ~100 addresses) | < 5 minutes |
| Graph endpoint response (pruned, < 500 nodes) | < 2s |
| VASP analysis completion | < 30s |
| Export generation (PDF + JSON) | < 30s |
| Concurrent cases supported | ≥ 10 |
| Max graph size rendered in browser | 1000 nodes, 5000 edges |

---

## 15. Glossary

| Term | Definition |
|---|---|
| **ANVESHAK** | अन्वेषक (Hindi: "Investigator"). The product name. |
| **Seed Wallet** | The initial TRON address(es) provided in a victim complaint, from which tracing begins. |
| **Hop** | One step in the transaction graph traversal. Hop 0 = seed wallet. Hop 1 = addresses that transacted directly with the seed. |
| **SUN** | The smallest unit of TRX. 1 TRX = 1,000,000 SUN. |
| **VASP** | Virtual Asset Service Provider. An exchange, payment processor, or custodial wallet service. |
| **Pruning** | The process of removing irrelevant nodes and edges from the raw transaction graph to focus on significant fund flows. |
| **Action Package** | The final exportable bundle (PDF + JSON) containing evidence, fund-flow paths, and VASP candidate analysis for law enforcement action. |
| **TronGrid** | The public API service for querying the TRON blockchain. |
| **I4C** | Indian Cyber Crime Coordination Centre. |
| **NCRP** | National Cyber Crime Reporting Portal (cybercrime.gov.in). |
| **TRC-20** | TRON token standard (similar to ERC-20). USDT on TRON is a TRC-20 token. |
| **BFS** | Breadth-First Search. The graph traversal algorithm used for blockchain tracing. |
| **Cytoscape.js** | JavaScript graph visualization library used for the interactive fund-flow graph in the frontend. |

---

*End of Product Specification.*
