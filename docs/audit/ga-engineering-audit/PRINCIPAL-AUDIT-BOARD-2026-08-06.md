# Principal Audit Board — SalesOS Re-audit (2026-08-06)

**Date:** 2026-08-06  
**Product audited:** SalesOS (`salesos/`) inside Muhide workspace  
**Platform intent:** Private Governed Institutional Intelligence — SalesOS is the shipped product under audit  
**Method:** 6 parallel explore agents + Principal synthesis  
**Evidence class:** Mostly **static** / **light validated** — not soak, not full browser journey suite, not full pytest/npm suites this board  
**Authority chain:** Executable evidence → this board → [00-EXECUTIVE-SUMMARY.md](./00-EXECUTIVE-SUMMARY.md) (2026-07-22 baseline) → [PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md)  
**Decision class:** Production GA GO / NO-GO for CTO  

> **Verdict:** **NO-GO** for Production GA. Classification: **production no-go**.  
> Do **not** invent Production GO, browser pass, or green full suites from this report.

---

## Final recommendation

| Release | Decision | Classification |
|---------|----------|----------------|
| **Production GA** | **NO-GO** | production no-go |
| **External Pilot** | **NO-GO** | production no-go |
| **Internal demo / engineering preview** | Conditional only after listed P0s | pilot-ready with conditions *(target, not current)* |

**Why NO-GO (synthesis):** Entitlement / quota / suspended-tenant / API-key enforcement can no-op when `app.state.db_session_factory` is never set; process-lifetime AsyncSession singletons lack tenant GUC with silent BYPASSRLS owner fallback if `APP_POSTGRES_PASSWORD` is empty; frontend “build succeeds instead of verifies,” blank SSR (providers null until `useEffect`), and ~42 undefined CSS vars; three decision engines with route collisions; 14 orphan `MetaData()`; dual compose; no offsite/WAL/staging readiness for GA cutover.

---

## Scorecard (0–100)

| Dimension | Score | Evidence basis |
|-----------|------:|----------------|
| Architecture | **42** | Multi-engine decision surface; route collisions; dual compose; orphan metadata sprawl |
| Backend | **48** | Middleware no-ops; session singleton / tenant isolation risks; residual P0 wiring gaps |
| Frontend | **41** | Build does not verify; blank SSR; undefined design tokens (~42 CSS vars) |
| Database / RLS | **55** | RLS intent present; owner BYPASSRLS fallback + missing tenant GUC undermine isolation |
| Security | **72** | Control presence improved vs stale register **48**; residual P0s remain — see note below |
| DevOps | **58** | Dual compose; no offsite/WAL/staging parity for GA |
| Testing | **56** | Suite exists; this board did **not** re-run full suites (low-load) |
| Docs | **61** | Audit/plan/honesty docs strong; some scoreboard drift vs live residual risks |
| Product readiness | **54** | Internal preview possible after P0s; external pilot / GA blocked |
| Technical debt | **71** | Debt mapped and partially remediated across waves; structural roots remain |
| **Production readiness** | **~42** | Enforcement gaps + FE verify gaps + DR/staging gaps |
| **Overall** | **~49** | Weighted synthesis across dimensions |

**Security score note:** **72** reflects **control presence** (auth shell, CSRF path, AI honesty gates, prior Wave 2+ remediations) and **supersedes** the stale 2026-07-22 register score of **48** for that dimension alone. Residual **P0** enforcement/isolation issues remain; Security **72** is **not** a Production GO signal.

---

## Top root causes (4)

1. **`app.state.db_session_factory` never set** → entitlement / quota / suspended-tenant / API-key middleware effectively **no-op** when factory is missing.
2. **Process-lifetime AsyncSession singletons** without tenant GUC + **silent BYPASSRLS owner fallback** if `APP_POSTGRES_PASSWORD` is empty → tenant isolation can fail open.
3. **Frontend build “succeeds instead of verifies”**; **blank SSR** (providers null until `useEffect`); **~42 undefined CSS vars** → shippable artifact does not prove UI correctness.
4. **Three decision engines / route collisions**; **14 orphan `MetaData()`**; **dual compose**; **no offsite / WAL / staging** readiness for GA cutover.

---

## Dimension summaries

### Architecture (~42)
SalesOS DDD layout remains recognizable, but product surface is fragmented: multiple decision engines, colliding routes, dual compose stacks, and orphan SQLAlchemy `MetaData()` islands. Architecture score stays **low 40s** until a single decision path and one operational compose/DR story are authoritative.

### Backend (~48)
Auth and middleware shells exist, but critical enforcement depends on a session factory that explore evidence indicates is **never set**, turning entitlement/quota/suspension/API-key checks into no-ops. Session singleton lifetime without tenant GUC compounds isolation risk. Classification remains **production no-go** for BE enforcement honesty.

### Frontend (~41)
FE can appear “green” while failing to verify: build path does not gate correctness; SSR renders without providers until client `useEffect`; design tokens (~42 CSS variables) are undefined in places. Decision package remains a **STUB** per [AI_HONESTY.md](./AI_HONESTY.md) — do not market as live GA AI.

### Database / RLS (~55)
RLS and app-role intent are stronger than early GA docs claimed, but isolation is undermined by owner BYPASSRLS fallback when app password is empty and by missing tenant GUC on long-lived sessions. Score is mid-50s: direction correct, fail-open paths unacceptable for GA.

### Security (~72)
Control inventory improved vs 2026-07-22 baseline (**48**). This board scores **72** for **presence** of controls and prior remediations, while explicitly retaining residual **P0** enforcement gaps (middleware no-ops, RLS fail-open). **Not** production-ready security posture.

### DevOps (~58)
Dual compose (root vs `salesos/`), incomplete offsite backup / WAL / PITR, and staging parity gaps keep DevOps below GA bar. Local drills and gates from prior waves are **not** a substitute for staging soak + signed go-live.

### Product / QA / Docs (~54 / ~56 / ~61)
Product readiness supports **conditional internal demo after P0s** only. Testing score reflects existence of suites without this board re-executing them (**not validated** for full green). Docs and governance (audit folder, PRODUCTION_PLAN, AI honesty) are relatively strong (**~61**) but must not outrun residual runtime evidence.

---

## P0 / P1 prioritized backlog (synthesis top items)

### P0 — must close before any external pilot

| ID | Item | Why |
|----|------|-----|
| P0-1 | Wire `app.state.db_session_factory` (or equivalent) so entitlement / quota / suspended-tenant / API-key middleware **cannot no-op** | Enforcement fail-open |
| P0-2 | Eliminate process-lifetime AsyncSession singletons without tenant GUC; **forbid** silent BYPASSRLS owner fallback when `APP_POSTGRES_PASSWORD` empty | Tenant isolation fail-open |
| P0-3 | Make FE build **verify** (fail on broken verify path); fix blank SSR providers; resolve undefined CSS vars (~42) | Artifact honesty / UX integrity |
| P0-4 | Collapse to **one** decision engine surface; remove route collisions; stop presenting FE decision stub as live AI | Product + AI honesty |
| P0-5 | Staging parity + offsite backup / WAL story before cutover claims | DR / ops NO-GO |

### P1 — high priority after P0

| ID | Item | Why |
|----|------|-----|
| P1-1 | Reduce / unify orphan `MetaData()` (14) into governed schema ownership | Maintainability + migration risk |
| P1-2 | Single authoritative compose / deploy path (retire dual-stack ambiguity) | Ops clarity |
| P1-3 | Reconcile GA_STATUS / wave scoreboards with residual P0 enforcement findings | Doc honesty |
| P1-4 | Focused regression suite for middleware + RLS tenant filters (approved narrow path) | Evidence upgrade |
| P1-5 | CTO/TL signed go-live checklist only after P0 evidence | Governance |

---

## Comparison vs 2026-07-22 baseline

| Dimension | 2026-07-22 baseline | This board (2026-08-06) | Delta / note |
|-----------|--------------------:|------------------------:|--------------|
| Security | **48** | **72** | Control presence up; **residual P0s remain** — supersedes stale register for control score only |
| Production readiness | **38** | **~42** | Slightly up; still **NO-GO** |
| Overall / board | low 40s | **~49** | Still **low 40s–50s**; not GA |
| Production GA | **NO-GO** | **NO-GO** | Unchanged |
| External pilot | **NO-GO** | **NO-GO** | Unchanged |

Waves 0–24 and later remediations improved control inventory and local evidence in places; this Principal Board does **not** convert those into Production GO. Live scoreboard context: [GA_STATUS.md](./GA_STATUS.md).

---

## What is NOT claimed / validation honesty

| Claim | Status this board |
|-------|-------------------|
| Production GA GO | **Not claimed** — **NO-GO** |
| External pilot ready | **Not claimed** — **NO-GO** |
| Full npm lint / build / test suite green | **Not validated** (not run this board; low-load) |
| Full pytest / coverage gate | **Not validated** |
| 48–72h staging soak complete | **Not claimed** |
| Full authenticated browser / Playwright GA pass | **Not validated** as GA evidence this board |
| Offsite backup + WAL/PITR production ready | **Not claimed** |
| FE Decision Engine live GA AI | **Not claimed** — STUB; see [AI_HONESTY.md](./AI_HONESTY.md) |
| Security 72 = no residual P0 | **False** — residual P0s remain |

**Labels used:** **not validated**, **light validated**, **production no-go**, **pilot-ready with conditions** *(target after P0s only)*.

---

## Related documents

| Doc | Role |
|-----|------|
| [00-EXECUTIVE-SUMMARY.md](./00-EXECUTIVE-SUMMARY.md) | 2026-07-22 CTO brief / baseline NO-GO |
| [PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md) | Waves 0–14 execution plan |
| [GA_STATUS.md](./GA_STATUS.md) | Live scoreboard (still NO-GO) |
| [AI_HONESTY.md](./AI_HONESTY.md) | AI marketing / stub honesty |
| [README.md](./README.md) | Audit folder index |

---

## Canvas companion (optional)

Interactive Principal Audit Board canvas (Cursor project):

`canvases/salesos-production-audit-board-2026-08-06.canvas.tsx`

Primary deliverable for governance and CTO circulation is **this markdown file**. The canvas is a companion view only — it does not change the **NO-GO** decision.

---

## Provenance (explore agents)

| Dimension | Agent ID (optional) |
|-----------|---------------------|
| Architecture | `393505ef` |
| Backend / DB | `f8450257` |
| Frontend | `6856d209` |
| Security | `5c30cc2b` |
| DevOps | `7f986f49` |
| Product | `d45781f4` |

**Synthesis:** Principal Audit Board, 2026-08-06. Evidence class: static + light-validated exploration; not soak / not full browser GA / not full suite re-run.
