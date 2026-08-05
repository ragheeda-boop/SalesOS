# 11 — Governance KPI Dashboard | لوحة مؤشرات الحوكمة

**Pack:** Enterprise Audit Board v2.2  
**Role:** Fixed performance indicators so the board measures **trend**, not only snapshot  
**Status:** Template — **no invented current numbers**; use `—` / `not validated` until a run measures them  
**Cadence:** Fill **per run**; refresh **monthly** between runs when data exists (L4 target)

---

## 1. Design rules

1. Every KPI has: **definition/formula**, **data source**, **cadence**, **direction** (↑ better / ↓ better).  
2. Missing data → `—` or `not validated` — never invent.  
3. Security residual P0s stay visible separately from AI Governance Index.  
4. Product tag required when multi-product (default: `SalesOS`).  
5. KPIs inform CTO backlog; they do **not** auto-declare Production GO.

---

## 2. Core KPI definitions

| ID | KPI | Definition / formula | Data source | Cadence | Direction |
|----|-----|----------------------|-------------|---------|-----------|
| **G-01** | Open P0 count | Count of findings severity **P0** with status `open` / `accepted-risk` (state accepted-risk in notes) | Findings register ([06-FINDINGS-SCHEMA.md](./06-FINDINGS-SCHEMA.md)); seed [APPENDIX-C-FINDINGS-REGISTER.md](../APPENDIX-C-FINDINGS-REGISTER.md) | Per run + monthly | ↓ better |
| **G-02** | Mean time to close P1 | Mean(`closed_at − opened_at`) for P1 findings closed in window; exclude still-open | Findings register timestamps | Monthly (rolling 90d preferred) | ↓ better |
| **G-03** | Architectural Drift rate / month | Δ`raw` (Axis 41) ÷ months between comparable measurements; or Δ count of DM-01…DM-10 weighted sum | Axis 41 appendix; [05-FITNESS-CATALOG.md](./05-FITNESS-CATALOG.md); [history/](./history/) | Per run; monthly if fitness automated | ↓ better (less new drift) |
| **G-04** | ADR implementation ratio | `ADRs with verified impl path` ÷ `Accepted ADRs in sample` (state sample) | ADR set + Axis 08/40 evidence | Per run | ↑ better |
| **G-05** | Decision Traceability completion % | Rows with all hops `✓` (or justified `n/a`) ÷ DTM sample rows × 100 | Axis 40 DTM in run report | Per run | ↑ better |
| **G-06** | Fitness Functions activated % | `Fitness functions with automated run + artifact in period` ÷ `Catalog entries in scope` × 100 | [05-FITNESS-CATALOG.md](./05-FITNESS-CATALOG.md) + CI/job artifacts | Per run + monthly | ↑ better |
| **G-07** | AI Governance Index | Axis **43** score `AIGOV` (mean of scored sub-factors); honesty hard-caps apply | Axis 43 scorecard; [AI_HONESTY.md](../AI_HONESTY.md) | Per run | ↑ better |
| **G-08** | Engineering Economics Trend | Ordinal movement of the six cost bands (Axis 42): count of bands that improved / worsened / unchanged vs prior run | Axis 42 tables across [history/](./history/) | Per run (needs prior) | ↑ improved count |

### Companion KPIs (recommended)

| ID | KPI | Definition / formula | Data source | Cadence | Direction |
|----|-----|----------------------|-------------|---------|-----------|
| **G-09** | Security residual P0s | Open P0 findings tagged Security / Axis 30 | Findings register (Security only) | Per run + monthly | ↓ better |
| **G-10** | Duplicate capability count | Count of confirmed duplicate capability clusters (Axis 26) | Axis 26 findings / DM-04 signals | Per run | ↓ better |
| **G-11** | Dead / orphan capability count | Dead capabilities + orphan ADRs/capabilities (Axes 27, DM-02/03) | Axes 27, 41 metrics | Per run | ↓ better |
| **G-12** | Audit Maturity Level | L1–L5 from [10-AUDIT-MATURITY-MODEL.md](./10-AUDIT-MATURITY-MODEL.md) | Maturity assessment in run | Per run | ↑ better (meta) |
| **G-13** | Unsigned go-live gates | Count of required go-live signatures still UNSIGNED | [runbooks/go-live-checklist.md](../runbooks/go-live-checklist.md) / GA_STATUS | Per run + monthly | ↓ better |

---

## 3. Dashboard table template (copy into each run)

**Product:** — (default SalesOS)  
**As of:** —  
**Prior comparable run:** — / none  
**Validation:** not validated | light validated | build validated  

| ID | KPI | Current | Prior | Δ | Cadence last met | Notes / evidence path |
|----|-----|---------|-------|---|------------------|------------------------|
| G-01 | Open P0 count | — | — | — | — | not validated |
| G-02 | Mean time to close P1 | — | — | — | — | not validated |
| G-03 | Architectural Drift rate / month | — | — | — | — | not validated |
| G-04 | ADR implementation ratio | — | — | — | — | not validated |
| G-05 | Decision Traceability completion % | — | — | — | — | not validated |
| G-06 | Fitness Functions activated % | — | — | — | — | not validated |
| G-07 | AI Governance Index | — | — | — | — | Separate from Security |
| G-08 | Engineering Economics Trend | — | — | — | — | needs prior run |
| G-09 | Security residual P0s | — | — | — | — | Separate from AI Gov |
| G-10 | Duplicate capability count | — | — | — | — | not validated |
| G-11 | Dead / orphan capability count | — | — | — | — | not validated |
| G-12 | Audit Maturity Level | — | — | — | — | meta; not Axis 39 |
| G-13 | Unsigned go-live gates | — | — | — | — | not validated |

**Standing product classification (context only):** production no-go until evidence changes it — do not encode fake GO in this table.

---

## 4. Trend reading (with history)

When ≥2 pack runs exist ([12-AUDIT-HISTORY-REPOSITORY.md](./12-AUDIT-HISTORY-REPOSITORY.md)):

| Question | Primary KPIs |
|----------|----------------|
| Is drift increasing? | G-03, Axis 41 `raw` / `drift_score` |
| Is tech debt decreasing? | G-10, G-11, Axis 24 findings closed |
| Is change cost improving? | G-08 (band movements) |
| Is AI governance honest & improving? | G-07 (watch honesty caps) |
| Is security residual shrinking? | G-01 (all P0), G-09 (security P0) |

Regression / improvement rules: see History Repository § comparison rules.

---

## 5. Refresh checklist (after each run + monthly)

1. Recompute G-01, G-09 from live findings register.  
2. Update G-02 if closures occurred in window.  
3. If fitness jobs ran: update G-06 and any automated DM inputs for G-03.  
4. Copy snapshot into latest run appendix **or** dated monthly note under `history/` (optional `KPI-YYYY-MM.md`).  
5. Do not backfill invented history.

---

*Governance KPI Dashboard — Enterprise Audit Board v2.2 — placeholders only until measured*
