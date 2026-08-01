---
EngineeringOS: v3
GeneratedAt: 2026-08-01T12:11:50Z
RepositoryCommit: c89025a
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Heuristic
Revalidation: Pending
---

# 27 â€” ADR INDEX

> Purpose: complete registry of Architecture Decision Records for SalesOS, as observed in the repository at commit `c89025a` (re-pinned from `3749c30` after ARB audit `32`).
> **Discrepancies are recorded here as observed facts. They are NOT fixed during bootstrap.**

## 1. Sources (evidence)

| Source | Path | Content |
|---|---|---|
| Parent repo ADRs | `docs/adr/index.md`, `docs/adr/0029/0030/0031/0032/0033/0034/0035/0036-*.md`, `docs/ADR-Data-001-identity-resolution-v3.md` | product-root ADR set incl. ADR-036 |
| Governance submodule | `engineering-os/adr/` (submodule HEAD `b82b9fb`, branch `main`) | 5 ADR files (001, 002, 003, 0032, 012); no separate index.md |
| Pending decisions | `docs/vnext/DECISIONS.md` | 16 decision items (D-001..D-016), all Proposed except D-016 Approved |
| Index references | `docs/adr/index.md` | lists ADR-001..003, 025..036 (DEC-139 registers ADR-036) |

## 2. Master ADR table (as-observed)

| ID | Title | Status (best evidence) | Date | Domain | File location |
|---|---|---|---|---|---|
| ADR-001 | Modular Monolith Foundation | Accepted | 2026-06-01 (index) / 2026-07-12 (file) | Architecture | `engineering-os/adr/ADR-001-modular-monolith-foundation.md` |
| ADR-002 | Executive Intelligence Workspace | Accepted | 2026-06-05 (index) / 2026-07-10 (file) | Product | `engineering-os/adr/ADR-002-executive-intelligence-workspace.md` |
| ADR-003 | Widget SDK v1 Freeze | Accepted | 2026-06-10 (index) / 2026-07-10 (file) | Widget SDK | `engineering-os/adr/ADR-003-widget-sdk-v1-freeze.md` |
| ADR-0032 | Widget SDK Reconciliation (alias of ADR-032) | Proposed (DEC-138; alias retained) | 2026-07-17 | Widget SDK | `engineering-os/adr/ADR-0032-widget-sdk-reconciliation.md` (canonical citation **ADR-032**) |
| ADR-012 | Activity Intelligence Capability | Proposed (not in index) | 2026-07-18 | Intelligence | `engineering-os/adr/ADR-012-activity-intelligence-capability.md` |
| ADR-025 | Entity Resolution Pipeline | Accepted (DEC-135 path correction; index File registered) | 2026-07-12 (file) | Entity Resolution | `salesos/backend/docs/adr/0025-entity-resolution.md` |
| ADR-026 | Hybrid Search (Full-text + Semantic) | Accepted (DEC-135 path correction; index File registered) | 2026-07-12 (file) | Search | `salesos/backend/docs/adr/0026-hybrid-search.md` |
| ADR-027 | Feature Store Implementation | Accepted (DEC-135 path correction; index File registered) | 2026-07-12 (file) | Feature Store | `salesos/backend/docs/adr/0027-feature-store.md` |
| ADR-028 | Knowledge Graph Integration | Accepted (DEC-135 path correction; index File registered) | 2026-07-12 (file) | Knowledge Graph | `salesos/backend/docs/adr/0028-knowledge-graph-integration.md` |
| ADR-029 | Number Never Issued | **Not Issued** (DEC-136 disposition; was PHANTOM) | 2026-08-01 | Governance | `docs/adr/0029-number-never-issued.md` |
| ADR-030 | Unified Provider Architecture | Accepted | 2026-07-16 (file) / 2026-07-08 (index) | Architecture | `docs/adr/0030-unified-provider-architecture.md` |
| ADR-031 | Webhook Auth: API Key Assessment | Accepted (No Change Required) | 2026-07-09 | Security | `docs/adr/0031-webhook-auth-api-key-assessment.md` |
| ADR-032 | Widget SDK Reconciliation | Proposed (DEC-138; matches body; alias ADR-0032) | 2026-07-17 | Widget SDK | `docs/adr/0032-widget-sdk-reconciliation.md` (body: `engineering-os/adr/ADR-0032-widget-sdk-reconciliation.md`) |
| ADR-033 | Decision Engine Lifecycle | Proposed (DEC-137; index Status matches file header) | 2026-07-17 | Decision Engine | `docs/adr/0033-decision-engine-lifecycle.md` |
| ADR-034 | Repository Pattern Compliance | Proposed (DEC-137; index Status matches file header) | 2026-07-17 | Architecture | `docs/adr/0034-repository-pattern-compliance.md` |
| ADR-035 | Sprint 0 Architecture Reconciliation | Proposed (consistent) | 2026-07-17 | Architecture | `docs/adr/0035-sprint-0-architecture-reconciliation.md` |
| ADR-036 | Engineering Organization — Layer Separation | Accepted (file header + criterion 9.1; DEC-139 multi-index) | 2026-08-01 | Governance | `docs/adr/0036-engineering-organization-layer-separation.md` |
| ADR-Data-001 | Identity Resolution Strategy v3 | Accepted (separate namespace, not in index) | 2026-07-19 | Data | `docs/ADR-Data-001-identity-resolution-v3.md` |

## 3. Pending decisions (docs/vnext/DECISIONS.md) â€” potential future ADRs

D-001 Monorepo vs Multi-repo (Proposed, rec: hybrid) Â· D-002 REST-first vs GraphQL-first (rec: REST) Â· D-003 API versioning (rec: `/api/v1`) Â· D-004 Event Bus Migration (rec: full Kafka, drop in-memory) Â· D-005 Agent Runtime (rec: hybrid embeddedâ†’sidecar) Â· D-006 AI Multi-Provider (rec: provider abstraction) Â· D-007 i18n Arabic/RTL (rec: react-intl) Â· D-008 Data Fabric (rec: connector SDK) Â· D-009 Caching unification (rec: Redis everywhere) Â· D-010 Frontend state (rec: React Query + Zustand) Â· D-011 Widget SDK v1.1 (rec: keep frozen) Â· D-012 Plugin vs Extension API (rec: Extension API) Â· D-013 Test consolidation (rec: pyramid audit) Â· D-014 Config management (rec: Pydantic + Vault) Â· D-015 Helm vs Raw K8s (rec: Helm umbrella) Â· D-016 Widget SDK Reconciliation (**Approved**, maps to ADR-0032).

## 4. ADR status conflicts â€” recorded, NOT fixed

| # | Conflict | Severity | Impact |
|---|---|---|---|
| 1 | ADR-025/026/027/028 indexed "Accepted" with **no files anywhere** | **RESOLVED (DEC-135)** — files at `salesos/backend/docs/adr/0025..0028-*.md`; `docs/adr/index.md` File column registered; this file committed with DEC-139 (6.5) | HIGH→closed for 6.1 path evidence; residual: broader EOS tree re-pin via **4.5** |
| 2 | ADR-029 phantom (no index row, no file) | **RESOLVED (DEC-136)** — Not Issued meta-record + `docs/adr/index.md` row; this file committed with DEC-139 (6.5) | MEDIUM→closed for 6.2 gap documentation; residual: broader EOS tree re-pin via **4.5** |
| 3 | ADR-033/034: index says Accepted, file header says Proposed | **RESOLVED (DEC-137)** — index Status **Proposed** matches file headers; residual: broader EOS re-pin narrative via **4.5** | HIGH→closed for 6.3 |
| 4 | ADR-032/0032: three different statuses (index Accepted / file Proposed / D-016 Approved) | **RESOLVED (DEC-138)** — canonical ID **ADR-032**; Status **Proposed**; D-016 Approved ≠ ADR Accepted | MEDIUM→closed for 6.4 |
| 5 | ADR-032 file location contradicts index (index says `docs/adr/` = 030..035; file is in submodule) | **RESOLVED (DEC-138)** — product-root naming bridge + body path documented | MEDIUM→closed for 6.4 |
| 6 | ADR-012 exists (720-line capability ADR) but unindexed | MEDIUM | Activity Intelligence decision invisible to registry |
| 7 | ADR-030 date mismatch (index 2026-07-08 vs file 2026-07-16); ADR-031 no date in file | LOW | Audit-trail accuracy |
| 8 | ADR-033 endpoint citations don't match code (`/api/v1/decisions/{evaluate,recommend,context/{id}}` not found; actual `/api/v1/decision/evaluate`, `/api/v1/decision/next-best-action`) | MEDIUM | Contract drift; tests written against cited paths would fail |
| 9 | ADR-Data-001 artifacts missing: `data/reports/identity_quality_report.md` absent, planned v3 script absent (actual is `phase4_identity_v4.py`) | MEDIUM | Evidence chain broken; implementation already at v4 |
| 10 | Numbering style drift: `ADR-0032` (submodule) vs `ADR-032` (index) vs `ADR-Data-001` (separate namespace) | **RESOLVED (DEC-138)** for ADR-032/0032 alias; ADR-Data-001 separate namespace remains | LOW→closed for 6.4 alias; Data-001 residual informational |
| 11 | Submodule dirty: `engineering-os/kernel/capability-registry.yaml` uncommitted change | LOW | Unreviewed governance drift (pre-existing) |
| 12 | Capability registry 4-way mismatch (catalog 40 / YAML ~22 / SDK ~25 / decorator 14) | HIGH | See 29; known audit finding DEBT-ARC-003 / E-21 (Capability Drift cluster CLOSED DEC-134a — residual INFO) |
| 13 | ADR-036 body exists / criterion 9.1 Accepted but missing from `docs/adr/index.md` + this file | **RESOLVED (DEC-139)** — registered in both indexes; Status Accepted matches file header (CTO/ARB); not invented | HIGH→closed for 6.5 multi-index |

## 5. When this file changes

- After any ADR is added, accepted, superseded, or its file location changes. Update in the same change that touches `docs/adr/` or `engineering-os/adr/`.

## 6. Cross-references

- Per-decision detail: `28_ADR_DEPENDENCY_MAP.md`
- Capabilityâ†”ADR mapping: `29_CAPABILITY_REGISTRY.md`
- Debt classification: `18_TECH_DEBT.md`
