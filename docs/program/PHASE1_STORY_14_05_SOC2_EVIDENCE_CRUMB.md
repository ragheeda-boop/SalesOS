# STORY-14-05 — SOC2 Type I evidence collection

> **Honesty:** Not Production GO. Type I **audit itself** is **post-GA** per `MASTER_EXECUTION_PLAN.md` A5 / Production Readiness.  
> **Sprint:** 25 · Owner: Security, Program Director.  
> **Status:** **CLOSED (evidence pack)** — in-repo assembly **light validated** · Type I audit = **residual-external / post-GA**.  
> **Pack path:** [`docs/compliance/soc2-type-i/`](../compliance/soc2-type-i/README.md)  
> **Board hub:** [`PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB.md`](./PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB.md)

## In-repo pack (Security stream)

| Evidence domain | Intent | Status |
|-----------------|--------|--------|
| Audit logging completeness | Index controls + tip/CI evidence pointers | **CLOSED (pack)** — [`01-audit-logging.md`](../compliance/soc2-type-i/01-audit-logging.md) · live 90d export = **not validated** / ops residual |
| Access review process | Documented process + sample evidence | **CLOSED (pack process)** — [`02-access-review.md`](../compliance/soc2-type-i/02-access-review.md) · signed worksheets = **Program Director residual** |
| Change management evidence | Tip-line / Deploy / PR process pointers (honest) | **CLOSED (pack)** — [`03-change-management.md`](../compliance/soc2-type-i/03-change-management.md) + [`PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md`](./PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md) @ `4754b8b` |
| Controls mapping sketch | TSC → repo pointers | **CLOSED (sketch)** — [`05-controls-mapping.md`](../compliance/soc2-type-i/05-controls-mapping.md) · ≠ auditor matrix |
| Gap inventory | Explicit residuals | [`04-gap-inventory.md`](../compliance/soc2-type-i/04-gap-inventory.md) |
| Log retention window | Ops residual (90d SOC2 Type I window per checklist) | Config default 90d present · live proof **not validated** / may be **residual-external** ops |
| BE runtime hooks | Audit / headers / rate-limit / CSRF / RLS | [`PHASE1_STORY_14_04_05_BE_SECURITY_SUPPORT_CRUMB.md`](./PHASE1_STORY_14_04_05_BE_SECURITY_SUPPORT_CRUMB.md) (`d0070fa`) |

## Explicit non-claims

| Item | Label |
|------|-------|
| SOC2 Type I audit completed / certified | **post-GA residual-external** — not a Phase 6 blocker |
| SOC2 Type II | **post-GA** — N/A at GA |
| Production GO / Companion acceptance | **Forbidden** |
| Stage 6 GHCR as compliance gate | **SKIPPED** (DEC-150 B) |

## Product roadmap alignment

- `PRODUCT_ROADMAP.md` D6.4: Type I **evidence collection underway** — does not require Type I audit complete pre-GA.  
- Story acceptance (Sprint-25): assemble audit logging / access review / change management evidence — **pack**, not auditor letter. **Met (in-repo).**

## Board close criteria (in-repo)

1. ~~Security lands an evidence index (paths + what’s proven vs not).~~ **Done** — `docs/compliance/soc2-type-i/`.  
2. Sprint-25 line updated: **CLOSED (evidence pack)** with Type I audit called out as **residual-external / post-GA**.  
3. This crumb flipped with honest validation labels only.  

## Still needs Program Director / auditor

See [`04-gap-inventory.md`](../compliance/soc2-type-i/04-gap-inventory.md): signed access reviews, CAB mapping, branch-protection screenshots, live 90d log export, formal Type I engagement.

## Non-goals

- Inventing auditor sign-off  
- Claiming Type I/II complete  
- Reopening Stage 6 GHCR as a SOC2 gate  
