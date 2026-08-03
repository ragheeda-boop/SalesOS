# STORY-14-05 — SOC2 Type I evidence collection

> **Honesty:** Not Production GO. Type I **audit itself** is **post-GA** per `MASTER_EXECUTION_PLAN.md` A5 / Production Readiness.  
> **Sprint:** 25 · Owner: Security, Program Director.  
> **Status:** **IN FLIGHT** (in-repo evidence pack assembly) · Type I audit = **residual-external / post-GA**.

## In-repo pack (Security stream)

| Evidence domain | Intent | Status |
|-----------------|--------|--------|
| Audit logging completeness | Index controls + tip/CI evidence pointers | **not validated** — awaiting Security land |
| Access review process | Documented process + sample evidence | **not validated** — awaiting Security land |
| Change management evidence | Tip-line / Deploy / PR process pointers (honest) | DevOps pack + BE hooks ready (`ea0b068` / `d0070fa`) — Security still must assemble index (**pack not validated** until landed). Type I **audit** = post-GA |
| Log retention window | Ops residual (90d SOC2 Type I window per checklist) | **not validated** / may be **residual-external** ops |

## AI honesty index (for Security / Evidence — required alignment)

Canonical SoT: [`docs/audit/ga-engineering-audit/AI_HONESTY.md`](../audit/ga-engineering-audit/AI_HONESTY.md).  
**Code check (tip):** `feature_ai_copilot: bool = False` in `salesos/backend/app/config.py`; FE `@salesos` decision package remains **STUB** (`salesos/frontend/packages/platform/decision/index.ts`).

| Claim | Evidence label |
|-------|----------------|
| Copilot / “AI-native GA” | **Not claimed** — flag default **False**; product API 403 when False |
| Decision FE package live GA | **Not claimed** — **STUB** throws; use Decision Center HTTP, not stub as GA AI |
| Live LLM / RAG GO | **Not claimed** |
| Production GO from AI harnesses | **Forbidden** |

**Harness residuals Security may cite (non-prod / CI only):**

- STORY-14-07 LLM regression — [`PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md`](./PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md) (`/api/v1/chaos/llm-regression`; fixtures only)
- STORY-14-06 AI failover — [`PHASE1_STORY_14_06_AI_FAILOVER_CRUMB.md`](./PHASE1_STORY_14_06_AI_FAILOVER_CRUMB.md) (fake providers; no live kill)

These prove **honesty + CI harness presence**, not live LLM GO or SOC2 Type I audit completion.

## Explicit non-claims

| Item | Label |
|------|-------|
| SOC2 Type I audit completed | **post-GA** — not a Phase 6 blocker |
| SOC2 Type II | **post-GA** — N/A at GA |
| Production GO / Companion acceptance | **Forbidden** |
| Stage 6 GHCR as compliance gate | **SKIPPED** (DEC-150 B) |
| Live LLM / `feature_ai_copilot=True` / Decision STUB as GA | **Forbidden** |

## Product roadmap alignment

- `PRODUCT_ROADMAP.md` D6.4: Type I **evidence collection underway** — does not require Type I audit complete pre-GA.  
- Story acceptance (Sprint-25): assemble audit logging / access review / change management evidence — **pack**, not auditor letter.

## Board close criteria (in-repo)

1. Security lands an evidence index (paths + what’s proven vs not).  
2. Sprint-25 line updated: **CLOSED (evidence pack)** with Type I audit called out as **residual-external / post-GA**.  
3. This crumb flipped with honest validation labels only.

## Non-goals

- Inventing auditor sign-off  
- Claiming Type I/II complete  
- Reopening Stage 6 GHCR as a SOC2 gate  
