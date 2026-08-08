# SalesOS GA — Countdown

> **This is the daily pre-launch page.** Open it first each morning until Production GA.
> **Owner:** Project Owner (sole decision-maker) · **AI:** executor only — records, verifies, proposes; never decides.
> **Current countdown anchor:** Soak ends `2026-08-10T14:10:06Z`.
> **Authority:** `RELEASE-GOVERNANCE-DECISION-2026-08-07.md` (Release Operations Mode; P0 definition §1A).

---

## Live status

| Field | Value |
|-------|-------|
| Soak PID | 16044 (alive) |
| Soak iteration | i00071 (2026-08-07T20:04:55Z) — PASS 7/0 |
| Soak end | `2026-08-10T14:10:06Z` |
| Freeze ends | `2026-08-10T14:10Z` OR soak closure |
| P0 blockers open | **1** — P0-01 tenant isolation/roles (see below) |
| RC register | RC-01…05 OPEN · RC-06/07/08 BLOCKED until soak |

> Update this block at the top of the file **only** with evidence (loop JSON timestamp / process check).

---

## The countdown

| Marker | When | Required | Owner | Done? |
|--------|------|----------|-------|:-----:|
| **T-72h** | 2026-08-07 | Soak started clean; soak gate K1 PASS | Project Owner | ✅ |
| **T-48h** | 2026-08-08 | Soak mid-point: K1 PASS sustained, no hard fails; check loop evidence | Project Owner | ☐ |
| **T-24h** | 2026-08-09 | Soak still PASS; review `RC-08` manifest + `P0-01` plan for window; pre-declare maintenance window schedule | Project Owner | ☐ |
| **T-12h** | 2026-08-10 ~02:00Z | Final soak sweep; prepare evidence-review packet (RC-01…06 + P0-01) | Project Owner | ☐ |
| **T-6h** | 2026-08-10 ~08:00Z | Soak closure report drafted; abort matrix reviewed; operator named for window | Project Owner | ☐ |
| **T-1h** | 2026-08-10 ~13:00Z | Window precondition checklist complete; write-pause agreed; all parties staged | Project Owner | ☐ |
| **Maintenance** | 2026-08-10 14:10Z+ | Open window → 15 migrations → owner-login release → smoke → verification → **P0-01** (roles/tenant topology/cross-tenant re-test) → migration report | Project Owner + named operator | ☐ |
| **GA** | After window + Owner Decision | Evidence review → Owner Decision → **Production GA** → Release Archive | Project Owner | ☐ |

---

## Open P0 blocker — P0-01 (tenant isolation / roles)

| Item | Detail |
|------|--------|
| Evidence | `PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md` §2 + §3.7 |
| Problem | Both accounts share tenant `326e0825-1834-4399-8cca-77c2679f172b`; cross-tenant test **INCONCLUSIVE**; roles swapped (`muhide.com`=user, `ratlfintech.com`=admin) |
| Decision needed (in window) | 1) Confirm role intent 2) Decide tenant topology 3) Provision cross-tenant test account if split 4) Re-run cross-tenant isolation test |
| Resolution options | Resolve → re-verify → close **OR** Project Owner accepts-with-residual (explicit) |
| Default if unresolved | **GA blocked** |

---

## Blocked RC decisions (sequential)

| RC | Item | Blocks |
|----|------|--------|
| RC-06 | Maintenance window authorization | P0-01 + migrations |
| RC-08 | Owner-login release (RC-06 window) | Owner Console |
| RC-07 | Final Production GO | Everything |

> RC-01…05 open for evidence review while soak runs (not blocked by soak).

---

## Daily checklist (each morning)

- [ ] Soak process alive (PID 16044) + last loop PASS (read `evidence/ops01-staging/loop-*.json`)
- [ ] No hard fails since last check
- [ ] RC / P0-01 status unchanged or new evidence reviewed
- [ ] Freeze respected: no new deploys/commits/dependency changes
- [ ] Update "Live status" block with evidence
- [ ] Next marker in the countdown table prepared

---

## Post-GA sequence (not before GA)

```
GA
 ↓
Postmortem (GA retrospective)
 ↓
Lessons Learned (recorded)
 ↓
v1.0.1 (first patch release)
 ↓
Verification Platform vNext (docs/vnext/verification-platform/)
```

---

*docs/audit/ga-engineering-audit/COUNTDOWN.md — created 2026-08-07. Daily pre-launch page; evidence-driven; owner decision only.*
