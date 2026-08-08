# Stream B M1 — Platform Integrity

**Date:** 2026-08-08  
**Stream:** B (Platform Integrity) — SalesOS Completion Program  
**Charter:** [COMPLETION-PROGRAM.md](../COMPLETION-PROGRAM.md)  
**Board:** [PROGRAM-BOARD.md](./PROGRAM-BOARD.md)  
**Priors:** [REMEDIATION-STRUCTURAL.md](../enterprise-audit-board/history/EAB-2026-08-06-003/REMEDIATION-STRUCTURAL.md), [FINDINGS-RECHECK.md](../enterprise-audit-board/history/EAB-2026-08-06-003/FINDINGS-RECHECK.md)  
**Commit:** none  
**Evidence-based Production GO:** **not claimed**

---

## Mission result

Pushed DUP-01 / AIGOV-01 / DRIFT-01 / DUP-02 / FIT-01 toward Fixed where code-possible.  
**No invent Fixed** — all five remain **Partial** (honest narrowed where advanced).

---

## Before → after disposition

| ID | Board / EAB-003 prior | After Stream B M1 | Residual (why not Fixed) |
|----|----------------------|-------------------|--------------------------|
| **DUP-01** (CP-B-01) | Partial — HTTP SoT OK; engines remain | **Partial (narrowed)** | ≥3 BE engines retained; FE hybrid Platform history + Runtime accept; OpenAPI SoT descriptions + FF-DUP-01 remount guard only |
| **AIGOV-01** (CP-B-02) | Partial — flag False; generate/evaluate gated | **Partial (narrowed)** | Arabic detect/prompts + telemetry/log now gated; `/ai/generate|evaluate` OpenAPI-deprecated; multi-engine transparency + FE STUB remain |
| **DRIFT-01** (CP-B-03) | Partial — MetaData 18 / ceiling 18 | **Partial (held)** | Remeasure **18**; freeze honesty updated; P1 pgvector consolidate **deferred** (outside Stream B code lock this wave) |
| **DUP-02** (CP-B-04) | Partial — webhook prefix Fixed; search deprecated | **Partial (narrowed)** | Prompt dual-registry quarantine tags/honesty strengthened; no consolidate DEC |
| **FIT-01** (CP-B-05) | Partial — minimal subset | **Partial (narrowed / closer to Fixed)** | FF-07/AIGOV + FF-DUP-01 added; host script exit 0; **not** full FF catalog; remote GH Actions green **not validated** |

---

## Work performed (minimal-diff)

### DUP-01
- Platform router: OpenAPI summary/description on evaluate/batch/history; `SOT_ROLE = "alternate"`
- Platform `engine.py`: quarantine module docstring
- Runtime router: OpenAPI summary/description on all remounted DIE routes (active paths **not** OpenAPI-deprecated)
- `DECISION-API-SOT.md` + `QUARANTINE.md` Stream B notes
- Fitness **FF-DUP-01** light remount posture checks

### AIGOV-01
- `copilot.py`: gate `/copilot/arabic/detect`, `/copilot/arabic/prompts`, `POST /copilot/telemetry/log` with `require_ai_copilot_enabled`
- `ai.py`: OpenAPI `deprecated=True` on generate/evaluate; dual-registry note on list prompts
- FE `/decisions` honesty banner names multi-engine hybrid residual
- `AI_HONESTY.md` §8 updated
- Fitness FF-07/AIGOV greps for new gates
- **Did not** flip `feature_ai_copilot` (remains False)

### DRIFT-01
- Remeasure `MetaData(` = **18** (ceiling held)
- `METADATA-ISLAND-FREEZE.md` Completion Program honesty + P1 backlog pointer
- No island code consolidate this wave (pgvector P1 needs Director unlock)

### DUP-02
- Studio `prompt_library_router`: experimental dual-registry OpenAPI tag + meta.honesty
- Domain `/ai/prompts` OpenAPI dual-capability description
- `CAPABILITY-DUP-REGISTER.md` updated

### FIT-01
- Extended `fitness-ci-subset.sh` / `.ps1` with FF-07/AIGOV + FF-DUP-01
- Workflow job rename + honesty footer
- `FITNESS-CI-SUBSET-PLAN.md` updated

---

## Files changed

| Area | Paths |
|------|-------|
| Decision Platform | `salesos/backend/app/modules/decision/router.py`, `engine.py` |
| Decision Runtime | `salesos/backend/runtime/decision_runtime/router.py` |
| AIGOV | `salesos/backend/app/routers/copilot.py`, `salesos/backend/app/routers/ai.py` |
| FE honesty | `salesos/frontend/src/app/(dashboard)/decisions/page.tsx` |
| DUP-02 prompt | `salesos/backend/app/modules/tenant_studio/prompt_library_router.py` |
| Fitness | `salesos/scripts/fitness-ci-subset.sh`, `.ps1`, `.github/workflows/fitness-ci-subset.yml` |
| SoT / freeze / plan | `DECISION-API-SOT.md`, `CAPABILITY-DUP-REGISTER.md`, `METADATA-ISLAND-FREEZE.md`, `FITNESS-CI-SUBSET-PLAN.md`, `AI_HONESTY.md`, `QUARANTINE.md` |
| This report | `docs/audit/ga-engineering-audit/completion/STREAM-B-M1.md` |

**Not touched (locks):** `salesos/backend/app/main.py`, TenantList / security P0 middleware, `feature_ai_copilot` default, prod migrate.

---

## Validation

| Check | Result | Label |
|-------|--------|-------|
| Host `powershell -File salesos/scripts/fitness-ci-subset.ps1` | **exit 0** (FF-07/AIGOV, FF-DUP-01, FF-09/10/12) | **light validated** |
| MetaData count | **18** ≤ ceiling 18 | light validated |
| Full pytest / npm lint/build | **Not run** | — |
| Remote GitHub Actions fitness job | **Not validated** | — |
| Browser / Production GO | **Not claimed** | production no-go (engineering) |

---

## Blockers / next CODE-POSSIBLE (needs Director or DEC)

| Item | Blocker |
|------|---------|
| DUP-01 Fixed | Engine deletion / Center-only FE history — DEC + product UX |
| DRIFT ceiling ↓ | P1 `pgvector_migration.py` MetaData→table (Director unlock outside decision lock) |
| DUP-02 Fixed | Prompt registry consolidate DEC |
| FIT-01 Fixed | Recorded remote GH Actions green + broader FF catalog agreement |
| AIGOV Fixed | Multi-engine product transparency + human AI GA evidence |

---

## Parent return summary

| Field | Value |
|-------|-------|
| Dispositions | All five **Partial** (narrowed where advanced; DRIFT held) |
| Validation | **light validated** (fitness host exit 0) |
| Production GO | **not claimed** |
| Commit | **none** |

*Stream B M1 — Completion Program — evidence governs — no invent Fixed*
