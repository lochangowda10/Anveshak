# ANVESHAK — Project Context

> **Complaint-to-Action Crypto Investigation Workflow for Indian Law Enforcement**
> Smart India Hackathon 2026 · SIH26183 · Team PHANTOMS

---

## 1. What Is ANVESHAK?

ANVESHAK transforms a **victim-reported suspect wallet address** into an
**investigator-ready action package** — automatically tracing fund flows on-chain,
pruning irrelevant branches, ranking likely VASP (Virtual Asset Service Provider)
endpoints, and generating evidence-backed outputs that Indian law-enforcement
agencies can use directly.

### The Core Pipeline

```
VICTIM COMPLAINT ─► SEED WALLET ─► LAYERING WALLETS ─► CANDIDATE VASP ─► EVIDENCE ─► ACTION PACKAGE
```

### Without ANVESHAK vs With ANVESHAK

| Today (Manual)                     | With ANVESHAK (Automated)             |
|------------------------------------|---------------------------------------|
| Officer traces wallets manually    | Automated pruned multi-hop tracing    |
| Evidence scattered in screenshots  | Provenance-tagged evidence chain      |
| VASP identified too late           | Ranked VASP lead within minutes       |
| No standardised case output        | Action-package generator              |

---

## 2. Problem Statement

**PS ID:** SIH26183
**Title:** Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges from
Victim-Reported Suspect Wallet Addresses through Automated Blockchain Analytics
**Theme:** Blockchain & Cybersecurity
**Category:** Software

---

## 3. Key Design Principles

| Principle                | Description                                                              |
|--------------------------|--------------------------------------------------------------------------|
| **Complaint-Aware**      | Complaint metadata stays attached throughout the investigation lifecycle |
| **India-LEA Workflow**   | Maps directly to Indian law-enforcement procedures & FIU-IND frameworks  |
| **Evidence Provenance**  | Every lead retains source, path, and confidence tier                     |
| **Pluggable Intelligence** | Works with public, agency, and licensed intelligence feeds             |

---

## 4. Technical Stack (Decided)

| Layer               | Technology          | Purpose                                     |
|---------------------|---------------------|---------------------------------------------|
| API Gateway         | **FastAPI**         | Case intake, REST endpoints                 |
| Chain Adapters      | **TronGrid** (MVP) | Blockchain data fetching (TRON + USDT)      |
| Database            | **PostgreSQL**      | Canonical transaction schema, case storage  |
| Graph Engine        | **NetworkX**        | Pruned multi-hop traversal                  |
| Attribution Engine  | **Python**          | Endpoint identification, confidence scoring |
| Frontend            | **React + Cytoscape** | Graph visualization, evidence UI          |

---

## 5. Delivery Roadmap

### Phase 1 — MVP (SIH Demo)
- TRON + USDT tracing
- 1–3 hop pruned traversal
- Seed VASP labels
- Investigation graph viewer
- Action-package generator

### Phase 2 — Confidence Engine + EVM
- Attribution confidence scoring
- Case management system
- EVM chain adapter (Ethereum, Polygon)

### Phase 3 — Multi-Chain + Integrations
- Bridge boundary detection
- Complaint-system integration (I4C / NCRP)
- Event-driven real-time tracing

---

## 6. Risks & Mitigations

| Risk                 | Severity | Mitigation                                      |
|----------------------|----------|--------------------------------------------------|
| Graph explosion      | HIGH     | Pruning filters + hop/degree thresholds + cache  |
| Label sparsity       | HIGH     | Multiple feeds + confidence tiers + provenance   |
| Mixers / bridges     | HIGH     | Detect boundary + flag uncertainty               |
| Custodial exchange   | MEDIUM   | Stop at VASP endpoint + lawful KYC request       |
| API rate limits      | MEDIUM   | Cache + incremental fetch + async jobs           |
| False attribution    | HIGH     | Evidence + confidence + human-in-the-loop        |

---

## 7. Stakeholders

- **I4C** (Indian Cybercrime Coordination Centre)
- **State Cyber Cells**
- **Investigating Officers**
- **Victims**
- **VASPs** (Exchanges)

---

## 8. References

1. SIH26183 Problem Statement — sih.gov.in
2. UNODC TOC Report 2024 — unodc.org
3. Chainalysis Reactor — chainalysis.com
4. Elliptic Investigator / TRM Labs — elliptic.co
5. Meiklejohn et al., IMC 2013 — sigcomm.org
6. Weber et al. 2019, Elliptic Data Set — kaggle.com
7. TRON Developer Hub — developers.tron.network
8. FIU-IND VDA Framework — fiuindia.gov.in
