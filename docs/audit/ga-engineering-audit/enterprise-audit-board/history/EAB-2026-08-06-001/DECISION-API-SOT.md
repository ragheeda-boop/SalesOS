# Decision API Source of Truth — EAB-2026-08-06-001

**Date:** 2026-08-06  
**Findings:** EAB-001-P0-DUP-01 (primary), EAB-001-P1-AIGOV-01 / EAB-001-P1-DUP-02 (partial)  
**Validation:** **light validated** (router Read + mount change; no pytest / Docker boot this wave)  
**Verdict:** Does **not** change Production GA **NO-GO**. Engines retained; HTTP collisions removed. No commit.

> **Completion Program Stream B M1 (2026-08-08):** OpenAPI operation summaries/descriptions
> strengthened on Platform + Runtime routers; Platform engine quarantine docstring;
> fitness **FF-DUP-01** light remount guard. Disposition remains **Partial (narrowed)** —
> ≥3 BE engines retained; FE hybrid history/accept residual documented in OpenAPI + UI banner.
> Results: [../../../completion/STREAM-B-M1.md](../../../completion/STREAM-B-M1.md).
>
> **EAB-2026-08-06-003 structural:** HTTP SoT remount still authoritative. Lab twin
> renamed to `@salesos/decision-platform-lab`. OpenAPI tags labeled SoT / alternate /
> remounted. Disposition remains **Partial (narrowed)** — engines not deleted.
> Board packaging: [../EAB-2026-08-06-003/REMEDIATION-STRUCTURAL.md](../EAB-2026-08-06-003/REMEDIATION-STRUCTURAL.md).
>
> **EAB-2026-08-06-002 post-verify:** HTTP SoT remount still authoritative. Disposition remains
> **Partial + residual** (engines not deleted). Non-decision capability dups moved to
> [../EAB-2026-08-06-002/CAPABILITY-DUP-REGISTER.md](../EAB-2026-08-06-002/CAPABILITY-DUP-REGISTER.md).
> Board packaging: [../EAB-2026-08-06-002/REMEDIATION-POST-VERIFY.md](../EAB-2026-08-06-002/REMEDIATION-POST-VERIFY.md).

---

## Canonical HTTP SoT (governed institutional decisions)

| Role | Module | Mount | Base path | Client guidance |
|------|--------|-------|-----------|-----------------|
| **Canonical SoT** | `domains.decision_center` | `prefix="/api/v1"` | `/api/v1/decisions*`, `/api/v1/decision-templates*` | Prefer for governed create/list/get/audit/feedback/templates (AGENTS.md / AI_HONESTY) |
| **Alternate capability** | `app.modules.decision` (Decision Platform) | `prefix=""` + router `prefix="/api/v1/decision"` | `/api/v1/decision/*` | Rule/scoring evaluate, batch, history, recommendations, rules, learning — **not** the Center ledger |
| **Runtime DIE (non-colliding)** | `runtime.decision_runtime` | `prefix="/api/v1/decision-runtime"` | `/api/v1/decision-runtime/...` | Company NBA evaluate / accept / execute / metrics — **deprecated former `/api/v1` mount** |

**Precedence rule:** For any client needing a durable, auditable decision record → **Decision Center**. Do not call Runtime under old `/api/v1/decisions*` paths (removed from that mount).

---

## Canonical paths (Center)

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/v1/decisions` | Create |
| GET | `/api/v1/decisions` | List (+ cursor) |
| GET | `/api/v1/decisions/{id}` | Get |
| GET | `/api/v1/decisions/{id}/audit` | Audit trail |
| POST/GET | `/api/v1/decisions/{id}/feedback` | Feedback |
| GET | `/api/v1/decisions/feedback/aggregate` | Aggregates |
| * | `/api/v1/decision-templates*` | Templates CRUD + seed |

## Platform paths (alternate; singular `decision`)

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/v1/decision/evaluate` | Platform evaluate (DecisionContext schema) |
| POST | `/api/v1/decision/batch` | Batch |
| GET | `/api/v1/decision/{id}/explain` | Explain |
| GET | `/api/v1/decision/history` | Platform history |
| GET | `/api/v1/decision/recommendations` | Recommendations |
| GET | `/api/v1/decision/scores` | Scores |
| GET | `/api/v1/decision/evidence` | Evidence |
| POST/GET | `/api/v1/decision/feedback*` | Platform feedback |
| GET/POST | `/api/v1/decision/rules` | Rules |
| GET | `/api/v1/decision/learning/*` | Learning |

## Runtime paths (remounted; former aliases deprecated)

| Method | New path | Deprecated alias (no longer mounted) |
|--------|----------|--------------------------------------|
| POST | `/api/v1/decision-runtime/decision/evaluate` | `/api/v1/decision/evaluate` (was Runtime; **Platform keeps** this path) |
| GET | `/api/v1/decision-runtime/decision/next-best-action` | `/api/v1/decision/next-best-action` |
| GET | `/api/v1/decision-runtime/decision/metrics` | `/api/v1/decision/metrics` |
| GET | `/api/v1/decision-runtime/decisions/history` | `/api/v1/decisions/history` |
| GET | `/api/v1/decision-runtime/decisions/{id}` | `/api/v1/decisions/{id}` (Center owns) |
| POST | `/api/v1/decision-runtime/decisions/{id}/accept` | `/api/v1/decisions/{id}/accept` |
| POST | `/api/v1/decision-runtime/decisions/{id}/execute` | `/api/v1/decisions/{id}/execute` |
| POST | `/api/v1/decision-runtime/decisions/{id}/feedback` | `/api/v1/decisions/{id}/feedback` (Center owns different schema) |
| GET | `/api/v1/decision-runtime/decisions/{id}/reasoning` | `/api/v1/decisions/{id}/reasoning` |

---

## Collisions — status after this change

| Former collision | Status |
|------------------|--------|
| Runtime vs Platform `POST /api/v1/decision/evaluate` | **Fixed** — Runtime remounted; Platform sole owner of that path |
| Runtime vs Center `GET/POST /api/v1/decisions/{id}*` | **Fixed** — Runtime under `/api/v1/decision-runtime` |
| Runtime `GET /api/v1/decisions/history` vs Center `{id}` | **Fixed** |
| Three BE engines still in codebase | **Residual (honest)** — not deleted; HTTP SoT documented |
| FE STUB vs lab twin | **Narrowed** — lab renamed `@salesos/decision-platform-lab`; FE STUB remains resolve target |

**Remaining collisions:** none on Decision HTTP mounts after remount (spot-check via routers.py). OpenAPI may still list three tags — expected.

**FE residual:** `/decisions` dashboard lists Platform history (`/api/v1/decision/history`) but accept/dismiss call Runtime under `/api/v1/decision-runtime/...` — cross-engine ID mismatch risk remains (pre-existing hybrid UI; not fixed this wave beyond path remount).

---

## FE package honesty (AIGOV-01 partial)

| Package path | Name | Role |
|--------------|------|------|
| `salesos/frontend/packages/platform/decision/` | `@salesos/decision-platform` (tsconfig path) | **STUB** — throws; do not market as live GA AI |
| `salesos/packages/platform/decision/` | `@salesos/decision-platform-lab` | Full twin / lab — **renamed** (EAB-003); not FE resolve target |

`feature_ai_copilot` remains **False**. Prefer Decision Center HTTP for product UI.

---

## P1-DUP-02 capability register

**Authoritative register (EAB-002):** [../EAB-2026-08-06-002/CAPABILITY-DUP-REGISTER.md](../EAB-2026-08-06-002/CAPABILITY-DUP-REGISTER.md)

Summary (still dual-capability / no remount):

| Capability | Routers | Mount | Who wins / notes |
|------------|---------|-------|------------------|
| Search (runtime) | `runtime.search_runtime.router` | `/api/v1` first | `GET /search`, `/search/suggest`, `/search/similar/{id}`, `/search/metrics`, `POST /search/ai` |
| Search (API/experimental) | `app.routers.search` | `/api/v1` second | `GET /search/analytics`, `/search/semantic`, `POST /search/similar` — **no path overlap**; dual *capability*, not route collision |
| Webhooks (subscriptions) | `app.modules.webhooks.router` | `/api/v1/webhooks` | Distinct from Stripe / employee webhook routers |
| Stripe webhook | `app.modules.billing.stripe_router` | `/api/v1` | Public signature-verified |
| Employee webhooks | `domains.employee.webhook_handler` | `/api/v1` | Employee domain |
| Prompt library | `tenant_studio.prompt_library_router` | `/api/v1` + `/studio/prompt-library` | Studio library; other prompt registries exist as code residual |

No remount for search/webhooks/prompts in EAB-001 Stream C or EAB-002 post-verify (paths already non-colliding for search).

---

## Finding status

| ID | Stream C | EAB-002 post-verify | Stream B M1 (2026-08-08) |
|----|----------|---------------------|--------------------------|
| **EAB-001-P0-DUP-01** | **partial** — HTTP SoT + remount; engines + FE twin residual | **Partial + residual** — SoT docs + Platform deprecation docstring; engines **not** deleted | **Partial (narrowed)** — OpenAPI SoT descriptions + FF-DUP-01; engines **not** deleted |
| **EAB-001-P1-AIGOV-01** | **partial** — SoT + FE package labels | **Partial + residual** — AI_HONESTY cross-links; twin name residual | See AI_HONESTY / STREAM-B-M1 (Arabic gated) |
| **EAB-001-P1-DUP-02** | **partial (doc only)** | **Partial + residual** — dedicated CAPABILITY-DUP-REGISTER; no code remount | Prompt dual-registry quarantine strengthened |

---

## Files changed (Stream C)

- `salesos/backend/app/boot/routers.py` — Runtime prefix `/api/v1/decision-runtime` + SoT comments
- `salesos/backend/runtime/decision_runtime/router.py` — docstring / deprecation note
- `salesos/backend/tests/e2e/test_critical_paths.py` — Runtime paths updated
- `salesos/frontend/src/app/(dashboard)/decisions/page.tsx` — accept/dismiss → decision-runtime
- This file + FINDINGS status partial
- FE/twin package.json + README notes (STUB vs full)

*Stream C — light validated — production no-go unchanged — no commit*
