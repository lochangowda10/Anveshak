# ANVESHAK — API Contract (Interface Specification)

> This document defines the data contracts between modules. All modules MUST
> conform to these interfaces. Changes require a PR reviewed by all dependent
> module owners.

---

## 1. Case Intake

### `POST /api/v1/cases`

**Request Body:**

```json
{
  "complaint_id": "string (optional — NCRP reference)",
  "victim_name": "string",
  "victim_contact": "string (optional)",
  "reported_at": "ISO 8601 datetime",
  "seed_wallets": [
    {
      "address": "string",
      "chain": "TRON | ETH | BTC",
      "reported_amount": "number (optional, in original token)",
      "token": "string (e.g., USDT)",
      "tx_hash": "string (optional — the fraud transaction)"
    }
  ],
  "description": "string (free-text complaint summary)",
  "tags": ["string (optional — e.g., 'pig-butchering', 'romance-scam')"]
}
```

**Response:** `201 Created`

```json
{
  "case_id": "uuid",
  "status": "PENDING",
  "created_at": "ISO 8601",
  "seed_wallets": ["..."]
}
```

---

## 2. Chain Adapter Interface

All chain adapters MUST implement this Python protocol:

```python
from typing import Protocol
from datetime import datetime

class Transaction:
    tx_hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    amount: float
    token: str
    chain: str
    raw: dict  # Original API response for provenance

class ChainAdapter(Protocol):
    """Interface that every blockchain adapter must implement."""

    async def get_transactions(
        self,
        address: str,
        *,
        direction: str = "both",  # "in" | "out" | "both"
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        token: str | None = None,
        limit: int = 200,
    ) -> list[Transaction]:
        """Fetch transactions for an address."""
        ...

    async def get_address_info(self, address: str) -> dict:
        """Get address metadata (balance, type, first/last seen)."""
        ...

    async def is_contract(self, address: str) -> bool:
        """Check if address is a smart contract."""
        ...
```

---

## 3. Graph Engine — Internal Schema

### Node (Address)

```python
@dataclass
class GraphNode:
    address: str
    chain: str
    node_type: str  # "seed" | "intermediate" | "vasp_candidate" | "unknown"
    label: str | None  # e.g., "Binance Hot Wallet"
    label_source: str | None  # "public" | "agency" | "licensed" | "heuristic"
    label_confidence: float  # 0.0 – 1.0
    first_seen: datetime
    last_seen: datetime
    in_degree: int
    out_degree: int
    total_received: float
    total_sent: float
```

### Edge (Transaction Flow)

```python
@dataclass
class GraphEdge:
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    token: str
    timestamp: datetime
    hop_depth: int  # from seed
    path_id: str  # unique path identifier for provenance
```

---

## 4. Ranking Engine — Scoring Output

```python
@dataclass
class VASPCandidate:
    address: str
    chain: str
    label: str | None
    confidence: float  # 0.0 – 1.0
    rank: int
    scoring_breakdown: dict
    # Example scoring_breakdown:
    # {
    #   "hop_depth_score": 0.8,
    #   "amount_relevance_score": 0.9,
    #   "time_gap_score": 0.7,
    #   "path_continuity_score": 0.85,
    #   "degree_fanout_score": 0.6,
    #   "label_match_score": 1.0
    # }
    evidence_refs: list[str]  # list of path_ids supporting this candidate
```

---

## 5. Evidence & Action Package

### `GET /api/v1/cases/{case_id}/evidence`

**Response:**

```json
{
  "case_id": "uuid",
  "generated_at": "ISO 8601",
  "seed_wallets": ["..."],
  "investigation_summary": {
    "total_hops_explored": 42,
    "total_addresses_found": 156,
    "addresses_after_pruning": 23,
    "total_flow_traced": 50000.00,
    "flow_retained_after_pruning_pct": 87.5
  },
  "vasp_candidates": [
    {
      "rank": 1,
      "address": "T...",
      "label": "WazirX",
      "confidence": 0.92,
      "scoring_breakdown": {},
      "evidence_paths": [
        {
          "path_id": "...",
          "hops": [
            {"from": "...", "to": "...", "amount": 1000, "tx_hash": "...", "timestamp": "..."}
          ]
        }
      ]
    }
  ],
  "action_package": {
    "recommended_actions": [
      "Issue information request to WazirX compliance team",
      "Request KYC details for deposit address T..."
    ],
    "legal_references": [
      "IT Act Section 69",
      "FIU-IND VDA Reporting Guidelines"
    ],
    "exportable_formats": ["PDF", "JSON"]
  }
}
```

---

## 6. Frontend ↔ Backend API Summary

| Endpoint                                  | Method | Module          |
|-------------------------------------------|--------|-----------------|
| `/api/v1/cases`                           | POST   | Case Intake     |
| `/api/v1/cases`                           | GET    | Case Intake     |
| `/api/v1/cases/{id}`                      | GET    | Case Intake     |
| `/api/v1/cases/{id}/trace`                | POST   | Graph Engine    |
| `/api/v1/cases/{id}/graph`                | GET    | Graph Engine    |
| `/api/v1/cases/{id}/candidates`           | GET    | Ranking Engine  |
| `/api/v1/cases/{id}/evidence`             | GET    | Evidence        |
| `/api/v1/cases/{id}/action-package`       | GET    | Evidence        |
| `/api/v1/cases/{id}/action-package/export`| GET    | Evidence        |
| `/api/v1/labels/search`                   | GET    | Attribution     |
| `/api/v1/health`                          | GET    | Core            |
