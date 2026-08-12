# A-09 / Wave 11 — 72h Health-Loop Failure Triage

**Date:** 2026-08-12  
**Checklist:** A-09 step 8 · [SOAK-GATE-CHECKLIST.md](./SOAK-GATE-CHECKLIST.md) K3  
**Evidence:** [evidence/ops01-staging/loop-summary-2026-08-10T141003Z.json](./evidence/ops01-staging/loop-summary-2026-08-10T141003Z.json)  
**Window:** 2026-08-07T14:10:06Z → 2026-08-10T14:10:03Z (72h requested)  
**Totals:** **854** iterations · **82** failures · fail rate **9.6%**  
**`soak_complete_claim`:** **false** (not flipped — gate criteria unmet)

**Targets:** API `https://salesos-staging.up.railway.app` · FE `https://sales-os-jet.vercel.app`  
**Harness:** `wave11-soak-gate.py --loop --interval 300 --duration-hours 72 --fail-soft --skip-alembic --skip-flags`

---

## Verdict

| Question | Answer |
|----------|--------|
| Can Wave 11 / PROD-W11-002 soak claim advance? | **No** |
| Can `soak_complete_claim` flip to true? | **No** — K4/K5 human; multi-hour DB outage not closed as accepted noise |
| Agent triage of 82 failures complete? | **Yes** (this document) |

---

## Classification (82 / 82)

| Category | Count | % of fails | Iterations / window | Hard checks |
|----------|------:|----------:|---------------------|-------------|
| **C1 — Staging DB outage / auth** (`api.health` → `status=degraded`, `database=unavailable` or auth error) | **80** | **97.6%** | Contiguous **i583–i663** (2026-08-09T15:15:15Z → 22:01:08Z, ~6h 46m) | `api.health` FAIL |
| **C2 — Edge / deploy blip** (HTTP 400 on ping+health) | **1** | **1.2%** | **i657** (inside C1 window, 21:30:37Z) | `api.ping` + `api.health` FAIL |
| **C3 — Transient probe timeout** (ping timeout; health OK) | **1** | **1.2%** | **i730** (2026-08-10T03:40:46Z) | `api.ping` FAIL |

**By failing check name (non-exclusive):** `api.health` **81** · `api.ping` **2** · FE routes **0** · redis/cache hard-fail **0**.

### C1 detail (root cause)

- Before outage (**i582**): `api.health` **ok**, uptime ≈ **234861s** (~65h).
- During outage: Redis/cache/graph stayed **connected**; Kafka **in_memory**; FE routes **PASS**.
- `/health/detailed` overall **`degraded`** with DB `status=error`:
  - **74** iters: message **`unavailable`** (consistent with `ENV=production` error masking in `health_detailed`).
  - **6** iters (**i658–i663**): message **`password authentication failed for user "salesos_app"`** with short oscillating uptimes (crash-loop / redeploy attempts).
- After recovery (**i664**): `api.health` **ok**, uptime ≈ **534s** (process restarted with working DB auth).
- **Interpretation:** Staging Postgres credentials / connectivity for `salesos_app` failed for nearly seven hours; end-of-window redeploys exposed explicit password auth failures; service recovered only after restart with working credentials. **Not an application logic bug** in SalesOS business code; **ops / credential / platform** incident.

### Harness observation (agent-fixed)

During all **80** C1 failures, `api.health_detailed` was recorded as **PASS** because the gate only required HTTP 200 — even when `overall=degraded`. That masked severity in per-check counts. Fixed in `salesos/scripts/wave11-soak-gate.py` (`classify_health_detailed` → **WARN** on degraded / DB error) + unit tests. Does **not** change hard-fail ownership (`api.health` remains the hard gate).

---

## Triage buckets

### Must-fix before Wave 11 soak claim

| ID | Item | Owner | Why |
|----|------|-------|-----|
| M1 | Written RCA for staging `salesos_app` auth / DB unavailable window (15:15–22:01Z 2026-08-09): what changed, who, rollback | DevOps / Platform | 97.6% of soak fails; P0-class for soak honesty |
| M2 | Confirm staging DB URL / app role password stable; no pending credential rotations without coordinated restart | DevOps | Prevent recurrence |
| M3 | Confirm `ENV=staging` on Railway SalesOS (error messages not production-masked) — noted closed 2026-08-12; keep evidence | DevOps | Masking hid auth cause for 74/80 C1 rows |
| M4 | Project Owner (K5) review of this triage + decide accept-with-conditions **vs** re-soak | TL / PO | Checklist K5; agents must not flip claim |

### Accept-as-noise

| ID | Item | Rationale |
|----|------|-----------|
| N1 | **C3** i730 ping `TimeoutError` (~10s) while `/health` **ok** | Single isolated probe flake; adjacent iters PASS |
| N2 | **C2** i657 HTTP 400 on ping/health | Single blip inside C1 recovery/redeploy window; not a standing FE/API defect |

*Note:* Accepting N1/N2 as noise does **not** allow claiming the soak clean. C1 must be handled under must-fix / needs-human.

### Needs-human

| ID | Item | Decision needed |
|----|------|-----------------|
| H1 | Treat C1 as **closed P0 with RCA** and keep claim false until re-soak, **or** accept soak evidence as “window elapsed with known ops incident” without claim flip | PO / TL |
| H2 | Whether to start a **new** ≥48–72h soak after M1–M3 | DevOps |
| H3 | K4 “no new P0 during soak” — classify C1 as soak P0 (recommended) until M1 signed | TL |
| H4 | Remaining A-09 Human-Gate (OAuth, WAL/PITR, max_connections, deploy token) — independent of this triage | Platform |

---

## Agent actions this pass

| Action | Status |
|--------|--------|
| Classify all 82 failures from loop JSON | Done |
| Produce this triage | Done |
| Flip `soak_complete_claim` | **Not done** (forbidden without K1–K5) |
| Fix gate false-PASS on degraded detailed | Done — `classify_health_detailed` + `tests/unit/test_wave11_soak_gate.py` |
| Change `feature_ai_copilot` | Not touched |
| Secret dumps | None |

---

## Gate checklist impact (honest)

| Gate | After this triage |
|------|-------------------|
| K1 staging cloud | PASS (unchanged) |
| K2 ≥48–72h wall-clock | **PARTIAL** — elapsed, but C1 incident blocks PASS until H1 |
| K3 evidence + hard-fail triage | **Agent triage DONE** — still needs TL acknowledgment |
| K4 no new P0 | **OPEN** — C1 is P0-class until M1 |
| K5 Project Owner review | **OPEN** |
| K6 `soak_complete_claim` | **false** |

---

## Commands / method (reproducible)

```text
# Count gate_pass=false under evidence/ops01-staging/; group by failed check name + detail pattern
# Primary summary file: loop-summary-2026-08-10T141003Z.json (854 iters, 82 failures)
```

**Validation:** classification **light validated** (full local scan of 82 fail JSONs). Staging live re-probe **not** required for this step. Claim advance: **not validated / no-go**.

---

*Evidence governs. AI assists. Humans decide.*
