# Progress — Wave 12 staging cloud unblock (2026-07-28)

**Status:** engineering prep advanced; **cloud tabletop still BLOCKED**  
**Classification:** not validated (no VPS credentials in this session)

## Repo changes

1. [`salesos/.github/workflows/deploy-staging.yml`](../../salesos/.github/workflows/deploy-staging.yml) — also triggers on `master` push (default branch previously 404 for develop-only workflow)
2. Staging fill-in runbook unchanged as authority: [runbooks/staging-fill-in.md](./runbooks/staging-fill-in.md)
3. SSRF pentest checklist ready for post-deploy: [runbooks/staging-ssrf-pentest.md](./runbooks/staging-ssrf-pentest.md)

## Human ops still required

- [ ] Create GitHub Environment `staging`
- [ ] Set `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY` (no values in git)
- [ ] Publish workflow to Actions-visible default branch on SalesOS remote
- [ ] Host `/opt/salesos-staging` + `.env.staging`
- [ ] Run deploy + rollback tabletop; store evidence under `evidence/wave12-staging/`

**Do not claim staging cloud DONE from this progress file.**
