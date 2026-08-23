# U4 — Accept-or-Resoak Decision (2026-08-22)

**Finding:** EAB-001-P0-OPS-01 / OPS01-04
**Date:** 2026-08-22
**Author:** Engineering Agent (automated — PO decision required)
**Depends on:** U1 (RCA), U2 (K4 disposition), U3 (PO review)

---

## Decision Record

### Option A: Accept Finished Window (Recommended)

| Attribute | Value |
|-----------|-------|
| Decision | Accept the 854-iteration soak window with documented residual risk |
| Rationale | Root cause fixed; staging parity achieved; 5 clean deploys; 9.6% failure rate entirely from single 7h outage now remediated |
| Conditions | (1) No credential rotation during future soak windows; (2) preDeployCommand aligned with railway.json |
| Residual risk | Future credential changes could cause similar outage; mitigated by rollback script |

### Option B: Re-Soak (Minimum 48h)

| Attribute | Value |
|-----------|-------|
| Decision | Start new soak window after config drift fix |
| Rationale | Cleaner evidence chain; avoids accepting a 9.6% failure window |
| Prerequisites | Config drift fix (preDeployCommand alignment) + credential stability verification |
| Estimated time | 48-72h after config fix |

---

## Engineering Recommendation

**Option A (Accept)** is recommended because:
1. The incident is fully understood and remediated
2. Staging parity is verified (not just deployed — schema_version confirmed)
3. The failure pattern is deterministic (single window, not random)
4. Re-soaking adds 48-72h delay with no new information expected
5. The 2 non-outage failures (transient network) are within acceptable bounds

---

## PO + DevOps Decision Required

| Role | Name | Date | Decision |
|------|------|------|----------|
| Project Owner | ___ | ___ | [ ] Accept (Option A) [ ] Re-soak (Option B) |
| DevOps | ___ | ___ | [ ] Accept (Option A) [ ] Re-soak (Option B) |

**Decision Notes:**
_____________________________________________
_____________________________________________

**Signatures:**

PO: _________________________ Date: ___________

DevOps: _________________________ Date: ___________
