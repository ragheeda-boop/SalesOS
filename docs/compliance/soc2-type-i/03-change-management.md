# 03 — Change management evidence (STORY-14-05)

> **Intent:** Tip-line / Deploy / PR / security-scan process pointers (honest).  
> **Label:** Pipeline evidence **light/build validated** @ tip `4754b8b` (per DevOps pack) · formal CAB minutes = **not validated**.  
> **Not:** Type I auditor opinion · Not Production GO.

## Control summary

| Element | Reality | Label |
|---------|---------|-------|
| GitHub Actions CI Stages 1–5 | Present; tip SUCCESS | **build validated** @ `4754b8b` |
| Deploy + Backend Health Gate | Present; tip SUCCESS | **build validated** |
| Security Scan workflow | Present; tip SUCCESS | **build validated** |
| Stage 6 GHCR | Quarantined DEC-150 B | **SKIPPED** (intentional — not unexplained gap) |
| Dependabot | Present | Design / process |
| Formal CAB / RFC archive | Not in this pack | **gap** / Program Director |

## Canonical tip-line URLs (DevOps pack — do not invent)

Source: [`PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md`](../../program/PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md)

| Workflow | Conclusion @ `4754b8b` | URL |
|----------|------------------------|-----|
| CI (Stages 1–5) | **SUCCESS** | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835457682 |
| Deploy Production | **SUCCESS** | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835457753 |
| Docker Smoke | **SUCCESS** | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835457157 |
| Security Scan | **SUCCESS** | https://github.com/ragheeda-boop/SalesOS/actions/runs/30835461517 |

### Stage 6 (quarantined — cite as designed)

From CI run `30835457682`:

- `Stage 6: Build Backend (QUARANTINED DEC-150 B)` → **skipped**
- `Stage 6: Build Frontend (QUARANTINED DEC-150 B)` → **skipped**

Do **not** reopen GHCR as a SOC2 gate.

## Workflow / policy file pointers

| Artifact | Path |
|----------|------|
| CI | `.github/workflows/ci.yml` (bandit Stage 5; Stage 6 quarantined) |
| Security Scan | `.github/workflows/security-scan.yml` (gitleaks, Trivy fs/config, pip-audit, …) |
| Deploy | `.github/workflows/deploy.yml` (`Backend Health Gate`) |
| Deploy production alias | `.github/workflows/deploy-production.yml` |
| Docker smoke | `.github/workflows/docker-smoke.yml` |
| Staging deploy | `.github/workflows/deploy-staging.yml` |
| Dependabot | `.github/dependabot.yml` |
| Health Gate land | commit `c0e4f6a` |
| Log-stream false-RED close | commit `654b33e` |
| Docs tip pin | `4754b8b` |

## Health Gate (runtime change control)

| Requirement | Evidence |
|-------------|----------|
| `/health` 200 | Deploy Health Gate job |
| `uptime_seconds` &lt; 900 | Rejects stale image false-green |
| `GET /api/v1/load/meta` ≠ 404 | Tip fingerprint |

## Process narrative (honest)

1. Changes land via git commits / PRs on `master` (this monorepo).  
2. CI Stages 1–5 + security jobs must pass for tip-line green (Watchdog Evidence #1).  
3. Deploy workflow rolls Railway published env; Health Gate rejects stale `/health`.  
4. Stage 6 GHCR push remains **quarantined** by DEC-150 B — absence is **policy**, not silent failure.  
5. Security Scan (gitleaks/Trivy/…) provides scheduled + push pipeline evidence.

## PD templates (unsigned)

| Template | Path | Status |
|----------|------|--------|
| CAB ↔ deploy mapping | [`07-cab-deploy-mapping-template.md`](./07-cab-deploy-mapping-template.md) | **LANDED** · filled archive residual |
| Branch-protection checklist | [`08-branch-protection-evidence-checklist.md`](./08-branch-protection-evidence-checklist.md) | **LANDED** · screenshots residual |

## Gaps

| Gap | Owner | Label |
|-----|-------|-------|
| Branch protection / required reviewers screenshots | Program Director / org admin | **residual-external** to git (checklist `08` LANDED) |
| CODEOWNERS | Engineering | **gap** (file absent) |
| CAB / change-ticket archive for each prod deploy | Program Director | **not validated** (template `07` LANDED) |
| Customer-facing change calendar | Product / PD | **not validated** |
