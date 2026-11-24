# ANVESHAK — Architecture Decision Records (ADR)

> We record every significant technical decision here. Once a decision is made,
> it's followed unless a new ADR supersedes it.

---

## ADR-001: Use FastAPI for Backend

**Status:** Accepted
**Date:** 2026-11-24
**Context:** Need an async-capable Python web framework with native OpenAPI support.
**Decision:** Use FastAPI with Uvicorn.
**Rationale:**
- Native async/await for concurrent blockchain API calls
- Auto-generated OpenAPI docs (critical for team velocity)
- Pydantic integration for request/response validation
- Strong Python typing support
**Consequences:** Team must learn async Python patterns. All endpoints must be async.

---

## ADR-002: PostgreSQL as Primary Database

**Status:** Accepted
**Date:** 2026-11-24
**Context:** Need relational storage for cases, transactions, labels, and evidence.
**Decision:** PostgreSQL 16+ with SQLAlchemy ORM and Alembic migrations.
**Rationale:**
- JSON/JSONB support for flexible blockchain data
- Strong indexing for transaction lookups
- Proven at scale for financial data
- Alembic provides version-controlled migrations
**Consequences:** All schema changes go through Alembic. No raw DDL in production.

---

## ADR-003: NetworkX for Graph Engine (MVP)

**Status:** Accepted
**Date:** 2026-11-24
**Context:** Need a graph library for multi-hop transaction traversal and pruning.
**Decision:** NetworkX for MVP; evaluate Neo4j / igraph for Phase 2 if performance
requires it.
**Rationale:**
- Pure Python — no external service dependency for MVP
- Sufficient for 1–3 hop graphs with pruning
- Rich algorithm library (shortest path, centrality, etc.)
- Easy to test and debug
**Consequences:** May need to migrate to a graph database if graphs exceed ~100K nodes.

---

## ADR-004: TRON-First Chain Support

**Status:** Accepted
**Date:** 2026-11-24
**Context:** Most India-targeted crypto fraud uses USDT on TRON (cheapest fees).
**Decision:** MVP supports TRON only via TronGrid API. EVM chains in Phase 2.
**Rationale:**
- TRON + USDT is the dominant fraud vector in Indian cybercrime reports
- TronGrid provides free-tier API access
- Focused scope for hackathon delivery
**Consequences:** Chain adapter must be abstracted behind an interface so EVM/BTC
can plug in later without touching the graph engine.

---

## ADR-005: React + Cytoscape.js for Frontend

**Status:** Accepted
**Date:** 2026-11-24
**Context:** Investigators need to visualize fund-flow graphs and interact with them.
**Decision:** React (Vite) + Cytoscape.js for graph rendering.
**Rationale:**
- Cytoscape.js is purpose-built for network graph visualization
- Supports interactive pan/zoom, click-to-inspect, layout algorithms
- React ecosystem for the rest of the UI (forms, tables, etc.)
**Consequences:** Frontend dev must learn Cytoscape.js API. Graph data must be
serialized in Cytoscape's JSON format from the backend.

---

## ADR-006: Pruning-First Graph Strategy

**Status:** Accepted
**Date:** 2026-11-24
**Context:** Naïve multi-hop traversal explodes: 1 → 20 → 400 → 8,000 nodes.
**Decision:** Apply pruning filters at every hop before fetching the next level.
**Filters:**
1. Hop limit (configurable, default 3)
2. Amount relevance (drop below threshold)
3. Time window (only txns within complaint timeframe ± buffer)
4. Degree cap (skip high-fan-out addresses like exchange hot wallets)
5. Path continuity (drop dead-end branches)
6. Duplicate removal
**Consequences:** May miss some paths. Confidence scoring must reflect pruning
decisions. Investigators can manually increase limits if needed.

---

## Template for New ADRs

```markdown
## ADR-XXX: <Title>

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-YYY
**Date:** YYYY-MM-DD
**Context:** <What problem or question prompted this decision?>
**Decision:** <What did we decide?>
**Rationale:** <Why this over alternatives?>
**Consequences:** <What trade-offs or follow-up work does this create?>
```
