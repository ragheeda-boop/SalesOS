# 10 — Audit Maturity Model | نموذج نضج التدقيق

**Pack:** Enterprise Audit Board v2.2  
**Role:** Measure maturity of the **audit/governance process itself** (meta), not product Production Readiness  
**Status:** Framework — assessment filled only during a run  
**Honesty:** SalesOS / AQLIYA likely starts at **L1–L2** until fitness automation exists. Do **not** claim L4/L5 without continuous evidence.

> **Meta-score:** Audit Maturity is **not** rolled into product Production Readiness (Axis 39). See [07-SCORING-MODEL.md](./07-SCORING-MODEL.md).

---

## 1. Levels (ladder)

```
Level 1 Manual Audit
  → Level 2 Repeatable Audit
    → Level 3 Automated Fitness
      → Level 4 Continuous Governance
        → Level 5 Continuous Architecture Assurance
```

| Level | Name | One-line meaning |
|-------|------|------------------|
| **L1** | Manual Audit | Ad-hoc expert judgment; findings exist but method is person-dependent |
| **L2** | Repeatable Audit | Same pack, axes, evidence labels, and run template every time |
| **L3** | Automated Fitness | Fitness functions run on a schedule/CI; drift metrics collected without heroics |
| **L4** | Continuous Governance | KPI trends + history comparisons drive decisions between full board runs |
| **L5** | Continuous Architecture Assurance | Architecture constraints enforced continuously; regressions blocked by policy/fitness |

---

## 2. Criteria per level

### L1 — Manual Audit

| Criterion | Expectation |
|-----------|-------------|
| Method | Expert-led review; axes may be informal |
| Evidence | Spot checks; labels often incomplete |
| Findings | Register may exist; IDs/schema inconsistent |
| Fitness | Absent or one-off scripts |
| History | No structured run-to-run comparison |
| KPIs | Snapshot narrative only |

### L2 — Repeatable Audit

| Criterion | Expectation |
|-----------|-------------|
| Method | This pack (Charter → Run Template); axes 01–43 catalog fixed |
| Evidence | [04-EVIDENCE-STANDARD.md](./04-EVIDENCE-STANDARD.md) labels used |
| Findings | [06-FINDINGS-SCHEMA.md](./06-FINDINGS-SCHEMA.md) IDs |
| Fitness | Catalog defined ([05-FITNESS-CATALOG.md](./05-FITNESS-CATALOG.md)); **not** necessarily automated |
| History | Runs registered in [history/](./history/); prior-run comparison when a prior pack run exists |
| KPIs | [11-GOVERNANCE-KPI-DASHBOARD.md](./11-GOVERNANCE-KPI-DASHBOARD.md) snapshot filled with evidence or `—` / `not validated` |
| Axes 40–43 | Mandatory on every full run |

### L3 — Automated Fitness

| Criterion | Expectation |
|-----------|-------------|
| Fitness | ≥ agreed subset of catalog functions execute in CI or scheduled job with artifacts |
| Drift | DM metrics (Axis 41) produced from run artifacts, not only manual count |
| Gate | Failures open findings or block merge for P0-class fitness (policy defined) |
| Honesty | AI honesty / security gates remain separate; automation does not invent GO |

### L4 — Continuous Governance

| Criterion | Expectation |
|-----------|-------------|
| Cadence | KPI dashboard refreshed at least monthly **and** per board run |
| Trend | Drift, debt, economics, AI Gov Index compared vs prior run ([12-AUDIT-HISTORY-REPOSITORY.md](./12-AUDIT-HISTORY-REPOSITORY.md)) |
| Decision use | Open P0 / MTTC-P1 / drift rate inform CTO backlog between full audits |
| Multi-product | Product-specific run instances share this pack; KPIs tagged by product |

### L5 — Continuous Architecture Assurance

| Criterion | Expectation |
|-----------|-------------|
| Enforcement | Architectural constraints (boundaries, dual-engine bans, ADR↔impl) continuously enforced |
| Assurance | Regressions detected and blocked before release without waiting for a board cycle |
| Traceability | Decision Traceability (Axis 40) measurable for material decisions on an ongoing basis |
| Economics | Cost-of-change bands re-baselined on material architecture change, not only annual audit |

---

## 3. How to assess current level

Use **lowest satisfied level** (weakest-link): claim L*n* only if **all** criteria for L*n* and below are met with evidence.

| Check | Evidence sources |
|-------|------------------|
| Pack in use? | Dated run cites pack version; axes 40–43 present |
| Evidence labels? | Run appendix uses `not validated` / `light validated` / `build validated` honestly |
| Findings schema? | Register matches [06-FINDINGS-SCHEMA.md](./06-FINDINGS-SCHEMA.md) |
| History entry? | Row in [history/RUNS-INDEX.md](./history/RUNS-INDEX.md) |
| KPI snapshot? | Table from [11-GOVERNANCE-KPI-DASHBOARD.md](./11-GOVERNANCE-KPI-DASHBOARD.md) — placeholders OK if not measured |
| Fitness automated? | CI/job IDs + artifact paths (required for L3+) |
| Continuous KPI use? | Monthly refresh evidence (required for L4+) |
| Continuous enforcement? | Policy/gate evidence (required for L5) |

**Default honesty for SalesOS / AQLIYA (2026-08):** until a pack-based run is approved **and** fitness automation exists, assess **L1 or L2** only:

- Pack published + Principal Board results sibling → process assets exist → **approaching L2** for SalesOS as institutional reference.  
- No pack-based Enterprise Board **run** yet → **do not claim L2 fully achieved** until first approved run closes with history + KPI snapshot.  
- **L3–L5: not achieved** — do not claim Continuous Governance or Architecture Assurance.

Record assessment in the run template section “Audit Maturity assessment.”

---

## 4. Exit criteria (promote to next level)

| From → To | Exit criteria (all required) |
|-----------|------------------------------|
| **L1 → L2** | Approved pack-based run completed; findings schema + evidence labels; axes 40–43 attempted or explicitly scoped; history registration + KPI snapshot (values may be `—` / `not validated`) |
| **L2 → L3** | Documented fitness subset automated with stored artifacts; at least one drift metric series from automation; failures create findings or gates |
| **L3 → L4** | ≥2 comparable pack runs in history; KPI dashboard shows trend columns; monthly (or agreed) refresh without waiting for full board; product tag on KPIs |
| **L4 → L5** | Continuous enforcement of material architecture constraints; regression block evidence; DTM sampling cadence defined and executed outside annual-only audits |

Promotion requires **evidence appendix** — narrative claims alone do not raise the level.

---

## 5. Relation to product scores

| Score type | What it measures | Rolls into Axis 39? |
|------------|------------------|---------------------|
| Product axes 01–43 | System under audit | Yes (per scoring rules) |
| **Audit Maturity L1–L5** | Governance process capability | **No** — meta only |
| Governance KPIs | Process + product trend indicators | Inform CTO; do not auto-upgrade GO |

Security (Axis 30) and AI Governance (Axis 43) remain **separate** product dimensions regardless of maturity level.

---

## 6. Report line (required on every run)

```text
Audit Maturity Level: L? — <name> | Evidence: <paths> | Exit toward L?: <gaps>
```

If not assessed: `Audit Maturity Level: not validated`.

---

*Audit Maturity Model — Enterprise Audit Board v2.2 — meta-score; no L4/L5 claimed*
