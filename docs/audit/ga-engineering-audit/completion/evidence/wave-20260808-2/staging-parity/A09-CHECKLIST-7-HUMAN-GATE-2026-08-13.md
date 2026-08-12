# A-09 checklist step 7 — Human-Gate status matrix (2026-08-13)

**Validation:** **light validated** (doc + prior EAB-003 / 2026-08-12 evidence; no forged ink)  
**Claims:** `staging_parity_complete=false` · `soak_complete_claim=false` · `production_go=false`  
**Constraints:** No signed acceptance forged · No `feature_ai_copilot` flip · No secret dumps · No invented `RAILWAY_TOKEN`

**Authority:** [staging-parity-checklist.md](../../../../runbooks/staging-parity-checklist.md) · [HUMAN-GATE-CARD.md](../../../HUMAN-GATE-CARD.md) HG-02b / HG-04 · [A09_STAGING_PARITY.md](../../../../../star-audit/A09_STAGING_PARITY.md)

---

## Exact status (each residual)

| Residual | Exact status | Agent-closable? | Human required | Done when |
|----------|--------------|:---------------:|----------------|-----------|
| **Google OAuth staging app** | **OPEN / NOT SET** — staging lacks a dedicated OAuth client; password login PASS does **not** close SSO | Prep only | Create Google Cloud OAuth client for staging; set `SSO_GOOGLE_CLIENT_ID` / `SSO_GOOGLE_CLIENT_SECRET` (+ redirect URIs) on Railway **staging** only; never reuse prod client | Staging Google SSO round-trip evidence (redacted) deposited |
| **PITR / WAL / offsite (staging posture)** | **OPEN — gap accepted-or-enable undecided** — prod rows 1–3 machine drills **DONE\***; staging Postgres historically **no** `WAL_ARCHIVE_*` / no staging PITR; managed schedule + native `volumeInstancePITRRestore` still **BLOCKED-HUMAN** (Not Authorized class) | Prep only (runbooks linked) | Enable staging WAL/offsite **or** ink written accept-gap for staging (not GA cutover CLOSE) | Dated decision + evidence **or** SIGN_HERE accept residual |
| **Postgres `max_connections`** | **OPEN — 100 vs prod 500** (per [SOAK-READINESS.md](../../../enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-READINESS.md)); no agent bump this pass | No | Raise staging to 500 **or** signed capacity acceptance that 100 is intentional for staging | Config screenshot/CLI evidence **or** signed note |
| **Rollback tabletop (staging cloud)** | **OPEN — template ready, execution unsigned** — local Wave 12 tabletop ≠ staging cloud; CI deploy still Unauthorized so pipeline rollback path unproven | Template **DONE** (this deposit) | Run dated staging tabletop; attach deployment IDs + health before/after | Dated notes under this folder with human name/date |

**Overall step 7:** **OPEN** (Human-Gate). Agent prep below does **not** close the gate.

---

## Agent-closed prep this pass (no human ink)

| Prep | Path | Status |
|------|------|:------:|
| Status matrix (this file) | `./A09-CHECKLIST-7-HUMAN-GATE-2026-08-13.md` | **DONE** |
| Staging OAuth setup checklist | [`runbooks/staging-oauth-setup.md`](../../../../runbooks/staging-oauth-setup.md) | **DONE** (doc) |
| Staging rollback tabletop template | [`./A09-STAGING-ROLLBACK-TABLETOP-TEMPLATE.md`](./A09-STAGING-ROLLBACK-TABLETOP-TEMPLATE.md) | **DONE** (unsigned) |
| Pointers to existing DR/PITR runbooks | [railway-managed-backup-schedule.md](../../../../runbooks/railway-managed-backup-schedule.md) · [wal-pitr-local-drill.md](../../../../runbooks/wal-pitr-local-drill.md) · [DR-ROWS-1-3-CLOSE-PACKET.md](../../../../../ops/DR-ROWS-1-3-CLOSE-PACKET.md) | Linked |
| Railway settings agent could change without ink | Staging `ENV=staging` already fixed 2026-08-12 ([A09-OPS-ENV-CELERY](./A09-OPS-ENV-CELERY-2026-08-12.md)); celery `POSTGRES_*` step 6 closed | **No further agent Railway write this pass** |

### Explicitly NOT done by agent

- Creating Google OAuth apps or writing SSO secrets  
- Enabling Railway managed backup schedule / native PITR  
- Changing `max_connections` on staging Postgres  
- Signing accept-gap / RPO / rollback completion  
- Claiming step 7 CLOSED  

---

## Sister deploy fold-in (before finish)

| Run | Time (UTC) | Gate | `railway up` | Conclusion |
|-----|------------|:----:|:------------:|:----------:|
| [31647956116](https://github.com/ragheeda-boop/SalesOS/actions/runs/31647956116) | 2026-08-12T22:40:54Z | **PASS** | **Unauthorized** | **failure** (token unchanged) |

Same class as [31638994692](https://github.com/ragheeda-boop/SalesOS/actions/runs/31638994692). Steps 1–2 remain **FAIL** / Human-Gate rotate. See updated [A09-CHECKLIST-1-5-2026-08-12.md](./A09-CHECKLIST-1-5-2026-08-12.md).

---

## Human action card (copy/paste)

1. **OAuth:** Follow [staging-oauth-setup.md](../../../../runbooks/staging-oauth-setup.md); deposit redacted login evidence.  
2. **WAL/PITR/offsite:** Either enable staging archive per [railway-managed-backup-schedule.md](../../../../runbooks/railway-managed-backup-schedule.md) **or** write “accept staging DR gap” with name/date (does not close prod OPS-01).  
3. **`max_connections`:** Bump staging Postgres 100→500 **or** ink capacity acceptance.  
4. **Rollback:** Execute [A09-STAGING-ROLLBACK-TABLETOP-TEMPLATE.md](./A09-STAGING-ROLLBACK-TABLETOP-TEMPLATE.md); fill SIGN_HERE.  
5. **Unblock CI first (recommended):** rotate `RAILWAY_TOKEN` so tabletop can use pipeline redeploy path.

---

*Step 7 remains OPEN. Evidence governs. Do not forge CLOSE.*
