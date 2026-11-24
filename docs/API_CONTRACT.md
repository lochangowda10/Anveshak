# ANVESHAK — API Contract & Module Interface Specification

> **Machine-Executable REST API & Internal Protocol Specification (MVP v1.0.0)**
> Every endpoint, payload, status code, validation rule, error format, and internal Python Protocol is defined here. Do not invent undocumented endpoints or fields.

---

## 1. Global Conventions

| Convention | Specification |
|---|---|
| **Base URL** | `/api/v1` |
| **Authentication (MVP)** | **None** — All endpoints are unauthenticated for MVP. Phase 2 adds JWT Bearer auth (`Authorization: Bearer <token>`). |
| **Content-Type** | `application/json` (except PDF export: `application/pdf`) |
| **Timestamps** | ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`) |
| **UUIDs** | UUID v4 strings (`xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`) |
| **TRON Address Regex** | `^T[1-9A-HJ-NP-Za-km-z]{33}$` (34 chars, Base58Check, starts with `T`) |
| **TX Hash Regex** | `^[a-fA-F0-9]{64}$` (64 hex characters) |
| **Pagination** | `page` (int, default `1`, min `1`), `page_size` (int, default `20`, min `1`, max `100`) |

### Standard Error Response Formats

**400 Bad Request / 404 Not Found / 409 Conflict / 500 Internal Server Error:**
```json
{
  "detail": "Human-readable error message"
}
```

**422 Unprocessable Entity (Pydantic Validation Error):**
```json
{
  "detail": [
    {
      "loc": ["body", "seed_wallets", 0, "address"],
      "msg": "Invalid TRON address format: must start with 'T' and be 34 Base58 characters",
      "type": "value_error"
    }
  ]
}
```

---

## 2. REST API Endpoints

### 2.1 Health Check

- **Method & Path:** `GET /api/v1/health`
- **Auth:** None (MVP)
- **Request Headers:** None required
- **Response `200 OK`:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected"
}
```
- **Response `503 Service Unavailable`** (if DB unreachable):
```json
{
  "status": "degraded",
  "version": "1.0.0",
  "database": "disconnected"
}
```

---

### 2.2 Create Case

- **Method & Path:** `POST /api/v1/cases`
- **Auth:** None (MVP)
- **Request Headers:** `Content-Type: application/json`

**Request Body Schema:**
| Field | Type | Required | Constraints |
|---|---|---|---|
| `complaint_id` | `string \| null` | No | Max 50 chars, alphanumeric + `/-_` (`^[A-Za-z0-9/_-]+$`), unique if provided |
| `victim_name` | `string` | **Yes** | Min 1 char, max 255 chars |
| `victim_contact` | `string \| null` | No | Max 255 chars |
| `reported_at` | `datetime` | **Yes** | ISO 8601 datetime, cannot be in the future |
| `description` | `string` | **Yes** | Min 1 char, max 5000 chars |
| `tags` | `string[]` | No | Max 10 items, each max 50 chars, lowercase trimmed |
| `seed_wallets` | `SeedWalletInput[]` | **Yes** | Min 1 item, max 10 items |

**`SeedWalletInput` Object:**
| Field | Type | Required | Constraints |
|---|---|---|---|
| `address` | `string` | **Yes** | Must match `^T[1-9A-HJ-NP-Za-km-z]{33}$` when `chain == "TRON"` |
| `chain` | `string` | No | Default `"TRON"`. MVP allows `"TRON"` only (enum: `"TRON"`, `"ETH"`, `"BTC"`) |
| `token` | `string` | No | Default `"USDT"`. Max 20 chars |
| `reported_amount` | `number \| null` | No | If provided, `> 0`, max 8 decimal places (MVP UI enforces 2 decimals) |
| `tx_hash` | `string \| null` | No | If provided, must match `^[a-fA-F0-9]{64}$` |

**Example Request:**
```json
{
  "complaint_id": "NCRP/2026/00412",
  "victim_name": "Rajesh Kumar",
  "victim_contact": "+91-9876543210",
  "reported_at": "2026-11-20T14:30:00Z",
  "description": "Victim transferred 50,000 USDT via TRC-20 to suspect wallet in a pig-butchering investment scam.",
  "tags": ["pig-butchering", "investment-fraud"],
  "seed_wallets": [
    {
      "address": "TN2YqTv7ykawJjgqQfcbRGFyEY8ehPkuGM",
      "chain": "TRON",
      "token": "USDT",
      "reported_amount": 50000.00,
      "tx_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
    }
  ]
}
```

**Response `201 Created`:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "complaint_id": "NCRP/2026/00412",
  "victim_name": "Rajesh Kumar",
  "victim_contact": "+91-9876543210",
  "description": "Victim transferred 50,000 USDT via TRC-20 to suspect wallet in a pig-butchering investment scam.",
  "status": "PENDING",
  "reported_at": "2026-11-20T14:30:00Z",
  "created_at": "2026-11-24T17:00:00Z",
  "updated_at": "2026-11-24T17:00:00Z",
  "trace_started_at": null,
  "trace_completed_at": null,
  "trace_config": null,
  "tags": ["pig-butchering", "investment-fraud"],
  "seed_wallets": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "address": "TN2YqTv7ykawJjgqQfcbRGFyEY8ehPkuGM",
      "chain": "TRON",
      "token": "USDT",
      "reported_amount": 50000.00,
      "tx_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
      "created_at": "2026-11-24T17:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `409 Conflict`: Duplicate `complaint_id` already exists (`{"detail": "Case with complaint_id 'NCRP/2026/00412' already exists"}`)
- `422 Unprocessable Entity`: Invalid TRON address, empty `seed_wallets`, `> 10` tags, future `reported_at`, or negative `reported_amount`

---

### 2.3 List Cases

- **Method & Path:** `GET /api/v1/cases`
- **Auth:** None (MVP)
- **Query Parameters:**
  | Param | Type | Default | Constraints | Description |
  |---|---|---|---|---|
  | `page` | `int` | `1` | `>= 1` | Page number (1-indexed) |
  | `page_size` | `int` | `20` | `1 <= page_size <= 100` | Items per page |
  | `status` | `string` | `null` | Valid status enum | Filter by exact case status |
  | `search` | `string` | `null` | Max 100 chars | Case-insensitive partial match on `victim_name` or `complaint_id` |
  | `date_from` | `datetime` | `null` | ISO 8601 | Filter `created_at >= date_from` |
  | `date_to` | `datetime` | `null` | ISO 8601 | Filter `created_at <= date_to` |
  | `sort_by` | `string` | `"created_at"` | `"created_at" \| "updated_at" \| "status" \| "victim_name"` | Sort column |
  | `sort_order` | `string` | `"desc"` | `"asc" \| "desc"` | Sort direction |

**Response `200 OK`:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "complaint_id": "NCRP/2026/00412",
      "victim_name": "Rajesh Kumar",
      "status": "TRACED",
      "reported_at": "2026-11-20T14:30:00Z",
      "created_at": "2026-11-24T17:00:00Z",
      "updated_at": "2026-11-24T17:05:00Z",
      "seed_wallets_count": 1,
      "primary_seed_address": "TN2YqTv7ykawJjgqQfcbRGFyEY8ehPkuGM",
      "tags": ["pig-butchering", "investment-fraud"]
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

---

### 2.4 Get Case Detail

- **Method & Path:** `GET /api/v1/cases/{case_id}`
- **Auth:** None (MVP)
- **Path Parameters:** `case_id` (`UUID`, required)

**Response `200 OK`:** Same schema as `201 Created` response in `POST /api/v1/cases`, plus `trace_summary` (nullable object when not yet traced).
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "complaint_id": "NCRP/2026/00412",
  "victim_name": "Rajesh Kumar",
  "victim_contact": "+91-9876543210",
  "description": "Victim transferred 50,000 USDT...",
  "status": "ANALYZED",
  "reported_at": "2026-11-20T14:30:00Z",
  "created_at": "2026-11-24T17:00:00Z",
  "updated_at": "2026-11-24T17:05:12Z",
  "trace_started_at": "2026-11-24T17:04:00Z",
  "trace_completed_at": "2026-11-24T17:05:10Z",
  "trace_config": {
    "hop_limit": 3,
    "time_window_before_days": 30,
    "time_window_after_days": 7,
    "degree_cap": 100,
    "amount_threshold_pct": 0.01
  },
  "tags": ["pig-butchering", "investment-fraud"],
  "seed_wallets": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "address": "TN2YqTv7ykawJjgqQfcbRGFyEY8ehPkuGM",
      "chain": "TRON",
      "token": "USDT",
      "reported_amount": 50000.00,
      "tx_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
      "created_at": "2026-11-24T17:00:00Z"
    }
  ]
}
```
- **Error `404 Not Found`:** `{"detail": "Case not found"}`
- **Error `422 Unprocessable Entity`:** Invalid UUID format for `case_id`

---

### 2.5 Trigger Blockchain Trace

- **Method & Path:** `POST /api/v1/cases/{case_id}/trace`
- **Auth:** None (MVP)
- **Path Parameters:** `case_id` (`UUID`, required)
- **Request Body (Optional — uses defaults if omitted or `{}`):**
```json
{
  "hop_limit": 3,
  "time_window_before_days": 30,
  "time_window_after_days": 7,
  "degree_cap": 100,
  "amount_threshold_pct": 0.01
}
```
| Field | Type | Default | Constraints |
|---|---|---|---|
| `hop_limit` | `int` | `3` | `1 <= hop_limit <= 5` |
| `time_window_before_days` | `int` | `30` | `1 <= x <= 365` |
| `time_window_after_days` | `int` | `7` | `0 <= x <= 90` |
| `degree_cap` | `int` | `100` | `10 <= x <= 1000` |
| `amount_threshold_pct` | `float` | `0.01` | `0.0 <= x <= 1.0` |

**Behavior:** Transitions case `status` from `PENDING` or `TRACE_FAILED` to `TRACING`, spawns background async task executing Graph Engine → Attribution & Ranking → Evidence Assembly, and returns immediately.

**Response `202 Accepted`:**
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "TRACING",
  "message": "Trace started"
}
```

**Error Responses:**
- `404 Not Found`: `{"detail": "Case not found"}`
- `409 Conflict`: `{"detail": "Trace already in progress"}` (if `status == "TRACING"`)
- `422 Unprocessable Entity`: Invalid config values (e.g. `hop_limit: 10`)

---

### 2.6 Get Investigation Graph (Cytoscape Format)

- **Method & Path:** `GET /api/v1/cases/{case_id}/graph`
- **Auth:** None (MVP)
- **Query Parameters:**
  - `include_pruned` (`bool`, default `false`) — if `false`, returns only `pruned == false` edges and connected nodes.

**Response `200 OK` (After trace):**
```json
{
  "nodes": [
    {
      "data": {
        "id": "TN2YqTv7ykawJjgqQfcbRGFyEY8ehPkuGM",
        "label": "TN2YqTv7...kuGM",
        "type": "seed",
        "hop_depth": 0,
        "in_degree": 1,
        "out_degree": 2,
        "total_received": 50000.0,
        "total_sent": 49500.0,
        "vasp_label": null,
        "vasp_confidence": null
      }
    },
    {
      "data": {
        "id": "TWazirXdeposit1234567890123456",
        "label": "TWazirXd...3456",
        "type": "vasp_candidate",
        "hop_depth": 2,
        "in_degree": 142,
        "out_degree": 3,
        "total_received": 48000.0,
        "total_sent": 47900.0,
        "vasp_label": "WazirX",
        "vasp_confidence": 0.92
      }
    }
  ],
  "edges": [
    {
      "data": {
        "id": "aaa1110000000000000000000000000000000000000000000000000000000001",
        "source": "TN2YqTv7ykawJjgqQfcbRGFyEY8ehPkuGM",
        "target": "TLayerA1qwerty123456789012345678",
        "amount": 49500.0,
        "token": "USDT",
        "timestamp": "2026-11-20T15:10:00Z",
        "hop_depth": 1,
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

**Response `200 OK` (Before trace):**
```json
{
  "nodes": [],
  "edges": [],
  "metadata": null
}
```
- **Error `404 Not Found`:** `{"detail": "Case not found"}`

---

### 2.7 Get Ranked VASP Candidates

- **Method & Path:** `GET /api/v1/cases/{case_id}/candidates`
- **Auth:** None (MVP)

**Response `200 OK`:**
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "candidates": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "rank": 1,
      "address": "TWazirXdeposit1234567890123456",
      "chain": "TRON",
      "label": "WazirX",
      "label_source": "public",
      "confidence": 0.92,
      "review_status": "pending",
      "scoring_breakdown": {
        "label_match_score": 1.0,
        "hop_depth_score": 0.75,
        "amount_relevance_score": 0.96,
        "time_gap_score": 0.99,
        "path_continuity_score": 1.0,
        "degree_fanout_score": 1.0
      },
      "alternative_labels": [],
      "evidence_path_ids": ["path-001"]
    }
  ],
  "total": 1
}
```
- **Error `404 Not Found`:** `{"detail": "Case not found"}`

---

### 2.8 Review VASP Candidate (Accept / Reject)

- **Method & Path:** `POST /api/v1/cases/{case_id}/candidates/{candidate_id}/review`
- **Auth:** None (MVP)
- **Request Body:**
```json
{
  "decision": "accepted",
  "notes": "Confirmed WazirX hot wallet deposit address."
}
```
(`decision`: `"accepted" | "rejected" | "pending"`)

**Response `200 OK`:** Updated candidate object.
- **Error `404 Not Found`:** Case or candidate not found.

---

### 2.9 Get Evidence Package

- **Method & Path:** `GET /api/v1/cases/{case_id}/evidence`
- **Auth:** None (MVP)

**Response `200 OK`:**
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "generated_at": "2026-11-24T17:05:12Z",
  "seed_wallets": [
    {
      "address": "TN2YqTv7ykawJjgqQfcbRGFyEY8ehPkuGM",
      "chain": "TRON",
      "reported_amount": 50000.00,
      "token": "USDT"
    }
  ],
  "investigation_summary": {
    "total_hops_explored": 2,
    "total_addresses_found": 12,
    "addresses_after_pruning": 3,
    "total_flow_traced": 50000.00,
    "flow_retained_after_pruning_pct": 96.0
  },
  "vasp_candidates": [
    {
      "rank": 1,
      "address": "TWazirXdeposit1234567890123456",
      "label": "WazirX",
      "label_source": "public",
      "confidence": 0.92,
      "scoring_breakdown": {
        "label_match_score": 1.0,
        "hop_depth_score": 0.75,
        "amount_relevance_score": 0.96,
        "time_gap_score": 0.99,
        "path_continuity_score": 1.0,
        "degree_fanout_score": 1.0
      },
      "evidence_paths": [
        {
          "path_id": "path-001",
          "total_amount": 48000.00,
          "hop_count": 2,
          "hops": [
            {
              "step": 1,
              "from": "TN2YqTv7ykawJjgqQfcbRGFyEY8ehPkuGM",
              "to": "TLayerA1qwerty123456789012345678",
              "amount": 49500.0,
              "token": "USDT",
              "tx_hash": "aaa1110000000000000000000000000000000000000000000000000000000001",
              "timestamp": "2026-11-20T15:10:00Z"
            },
            {
              "step": 2,
              "from": "TLayerA1qwerty123456789012345678",
              "to": "TWazirXdeposit1234567890123456",
              "amount": 48000.0,
              "token": "USDT",
              "tx_hash": "bbb2220000000000000000000000000000000000000000000000000000000002",
              "timestamp": "2026-11-20T16:45:00Z"
            }
          ]
        }
      ]
    }
  ]
}
```
- **Error `404 Not Found`:** `{"detail": "Case not found"}`

---

### 2.10 Get Action Package (JSON)

- **Method & Path:** `GET /api/v1/cases/{case_id}/action-package`
- **Auth:** None (MVP)
- **Response `200 OK`:** Full JSON structure defined in `docs/ACTION_PACKAGE_SPEC.md` Section 2.
- **Error `404 Not Found`:** `{"detail": "Action package not generated yet"}`

---

### 2.11 Export Action Package (PDF)

- **Method & Path:** `GET /api/v1/cases/{case_id}/action-package/export`
- **Auth:** None (MVP)
- **Response `200 OK`:**
  - Header: `Content-Type: application/pdf`
  - Header: `Content-Disposition: attachment; filename="ANVESHAK_REPORT_{case_id}.pdf"`
  - Body: Binary PDF stream generated by ReportLab.
- **Error `404 Not Found`:** `{"detail": "Action package not generated yet"}`

---

### 2.12 Search / Add VASP Labels

- **Method & Path:** `GET /api/v1/labels/search`
- **Auth:** None (MVP)
- **Query Parameters:**
  - `address` (`string`, optional) — exact address match
  - `label` (`string`, optional) — case-insensitive substring match
  - `chain` (`string`, default `"TRON"`)
- **Response `200 OK`:**
```json
{
  "labels": [
    {
      "id": 1,
      "address": "TWazirXdeposit1234567890123456",
      "chain": "TRON",
      "label": "WazirX",
      "label_type": "exchange",
      "source": "public",
      "confidence": 0.60
    }
  ]
}
```

- **Method & Path:** `POST /api/v1/labels`
- **Auth:** None (MVP)
- **Request Body:**
```json
{
  "address": "TManualLabel12345678901234567890",
  "chain": "TRON",
  "label": "CoinDCX Deposit",
  "label_type": "exchange",
  "source": "agency",
  "confidence": 0.95
}
```
- **Response `201 Created`:** Created label object.

---

## 3. Internal Python Protocols (Module Interfaces)

All modules MUST conform to these typed Python interfaces:

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class TransactionData:
    """Canonical normalized transaction returned by any ChainAdapter."""
    tx_hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    amount: float
    token: str
    chain: str
    raw_data: dict  # Full raw API payload for audit provenance


class ChainAdapter(Protocol):
    """Interface that every blockchain adapter (TRON, EVM, BTC) must implement."""

    async def get_transactions(
        self,
        address: str,
        *,
        direction: str = "both",  # "in" | "out" | "both"
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        token: str | None = None,
        limit: int = 200,
    ) -> list[TransactionData]:
        """Fetch normalized transactions for a blockchain address."""
        ...

    async def get_address_info(self, address: str) -> dict:
        """Return account metadata (balance, create_time, type)."""
        ...

    async def is_contract(self, address: str) -> bool:
        """Return True if address is a smart contract."""
        ...


@dataclass
class GraphNodeData:
    address: str
    chain: str
    node_type: str  # "seed" | "intermediate" | "vasp_candidate" | "unknown"
    hop_depth: int
    in_degree: int = 0
    out_degree: int = 0
    total_received: float = 0.0
    total_sent: float = 0.0
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    label: str | None = None
    label_source: str | None = None
    label_confidence: float | None = None


@dataclass
class GraphEdgeData:
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    token: str
    timestamp: datetime
    hop_depth: int
    path_id: str
    pruned: bool = False
    prune_reason: str | None = None


@dataclass
class VASPCandidateData:
    address: str
    chain: str
    label: str | None
    label_source: str | None
    confidence: float
    rank: int
    scoring_breakdown: dict[str, float]
    evidence_path_ids: list[str] = field(default_factory=list)
    alternative_labels: list[dict] = field(default_factory=list)
```
