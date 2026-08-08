# Staging Parity Checklist (A-09 / OPS residual)

**Status:** Machine baseline exists (2026-08-07) — **residuals Human-Gate**  
**Authority:** [STAGING-vs-PRODUCTION-DIFF.md](../enterprise-audit-board/history/EAB-2026-08-06-003/STAGING-vs-PRODUCTION-DIFF.md) · [A09_STAGING_PARITY.md](../../star-audit/A09_STAGING_PARITY.md)  
**Does not grant:** Production GO or soak complete

---

## Already machine-verified (cite EAB-003; do not re-invent)

| Item | Result (2026-08-07) |
|------|---------------------|
| Deployed commit staging vs prod | SAME `4750038c` |
| OpenAPI byte identity | SAME |
| `DEBUG=false`, secret isolation | SAME / DIFFERENT-hashes OK |
| Neo4j connected both | SAME |
| `/health` subsystems | SAME class |
| Staging empty data vs prod volume | Intentional (not a parity fail) |

---

## Still OPEN / Human-Gate

| # | Residual | Owner | Done when |
|---|----------|-------|-----------|
| P1 | Google OAuth staging app (`SSO_GOOGLE_CLIENT_ID/SECRET`) | Platform | Staging login round-trip evidence (no secrets in git) |
| P2 | Staging WAL archive + offsite backup posture | DevOps | Documented decision: accept gap **or** enable + drill |
| P3 | Postgres `max_connections` 100→500 (or accepted capacity note) | DevOps | Config evidence or signed acceptance |
| P4 | Staging deploy via `deploy-staging.yml` (not only manual CLI) | DevOps | Successful GH Actions run linked |
| P5 | Staging rollback tabletop | DevOps | Dated notes under evidence |
| P6 | GH Environments inventory (re-probe `total_count`) | DevOps | Environments exist + secrets bound |

Deposit redacted evidence under:

`docs/audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/`

---

## Agent cannot

- Create Google OAuth apps or org secrets  
- Enable Railway managed schedules without account auth  
- Flip soak/parity CLOSED without human ink  

**Validation:** **not validated** for residual close (by design).
