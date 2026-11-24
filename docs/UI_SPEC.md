# ANVESHAK — Frontend UI Specification

> **Target Stack:** React 18 · TypeScript (strict) · Vite · Cytoscape.js (+ `cytoscape-dagre`) · TailwindCSS · shadcn/ui (Radix)
> **Design Philosophy:** Clean, high-contrast forensic workbench for Indian Law Enforcement Investigating Officers. Desktop-first (`>= 1024px`).

---

## 1. Layout & Global Shell

### 1.1 App Shell
- **Left Sidebar (Fixed `240px` width, Dark Slate `#0F172A`):**
  - Top Brand Header: `ANVESHAK` + `SIH26183` subtle badge.
  - Navigation Items:
    1. `Dashboard` (`/` — Home icon)
    2. `Cases` (`/cases` — FolderSearch icon)
    3. `New Case` (`/cases/new` — PlusCircle icon, primary accent)
  - Bottom Footer: `v1.0.0-mvp · TRON Mainnet`
- **Main Content Area (Light `#F8FAFC`, scrollable, padding `24px`):**
  - Top Bar: Breadcrumbs + Global Toast notification portal (top-right).

### 1.2 Status Badge Color Mapping (Global Component: `<StatusBadge />`)
| Status | Background | Text | Extra |
|---|---|---|---|
| `PENDING` | `bg-gray-100` | `text-gray-700` | — |
| `TRACING` | `bg-blue-100` | `text-blue-700` | Animated pulse dot |
| `TRACED` | `bg-green-100` | `text-green-700` | — |
| `ANALYZED` | `bg-purple-100` | `text-purple-700` | — |
| `EXPORTED` | `bg-emerald-100` | `text-emerald-800` | — |
| `CLOSED` | `bg-slate-200` | `text-slate-700` | — |
| `TRACE_FAILED` | `bg-red-100` | `text-red-700` | — |
| `ANALYSIS_FAILED` | `bg-orange-100` | `text-orange-700` | — |

---

## 2. Screen Specifications

### Screen 1: Dashboard (`/`)
- **Header:** `"Investigation Dashboard"` + `"Refresh"` button + `"New Case"` primary button.
- **Top Metrics Row (4 KPI Cards):**
  1. Total Cases
  2. Active Traces (`TRACING` count)
  3. Analyzed / Ready for Export (`ANALYZED + EXPORTED` count)
  4. Failed Traces (`TRACE_FAILED + ANALYSIS_FAILED` count)
- **Middle Section (2-column grid):**
  - Left: **Cases by Status** (simple horizontal bar or SVG pie chart showing distribution).
  - Right: **Recent 10 Cases Table**
    - Columns: `Case ID` (first 8 chars + copy tooltip), `Victim Name`, `Status` (`<StatusBadge />`), `Seed Wallet` (`T1234...5678`), `Created At` (relative + ISO tooltip), `Actions` (`View` link to `/cases/:id`).
- **States:**
  - *Loading:* Skeleton rows.
  - *Empty:* Centered card: `"No cases yet. Create your first investigation case."` + `"Create Case"` CTA button.
  - *Error:* Red alert banner with `"Retry"` button.

---

### Screen 2: Case List (`/cases`)
- **Header:** `"All Investigation Cases"` + `"New Case"` button (top-right).
- **Filter Bar:**
  - Search input (`placeholder="Search victim name or complaint ID..."`, debounced 300ms)
  - Status dropdown (`All`, `PENDING`, `TRACING`, `TRACED`, `ANALYZED`, `EXPORTED`, `CLOSED`, `TRACE_FAILED`)
  - Date From / Date To inputs
  - `"Clear Filters"` button
- **Full-Width Table:**
  - Columns: `Case ID` (truncated UUID), `Complaint ID` (or `—`), `Victim Name`, `Status` (`<StatusBadge />`), `Seed Wallets` (count badge), `Created At`, `Updated At`, `Actions` (`View`).
  - Sorting: Clickable headers for `Created At`, `Updated At`, `Status`, `Victim Name`. Default: `created_at DESC`.
- **Pagination Bar (Bottom):**
  - `"Showing X–Y of Z cases"` + Previous / Page numbers / Next (`20` items per page).
- **Empty State (when filters match nothing):** `"No cases match your filters."` + `"Reset Filters"` button.

---

### Screen 3: Create Case (`/cases/new`)
- **Header:** `"Register New Investigation Case"`
- **Form Fields & Inline Validation:**
  1. `Victim Name` (`text`, required, 1–255 chars)
  2. `Victim Contact` (`text`, optional, max 255 chars)
  3. `Complaint ID / NCRP Reference` (`text`, optional, max 50 chars, pattern `^[A-Za-z0-9/_-]+$`)
  4. `Reported Date & Time` (`datetime-local`, required, default current time, cannot be future)
  5. `Description` (`textarea`, required, max 5000 chars, live character counter `0 / 5000`)
  6. `Tags` (chip/tag input with quick-select suggestions: `pig-butchering`, `romance-scam`, `investment-fraud`, `job-scam`, `loan-fraud`, `other`; max 10 tags)
  7. **Seed Wallets Section (Dynamic Array, minimum 1 row):**
     - Header + `"+ Add Wallet"` button (max 10)
     - Each row contains:
       - `Address` (`text`, required; inline validation: must match `^T[1-9A-HJ-NP-Za-km-z]{33}$` -> error `"Invalid TRON address: must start with T and be 34 Base58 characters"`)
       - `Chain` (select, default `"TRON"`, disabled in MVP with tooltip `"TRON only in MVP"`)
       - `Token` (select/text, default `"USDT"`)
       - `Reported Amount` (`number`, optional, step `0.01`, must be `> 0`)
       - `TX Hash` (`text`, optional, 64 hex chars validation)
       - Remove button (`X`, disabled if only 1 wallet remains)
- **Submit Action:**
  - `"Create Investigation Case"` button (disabled while submitting, shows spinner).
  - Calls `POST /api/v1/cases`.
  - On `201`: Toast `"Case created"` → redirect to `/cases/{id}`.
  - On `409/422`: Map API errors to inline fields + toast error.

---

### Screen 4: Case Detail (`/cases/:id`)
- **Top Sticky Header:**
  - Case Title: `Case #{id.slice(0,8)}` + `Complaint ID` (if present) + `<StatusBadge />`
  - Timestamps: `Reported: ...` · `Created: ...`
  - Quick Action Button:
    - If `status === 'PENDING'` or `'TRACE_FAILED'`: `"Start Trace"` (blue primary button) → opens optional Trace Config popover or runs defaults via `POST /api/v1/cases/{id}/trace`.
    - If `status === 'ANALYZED'` or `'EXPORTED'`: `"Export PDF"` quick button.
- **Tab Bar (5 Tabs):**
  1. `Overview`
  2. `Graph`
  3. `Candidates` (shows count badge, e.g. `Candidates (2)`)
  4. `Evidence`
  5. `Action Package`

#### Tab 1: Overview
- Victim Details Card (Name, Contact, Complaint ID, Description, Tags).
- Seed Wallets Table (Address with TronScan link, Chain, Token, Reported Amount, TX Hash).
- Trace Configuration Card (if trace has run: hop limit, time window, degree cap, amount threshold).

#### Tab 2: Graph (Cytoscape Interactive Component)
- **States:**
  - `PENDING`: Empty state card `"Click 'Start Trace' to begin automated blockchain analysis."` with `"Start Trace"` button.
  - `TRACING`: Centered spinner + `"Tracing TRON blockchain flows (1–3 hops)..."` + elapsed timer. Polls `GET /api/v1/cases/{id}` every **3,000 ms**. When status leaves `TRACING`, fetches `GET /api/v1/cases/{id}/graph`.
  - `TRACE_FAILED`: Red error state `"Trace failed. Check TronGrid connectivity or retry."` + `"Retry Trace"` button.
  - `TRACED / ANALYZED / EXPORTED`: Renders Cytoscape canvas + Trace Metadata strip + Right Inspection Drawer.
- **Trace Metadata Strip (above canvas):**
  - `Hops Explored` | `Addresses Found` | `After Pruning` | `Cycles Detected` | `Elapsed Time`
- **Graph Toolbar:**
  - `Fit to Screen` | `Zoom In (+)` | `Zoom Out (-)` | `Layout` dropdown (`Dagre (Hierarchical)` default, `Circle`, `Grid`) | `Show Pruned Edges` toggle | `Save as PNG` button.
- **Cytoscape Styling Rules:**
  - `seed` node: `#EF4444` (Red) circle, `40px`, white label text.
  - `intermediate` node: `#64748B` (Slate gray) circle, `30px`.
  - `vasp_candidate` node: `#10B981` (Emerald green) diamond shape, `36px`, bold border.
  - `unknown` node: `#CBD5E1` (Light gray) circle, `25px`.
  - Edges: Directed arrow (`triangle`), width scaled linearly by amount (`1px` min to `5px` max), label `"{amount} USDT"`, color darkened by `hop_depth`.
- **Click-to-Inspect Side Panel (`320px`, slides open on node/edge click):**
  - *Node Selected:* Full TRON address (with copy button + TronScan link), Node Type badge, Hop Depth, VASP Label & Confidence (if attributed), In-Degree / Out-Degree, Total Received / Sent (USDT).
  - *Edge Selected:* TX Hash (with TronScan link `https://tronscan.org/#/transaction/{hash}`), From → To, Amount + Token, Timestamp, Hop Depth.

#### Tab 3: Candidates
- **Ranked VASP Candidates Table:**
  - Columns: `Rank` (`#1`, `#2`...), `VASP Label` (e.g. `"WazirX"` or `"Unattributed High-Volume"`), `Address` (copyable + TronScan link), `Source` (`public` / `agency` / `heuristic`), `Confidence` (progress bar + `%`), `Review Status`, `Actions` (`Accept` ✓ / `Reject` ✗ buttons calling `POST .../review`).
  - **Expandable Row:** Clicking a row expands the **6-Signal Scoring Breakdown** (`label_match_score`, `hop_depth_score`, `amount_relevance_score`, `time_gap_score`, `path_continuity_score`, `degree_fanout_score`) as horizontal mini-bars + linked `evidence_path_ids`.
- **Empty State:** `"No VASP candidates identified above the 20% confidence threshold."`

#### Tab 4: Evidence
- **Investigation Summary Banner:** Total flow traced, Flow retained after pruning `%`, Hops explored.
- **Evidence Paths Accordion:** Grouped by VASP Candidate.
  - Each Path card shows `Path ID`, `Total Flow (USDT)`, `Hop Count`, and a vertical timeline table of every hop (`Step`, `From`, `To`, `Amount`, `TX Hash` linked to TronScan, `Timestamp`).

#### Tab 5: Action Package
- **Action Bar:** `"Download PDF Report"` (calls `GET /api/v1/cases/{id}/action-package/export`) + `"Download JSON"` (downloads `GET /api/v1/cases/{id}/action-package`).
- **On-Screen Preview:**
  - Classification Banner: `CONFIDENTIAL — LAW ENFORCEMENT USE ONLY`
  - Recommended Actions Cards (with Priority badge, Legal Basis, Target Entity, Urgency badge)
  - Applicable Legal References Table (IT Act, IPC, CrPC, PMLA, FIU-IND)
  - Mandatory Disclaimers Box

---

## 3. Frontend Architecture & API Client

- **State Management:** React Context (`CaseContext`) for active case state; local `useState` for form & UI state. No Redux/Zustand in MVP.
- **API Client (`src/services/api.ts`):** Typed `fetch` wrapper reading `import.meta.env.VITE_API_BASE_URL` (default `http://localhost:8000/api/v1`). Throws structured `ApiError(status, detail)` caught by components to display toast notifications.
