---
EngineeringOS: v3
GeneratedAt: 2026-08-01T20:10:52Z
RepositoryCommit: 9fa8e9f
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Measured
Revalidation: Active (DEC-142)
---

# 10 â€” AI CONTEXT INDEX

> Index of the context files an agent should load before working. Read order by task type.

## 1. Default read order (every agent)

1. `00_PROJECT_CONSTITUTION.md` â€” freeze rule, truth hierarchy, honesty labels.
2. `02_CURRENT_STATE.md` â€” GA no-go scoreboard, blockers, discrepancies.
3. `03_REPOSITORY_MAP.md` â€” where things live.
4. `04_DIRECTORY_CATALOG.md` â€” directories, ownership, safe-to-modify.
5. `23_PROJECT_FINGERPRINT.json` â€” machine facts (SHA, counts, danger paths).
6. `21_RUNTIME_STATE.json` â€” live coordination (blocks, parallel groups).
7. `22_FILE_LOCKS.json` â€” what is locked and by whom.

## 2. Task-type read order

| Task | Read first |
|---|---|
| API work (add/change endpoint) | `14` + `28` (ADR contracts) + `08` + `05` |
| DB/migration work | `13` + `02` + `28` (refresh-token enabled-state unverified) |
| Capability/registry work | `29` + `06` + `07` + `28` |
| Security work | `15` + `02` + `00` |
| CI/CD work | `12` + `16` + `02` + `21` |
| Frontend feature work | `09` (owner Claude) + `05` Â§8-10 + `14` + `17` |
| Decision Center work | `29` (CAP-016) + `18` (stub) + `02` (AI honesty) |
| Tests | `17` + `07` + `12` |
| Tech debt / refactor | `18` + `07` + `28` |
| New agent onboarding | `11` (bootstrap) + this file + `26` |

## 3. Evidence anchor files

| Evidence | Path |
|---|---|
| Canonical GA NO-GO | `docs/audit/ga-engineering-audit/GA_STATUS.md` |
| Executive summary | `docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md` |
| Waves plan | `docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md` |
| AI honesty | `docs/audit/ga-engineering-audit/AI_HONESTY.md` |
| ADR index (live) | `27_ADR_INDEX.md` |
| Capabilities | `29_CAPABILITY_REGISTRY.md` |
| Business Truth bridge (ADR-036 / 9.2) | `33_PROGRAM_LAYER_BRIDGE.md` |
| Program → Engineering bridge | `docs/program/ENGINEERING_LAYER_BRIDGE.md` |
| Security report | `salesos/security-audit-report-latest.json` |

## 4. When this file changes

- When the file list reorders or new context files appear. Mirror `11` and `31`.
