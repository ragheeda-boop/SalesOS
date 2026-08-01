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

# 00 â€” PROJECT CONSTITUTION

> Authority: This `.engineering/` directory is the coordination layer for AI agents working on the SalesOS repository. It observes, indexes, classifies, and cross-references the repository at commit `c89025a` (branch `master`; re-pinned from `3749c30` after ARB audit `32`). It does NOT change repository behavior.

## 1. The Engineering Bootstrap Freeze Rule

```text
Engineering Bootstrap Freeze Rule

During EOS Bootstrap:

- Production code is immutable.
- Infrastructure code is immutable.
- Documentation outside .engineering is immutable.
- ADRs are immutable.
- Capability definitions are immutable.

EOS may only observe, index, classify, and cross-reference.

Any discrepancy discovered must be recorded, never corrected.

Remediation belongs to future implementation sprints.
```

### Scope of the freeze

| Area | Immutable | Evidence source |
|---|---|---|
| `salesos/backend/**` (app, domains, runtime, sdk, intelligence) | Yes | Fingerprint 23 |
| `salesos/frontend/**` (src, packages, apps) | Yes | Fingerprint 23 |
| `.github/workflows/**`, `.github/dependabot.yml` | Yes | Fingerprint 23 |
| `salesos/infra/**` (k8s, terraform, monitoring, caddy, docker) | Yes | Fingerprint 23 |
| `docs/**` (audits, ADRs, ops, vNext) | Yes | Fingerprint 23 |
| `engineering-os/**` (governance submodule, capability-registry.yaml) | Yes | Fingerprint 23 |
| `.engineering/**` | **Mutable by agents under CHANGE PROTOCOL (25)** | This directory |

## 2. Truth hierarchy (conflict resolution)

1. **Executable evidence** (git-tracked files, CI runs, test results) â€” wins over prose.
2. **`docs/audit/ga-engineering-audit/`** (00-EXECUTIVE-SUMMARY, GA_STATUS, PRODUCTION_PLAN, AI_HONESTY) â€” canonical GA posture.
3. **This `.engineering/` directory** â€” coordination layer; must never contradict the audit.
4. **`AGENTS.md`, `PRODUCT_BIBLE.md`, `salesos/CANONICAL_ARCHITECTURE.md`** â€” supporting context.
5. **Superseded GO claims** (`docs/vnext/reports/GO_NO_GO_DECISION.md`, `GA_CHECKLIST.md`) â€” **NOT to be used**. Must not be cited as authority.

> If `docs/audit/ga-engineering-audit/GA_STATUS.md` maturity scores conflict with anything else, the audit wins for GO/NO-GO.

## 3. Governance status (frozen observation)

- **GA status: `production no-go`.** Production Readiness ~78 (Wave 24), Security 51.6/100 (security-audit-report-latest.json, 30 critical failures). This label is **immutable** within EOS reports; no agent may upgrade it.
- Remaining NO-GO blockers are human/operational: soak claim, Google OAuth connection, interactive login password, staging SSRF pentest/tabletop, CTO+TL signatures, PRC sign-off, WAL/PITR+offsite backup, RPO acceptance, credential rotation.
- AI honesty: `feature_ai_copilot=False` by default (`salesos/backend/app/config.py`); frontend Decision package is a **STUB** (throws "Not implemented"); never market stubs as production AI.

## 4. Observation-not-fix doctrine

All discrepancies found during bootstrap are **observed facts**, recorded in:

- `18_TECH_DEBT.md` â€” severity + impact classification.
- `27_ADR_INDEX.md` / `28_ADR_DEPENDENCY_MAP.md` â€” ADR conflicts.
- `29_CAPABILITY_REGISTRY.md` â€” capability drift.
- `30_ENGINEERING_BOOTSTRAP_REPORT.md` â€” executive rollup + confidence table.

No agent fixes these during bootstrap. Remediation belongs to future sprints (see `19_EXECUTION_STRATEGY.md`).

## 5. Agent conduct rules

1. **Ownership:** Assignments follow `09_OWNERSHIP_MAP.md` and `31_AI_TASK_ROUTING.md`.
2. **Locks:** Before modifying a file, acquire a write lock in `22_FILE_LOCKS.json`. Danger paths are read-only and may never be modified by an agent.
3. **Traceability:** Every element you touch must reference its Capability (`CAP-*`), ADR (`ADR-*`), directory (`DIR:`), file (`FILE:`), database (`DB:`), tests (`TST:`), CI (`CI:`), deployment (`DEP:`), and owner, per the ID schema in `10_AI_CONTEXT_INDEX.md`.
4. **Honesty labels:** Use AGENTS.md Â§5 labels (`not validated` / `light validated` / `build validated` / `pilot-ready with conditions` / `production no-go`). Never invent a stronger claim.
5. **State protocol:** Update `21_RUNTIME_STATE.json` on any sprint/blocker/lock change; update `20_NEXT_READY.md` when picking up work.
6. **No scope creep:** If a discrepancy is found, record it. Do not begin remediation without an explicit human task.

## 6. Validation honesty (AGENTS.md Â§5)

| Label | Meaning |
|---|---|
| `not validated` | Not run / no evidence |
| `light validated` | Spot checks only |
| `build validated` | Install/lint/typecheck/build/test commands run with recorded outcome |
| `pilot-ready with conditions` | Narrow use after listed P0s closed |
| `production no-go` | Must not ship GA |

Current classification (2026-07-30 / frozen): **production no-go**.

## 7. When this file changes

- When the repository's governance posture changes (e.g., a future audit upgrades GA status) â€” requires human approval and a new fingerprint.
- When the freeze rule is lifted (end of bootstrap) â€” requires explicit human decision recorded in `30_ENGINEERING_BOOTSTRAP_REPORT.md`.
- Otherwise: **do not modify.**

## 8. Canonical cross-references

| Reference | File |
|---|---|
| Repo topology | `03_REPOSITORY_MAP.md`, `24_REPOSITORY_MANIFEST.json` |
| GA posture | `02_CURRENT_STATE.md`, `docs/audit/ga-engineering-audit/GA_STATUS.md` |
| Locks | `22_FILE_LOCKS.json` |
| Live state | `21_RUNTIME_STATE.json` |
| Change protocol | `25_CHANGE_PROTOCOL.md` |
| Coordination | `26_AGENT_COORDINATION.md` |
| Business Truth layer (ADR-036 / criterion 9.2) | `33_PROGRAM_LAYER_BRIDGE.md` → `docs/program/` (pointers only; no duplication) |
| Reciprocal program bridge | `docs/program/ENGINEERING_LAYER_BRIDGE.md` |
