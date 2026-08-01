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

# 12 â€” CI CATALOG

> Every pipeline definition with trigger, steps, and known blockers. Location fix (2026-07-30): workflows moved from `salesos/.github/workflows/` â†’ `.github/workflows/` (undiscoverable before). Dependabot at `.github/dependabot.yml` with `directory: /salesos/frontend`, `/salesos/backend`.

## 1. Workflows (`.github/workflows/`)

| Workflow | Trigger | Steps (as-built) | Blockers (SEC finding) |
|---|---|---|---|
| `ci.yml` | push/PR | lint â†’ typecheck â†’ backend unit+integration â†’ frontend unit â†’ build | e2e job has **NO services** (DB/Redis) â†’ e2e cannot run in CI |
| `security-scan.yml` | push/PR (scheduled) | gitleaks (**blocking**; was continue-on-error, now removed 2026-07-30) + SAST | â€” |
| `docker-smoke.yml` | push/PR | docker build + smoke test | â€” |
| `deploy.yml` | manual/trigger | build â†’ deploy | **undeclared outputs `slot`, `image_tag`** (SEC finding); CI-08 GHCR 403 (BLOCKED) |
| `deploy-staging.yml` | manual | staging deploy | CI-09 VPS/SSH secrets (BLOCKED) |
| `deploy-production.yml` | manual | production deploy | production no-go (frozen) |

## 2. Local checks (approved usage only)

| Check | Command | Where |
|---|---|---|
| Backend lint | `ruff` via `salesos/backend/scripts/lint.sh` | `salesos/backend` |
| Arch compliance | `python scripts/arch-compliance.py` | `salesos/backend` |
| Coverage gate | `python scripts/check-coverage.py` | `salesos/backend` |
| Alembic current | `docker compose exec backend alembic current` | `salesos` |
| FE lint | `npm run lint` (approval required) | `salesos/frontend` |
| FE typecheck | `npx tsc --noEmit` (approval required) | `salesos/frontend` |
| FE build | `npm run build` (approval required) | `salesos/frontend` |

## 3. CI blockers (live)

- **CI-08** GHCR push 403 â€” blocked (swarm keeps working per DEC-107).
- **CI-09** VPS/SSH deploy secrets missing â€” blocked.
- GA deploy workflows blocked by production no-go posture (frozen).

## 4. Security scanning

- Gitleaks: now blocking. Evidence note: configs (`gitleaks.toml`) previously untracked/gitignored (SEC finding) â€” verify current tracking before relying on scan coverage.
- SAST integrated in security-scan.

## 5. When this file changes

- On workflow add/edit/trigger change. Mirror `16` (deploy), `30` (report), `21` (blockers).
