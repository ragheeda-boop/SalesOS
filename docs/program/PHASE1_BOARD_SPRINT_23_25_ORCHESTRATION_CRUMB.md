# Board orchestration — Sprint 23 / 24 / 25 residuals

> **Role:** Validation/Evidence Stream board synthesis.  
> **Honesty:** Never claim Production GO, Companion acceptance, or Stage 6 as a gate.  
> **Evidence #1 tip-line:** advance only on absolute tip **full tip-line green** (S1–5 + Deploy Health Gate when run; +S7 if path-triggered).  
> **Updated:** 2026-08-03T22:17Z · Evidence #1 pin **`26f2ab5`** · absolute tip **`a8966c0`** settling · Bugbot/Security review findings ingested · No Production GO

## Parallel streams

| Stream | Story / work | Status | Crumb / notes |
|--------|--------------|--------|---------------|
| Watchdog tip-line | Evidence #1 | **pin `26f2ab5`** (hold) | Absolute tip **`a8966c0`** — Security Scan green; CI/Smoke/Deploy in progress. Advance #1 **only** on full tip-line green |
| DevOps 14-01 | HTTP tip path | **CLOSED** (light/build validated) | Active `b95db185` · harness ×2 |
| DevOps 14-01 | True 2h soak | **IN PROGRESS** (attempt 2) · **not PASS** | `.tmp-1401-field-soak-r2/` ~1.4h/7200 · iter 9 ok · `field_2h_soak_claim=false` · no `soak_final.json` |
| DevOps scrub | `.tmp-1401-*` JWT evidence | **IN FLIGHT** (HIGH) | Bugbot: JWT evidence must **not** be in git — scrub + gitignore in flight |
| DevOps recover | Log-stream false-RED | **CLOSED** @ **`26f2ab5`** | 20m Railway SUCCESS poll |
| BE logout revoke | `revoke_by_refresh_jti` wiring | **IN FLIGHT** (MEDIUM) | Not wired to `/logout` path — BE fixing; FE-SEC-03 honesty = **partial** until landed |
| BE cookies / session | Refresh httpOnly + logout | **STANDBY** / partial | httpOnly refresh present; BFF access = FE-SEC-02 |
| FE → Security | CSRF + logout + refresh | **LANDED** @ `34f4a81` / `2148dd7` · **light validated** | FE-SEC-01/04 Fixed. FE-SEC-03 **partial Fixed**. FE-SEC-02 **Open**. Live logout **not validated** |
| FE-SEC-02 | Access JWT LS / BFF | **Open** residual (High) | Security review: no new medium+ in changed code; FE-SEC-02 still Open |
| Security 14-04 | Firm handoff | **CLOSED (in-repo)** · handoff **READY** | Firm/zero-criticals residual-external — **NOT claimed** |
| Security 14-05 | SOC2 + PD templates | **CLOSED (evidence pack)** @ `11d0d3f` | Type I NOT certified · PD signatures residual |
| Reviews | Bugbot + Security Review | **LANDED findings** | HIGH tmp JWT scrub · MEDIUM logout JTI revoke · FE-SEC-02 Open · live logout not validated |
| QA Sprint-25 | RC prep | **INVENTORY ONLY / not validated** | Prefer RC `26f2ab5` until #1 advances |

## FE residuals → 14-04 tracker

| ID | Status | Notes |
|----|--------|-------|
| FE-SEC-01 | **Fixed** @ `34f4a81` | CSRF mint/attach on axios |
| FE-SEC-02 | **Open** residual | Access JWT LS / XSS — BFF/httpOnly slice flags OFF; Security: no new medium+ in changed code |
| FE-SEC-03 | **Partial Fixed** @ `2148dd7` | FE calls `/logout`; BE `revoke_by_refresh_jti` **not wired** — BE fixing · live logout **not validated** |
| FE-SEC-04 | **Fixed** @ `2148dd7` | Cookie-first refresh (+ LS fallback) |

Register: [`salesos/docs/pentest/FINDINGS_TRACKER.md`](../../salesos/docs/pentest/FINDINGS_TRACKER.md) — FE tip `2148dd7` light validated (Jest 9 PASS) ≠ story AC close · ≠ Production GO

## Acceptance extract (hub honesty)

| Story | Rule |
|-------|------|
| **14-04** | **CLOSED (in-repo)** · handoff READY; firm/zero-criticals **NOT claimed**; FE-SEC-02 Open; FE-SEC-03 **partial** until BE JTI revoke wired |
| **14-05** | **CLOSED (evidence pack)** @ `11d0d3f`; PD templates **LANDED** (unsigned `06`–`09`); signatures / screenshots / live 90d export residual; Type I post-GA **NOT certified** |
| **QA** | Candidate RC `26f2ab5` pinned — results **NOT VALIDATED**; 100% pass **forbidden**; Board RC declare pending |
| **Soak** | Attempt 2 IN PROGRESS (~1.4h / 5120s of 7200) ≠ PASS · **not validated** |

## CLOSED vs residual-external

| Item | Classification |
|------|----------------|
| 14-04 in-repo pack | **CLOSED (in-repo) / IN_REPO_READY** (via `a5b32df`+) |
| 14-04 firm handoff package | **READY** (brief v1.2 + vendor checklist + intake) |
| 14-04 FE-SEC-02 | **Open residual** (BFF httpOnly proposal; High) |
| 14-04 FE-SEC-03/04 | **Fixed** @ `2148dd7` (light validated Jest 9 PASS) |
| 14-04 firm / staging SSRF | **residual-external** |
| 14-05 pack | **CLOSED** light validated @ `11d0d3f` · PD templates `06`–`09` **LANDED** (unsigned) |
| FE CSRF land | **light validated** support only |
| Production GO | **Forbidden** |

## Sprint plan pointers

| Sprint | File | Board focus |
|--------|------|-------------|
| 23 | [`SPRINT_PLAN/Sprint-23.md`](./SPRINT_PLAN/Sprint-23.md) | 14-01 tip-path CLOSED; 2h soak attempt 2 IN PROGRESS (~4856s) ≠ PASS; Evidence #1 `26f2ab5` |
| 24 | [`SPRINT_PLAN/Sprint-24.md`](./SPRINT_PLAN/Sprint-24.md) | 14-04 CLOSED (in-repo) · handoff READY · FE-SEC-02 Open · residual-external firm |
| 25 | [`SPRINT_PLAN/Sprint-25.md`](./SPRINT_PLAN/Sprint-25.md) | 14-05 CLOSED (evidence pack) @ `11d0d3f` + PD templates LANDED; QA candidate RC `26f2ab5` / results **NOT VALIDATED**; Type I audit post-GA |

## Board update rule

Update story crumb → Sprint one-liner → this hub. Prefer honest labels only. Advance Evidence #1 only after absolute tip tip-line green. No Production GO / zero-criticals invent.
