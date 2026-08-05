# 12 — Audit History Repository | مستودع تاريخ التدقيق

**Pack:** Enterprise Audit Board v2.2  
**Role:** Every Enterprise Board **run** becomes part of a historical record for trend, regression, and improvement  
**Status:** Structure ready — **no pack-based run registered yet**  
**Chain:** `Run 1 → Run 2 → Run 3 → Trend → Regression → Improvement`

---

## 1. Purpose

Enable honest answers over time:

| Question | How history helps |
|----------|-------------------|
| Is architectural drift increasing? | Compare Axis 41 `raw` / DM metrics across runs |
| Is tech debt decreasing? | Compare open debt findings, G-10/G-11 |
| Is change cost improving? | Compare Axis 42 bands (G-08) |
| Did AI governance regress? | Compare Axis 43 / G-07 (honesty caps intact) |
| Did Security residual grow? | Compare G-09 separately from AI |

Principal Board 2026-08-06 is a **results sibling**, not a v2.2 pack run — see [history/README.md](./history/README.md).

---

## 2. Repository structure

```
enterprise-audit-board/
├── history/
│   ├── README.md           # Purpose + sibling pointer
│   ├── RUNS-INDEX.md       # Master index table
│   └── (optional) KPI-YYYY-MM.md
└── (run bodies live under ga-engineering-audit/ — see naming)
```

| Path | Role |
|------|------|
| [history/README.md](./history/README.md) | Empty-repo purpose; sibling artifact link |
| [history/RUNS-INDEX.md](./history/RUNS-INDEX.md) | One row per pack-based run |
| Run body | Dated file under `docs/audit/ga-engineering-audit/` (not buried only in history/) |

---

## 3. Naming and storage

### Run ID

```text
EAB-YYYY-MM-DD
```

Optional suffix for same-day re-open: `EAB-YYYY-MM-DD-r2`.

### Run body path

```text
docs/audit/ga-engineering-audit/ENTERPRISE-AUDIT-BOARD-RUN-YYYY-MM-DD.md
```

Start from [09-AUDIT-RUN-TEMPLATE.md](./09-AUDIT-RUN-TEMPLATE.md). Do **not** create until human-approved run opens.

### Index row

Add/update a row in [history/RUNS-INDEX.md](./history/RUNS-INDEX.md) when the run **opens** (Status: `open`) and again when **closed** (Status: `closed` | `abandoned`).

### Pack version

Record pack version used (e.g. `v2.2`). Methodology changes between versions must be noted in comparison (axes added ≠ automatic score regression).

---

## 4. Registration fields (required)

Copied into run template + index:

| Field | Example |
|-------|---------|
| Run ID | `EAB-YYYY-MM-DD` |
| Date opened / closed | ISO dates |
| Scope | SalesOS / product tag + path extras |
| Pack version | v2.2 |
| Overall classification | production no-go / pilot-ready with conditions / Production GO |
| Prod Readiness (Axis 39) | score or `—` / `not validated` |
| Drift (`raw` / `drift_score`) | or `—` |
| AI Gov Index (G-07 / Axis 43) | or `—` |
| Audit Maturity Level | L1–L5 or `not validated` |
| Path | Relative link to run body |
| Prior run ID | `EAB-…` or `none` |
| Status | `open` / `closed` / `abandoned` |

---

## 5. Comparison rules vs prior run

**Comparable** only if:

1. Same **product tag** (e.g. SalesOS).  
2. Both are **pack-based** Enterprise Board runs (not Principal Board alone).  
3. Overlapping axis set documented; if pack major version differs, mark comparison `method-delta`.  
4. Metrics use the same formulas (or document formula change).

### Classification of Δ

| Signal | Rule |
|--------|------|
| **Improvement** | Open P0 ↓; or `drift_score` ↑ by ≥ agreed threshold; or economics bands net-improved; or AIGOV ↑ without honesty-cap breach |
| **Regression** | Open P0 ↑; or `raw` drift ↑; or new Security P0; or AIGOV honesty hard-cap newly triggered; or DTM completion % ↓ materially |
| **Stable** | Within noise band (state thresholds in run notes; default: no P0 change and |Δdrift_score| &lt; 5) |
| **Not comparable** | Missing prior; scope mismatch; `not validated` on both sides for that metric |

**Do not** average Principal Board scores into Enterprise run scores to erase NO-GO.

**Default thresholds** (adjust in run notes if needed):

- Material DTM change: |Δ G-05| ≥ 10 percentage points  
- Material drift: |Δ drift_score| ≥ 5 **or** any new DM-04/DM-10 finding  
- Economics: count Extreme/High rows increased → regression signal even if overall narrative is “busy”

---

## 6. Trend section (required when prior exists)

In each closed run report ([08-REPORTING-STANDARD.md](./08-REPORTING-STANDARD.md)):

```markdown
## Comparison to prior run
| Metric | Prior (EAB-…) | Current | Δ | Reading |
|--------|---------------|---------|---|---------|
| Open P0 (G-01) | — | — | — | not validated |
| Drift score | — | — | — | not validated |
| AI Gov Index | — | — | — | not validated |
| Economics trend (G-08) | — | — | — | not validated |
| Maturity Level | — | — | — | not validated |
```

If no prior pack run: write **`No prior pack-based run — baseline`**.

---

## 7. Link from Audit Run Template

[09-AUDIT-RUN-TEMPLATE.md](./09-AUDIT-RUN-TEMPLATE.md) includes:

- History registration fields  
- Prior run ID  
- Instruction to update [history/RUNS-INDEX.md](./history/RUNS-INDEX.md) on open and close  

Execution Guide step: after each run, register in history + refresh KPI dashboard ([03-EXECUTION-GUIDE.md](./03-EXECUTION-GUIDE.md)).

---

## 8. Honesty

- Empty index is correct until the first approved pack run.  
- Sibling Principal Board may be **cited** for context; it is **not** Run 1 of this repository unless a future decision explicitly backfills it as non-comparable context (prefer keep separate).  
- No fabricated trend arrows.

---

*Audit History Repository — Enterprise Audit Board v2.2 — structure ready; runs await approval*
