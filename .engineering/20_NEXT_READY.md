---
EngineeringOS: v3
GeneratedAt: 2026-08-01T14:10:00Z
RepositoryCommit: pending
RepositoryBranch: master
Generator: Execution Orchestrator
Status: ACTIVE
EvidenceLevel: Heuristic
Baseline: AI Organization v1.0 (ARB-2026-08-01-003)
---

# 20 — NEXT READY

> Orchestrator-owned dispatch queue. Agents do **not** self-select. Criterion IDs from `PHASE_0_EXIT_CHECKLIST.md`.

## Active this cycle

| # | Criterion | State | Owner | Workers | Notes |
|---|-----------|-------|-------|---------|-------|
| 1 | **7.5** Deferred-8 RLS | **VERIFIED/CLOSED** | Orchestrator | — | 18/54; Arch+Validation PASS @ 578e4f2 |
| 2 | **1.1** Decision Center IDOR | UNDER_VALIDATION | Engineering Validator | `validation/evidence-worker` | Arch PASS @ 31f3aee |
| 3 | **1.2** Webhook SSRF | READY_FOR_REVIEW | Architecture Reviewer | `architecture/adr-worker` | DEC-125 Cursor COMPLETE (board) |
| 4 | **2.3** R-14 Railway | UNDER_VALIDATION (CONDITIONAL) | Engineering Validator | `validation/evidence-worker` | Arch CONDITIONAL; D+E done |
| 2 | **1.1** Decision Center cross-tenant IDOR | READY_FOR_REVIEW | Architecture Reviewer | `architecture/adr-worker` | DEC-124 COMPLETE; HTTP IDOR regression 9/9 PASS; review only |
| 3 | **2.3** R-14 Railway Slices D–E | ASSIGNED / IN_PROGRESS | Backend Lead (+ ops) | `backend/migration-worker` (prod path) | Staging C done; D=prod image; E=bypass-probe |

## Parallel READY (next after capacity)

| Criterion | Owner | Blocked by |
|-----------|-------|------------|
| 1.2 Webhook SSRF | Backend Lead | after 1.1 handoff or parallel if disjoint |
| 1.3 CSRF X-API-Key | Architecture Reviewer | **READY FOR REVIEW** DEC-127 (Docker 11 passed); not CLOSED |
| 4.5 `.engineering/` committed | Engineering Validator | none |
| 7.4 Companies dead-column DEC | Backend Lead | after 7.5 closes |
| 7.6 alembic check clean | Backend Lead | after 7.5 |

## BLOCKED (ops/human — keep swarm busy elsewhere)

| Item | Blocked by |
|------|------------|
| 3.10 CI-08 | Org GHCR Packages write |
| 3.11 CI-09 | VPS secrets |
| 3.6 / 3.9 publish GREEN | CI-08 |

## Rule

No work without a Phase 0 criterion ID. Success = criteria CLOSED toward **54/54** (now **17/54**).
