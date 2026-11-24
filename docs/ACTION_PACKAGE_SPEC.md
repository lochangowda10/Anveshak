# ANVESHAK — Evidence & Action Package Specification

> **Output & Export Specification (MVP v1.0.0)**
> Defines the exact JSON schema, ReportLab PDF layout, Indian legal mappings, and deterministic action-generation rules.

---

## 1. Purpose

An **Action Package** is the final investigator-ready deliverable of an ANVESHAK investigation. It bridges on-chain blockchain analytics and Indian Law Enforcement procedures so an Investigating Officer (IO) can immediately:
1. Issue a **Section 91 CrPC** (or BNSS Section 94 equivalent) information/KYC request to the identified VASP.
2. Issue a **Section 102 CrPC** / **FIU-IND** account freeze request when confidence is high.
3. Attach a tamper-evident, provenance-tagged digital evidence annexure to an FIR or NCRP case file.

---

## 2. Action Package JSON Schema

Persisted in `action_packages.json_data` and returned by `GET /api/v1/cases/{case_id}/action-package`.

```json
{
  "package_id": "880e8400-e29b-41d4-a716-446655440099",
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "generated_at": "2026-11-24T17:05:12Z",
  "classification": "CONFIDENTIAL — LAW ENFORCEMENT USE ONLY",

  "case_summary": {
    "complaint_id": "NCRP/2026/00412",
    "victim_name": "Rajesh Kumar",
    "reported_at": "2026-11-20T14:30:00Z",
    "description": "Victim transferred 50,000 USDT via TRC-20 to suspect wallet.",
    "seed_wallets": [
      {
        "address": "TFNyk1vSQ82XBvvboW7mLBtneeDToVt1KW",
        "chain": "TRON",
        "reported_amount": 50000.00,
        "token": "USDT"
      }
    ],
    "tags": ["pig-butchering", "investment-fraud"]
  },

  "investigation_summary": {
    "trace_started_at": "2026-11-24T17:04:00Z",
    "trace_completed_at": "2026-11-24T17:05:10Z",
    "elapsed_seconds": 70.0,
    "total_hops_explored": 3,
    "total_addresses_found": 156,
    "addresses_after_pruning": 23,
    "total_flow_traced_usdt": 50000.00,
    "flow_retained_pct": 87.5,
    "pruning_breakdown": {
      "hop_limit": 120,
      "amount_below_threshold": 8,
      "time_window": 3,
      "degree_cap": 1,
      "path_discontinuity": 0,
      "duplicate": 1
    }
  },

  "vasp_candidates": [
    {
      "rank": 1,
      "address": "TNgEDH3RhWAWm7yBDmJgwWBZiGkjEnFaK7",
      "chain": "TRON",
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
              "from": "TFNyk1vSQ82XBvvboW7mLBtneeDToVt1KW",
              "to": "TNMKZSJx7g5Ryv91BXgv2q56VRQwi1ozue",
              "amount": 49500.00,
              "token": "USDT",
              "tx_hash": "aaa1110000000000000000000000000000000000000000000000000000000001",
              "timestamp": "2026-11-20T15:10:00Z",
              "block": 67123456
            },
            {
              "step": 2,
              "from": "TNMKZSJx7g5Ryv91BXgv2q56VRQwi1ozue",
              "to": "TNgEDH3RhWAWm7yBDmJgwWBZiGkjEnFaK7",
              "amount": 48000.00,
              "token": "USDT",
              "tx_hash": "bbb2220000000000000000000000000000000000000000000000000000000002",
              "timestamp": "2026-11-20T16:45:00Z",
              "block": 67125200
            }
          ]
        }
      ]
    }
  ],

  "recommended_actions": [
    {
      "priority": 1,
      "action": "Issue Section 91 CrPC notice to WazirX requesting KYC details, IP logs, and linked bank accounts for deposit address TNgEDH3RhWAWm7yBDmJgwWBZiGkjEnFaK7.",
      "legal_basis": "Section 91, Code of Criminal Procedure, 1973",
      "target_entity": "WazirX",
      "target_address": "TNgEDH3RhWAWm7yBDmJgwWBZiGkjEnFaK7",
      "urgency": "HIGH"
    },
    {
      "priority": 2,
      "action": "Request immediate account freeze / lien marking for deposit address TNgEDH3RhWAWm7yBDmJgwWBZiGkjEnFaK7 pending investigation.",
      "legal_basis": "Section 102, Code of Criminal Procedure, 1973; FIU-IND VDA Guidelines",
      "target_entity": "WazirX",
      "target_address": "TNgEDH3RhWAWm7yBDmJgwWBZiGkjEnFaK7",
      "urgency": "HIGH"
    },
    {
      "priority": 3,
      "action": "Preserve all digital evidence (raw transaction hashes, TronGrid responses, and this report) under Section 65B Indian Evidence Act.",
      "legal_basis": "Section 65B, Indian Evidence Act, 1872",
      "target_entity": "Investigating Officer",
      "target_address": null,
      "urgency": "MEDIUM"
    }
  ],

  "legal_references": [
    {"code": "IT Act Sec 66C", "title": "Punishment for identity theft"},
    {"code": "IT Act Sec 66D", "title": "Punishment for cheating by personation using computer resource"},
    {"code": "IPC Sec 420", "title": "Cheating and dishonestly inducing delivery of property"},
    {"code": "CrPC Sec 91", "title": "Summons to produce document or other thing"},
    {"code": "CrPC Sec 102", "title": "Power of police officer to seize certain property"},
    {"code": "IEA Sec 65B", "title": "Admissibility of electronic records"},
    {"code": "PMLA 2002", "title": "Prevention of Money Laundering Act (VDA Reporting)"},
    {"code": "FIU-IND VDA", "title": "FIU-IND Virtual Digital Asset AML/CFT Guidelines"}
  ],

  "disclaimers": [
    "This analysis is based on publicly available on-chain data and may not represent the complete picture of fund flows.",
    "On-chain tracing ends at the exchange deposit address. KYC information beyond this point requires lawful VASP cooperation.",
    "VASP attribution confidence scores are algorithmic estimates and must be verified through official channels.",
    "Recovery of funds is not guaranteed.",
    "This document is generated by ANVESHAK and should be reviewed by the investigating officer before official use."
  ],

  "metadata": {
    "anveshak_version": "1.0.0-mvp",
    "graph_engine_version": "1.0.0",
    "label_database_updated_at": "2026-11-24T00:00:00Z"
  }
}
```

---

## 3. Recommended Action Generation Rules (Deterministic)

Actions are generated per non-rejected VASP candidate (up to top 3) using these exact thresholds:

| Candidate Confidence (`c`) | Generated Actions | Urgency |
|---|---|---|
| `c >= 0.70` | 1. **Issue Section 91 CrPC notice** requesting KYC, IP logs, and withdrawal history for `address`<br>2. **Request account freeze** under Section 102 CrPC & FIU-IND VDA Guidelines | `HIGH` |
| `0.40 <= c < 0.70` | 1. **Issue Section 91 CrPC notice** requesting KYC / transaction history for `address` (no freeze recommendation yet) | `MEDIUM` |
| `0.20 <= c < 0.40` | 1. **Request transaction history / verify attribution** for `address`<br>2. **Flag for manual blockchain analyst review** | `LOW` |
| **0 candidates found** | 1. **No VASP endpoints identified** within hop/pruning limits. Expand `hop_limit` or check manual intelligence feeds. | `MEDIUM` |

**Always appended to `recommended_actions`:**
- `"Preserve all digital evidence (transaction hashes, raw API payloads, and report) for Section 65B Indian Evidence Act compliance."` (`MEDIUM`)
- `"Document chain of custody for all exported artifacts."` (`LOW`)

---

## 4. PDF Report Specification (ReportLab)

- **Library:** `reportlab` (`platypus` + `canvas`)
- **Page Size:** A4 (`595.27 x 841.89 pt`), Margins: `40pt` all sides
- **Fonts:** Built-in `Helvetica` and `Helvetica-Bold` (no external font files required)
- **Header / Footer (Pages 2+):**
  - Top-right header: `ANVESHAK | Case {case_id[:8]} | CONFIDENTIAL`
  - Bottom footer: `Page {n} | Generated {generated_at}`
- **Storage Path:** `storage/action_packages/{case_id}.pdf`
- **Download Filename:** `ANVESHAK_REPORT_{case_id}_{YYYYMMDD_HHMMSS}.pdf`

### Page-by-Page Layout

1. **Page 1 — Cover Page:**
   - Top banner: Dark navy bar (`#0F172A`) with white text `"ANVESHAK"` (placeholder text logo)
   - Title (`24pt Bold`): `"CRYPTOCURRENCY INVESTIGATION REPORT"`
   - Subtitle (`13pt`): `"Complaint-to-Action On-Chain Evidence & VASP Attribution Package"`
   - Classification Box (Red border): `"CONFIDENTIAL — LAW ENFORCEMENT USE ONLY"`
   - Metadata Table: `Case ID`, `Complaint / NCRP ID`, `Victim Name`, `Reported Date`, `Generated At`

2. **Page 2 — Case Summary:**
   - Victim details & Complaint description
   - **Seed Wallets Table:** `Address`, `Chain`, `Token`, `Reported Amount`, `TX Hash`

3. **Page 3 — Investigation Summary:**
   - Key Metrics Table: `Hops Explored`, `Total Addresses Found`, `Addresses After Pruning`, `Total Flow Traced (USDT)`, `Flow Retained (%)`, `Trace Duration (s)`
   - Pruning Breakdown Table (counts for all 6 filters)

4. **Page 4+ — VASP Candidates & Evidence Paths:**
   - Up to top 5 non-rejected candidates, each starting cleanly with:
     - Heading: `Candidate #{rank}: {label or "Unknown Entity"} ({confidence * 100:.1f}% Confidence)`
     - Target Address, Label Source, 6-Signal Scoring Breakdown table
     - **Evidence Paths Table:** `Step`, `From Address`, `To Address`, `Amount (USDT)`, `Timestamp`, `TX Hash` (rendered as clickable hyperlink to `https://tronscan.org/#/transaction/{tx_hash}`)

5. **Next Page — Recommended Actions:**
   - Numbered table/cards: `Priority`, `Urgency`, `Target Entity & Address`, `Action`, `Legal Basis`

6. **Next Page — Legal References:**
   - 2-column table of all 8 Indian statutory references (`Code / Section`, `Description`)

7. **Final Page — Disclaimers & Provenance:**
   - Bulleted list of all 5 mandatory disclaimers
   - Version block (`anveshak_version`, `graph_engine_version`, `label_database_updated_at`)
