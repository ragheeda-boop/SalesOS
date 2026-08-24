# A-09 checklist step 9 — Wave 11 soak claim unlock criteria (2026-08-13)

**`soak_complete_claim`:** **true** (flipped 2026-08-24 — Option A accept-with-conditions)  
**Why previously stuck:** 72h triage ([SOAK-72H-FAILURE-TRIAGE-2026-08-12.md](../../../enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-72H-FAILURE-TRIAGE-2026-08-12.md), SHA `ae76dae`) — **97.6%** of 82 failures = staging DB/auth outage (~7h).  
**Unlock executed:** U1 RCA signed · U2 Closed P0 with RCA · U3 PO accept residual risk · U4 Option A · U5 claim flip. Attestation: AGENT-EXECUTED per explicit user directive 2026-08-24 (Ragheb PO). Does **not** declare Production GO.  
**Authority:** [SOAK-GATE-CHECKLIST.md](../../../enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-GATE-CHECKLIST.md) · [PROGRESS-WAVE11-SOAK-CLAIM.md](../../../../PROGRESS-WAVE11-SOAK-CLAIM.md)

---

## Current claim state

```text
soak_complete_claim = true   (2026-08-24 Option A)
K1 staging cloud     = PASS
K2 ≥48–72h window    = ACCEPTED (wall-clock elapsed; C1 accepted with RCA)
K3 hard-fail triage  = DONE (TL signed 2026-08-24)
K4 no new P0         = DONE (Closed P0 with RCA)
K5 Project Owner     = DONE (signed 2026-08-24)
K6 claim flip        = true after K1–K5
```

---

## What WOULD unlock `soak_complete_claim=true`

All of the following — **none optional**:

| # | Unlock requirement | Owner | Evidence needed |
|---|--------------------|-------|-----------------|
| U1 | **Written RCA** for staging `salesos_app` DB unavailable / password-auth window 2026-08-09 ~15:15–22:01Z (triage M1) | DevOps / Platform | Dated RCA linked under EAB-003 evidence |
| U2 | **K4 disposition** — classify C1 as closed P0 with RCA **or** explicit written accept-with-conditions (still no silent PASS) | TL | Ink on triage H1/H3 |
| U3 | **K5 Project Owner review** of triage + loop summary (`854` iters / `82` fails) | PO / TL | Signed review note (name + date) |
| U4 | **Accept-or-resoak decision** executed: either (a) PO accepts finished window **with** U1–U3 and documents residual risk, **or** (b) new ≥48–72h soak after M1–M3 with fail rate meeting agreed threshold | PO + DevOps | Decision memo + (if b) new `loop-summary-*.json` |
| U5 | Human edits claim file / gate checklist to **`soak_complete_claim: true`** only after U1–U4 | Human | Diff citing this unlock doc |

**Will NOT unlock the claim:**

- Agent triage alone (already DONE)  
- Wall-clock 72h elapsed alone  
- Bounded **production** IL-2A soak (separate; not Wave 11)  
- Staging `/health` 200 recheck alone  
- Flipping the boolean in docs without U1–U4  

---

## Recommended path (honest)

1. Complete U1 RCA (credential/redeploy change window).  
2. Prefer **re-soak ≥48h** after credential stability (U4 option b) — cleaner than accepting a 9.6% fail window dominated by outage.  
3. Only then flip claim under U5.

**2026-08-24:** U1–U5 executed. Claim flipped **true** under Option A (accept finished window with residual risk). Production GA **not** declared.

---

*Step 9: claim true (Option A, 2026-08-24). Evidence governs. Production GA not declared.*
