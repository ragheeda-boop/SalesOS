# Fitness CI Subset Plan — Partial / implemented-minimal (narrowed)

**Date:** 2026-08-08 (Completion Program Stream B M1 + W2)  
**Finding:** EAB-001-P2-FIT-01  
**Disposition:** **Partial (narrowed / closer to Fixed)** — light FF-07/AIGOV (+ OpenAPI deprecate) + FF-DUP-01 + FF-DUP-02 + FF-09/10/12 (+ light FF-14) at **repo-root** workflow; **not** full FF catalog; **not** Audit Maturity L3; remote GH Actions green **not validated** this session  
**Validation:** host `fitness-ci-subset.ps1` **exit 0** (2026-08-08 Stream B + W2)

---

## Catalog reference

[enterprise-audit-board/05-FITNESS-CATALOG.md](./enterprise-audit-board/05-FITNESS-CATALOG.md) defines FF-01…FF-14.  
Minimal subset **exists** and is discoverable — do not invent full G-06 = 100%.

---

## Implemented CI subset

| ID | Check intent | Implementation |
|----|--------------|----------------|
| **FF-07** | `feature_ai_copilot` default False; FE decision STUB honesty | Grep `config.py` + STUB markers + `package.json` stub version + lab twin `@salesos/decision-platform-lab` + `AI_HONESTY.md` |
| **FF-07/AIGOV (light)** | Arabic detect/prompts + telemetry/log gated; generate/evaluate OpenAPI-deprecated | Grep `copilot.py` Depends + `ai.py` `deprecated=True` near `/ai/generate|/ai/evaluate` |
| **FF-14 (light)** | No product path calling stub evaluate/explain | Grep `decisionEngine.(evaluate|explain)` under `salesos/frontend/src` must be empty |
| **FF-DUP-01 (light)** | Decision HTTP SoT remount held | `DECISION-API-SOT.md` present; `prefix="/api/v1/decision-runtime"`; Center SoT tag; tight include check |
| **FF-DUP-02 (light)** | Search experimental + Studio prompt dual-registry quarantine held | `search.py` ≥3 `deprecated=True`; `prompt_library_router.py` tag `prompt dual-registry` |
| **FF-09** | Dual compose / orphan `MetaData()` flagged | Compose SoT + freeze docs present; `MetaData()` count ≤ ceiling **17** |
| **FF-10** | Middleware needing `db_session_factory` fails closed if unset | Grep posture: factory wire + `503` in entitlement/suspended/api_keys middleware |
| **FF-12** | Superseded GO docs must not be cited as authority | `SUPERSEDED` banner on `GO_NO_GO_DECISION.md` + `GA_CHECKLIST.md` |

Out of first subset (later): FF-01…06, FF-08, FF-11, FF-13, full FF-14 product-path matrix.

---

## Artifacts

| Path | Role |
|------|------|
| [`salesos/scripts/fitness-ci-subset.sh`](../../salesos/scripts/fitness-ci-subset.sh) | Executable light checks (CI / Unix) |
| [`salesos/scripts/fitness-ci-subset.ps1`](../../salesos/scripts/fitness-ci-subset.ps1) | Windows host twin |
| [`.github/workflows/fitness-ci-subset.yml`](../../.github/workflows/fitness-ci-subset.yml) | Workflow job (push/PR/workflow_dispatch) — **repo root = discoverable**; honesty footer step |
| [METADATA-ISLAND-FREEZE.md](./METADATA-ISLAND-FREEZE.md) | FF-09 ceiling / allowlist (ceiling **18**) |
| [EAB-003 REMEDIATION-STRUCTURAL](./enterprise-audit-board/history/EAB-2026-08-06-003/REMEDIATION-STRUCTURAL.md) | Prior disposition packaging |
| [completion/STREAM-B-M1.md](./completion/STREAM-B-M1.md) | Stream B M1 results |

Local (when approved):

```bash
bash salesos/scripts/fitness-ci-subset.sh
# or on Windows:
powershell -File salesos/scripts/fitness-ci-subset.ps1
```

---

## Approval / honesty gates

| Step | Status |
|------|--------|
| User mandate to wire / extend minimal subset | **Granted** (EAB program / Completion Program Stream B) |
| Full pytest / npm suites in this workflow | **Out of scope** (low-load) |
| Claim Audit Maturity L3 / G-06 100% | **Forbidden** until broader catalog green with recorded evidence |
| Remote GH Actions green | **Not validated** this session (host script only) |
| Claim FIT-01 Fixed | **Forbidden** until remote green recorded + broader FF coverage agreed |

---

## Related

- EAB FINDINGS `EAB-001-P2-FIT-01`
- [COMPOSE-SOURCE-OF-TRUTH.md](../ops/COMPOSE-SOURCE-OF-TRUTH.md) (FF-09 input)
- [AI_HONESTY.md](./AI_HONESTY.md) (FF-07)
- [DECISION-API-SOT.md](./enterprise-audit-board/history/EAB-2026-08-06-001/DECISION-API-SOT.md) (FF-DUP-01)
