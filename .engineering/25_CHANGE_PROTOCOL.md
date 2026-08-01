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

# 25 â€” CHANGE PROTOCOL

> The only sanctioned path for changing repository state. Bootstrap freeze applies: **observe-record, never correct** â€” until a change passes this protocol with Human authority.

## 1. Change classes

| Class | Examples | Authority |
|---|---|---|
| C1 â€” Design-only | drafts, proposals, regression-test designs | agent, recorded in `.engineering/` |
| C2 â€” Code change | fix, feature, refactor | Human approval + this protocol |
| C3 â€” Security-relevant | auth/CSRF/RBAC/RLS/secrets/middleware | Human approval + security review (never weakened) |
| C4 â€” Governance | ADR, capability catalog, constitution, docs/** | Human only (frozen) |
| C5 â€” Deploy | any remote deploy, GHCR push | Human only; blocked by CI-08/CI-09 + no-go |

## 2. Change lifecycle

1. **Identify** â†’ locate files via `05`/`03`, ownership via `09`, debts via `18`.
2. **Gate** â†’ confirm class (C1..C5); confirm Human authority if C2+.
3. **Lock** â†’ register in `21_RUNTIME_STATE.json` + `22_FILE_LOCKS.json` (avoid parallel conflicts).
4. **Implement** â†’ minimal patch following repo conventions; NO comments unless asked.
5. **Verify** â†’ narrowest relevant check (approved commands only); record evidence + label (Â§5).
6. **Record** â†’ update `02` (state), `18` (debt status), `30` (report), and affected catalogs.
7. **Report** â†’ files changed + commands run + validation status.

## 3. Rules (non-negotiable)

| # | Rule |
|---|---|
| R1 | Never modify: identity `_keys/*`, `.env*`, `prometheus-token`, `docs/**`, `engineering-os/**`, `AGENTS.md`, `salesos/server/server.js` (without approval). |
| R2 | Never run heavy commands (`npm run build`, full `pytest`, `prisma migrate`, installs) without explicit approval. |
| R3 | Never weaken security controls "to unblock demos". |
| R4 | Never commit unless explicitly asked. |
| R5 | Never claim a pass without command evidence. |
| R6 | Prefer Docker for backend work (host Poetry broken on Windows). |
| R7 | No comments in code unless requested. |

## 4. Architecture rules that must hold after any change

From `tests/test_architecture.py` + `scripts/arch-compliance.py`:
1. SDK-import rule â€” kernel must not import `app/`.
2. Kernelâ†’commercial forbiddance.
3. No `app` import inside `sdk`.
4. (SDK consumers) FE goes through SDK/API only.
5. Commercial-modules-forbidden (`data/`, root, `sales-os/` must not import `app/`/`domains/`).

## 5. When this file changes

- When the protocol itself changes (Human authority). Mirror `00`, `26`, `11`.
