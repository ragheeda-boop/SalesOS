# A-09: Staging Parity Assessment

> **Last Updated:** 2026-08-12  
> Classification: INFRASTRUCTURE AUDIT  
> **Validation:** **light validated** for host liveness + prior machine parity baseline; **A-09 residual OPEN** (not closed)

---

## Current State (2026-08-12 refresh)

| Metric | Production | Staging | Status |
|--------|------------|---------|--------|
| **Host** | `salesos-production-96c0.up.railway.app` | `salesos-staging.up.railway.app` | Both `/health` **200** (probed) |
| **Git branch** | `master` | **No `staging` branch** | Gap |
| **CI deploy workflow** | `deploy.yml` / `deploy-production.yml` | `deploy-staging.yml` exists | Wiring present; full CI exercise residual |
| **Parity baseline** | See EAB-003 DIFF (2026-08-07) | Same commit class at baseline freeze | Machine baseline exists; Human-Gate residuals OPEN |
| **Business data for Decision soak** | Populated | Historically empty / not seeded for IL-2A | Functional soak → prod (bounded) |
| **48–72h health soak claim** | N/A | Harness finished 2026-08-10; **`soak_complete_claim=false`** | OPEN |

Supersedes the stale “409 commits behind / no staging host” reading for **host existence**. Critical diffs and Human-Gate items in [`STAGING-vs-PRODUCTION-DIFF.md`](../ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/STAGING-vs-PRODUCTION-DIFF.md) and [`staging-parity-checklist.md`](../ga-engineering-audit/runbooks/staging-parity-checklist.md) still govern **parity complete**.

---

## Known Issues (GO gaps)

1. **No `staging` git branch** — Railway env + workflow only  
2. **Human-Gate residuals** — Google OAuth staging app; WAL/PITR/offsite; `max_connections`; rollback tabletop; GH Environment re-probe  
3. **PROD-W11-002 soak claim** — not flipped (health-loop had failures; Decision path not part of that harness)  
4. **Staging not seeded** for Decision→AgentTask functional parity  

---

## 2026-08-12 bounded prod IL-2A soak (not staging parity)

Documented in [`docs/reports/A09-BOUNDED-PROD-IL2A-SOAK-2026-08-12.md`](../../reports/A09-BOUNDED-PROD-IL2A-SOAK-2026-08-12.md).

- 8/8 evaluate **200**; AgentTask isolation/idempotency **PASS** (DB)  
- Explicitly **not** A-09 / Wave 11 close  

---

## Recommendations

| Priority | Action | Owner |
|----------|--------|-------|
| P0 | Close Human-Gate checklist items (OAuth, backup posture acceptance, CI deploy evidence) | DevOps / Platform |
| P0 | Seed staging tenant+companies **or** accept prod-only functional soak until seed exists | DevOps / Backend |
| P1 | Human review of 72h health-loop failures → Soak Report before any claim flip | TL / DevOps |
| P2 | Optional `staging` branch policy if required by release process | DevOps |

---

*A-09 remains OPEN. Evidence governs.*
