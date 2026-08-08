# KPI Snapshot — EAB-2026-08-06-001

**Product:** SalesOS  
**As of:** 2026-08-06  
**Prior pack run:** none (baseline)  
**Validation:** light validated for counted items; `—` / `not validated` where unmeasured

| ID | KPI | Current | Prior | Δ | Notes |
|----|-----|---------|-------|---|-------|
| G-01 | Open P0 count | **5** | — | — | FINDINGS.md P0 |
| G-02 | Mean time to close P1 | — | — | — | not validated (no closures timed this run) |
| G-03 | Architectural Drift rate / month | — | — | — | baseline only; rate needs ≥2 runs |
| G-04 | ADR implementation ratio | **~0.4** (sample) | — | — | ~2–3 of ~5 sampled Accepted ADRs partial/mismatch; light validated |
| G-05 | Decision Traceability completion % | **~0%** full-hop | — | — | 0/8 sample rows fully ✓ end-to-end |
| G-06 | Fitness Functions activated % | **0%** | — | — | Catalog defined; none automated |
| G-07 | AI Governance Index | **~39** | — | — | Axis 43; separate from Security |
| G-08 | Engineering Economics Trend | — | — | — | needs prior pack run |
| G-09 | Security residual P0s | **2** | — | — | SEC-01, SEC-02 (factory + session/BYPASSRLS) |
| G-10 | Duplicate capability count | **≥4** clusters | — | — | decision, search, webhooks, prompt registry |
| G-11 | Dead / orphan capability count | **≥3** | — | — | FE decision twin, marketplace tip stubs, orphan MetaData KEEP |
| G-12 | Audit Maturity Level | **L2** | — | — | meta; first pack run closed |
| G-13 | Unsigned go-live gates | **≥1** (CTO/TL) | — | — | go-live-checklist UNSIGNED per GA_STATUS |

**Standing product classification:** **production no-go**

**Live numbers belong in this run folder.** Dashboard doc links here — do not invent trends.

---

*KPI Snapshot — EAB-2026-08-06-001*
