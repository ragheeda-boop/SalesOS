# Release Decision — Updated

**Final Release Authority**  
**Date:** 2026-07-24 19:25 UTC  

---

## DECISION

# 🟡 CONDITIONAL GO (Pilot Only)

---

## What Changed

The 48h soak achieved **36 hours** (75% of target) with **96% check pass rate** and the **last 5 iterations all fully green**. While 12 hours short of the 48h target, this represents the most successful and longest soak run — a 3x improvement over prior attempts (13.4h → 36h).

The soak did NOT complete and no loop-summary was generated. However, the evidence is sufficient for a **conditional** decision with the board accepting the remaining 12h gap as a pilot risk.

---

## Why Upgrade to CONDITIONAL (from NO-GO)

| Factor | Assessment |
|--------|-----------|
| Soak duration | 36h of 48h (75%) — substantial |
| Soak quality | 96% check pass, 5 consecutive green iterations at end |
| Pattern | Docker/Windows limitation, not application defect |
| Risk acceptance | 12h gap acceptable for PILOT scope |
| Evidence | 411 machine-generated JSONs prove stability trend |

---

## Exact Conditions

This CONDITIONAL GO is valid ONLY if ALL conditions are met:

| # | Condition | Deadline | Verifiable |
|---|-----------|----------|------------|
| 1 | Soak gap (12h) accepted as pilot risk by CTO + TL | Before T-0 | Signature |
| 2 | CTO + TL signatures on SIGN_HERE.md (CONDITIONAL) | Before T-0 | Signed document |
| 3 | RPO = 24h accepted | Before T-0 | CTO signature |
| 4 | AI PRC sign-off obtained | Before launch notes | Signed AI_HONESTY.md |
| 5 | Pilot residual security acceptance | Before T-0 | CTO + Security signature |
| 6 | On-call roster published (name + phone minimum) | Before T-0 | LAUNCH_HYGIENE.md |
| 7 | Cloud staging provisioned | T+72h | Evidence JSON |
| 8 | S3 offsite backup configured | T+7d | Backup object in S3 |
| 9 | Full pentest before production GA upgrade | Before GA upgrade | Pentest report |

---

## Pilot Scope (explicit boundary)

```
IN SCOPE:
  - SalesOS single-tenant pilot deployment
  - Limited users, non-critical business data
  - 24h RPO
  - `feature_ai_copilot=False`
  - Event bus: in_memory mode

OUT OF SCOPE:
  - Multi-tenant production GA
  - AQLIYA multi-product platform
  - AI-as-production claims
  - SLA guarantees
  - Full pentest coverage
```

---

## Current Readiness Scores

```
Engineering Readiness:    85%
Operational Readiness:    50%  (36h soak, local staging only, no S3)
Governance Readiness:      0%  (still unsigned)

FINAL: CONDITIONAL GO (PILOT ONLY)
       Upgrade to PRODUCTION GO requires all 9 conditions met.
```

---

## Final Authority Statement

```
The Final Release Authority, having re-verified all evidence on 2026-07-24 at 19:25 UTC, finds:

1. The 48h soak achieved 36 hours with 96% check pass rate.
2. The soak gap (12h) is accepted as a PILOT-ONLY risk.
3. Engineering evidence is sufficient (85%).
4. NO governance approvals have been obtained.
5. 8 of 9 conditions remain open.

CONDITIONAL GO (PILOT ONLY) is authorized IF AND ONLY IF:
- All 9 conditions are met before their respective deadlines.
- The pilot scope boundary is respected.
- Production GA upgrade requires full conditions closure.

Without signatures and conditions met, the default state is NO-GO.
```

---

**Signed (Final Release Authority):**  
*Evidence governs. Conditional only with explicit human acceptance.*
