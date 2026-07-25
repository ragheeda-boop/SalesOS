# Staging compose (SalesOS)

| File | Purpose |
|------|---------|
| `docker-compose.staging.yml` | **Cloud/VPS** staging target (GHCR images, full stack). Needs real host + `.env.staging`. |
| `docker-compose.staging-virtual.yml` | **Local virtual staging** stand-in (`salesos-staging-local`). Ports `:8001`/`:3002`. Not cloud. |

Scripts (from `salesos/`):

- `.\scripts\staging-virtual-up.ps1`
- `.\scripts\staging-virtual-down.ps1`
- `.\scripts\staging-virtual-deploy-rollback.ps1`

Docs: `docs/audit/ga-engineering-audit/PROGRESS-WAVE12-STAGING-VIRTUAL.md`

**Honesty:** virtual path ≠ cloud staging. Production remains **NO-GO** until real VPS tabletop + other GA blockers close.
