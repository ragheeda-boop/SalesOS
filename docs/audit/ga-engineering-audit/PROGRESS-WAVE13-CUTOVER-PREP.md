# Progress — Wave 12/13 prod cutover prep (2026-07-28)

**Prod Alembic execution:** **BLOCKED** pending approval  
**Signatures:** **UNSIGNED** — [SIGN_HERE.md](./SIGN_HERE.md)

## Engineering checklist (pre-cutover)

- [x] Local migrate prep docs exist ([PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md))
- [x] Pre-deploy gates script present (`salesos/scripts/pre-deploy-gates.ps1`)
- [x] Go-live checklist present ([runbooks/go-live-checklist.md](./runbooks/go-live-checklist.md))
- [ ] Staging cloud tabletop PASS
- [ ] Cloud soak claim true
- [ ] Primary DR or signed RPO exception
- [ ] Explicit human approval for `alembic upgrade head` on production
- [ ] CTO + Tech Lead ink on SIGN_HERE

## Forbidden this session

- No production migrate executed
- No forged signatures
- No Production GO claim

When approved, follow migrate prep + [deploy-rollback.md](./runbooks/deploy-rollback.md); smoke GA routes; then collect signatures.
