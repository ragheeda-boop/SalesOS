# 07 — Scoring Model | نموذج التقييم

**Pack:** Enterprise Audit Board v2.1  
**Role:** Per-axis scores, dimension rollups, economics bands, drift formula, GO synthesis  
**Status:** Method only — **no scores filled** in framework docs

---

## 1. Per-axis score (0–100)

| Score band | Meaning |
|------------|---------|
| 90–100 | Evidence of strong control / alignment; residual P3–P4 only |
| 70–89 | Mostly healthy; tracked P1–P2 with owners |
| 50–69 | Material gaps; pilot conditions likely blocked |
| 30–49 | Weak; multiple P0/P1 or large unvalidated surface |
| 0–29 | Critical failure or honesty breach |
| **N/A** | Out of approved scope (justify) |

Unexecuted axis → leave **blank** or mark `not scored — not validated`. **Do not invent numbers.**

---

## 2. Dimension rollups

| Dimension | Axes (primary) | Rollup method |
|-----------|----------------|---------------|
| **Architecture & Domain** | 01–07, 23–28 | Mean of scored axes; any P0 on 01/07/28 caps dimension ≤49 |
| **Docs & Decision Lineage** | 08–10, **40** | Mean; missing DTM for sample set caps ≤59 |
| **Data & Runtime** | 11, 15–19 | Mean of scored |
| **Product & Ops** | 20–22, 29, 31 | Mean; UNSIGNED go-live with P0 open → ≤49 |
| **Security** | **30** only | Axis 30 score (do **not** blend AI) |
| **AI Governance** | 12–14 + **43** | Axis **43** is the dimension score; 12–14 are inputs/evidence |
| **Engineering Economics** | **42** (+ signals from 23–24) | **Not** a 0–100 mean — see §3 |
| **Drift** | **41** (+ 08, 26, fitness) | Drift score formula §4 |
| **Delivery honesty** | 32–34 | Mean; testing honesty P0 → dimension ≤39 |
| **Executive synthesis** | 35–39 | Narrative + verdict; not averaged into “feel-good” GO |

Missing mandatory v2.1 axes (40–43) in a claimed “full” run → overall synthesis stays **production no-go**.

---

## 3. Engineering Economics — ordinal cost bands (Axis 42)

Do **not** invent dollar figures. Use:

| Band | Meaning (CTO lens) |
|------|---------------------|
| **Low** | Localized change; clear extension point; &lt;1 engineer-week typical |
| **Med** | Cross-module; docs+tests+ADR needed; order of weeks |
| **High** | Structural friction (dual paths, missing SoT); month-scale / multi-team |
| **Extreme** | Architecture refactor prerequisite; unsafe without major program |

**Required cost rows:**

1. Add Capability  
2. Add country/locale (دولة)  
3. Add Tenant  
4. Framework upgrade  
5. DB change  
6. Delete Module  

**Dimension output:** table of six bands + “dominant friction” narrative. Optional: map Extreme→0–24, High→25–49, Med→50–74, Low→75–100 **only** if a single index is needed — label it `economics_index (derived)` and keep bands authoritative.

---

## 4. Drift score formula sketch (Axis 41)

Let metrics DM-01…DM-10 be non-negative counts ([05-FITNESS-CATALOG.md](./05-FITNESS-CATALOG.md)).

```text
raw = w1*DM-01 + w2*DM-02 + w3*DM-03 + w4*DM-04 + w5*DM-05
    + w6*DM-06 + w7*DM-07 + w8*DM-08 + w9*DM-09 + w10*DM-10
```

Suggested default weights (adjust in run notes if needed):  
`w1=3, w2=2, w3=2, w4=4, w5=3, w6=3, w7=2, w8=3, w9=2, w10=5`  
(AI honesty breaches and dual engines weigh heavier.)

```text
drift_score = max(0, 100 - min(100, raw))
```

- Higher **drift_score** = healthier (less drift).  
- First run: publish `raw`, weights, and `drift_score` as **baseline**.  
- Later runs: report Δraw and Δscore.  
- If metrics not collected: Axis 41 = `not scored — not validated` (do not fake 70).

---

## 5. AI Governance dimension (Axis 43)

Score each sub-factor 0–100 or N/A:

AI Safety, Explainability, Auditability, Prompt Governance, Tool Governance, Memory Governance, Human Override, Decision Transparency, Model Independence, Vendor Lock-in.

```text
AIGOV = mean(scored sub-factors)
```

**Hard caps (honesty):**

- If `feature_ai_copilot` default is not False in SoT config → cap **≤29** and open P0.  
- If FE Decision STUB is presented as live GA AI → cap **≤29** and open P0.  
- If consequential AI path lacks Human Override → cap **≤49**.  

**Security (30) and AIGOV (43) must appear as separate lines** on the scorecard — never merged.

---

## 6. Overall production readiness synthesis (Axis 39)

Rules (binding):

1. **No Production GO** without executable evidence appendix and closed P0s.  
2. Any mandatory axis `not validated` that is P0 for GA → classification **production no-go**.  
3. Security &lt; 60 **or** AIGOV honesty hard-cap triggered → **production no-go**.  
4. Drift score &lt; 40 (when measured) → cannot claim better than **pilot-ready with conditions**, and only if P0s closed.  
5. Economics with ≥2 **Extreme** rows → call out as structural gate in CTO brief (not automatic GO).  
6. Default when uncertain: **production no-go**.  
7. Comparison to Principal Board 2026-08-06 allowed **only** with evidence deltas — do not “average up” to erase NO-GO.

Allowed classifications: `production no-go` | `pilot-ready with conditions` | `Production GO` (rare; evidence-gated).

---

## 7. Scorecard skeleton (empty)

| Axis | Score | Label | Findings |
|------|-------|-------|----------|
| 01 … 43 | — | not validated | — |
| Security dim | — | — | Axis 30 |
| AI Governance dim | — | — | Axis 43 |
| Drift score | — | — | Axis 41 |
| Economics bands | — | — | Axis 42 |
| **Overall** | — | **production no-go** (pending run) | Axis 39 |

---

*Scoring Model — Enterprise Audit Board v2.1 — no fabricated scores*
