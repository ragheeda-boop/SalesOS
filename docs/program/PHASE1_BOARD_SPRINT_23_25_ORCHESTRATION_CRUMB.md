# Board orchestration — Sprint 23 / 24 / 25 residuals

> **Role:** Validation/Evidence Stream board synthesis.  
> **Honesty:** Never claim Production GO, Companion acceptance, or Stage 6 as a gate.  
> **Evidence #1 tip-line:** advance only on absolute tip **full tip-line green** (S1–5 + Deploy Health Gate when run; +S7 if path-triggered).  
> **Updated:** 2026-08-03T20:37Z · Evidence #1 **hold** `4754b8b` until absolute tip (`d0070fa`+) tip-line settles green

## Parallel streams

| Stream | Story / work | Status | Crumb / notes |
|--------|--------------|--------|---------------|
| Watchdog tip-line | Evidence #1 | **hold** `4754b8b` | Absolute tip moved: `ea0b068` → `d0070fa` (settling). Advance #1 only on full tip-line green |
| DevOps 14-01 | HTTP tip path | **CLOSED** (light/build validated) | [`PHASE1_STORY_14_01_LOAD_SLO_CRUMB.md`](./PHASE1_STORY_14_01_LOAD_SLO_CRUMB.md) · Active `b95db185` · harness ×2 |
| DevOps 14-01 | True 2h wall-clock soak | **IN PROGRESS** (OPTIONAL) | Tip `ea0b068` — STARTED UTC **2026-08-03T17:34:01Z**; ITER 1 ok; evidence `.tmp-1401-field-soak/`. **Not PASS** until `true_2h_wall_clock_achieved`. Still **OPTIONAL** |
| DevOps → Security | Support evidence pack | **LANDED** @ `ea0b068` | [`PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md`](./PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK.md) + soak runner — ≠ pentest/SOC2 close |
| DevOps deploy | Stale-image Health Gate | **CLOSED/covered** since `c0e4f6a` | Docs tip `4754b8b`; log-stream false-RED CLOSED @ `654b33e` |
| BE → Security | Readiness hooks | **LANDED** @ `d0070fa` | [`PHASE1_STORY_14_04_05_BE_SECURITY_SUPPORT_CRUMB.md`](./PHASE1_STORY_14_04_05_BE_SECURITY_SUPPORT_CRUMB.md) — no new P0 fix; BE **STANDBY** |
| Security 14-04 | Pentest (in-repo max) | **CLOSED (in-repo) / IN_REPO_READY** | [`PHASE1_STORY_14_04_PENTEST_CRUMB.md`](./PHASE1_STORY_14_04_PENTEST_CRUMB.md) · pack under `salesos/docs/pentest/` + `docs/program/evidence/story-14-04/` · firm/SSRF tabletop = residual-external · AC zero-criticals **not validated** |
| Security 14-05 | SOC2 Type I evidence pack | **CLOSED (evidence pack)** | [`PHASE1_STORY_14_05_SOC2_EVIDENCE_CRUMB.md`](./PHASE1_STORY_14_05_SOC2_EVIDENCE_CRUMB.md) · pack [`docs/compliance/soc2-type-i/`](../compliance/soc2-type-i/README.md) · Type I audit = post-GA residual-external · ≠ certified |
| BE 14-02 / 14-03 | Chaos / DR harness | **LANDED BE** | Stream A crumbs; live kill / live prod restore not claimed |
| AI 14-06 / 14-07 | Failover / LLM regression | **LANDED BE** | `feature_ai_copilot` False; live LLM kill not claimed |
| QA Sprint-25 | Full regression on RC | **not validated** | Consider QA crumb when Security packs land; RC soak ≠ claimed |
| BE / FE / AI | Product code | **STANDBY** | Unless Security/DevOps findings need them |

## Acceptance extract (hub honesty)

| Story | AC claim | Honest board rule |
|-------|----------|-------------------|
| **14-04** | Zero unresolved criticals | **Firm/external** required to claim AC. In-repo = pack + remediation only → may **CLOSED (in-repo max)** with **residual-external** firm. Never invent critical=0 from CI Security Scan alone |
| **14-05** | Evidence assembled | **CLOSED (evidence pack)** @ [`docs/compliance/soc2-type-i/`](../compliance/soc2-type-i/README.md). **Type I audit** = **post-GA residual-external** (A5) — ≠ certified; not Phase 6 blocker |
| **Sprint-25 QA** | 100% pass on RC candidate | **not validated** — open QA crumb if/when Security packs land and Board wants RC track |
| **14-01 soak** | Real 2h | **OPTIONAL**; IN PROGRESS ≠ PASS until wall-clock achieved |

## CLOSED vs residual-external (honest)

| Item | Classification |
|------|----------------|
| 14-01 BE HTTP companion + Railway HTTP tip path (phases 1–5) | **CLOSED** (light/build validated) |
| 14-01 true 2h field soak | **OPTIONAL · IN PROGRESS** — not PASS yet |
| Stale-image / log-stream deploy gates | **CLOSED** |
| DevOps Security support pack + soak runner | **LANDED** @ `ea0b068` (support only) |
| BE Security support crumb | **LANDED** @ `d0070fa` — BE STANDBY |
| 14-04 in-repo pack | **CLOSED (in-repo) / IN_REPO_READY** — criticals claim still requires firm+retest |
| 14-04 external firm / staging SSRF tabletop | **residual-external** |
| 14-05 in-repo evidence pack | **CLOSED (evidence pack)** — light validated; Type I audit = **post-GA residual-external** · ≠ Type I certified |
| Sprint-25 QA 100% RC | **not validated** |
| Production GO / GA GO / Companion as acceptance / Stage 6 GHCR gate | **Forbidden / SKIPPED** |

## Sprint plan pointers

| Sprint | File | Board focus |
|--------|------|-------------|
| 23 | [`SPRINT_PLAN/Sprint-23.md`](./SPRINT_PLAN/Sprint-23.md) | 14-01 tip-path CLOSED; 2h soak OPTIONAL IN PROGRESS; 14-02/14-03 LANDED BE |
| 24 | [`SPRINT_PLAN/Sprint-24.md`](./SPRINT_PLAN/Sprint-24.md) | 14-04 CLOSED (in-repo) + residual-external firm; 14-03/14-06 LANDED BE |
| 25 | [`SPRINT_PLAN/Sprint-25.md`](./SPRINT_PLAN/Sprint-25.md) | 14-05 CLOSED (evidence pack); Type I audit post-GA; 14-07 LANDED BE; QA RC **not validated** |

## Board update rule

When a stream lands evidence: update the story crumb first, then Sprint acceptance one-liner, then this table. Prefer **light validated** / **build validated** / **not validated** / **residual-external** / **IN PROGRESS** — never invent stronger labels. Advance Evidence #1 only after absolute tip tip-line green.
