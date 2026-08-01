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

# 11 â€” AGENT BOOTSTRAP

> Quickstart for a new agent entering this repository. Intended to be loaded as the first instruction set.

## 1. Who you are

You are an autonomous agent working inside the **SalesOS** monorepo (product of **AQLIYA**). Principle: **AI assists. Humans decide. Evidence governs.** GA posture is frozen at **production no-go** (`docs/audit/ga-engineering-audit/`).

## 2. First actions

1. Read `10_AI_CONTEXT_INDEX.md` (default read order).
2. Read `00_PROJECT_CONSTITUTION.md` and `02_CURRENT_STATE.md` â€” do not exceed frozen scope.
3. Check `21_RUNTIME_STATE.json` + `22_FILE_LOCKS.json` â€” do not touch locked files or conflict with parallel agents.
4. Identify your task owner from `09_OWNERSHIP_MAP.md` and your paths from `05_FILE_CATALOG.md`.

## 3. Rules you must obey

| # | Rule |
|---|---|
| 1 | Bootstrap freeze: do not modify production/infra/docs-outside-`.engineering`/ADRs/capability definitions. **Observe-record, never correct.** |
| 2 | Do not touch: `identity/_keys/*`, `.env*`, `prometheus-token`, `docs/**`, `engineering-os/**`, `AGENTS.md`. |
| 3 | Report changes honestly with AGENTS.md Â§5 labels. Never claim a pass without command evidence. |
| 4 | Prefer read-only exploration (Grep/Read/Glob) over heavy commands. Heavy commands require explicit approval. |
| 5 | Do not market stubs (e.g., `@salesos/decision-platform`) as production AI. |
| 6 | Do not commit unless explicitly asked. |
| 7 | Respect DEC-107: keep parallel ready agents busy even when CI-08/CI-09 are blocked. |

## 4. Path shortcuts

- Repo root: `C:\Users\raghe\Documents\Muhide`
- Backend: `salesos/backend/`
- Frontend: `salesos/frontend/`
- CI: `.github/workflows/`
- GA truth: `docs/audit/ga-engineering-audit/`
- Business Truth (program): `docs/program/` — enter via `33_PROGRAM_LAYER_BRIDGE.md`
- This system: `.engineering/` — program enters via `docs/program/ENGINEERING_LAYER_BRIDGE.md`

## 5. Verification flow (before you claim done)

1. Scope: what paths did you touch? Did you respect ownership/locks?
2. Evidence: run the narrowest relevant check (test file, `alembic current` via Docker, `tsc --noEmit` â€” all approval-gated).
3. Label: `not validated` / `light validated` / `build validated`.
4. Report: files changed + commands run + validation status (see `30`).

## 6. When this file changes

- When onboarding rules change. Mirror `00`, `10`, `25`, `26`, `31`.
