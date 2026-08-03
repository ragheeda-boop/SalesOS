# Board orchestration — Sprint 23 / 24 / 25 residuals

> **Role:** Validation/Evidence Stream board synthesis.  
> **Honesty:** Never claim Production GO, Companion acceptance, or Stage 6 as a gate.  
> **Evidence #1 tip-line:** advance only on absolute tip **full tip-line green** (S1–5 + Deploy Health Gate when run; +S7 if path-triggered).  
> **Updated:** 2026-08-03T22:20Z · Evidence #1 **hold** `26f2ab5` · absolute tip **`6a70dc8`** (QA RC candidate land) settling · soak ~81m IN PROGRESS ≠ PASS · No Production GO

## Parallel streams

| Stream | Story / work | Status | Crumb / notes |
|--------|--------------|--------|---------------|
| Watchdog tip-line | Evidence #1 | **pin `26f2ab5`** (hold) | Absolute tip **`6a70dc8`** (or later). Advance #1 **only** on full tip-line green (S1–5 + Deploy Health Gate) |
| DevOps 14-01 | HTTP tip path | **CLOSED** (light/build validated) | Active `b95db185` · harness ×2 |
| DevOps 14-01 | True 2h soak | **IN PROGRESS** (~91m / 5460s) · **not PASS** | `.tmp-1401-field-soak-r2/` iter 10 ok · `field_2h_soak_claim=false` · no `soak_final.json` |
| DevOps scrub | `.tmp-1401-*` JWT evidence | **IN FLIGHT** (HIGH) | Bugbot scrub + gitignore |
| DevOps recover | Log-stream false-RED | **CLOSED** @ **`26f2ab5`** | 20m Railway SUCCESS poll |
| BE logout revoke | `revoke_by_refresh_jti` | **IN FLIGHT** (MEDIUM) | FE-SEC-03 honesty = **partial** until wired |
| FE-SEC-02 | BFF httpOnly access | **IN FLIGHT** FE/BE | High residual; flags OFF / slice in flight — no half-break |
| FE → Security | CSRF + logout + refresh | **LANDED** @ `34f4a81` / `2148dd7` | FE-SEC-01/04 Fixed; 03 partial; live logout not validated |
| Security 14-04 | Firm handoff | **CLOSED (in-repo)** · handoff **READY** | Firm/zero-criticals residual-external — **NOT claimed** |
| Security 14-05 | SOC2 + PD templates | **CLOSED (pack)** @ `11d0d3f` · PD templates **LANDED** @ `682a50d` (`06`–`09`, unsigned) | Signatures / screenshots / live 90d export residual · Type I NOT certified |
| CODEOWNERS | Repo ownership | **IN FLIGHT** | Launching now |
| Go-Live / Hypercare | Runbooks | **IN FLIGHT** | Launching now |
| Reviews | Bugbot + Security | **LANDED findings** | HIGH tmp JWT · MEDIUM logout JTI · FE-SEC-02 Open |
| QA Sprint-25 | RC regression evidence | **CANDIDATE DOCUMENTED** @ tip **`6a70dc8`** | Candidate RC pin **`26f2ab5`** · empty results tables **NOT VALIDATED** · Board freeze **pending** · no 100% pass ([`PHASE1_SPRINT25_QA_REGRESSION_CRUMB.md`](./PHASE1_SPRINT25_QA_REGRESSION_CRUMB.md)) |

## Top-5 in-repo residuals (feed)

| # | Residual | Owner / stream | Status |
|---|----------|----------------|--------|
| 1 | FE-SEC-02 BFF httpOnly | FE/BE | **IN FLIGHT** |
| 2 | Sprint-25 RC regression evidence | QA | **CANDIDATE** @ `6a70dc8` / RC `26f2ab5` — Board freeze pending · **NOT VALIDATED** |
| 3 | CODEOWNERS | Platform / DevOps | **IN FLIGHT** (launching) |
| 4 | Go-Live / Hypercare runbooks | DevOps / Ops | **IN FLIGHT** (launching) |
| 5 | CAB tip↔ticket scaffold | 14-05 PD templates | **IN FLIGHT** (launching) |

## FE residuals → 14-04 tracker

| ID | Status | Notes |
|----|--------|-------|
| FE-SEC-01 | **Fixed** @ `34f4a81` | CSRF mint/attach on axios |
| FE-SEC-02 | **Open / IN FLIGHT** | BFF httpOnly FE/BE stream |
| FE-SEC-03 | **Partial Fixed** @ `2148dd7` | BE `revoke_by_refresh_jti` unwired · live logout not validated |
| FE-SEC-04 | **Fixed** @ `2148dd7` | Cookie-first refresh |

Register: [`salesos/docs/pentest/FINDINGS_TRACKER.md`](../../salesos/docs/pentest/FINDINGS_TRACKER.md)

## Acceptance extract (hub honesty)

| Story | Rule |
|-------|------|
| **14-04** | CLOSED (in-repo) · handoff READY; firm/zero-criticals **NOT claimed**; FE-SEC-02 Open/IN FLIGHT; FE-SEC-03 partial |
| **14-05** | **CLOSED (evidence pack)** @ `11d0d3f`; PD templates **LANDED** @ `682a50d` (unsigned `06`–`09`); signatures residual; Type I **NOT certified** |
| **QA** | Tip `6a70dc8` documents candidate RC **`26f2ab5`** · results tables empty **NOT VALIDATED** · Board freeze pending · **no 100% pass** |
| **Soak** | ~91m / 5460s of 7200 IN PROGRESS ≠ PASS · **not validated** |

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
| 25 | [`SPRINT_PLAN/Sprint-25.md`](./SPRINT_PLAN/Sprint-25.md) | QA tip `6a70dc8` candidate RC `26f2ab5` **NOT VALIDATED**; 14-05 PD templates **LANDED** @ `682a50d` (unsigned); Type I post-GA |

## Board update rule

Update story crumb → Sprint one-liner → this hub. Prefer honest labels only. Advance Evidence #1 only after absolute tip tip-line green. No Production GO / zero-criticals invent.
