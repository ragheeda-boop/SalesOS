# Scorecard — EAB-2026-08-06-001

**Evidence class:** light validated (static)  
**Rule:** Prefer ranges / honest integers with notes; `not validated` where access insufficient  
**Mandatory axes 40–43:** scored from this run's evidence

---

## Axis scores (0–100)

| Axis | Name | Score | Label | Finding IDs |
|------|------|------:|-------|-------------|
| 01 | Architecture Governance | 40 | light validated | EAB-001-P1-DOC-01, EAB-001-P0-DUP-01 |
| 02 | Business Architecture | 50 | light validated | EAB-001-P1-LINEAGE-01 |
| 03 | Information Architecture | 48 | light validated | EAB-001-P0-FE-01 |
| 04 | Capability Architecture | 45 | light validated | EAB-001-P0-DUP-01, EAB-001-P1-DUP-02 |
| 05 | Service Architecture | 42 | light validated | EAB-001-P1-OPS-02, EAB-001-P0-SEC-01 |
| 06 | Domain Model | 48 | light validated | EAB-001-P1-DRIFT-01 |
| 07 | DDD Boundaries | 50 | light validated | — (layout recognizable; not deep import-graph) |
| 08 | ADR Compliance | 45 | light validated | EAB-001-P1-ADR-01 |
| 09 | SES Compliance | 20 | light validated | EAB-001-P1-SES-01 |
| 10 | Product Bible Compliance | 40 | light validated | EAB-001-P1-DOC-01 |
| 11 | Runtime Audit | 45 | light validated | EAB-001-P0-SEC-02, EAB-001-P1-OPS-02 |
| 12 | AI Agent Audit | 35 | light validated | EAB-001-P1-AIGOV-01 |
| 13 | Prompt Audit | 38 | light validated | EAB-001-P1-DUP-02 |
| 14 | Knowledge Audit | 42 | light validated | EAB-001-P1-LINEAGE-01 |
| 15 | Event Audit | 45 | light validated | EVENT_BUS in_memory default |
| 16 | Graph Audit | 48 | light validated | Neo4j present; product completeness open |
| 17 | Search Audit | 45 | light validated | EAB-001-P1-DUP-02 |
| 18 | Data Lineage Audit | 35 | light validated | EAB-001-P1-LINEAGE-01 |
| 19 | Canonical Object Audit | 48 | light validated | ER module exists; pipeline break |
| 20 | Customer Journey Audit | 50 | light validated | PAGE_MAP / e2e exist; browser GA not validated |
| 21 | Business Rule Audit | 45 | light validated | EAB-001-P0-DUP-01 |
| 22 | Operational Readiness | 40 | light validated | EAB-001-P0-OPS-01 |
| 23 | Platform Extensibility | 48 | light validated | modules/packages numerous; high friction |
| 24 | Technical Debt Evolution | 55 | light validated | Debt mapped; structural roots remain |
| 25 | Legacy Detection | 50 | light validated | EAB-001-P1-DRIFT-01 |
| 26 | Duplicate Capability | 35 | light validated | EAB-001-P0-DUP-01, EAB-001-P1-DUP-02 |
| 27 | Dead Capability | 45 | light validated | STUB/twin packages; marketplace tips |
| 28 | Architecture Fitness Tests | 15 | light validated | EAB-001-P2-FIT-01 |
| 29 | Release Governance | 50 | light validated | UNSIGNED go-live; waves documented |
| 30 | Security | **70** | light validated | EAB-001-P0-SEC-01/02; control presence |
| 31 | DevOps / DR | 45 | light validated | EAB-001-P0-OPS-01, EAB-001-P1-OPS-02 |
| 32 | Testing Honesty | 55 | light validated | Suites exist; **not re-run** this board |
| 33 | Backend Scorecard | 46 | light validated | P0 wiring gaps |
| 34 | Frontend Scorecard | 40 | light validated | EAB-001-P0-FE-01 |
| 35 | CTO Readiness | 40 | light validated | Narrative — see RUN-REPORT |
| 36 | CEO Executive Summary | 55 | light validated | Delivered — honesty high |
| 37 | 30/60/90 Recovery | 55 | light validated | Delivered in RUN-REPORT |
| 38 | 12-Month Roadmap | 55 | light validated | Delivered in RUN-REPORT |
| 39 | Production Readiness Synthesis | **41** | light validated | **production no-go** |
| 40 | Decision Traceability Matrix | **35** | light validated | Sample DTM incomplete |
| 41 | Architectural Drift Detection | **0** | light validated | drift_score formula (raw≈125) |
| 42 | Engineering Economics | bands | light validated | See economics table (not 0–100 mean) |
| 43 | AI Governance Score | **39** | light validated | Honesty gates hold; structural weak |

---

## Dimension rollups

| Dimension | Score / bands | Notes |
|-----------|---------------|-------|
| Architecture & Domain | ~44 | P0 dual engines + MetaData sprawl |
| Docs & Decision Lineage | ~35 | SES missing; DTM breaks; ADR index drift |
| Data & Runtime | ~43 | Lineage break; singleton sessions |
| Product & Ops | ~45 | DR P0; UNSIGNED gates |
| **Security (Axis 30)** | **~70** | Separate from AI; residual P0s remain |
| **AI Governance (Axis 43)** | **~39** | Separate from Security |
| Drift score (Axis 41) | **0** (raw ≈125) | Baseline; MetaData weight dominates |
| Engineering Economics | High–Extreme dominant | ≥2 Extreme rows |
| Delivery honesty | ~50 | Testing not re-run; FE verify gaps |
| **Overall (synthesis)** | **~46** | **production no-go** |

---

## Security note

Score **~70** reflects **control presence** (CSRF, RS256 JWT, RBAC deps, RLS intent, AI honesty flags) re-spot-checked against Principal Board **72**. Residual **P0** fail-open / BYPASSRLS paths remain — **not** a Production GO signal. Supersedes stale 2026-07-22 Security **48** for control inventory only.

---

## Comparison to Principal Board (sibling, not prior EAB)

| Dimension | Principal 2026-08-06 | This EAB run | Note |
|-----------|---------------------:|-------------:|------|
| Production readiness | ~42 | **~41** | Confirmed NO-GO |
| Security | 72 | **~70** | Re-spot-check; residual P0s |
| Overall | ~49 | **~46** | Deeper drift/AI axes pulled synthesis |
| AI Governance | (not separate axis) | **~39** | New mandatory Axis 43 |

---

*Scorecard — EAB-2026-08-06-001*
