---
EngineeringOS: v3
GeneratedAt: 2026-08-01T21:00:00Z
RepositoryCommit: 9fa8e9f
RepositoryBranch: master
Generator: Backend Lead (DEC-141)
Status: Active (ADR-036 Phase 2 bridge)
EvidenceLevel: Measured
Revalidation: Active (DEC-142)
---

# 33 — PROGRAM LAYER BRIDGE

> **Purpose:** `.engineering/` → `docs/program/` references only. **No data duplication.**  
> **Authority:** ADR-036 Phase 2 · Phase 0 criterion **9.2** · DEC-141  
> **Rule:** Engineering Spec lives here. Business Truth lives in `docs/program/`. Link; do not copy sprint status, DEC bodies, or Phase 0 counts into EOS catalogs.

---

## Layer map (pointer only)

| Layer | Location | Owns | Does not own |
|-------|----------|------|--------------|
| Business Truth | `docs/program/` | Vision, roadmap, sprint, DEC-*, risks, Phase 0 exit | Architecture catalogs, ownership maps, EOS locks |
| Engineering Spec | `.engineering/` | Architecture, ADR index (EOS), capability map, locks, quality gates | Sprint board status, business priority |
| AI Organization | `.ai/` | Org baseline 1.0 (ARB-003); full Agent OS runtime DEFERRED (9.3 / DEC-146) | Running scheduler/queue |
| Implementation | `salesos/` | Code, tests, infra | Governance prose |

Full four-layer decision: `docs/adr/0036-engineering-organization-layer-separation.md`.

---

## Canonical Business Truth entry points

| Need | Path (do not duplicate contents here) |
|------|----------------------------------------|
| Phase 0 exit criteria | `docs/program/PHASE_0_EXIT_CHECKLIST.md` |
| Execution DAG (READY/BLOCKED) | `docs/program/EXECUTION_DAG.md` |
| Sprint delivery board | `docs/program/SPRINT_05_DELIVERY_BOARD.md` |
| Decision log | `docs/program/DECISION_LOG.md` |
| Decision packages | `docs/program/decisions/` |
| Risk register | `docs/program/RISK_REGISTER.md` |
| Master execution plan | `docs/program/MASTER_EXECUTION_PLAN.md` |
| Product roadmap | `docs/program/PRODUCT_ROADMAP.md` |
| Reverse bridge (program → engineering) | `docs/program/ENGINEERING_LAYER_BRIDGE.md` |

---

## Reciprocal

Program agents enter Engineering Spec via `docs/program/ENGINEERING_LAYER_BRIDGE.md`.

---

## Honesty

- Fingerprint re-measured at tip `9fa8e9f` (DEC-142); EvidenceLevel **Measured**; Revalidation **Active** — criteria **4.2 / 4.4 / 4.7** **CLOSED** (DEC-142a). Residuals ARB **4.1 / 4.8**.
- **Production GO not claimed. CI GREEN not met.**
