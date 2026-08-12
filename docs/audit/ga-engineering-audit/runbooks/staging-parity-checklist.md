# Staging Parity Checklist (A-09 / OPS residual)

**Status:** Machine baseline exists (2026-08-07) — **residuals Human-Gate** (A-09 **CONDITIONAL / OPEN**)  
**Authority:** [STAGING-vs-PRODUCTION-DIFF.md](../enterprise-audit-board/history/EAB-2026-08-06-003/STAGING-vs-PRODUCTION-DIFF.md) · [A09_STAGING_PARITY.md](../../star-audit/A09_STAGING_PARITY.md) · [staging-branch-strategy.md](./staging-branch-strategy.md) · [A09-CHECKLIST-10-FINAL-PARITY-2026-08-13.md](../completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-10-FINAL-PARITY-2026-08-13.md)  
**Does not grant:** Production GO or soak complete  

**2026-08-13:** Steps 7 / 9 / 10 documented honestly — Human-Gate prep + soak unlock criteria + final assessment **CONDITIONAL / OPEN**. Post-«تم التدوير» deploy still Unauthorized ([31648777919](https://github.com/ragheeda-boop/SalesOS/actions/runs/31648777919)). See [A09-CHECKLIST-PROGRESS-2026-08-12.md](../completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-PROGRESS-2026-08-12.md).

**2026-08-12 advancement:** Host live; `staging` branch strategy documented; Decision seed applied; `deploy-staging.yml` switched to env **name**. Bounded **production** IL-2A soak remains separate evidence — **not** staging parity / Wave 11 claim.

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

### Added 2026-08-12 / 13 (agent)

| Item | Result |
|------|--------|
| Staging `/health` | **200** |
| Git `staging` branch strategy | Documented + remote branch |
| Minimal Decision seed (muhide + 5 companies) | Applied (`companies=22` / `muhide_tenant=1`) |
| GH Environment `staging` | Exists; Railway secrets bound; health URL var set |
| `FEATURE_AI_COPILOT` on staging | `false` |
| Staging login (muhide seed) | **PASS** (password not in evidence) |
| Decision-runtime evaluate smoke | **PASS** (`recommend_call`) |
| celery-worker / celery-beat / `agent_dispatch_all` | **PASS** (light) — scheduler→worker succeed |
| Neo4j / `:6432` residual | **CLOSED** (celery Postgres vars) |
| Human-Gate step 7 prep | Status matrix + OAuth runbook + rollback template — **ink OPEN** |
| Soak claim unlock criteria | Documented; `soak_complete_claim=false` |
| Final parity assessment | **CONDITIONAL / OPEN** |
| `deploy-staging.yml` end-to-end | **FAIL** — `RAILWAY_TOKEN` Unauthorized ([31648777919](https://github.com/ragheeda-boop/SalesOS/actions/runs/31648777919) post-rotate) |

---

## Still OPEN / Human-Gate

| # | Residual | Owner | Done when |
|---|----------|-------|-----------|
| P1 | Google OAuth staging app (`SSO_GOOGLE_CLIENT_ID/SECRET`) | Platform | Staging login round-trip evidence (no secrets in git) — [staging-oauth-setup.md](./staging-oauth-setup.md) |
| P2 | Staging WAL archive + offsite backup posture | DevOps | Documented decision: accept gap **or** enable + drill |
| P3 | Postgres `max_connections` 100→500 (or accepted capacity note) | DevOps | Config evidence or signed acceptance |
| P4 | Staging deploy via `deploy-staging.yml` green run | DevOps | Successful GH Actions run linked |
| P5 | Staging rollback tabletop | DevOps | Dated notes — template [A09-STAGING-ROLLBACK-TABLETOP-TEMPLATE.md](../completion/evidence/wave-20260808-2/staging-parity/A09-STAGING-ROLLBACK-TABLETOP-TEMPLATE.md) |
| P6 | Fix staging `ENV=production` mislabel | DevOps | **CLOSED** 2026-08-12 (`ENV=staging`) |
| P7 | Wave 11 soak claim | TL / DevOps | Unlock U1–U5 — [A09-CHECKLIST-9-SOAK-CLAIM-UNLOCK-2026-08-13.md](../completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-9-SOAK-CLAIM-UNLOCK-2026-08-13.md) |

Deposit redacted evidence under:

`docs/audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/`

---

## Agent cannot

- Create Google OAuth apps or org secrets  
- Enable Railway managed schedules without account auth  
- Flip soak/parity CLOSED without human ink  

**Validation:** **light validated** for agent-closed items; **not validated** for Human-Gate residual close.
