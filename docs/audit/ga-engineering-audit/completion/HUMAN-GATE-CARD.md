# HUMAN-GATE-CARD — Exact Actions for Project Owner / Ops

**Date:** 2026-08-08 (refreshed WAVE-20260808-5)  
**Program:** [COMPLETION-PROGRAM.md](../COMPLETION-PROGRAM.md)  
**Stream:** A (OPS Launch) + D pointers  
**Principle:** Agents prepare cards; humans execute field/cloud/ink. Do not forge evidence.

**Already recorded:** SIGN_HERE Decision=**GO** (رغيد المدني, CTO+TL dual-role, 2026-08-08) — **human-declared**. Engineering residuals below remain.

**Live soak note:** Staging 72h harness **IN PROGRESS** (PID **16044**; **264** loop JSON @ 2026-08-08T12:21Z, last `gate_pass=True`). **`soak_complete_claim` stays false.** Do **not** invent 48h PASS.

---

## Do these 3 next

1. **Keep soak harness** (PID 16044 — do not start a second loop) through ≥48–72h; then TL review SOAK-GATE-CHECKLIST **K2–K6** before any claim flip. Session closeout still lists “72h soak” — that clock is **already running**.  
2. **`workflow_dispatch` `deploy-staging.yml`** only if you need a **new** staging bake (HG-01). Do not reset soak evidence without intent.  
3. After soak window: staging Neo4j restore + Redis/Postgres rotation (HG-06) · SSRF pentest (HG-05) · RPO ink (HG-07)  

---

## Priority order

1. Keep soak harness healthy through ≥48–72h; TL review before claim  
2. Staging parity residuals (Google OAuth, WAL/offsite decision, max_connections, CI deploy)  
3. GH Environments re-probe / secrets hygiene if needed  
4. Human CLOSE on DR checklist rows 1–3 (facts already DONE\*)  
5. Railway managed backup schedule + native PITR (API Not Authorized class)  
6. Staging SSRF/KG pentest execute  
7. Credential rotation (field) using evidence template  
8. RPO/RTO signed acceptance  
9. Independent second-role review (dual-role P1 residual)  
10. Production migrate — only after evidence gates you accept  

---

## Gate HG-01 — GitHub Environments / staging secrets

| Field | Value |
|-------|--------|
| Why | RELEASE-BACKLOG #4; cloud deploy/rollback + soak need durable staging target |
| Probe note | Historical: Environments `total_count: 0` — re-probe before assuming still empty |
| Exact actions | 1) Create/confirm GH Environment `staging` (and `production` if missing) 2) Add required `STAGING_*` / deploy secrets per [runbooks/staging-fill-in.md](../runbooks/staging-fill-in.md) 3) Prefer `deploy-staging.yml` evidence (not only manual CLI) 4) Deposit under `completion/evidence/wave-20260808-2/staging-parity/` |
| Agent cannot | Create org secrets; claim cloud deploy PASS |
| Done when | Dated deploy + rollback tabletop evidence linked |

---

## Gate HG-02 — Staging soak ≥48–72h

| Field | Value |
|-------|--------|
| Why | OPS01-04 OPEN; `soak_complete_claim` must stay false until K1–K6 met |
| Docs | [staging-soak.md](../runbooks/staging-soak.md) · [SOAK-GATE-CHECKLIST.md](../enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-GATE-CHECKLIST.md) · [ops01-human-execution-pack.md](../runbooks/ops01-human-execution-pack.md) · [SOAK-PROGRESS-SNAPSHOT-2026-08-08.md](./SOAK-PROGRESS-SNAPSHOT-2026-08-08.md) |
| Status helper | `powershell -NoProfile -ExecutionPolicy Bypass -File docs\audit\ga-engineering-audit\runbooks\ops01-soak-restart.ps1 -StatusOnly` |
| Agent cannot | Flip `soak_complete_claim: true`; invent 48h/576 complete |
| Done when | Duration evidence + TL review + checklist K1–K6 + claim flip by human |

### Soak command block (human / ops)

```powershell
# From repo root — status first (prefer existing live PID writer)
cd C:\Users\raghe\Documents\Muhide
powershell -NoProfile -ExecutionPolicy Bypass -File docs\audit\ga-engineering-audit\runbooks\ops01-soak-restart.ps1 -StatusOnly

# Only if no live loop writing the same evidence dir:
# powershell -NoProfile -ExecutionPolicy Bypass -File docs\audit\ga-engineering-audit\runbooks\ops01-soak-restart.ps1 -Start -DurationHours 72 -FailSoft

# Evidence pattern: enterprise-audit-board/.../evidence/ops01-staging/loop-*.json
# After ≥48h (prefer 72h): human reviews SOAK-GATE-CHECKLIST K1–K6 — only then flip soak_complete_claim
```

---

## Gate HG-02b — Staging parity residuals (A-09)

| Field | Value |
|-------|--------|
| Why | Code/commit parity machine-verified 2026-08-07; residuals block full “parity CLOSED” |
| Doc | [staging-parity-checklist.md](../runbooks/staging-parity-checklist.md) · [STAGING-vs-PRODUCTION-DIFF.md](../enterprise-audit-board/history/EAB-2026-08-06-003/STAGING-vs-PRODUCTION-DIFF.md) |
| Exact actions | Google OAuth staging app; WAL/offsite decision; max_connections or acceptance; CI staging deploy; rollback tabletop |
| Done when | Checklist P1–P6 evidence deposited (redacted) |

---

## Gate HG-03 — DR cutover CLOSE (rows 1–3)

| Field | Value |
|-------|--------|
| Why | RC-P0-01: facts DONE\* but gate CLOSED? still OPEN |
| Exact actions | 1) Read OPS-01 row1–3 evidence JSON 2) Ink human CLOSE on [DR-GA-GAPS-CHECKLIST.md](../../../ops/DR-GA-GAPS-CHECKLIST.md) rows 1–3 **or** explicit CLOSE packet 3) Note automation residuals remain BLOCKED-HUMAN if schedule not enabled |
| Agent cannot | Forge CLOSE ink |
| Done when | Checklist rows show human CLOSE with name/date |

---

## Gate HG-04 — Offsite / WAL schedule automation (Railway)

| Field | Value |
|-------|--------|
| Why | OPS01 automation BLOCKED-HUMAN (API Not Authorized class) |
| Exact actions | Enable managed backup cadence; enable native PITR restore path; capture screenshots/API evidence |
| Agent cannot | Authorize Railway account scopes |
| Done when | Schedule evidence + failed_count policy linked |

---

## Gate HG-05 — Staging SSRF / KG pentest

| Field | Value |
|-------|--------|
| Why | RELEASE-BACKLOG #5; code defenses exist; staging execute OPEN |
| Doc | [staging-ssrf-pentest.md](../runbooks/staging-ssrf-pentest.md) (SSRF + KG tabletop) |
| Local only | `url_safety` regression PASS this wave ≠ staging PASS |
| Prerequisite | Staging host (exists) + test principal |
| Agent cannot | Claim PASS without dated staging evidence |
| Done when | Checklist results deposited with date + TL sign-off |

---

## Gate HG-06 — Credential rotation

| Field | Value |
|-------|--------|
| Why | RELEASE-BACKLOG #10 |
| Exact actions | Follow [CREDENTIAL_ROTATION_RUNBOOK.md](../../../ops/CREDENTIAL_ROTATION_RUNBOOK.md); fill [CREDENTIAL-ROTATION-EVIDENCE-TEMPLATE.md](./CREDENTIAL-ROTATION-EVIDENCE-TEMPLATE.md) **out of band** — never commit secrets |
| Pointer | [CREDENTIAL-ROTATION-INSTRUCTIONS.md](./CREDENTIAL-ROTATION-INSTRUCTIONS.md) |
| Agent cannot | Perform live rotation or store secrets in git |
| Done when | Redacted rotation log + services healthy + reviewer sign-off |

---

## Gate HG-07 — RPO/RTO acceptance

| Field | Value |
|-------|--------|
| Why | OPS01-08 BLOCKED-HUMAN |
| Exact actions | Recompute RPO given WAL facts; ink SIGN_HERE RPO item |
| Done when | Signed acceptance with capability statement |

---

## Gate HG-08 — Dual-role residual (P1)

| Field | Value |
|-------|--------|
| Why | Same person signed CTO + Tech Lead |
| Exact actions | Optional independent second reviewer countersign or explicit risk acceptance note |
| Done when | Second independent ink **or** written acceptance of dual-role risk |

---

## Gate HG-09 — Production migrate (DO NOT START casually)

| Field | Value |
|-------|--------|
| Why | [PROD-MIGRATION-RISK.md](../PROD-MIGRATION-RISK.md); cutover package PREPARED — NOT EXECUTED |
| Exact actions | Only after gates you accept; maintenance window; dress rehearsal on **non-prod** first ([MIGRATION-DRESS-REHEARSAL.md](./MIGRATION-DRESS-REHEARSAL.md) when present) |
| Forbidden for agents | `alembic upgrade` on production |

---

## Agent-completed this card

- Published exact gate list with links  
- Distinguished HUMAN-GO-INK vs engineering OPEN  
- Documented **live** soak mid-window (claim false)  
- Soak status/restart script + staging parity residual checklist  
- SSRF+KG checklist + cred rotation evidence template  

**Validation:** **not validated** for cloud/field execution (by design). Soak inventory **light validated**.

---

*HUMAN-GATE-CARD — Stream A (+D pointers) — Completion Program — 2026-08-08 — no secrets — no forged PASS*
