# AI Feature-Flag Reconciliation — PO Decision Memo

**Date:** 2026-09-12  
**Agent:** A2 — AI Feature-Flag Reconciliation  
**Workspace:** `D:\AISalesOS`  
**Status:** INVENTORY + PREPARED CORRECTION — **not applied**  
**Classification:** honesty split-brain; production remains **NO-GO**  
**This file is the only file written this session.**

---

## 0. PO decision (read this first)

**RECOMMENDATION: Option B — revert `Settings.feature_ai_copilot` default to `False`.**

Do **not** apply either option until PO signs below. This memo prepares both patches.

| | Option A | Option B (recommended) |
|--|----------|------------------------|
| Code default | Keep `True` | Revert to `False` |
| Honesty / SoT docs | Rewrite to match True | Already match False |
| Tests / harnesses | Keep True asserts; rewrite soak + FF-07 + pentest marker | Flip 12 backend test files (17 asserts) |
| Production risk | Default-on copilot mutate path unless env overrides | Fail-closed default; env can still enable in lab |
| Effort | Large honesty rewrite across living docs + FE strings + gates | Small: `config.py` + 12 tests + comment/name hygiene |

**PO sign-off (human):**

| Field | Value |
|-------|-------|
| Decision | ☐ A — keep True / update honesty  ☐ B — revert False / flip tests  ☐ Defer |
| Signed by | |
| Date | |
| Notes | |

---

## 1. Evidence labels used below

| Label | Meaning |
|-------|---------|
| **FACT** | Observed in repo on 2026-09-12 (read/grep only; no suite run) |
| **INFERENCE** | Reasonable conclusion from those facts |
| **RECOMMENDATION** | What PO should choose, and why |

Validation of this memo: **light validated** (grep + file reads). Pytest / npm / flag flip: **not run / not applied**.

---

## 2. What is actually true today

### 2.1 Authority conflict (the split-brain)

| Source | Claim | Authority class |
|--------|-------|-----------------|
| `salesos/backend/app/config.py` L162 | `feature_ai_copilot: bool = True` | **Runtime Settings default** (Pydantic; env `FEATURE_AI_COPILOT` overrides) |
| `docs/audit/ga-engineering-audit/AI_HONESTY.md` | Default **`False`**; “Do **not** flip `feature_ai_copilot` to True” | **Standing AI honesty SoT** |
| `docs/audit/ga-engineering-audit/PHASE3_GATE_EVIDENCE_PACK.md` §3.5 | Flag flipped False → True (2026-08-19); 12 harnesses + 12 tests | Phase 3 **code-gate evidence** |
| `docs/audit/ga-engineering-audit/SALESOS_MASTER_CLOSURE_SEQUENCE.md` | Keep False until Phase 3 AI Gate evidence-closed | Product-closure order (locked 2026-08-17) |
| `docs/audit/ga-engineering-audit/enterprise-audit-board/07-SCORING-MODEL.md` | If default is not False → AIGOV cap **≤29** + open P0 | EAB scoring hard cap |
| `AGENTS.md` §6 | Default False | Agent standing rule (stale vs config) |
| `AGENTS.md` §15 | Flag flip COMPLETE → True | Session history of Phase 3 |
| `.cursor/rules/essentials.mdc` | Keep default **False** unless evidence-validated | Workspace rule |
| Prod/staging templates + k8s | `FEATURE_AI_COPILOT=false` | Deploy SoT for non-lab |
| `docs/reports/PROVIDER-EVAL-2026-08-23.md` | Flag may be True for Phase 3 evidence; **does not** overturn provider NO-GO | Provider honesty |

**FACT:** The Phase 3 pack flipped the *code default* to True and updated 12 tests to assert True. `AI_HONESTY.md`, soak/FF-07 gates, production templates, EAB scoring, and most honesty strings were **not** updated.

**FACT:** Production GA remains **NO-GO**. Provider path remains **DEV-only** (AI Horde / FreeLLMAPI local). FE `@salesos` Decision package remains a **STUB**.

**INFERENCE:** Phase 3 closed a *code-completeness* gate, not a *production AI* gate. The flip was never reconciled with the honesty SoT.

### 2.2 Runtime behavior (what a process actually does)

**FACT — product gates honor Settings (currently default True):**

- `app/routers/copilot.py` `require_ai_copilot_enabled()` — 403 only when flag is False. Product mutate/detect paths are **open** at default True.
- `app/routers/ai.py` same gate on `POST /ai/generate` and `POST /ai/evaluate`.
- `GET /copilot/status` returns `{ feature_ai_copilot: <settings>, classification, ga_ready: false }`. `ga_ready` stays False even when the flag is True.

**FACT — two runtime JSON surfaces hardcode False (inconsistent with Settings):**

```60:60:salesos/backend/app/modules/chaos_resilience/router.py
        "feature_ai_copilot": False,
```

```81:81:salesos/backend/app/modules/tenant_studio/ai_policies_engine.py
        "feature_ai_copilot": False,
```

**FACT — admin in-memory seed is a second flag, still False:**

```234:240:salesos/backend/app/modules/admin/repositories.py
            # Align with Settings.feature_ai_copilot=False (GA honesty Wave 6).
            FeatureFlag(
                id=uuid.uuid4(),
                key="ai_copilot",
                ...
                enabled=False,
```

**FACT — deploy/env layer still pins False** (except local preview `.env`):

| Location | Value |
|----------|-------|
| `salesos/.env.production.template` | `FEATURE_AI_COPILOT=false` |
| `salesos/.env.production` | `FEATURE_AI_COPILOT=false` |
| `salesos/.env.staging*` | `FEATURE_AI_COPILOT=false` |
| `salesos/backend/.env.production.template` | `FEATURE_AI_COPILOT=false` |
| `salesos/infra/k8s/configmap.yaml` | `FEATURE_AI_COPILOT: "false"` |
| `salesos/infra/staging/docker-compose.staging-virtual.yml` | `FEATURE_AI_COPILOT: "false"` |
| `salesos/scripts/railway-setup.sh` / `generate-secrets.sh` | `false` |
| `salesos/.env` (local, typically gitignored) | `FEATURE_AI_COPILOT=true` (lab preview per `AI-LIVE-PREVIEW-DECISION-2026-08-22.md`) |

**FACT — FE has a dual gate:** `useAiCopilotEnabled` requires `NEXT_PUBLIC_FEATURE_AI_COPILOT=true` **and** `/copilot/status` `feature_ai_copilot === true`. Dockerfile ARG defaults empty (disabled). i18n copy still describes the disabled state.

**FACT — honesty strings in live routers still say “remains False”** while the same handlers echo `settings.feature_ai_copilot` (True by default). Example: `ai_policies_router.py`, `outreach_router.py`, `website_intelligence_router.py`, `prompt_library_router.py`.

**INFERENCE:** A backend started with no env override enables product copilot/AI mutate endpoints. Staging/prod templates currently override that. Local compose without the override does not. Honesty copy and two meta payloads will **lie** about the flag value.

### 2.3 Tests vs names

**FACT:** 12 backend unit files (17 assertions) assert `is True`. Most function names still say `remains_false` / `stays_false`. That is the Phase 3 mechanical flip; names were not renamed.

**FACT:** Frontend API tests **mock** `feature_ai_copilot: false` — they do not read `Settings`. Frontend honesty tests assert the string `feature_ai_copilot remains False`.

**FACT:** Living gates still require the *code* default to be False:

- `salesos/scripts/fitness-ci-subset.sh` / `.ps1` FF-07 greps `feature_ai_copilot:\s*bool\s*=\s*False`
- `salesos/scripts/wave11-soak-gate.py` FAILs if Settings prints True
- `salesos/scripts/story_14_04_inrepo_pentest_pack.py` requires marker `feature_ai_copilot: bool = False`

---

## 3. Inventory method and counts

Searched (read-only): `feature_ai_copilot`, `FEATURE_AI_COPILOT`, `NEXT_PUBLIC_FEATURE_AI_COPILOT`, `ai_copilot` (admin seed alias).

Excluded from unique counts: `node_modules`, `.git`, `.next`, `dist`, `__pycache__`, `project-audit/`, and the duplicate tree `docs/docs/**` (mirror of `docs/`).

| Metric | Count |
|--------|------:|
| Unique files mentioning `feature_ai_copilot` | **269** |
| Additional alias-only files (`FEATURE_AI_COPILOT` / `NEXT_PUBLIC_FEATURE_AI_COPILOT` only) | **~18** |
| Cursor rule files | **2** |
| **Unique inventory (approx.)** | **~289** |
| Backend tests asserting Settings `True` | **12 files / 17 asserts** |
| Frontend tests mentioning the flag | **13** |
| Runtime paths that **hardcode** False (ignore Settings) | **2** |
| Deploy/env pins to False | **≥9** |

Kind breakdown of the 269 `feature_ai_copilot` files (approx.):

| Kind | ~Files |
|------|-------:|
| runtime code | 40 |
| comment-only / honesty string in runtime | (included in the 40; most files mix both) |
| test (backend + frontend) | 25 |
| harness / CI / deploy script | 10 |
| frontend (app/lib/features, excl. tests) | ~35 |
| document / report / crumb / audit | ~155 |
| AGENTS.md / rules (in 269 + 2 extra) | 3 |

---

## 4. Complete reference map

Columns: **path · kind · current value/claim · authority**.  
“Echoes Settings” = JSON/field returns `settings.feature_ai_copilot` (True unless env overrides).  
“Honesty False” = comment or user-facing string still claims False.

### 4.1 Runtime code (Settings + gates)

| Path | Kind | Current value / claim | Authority |
|------|------|----------------------|-----------|
| `salesos/backend/app/config.py` | runtime | **Default `True`** (comment: Phase 3 flip 2026-08-19) | **Settings SoT** |
| `salesos/backend/app/routers/copilot.py` | runtime | Gates on Settings; disabled copy says `=False`; `ga_ready` always False | Product copilot gate |
| `salesos/backend/app/routers/ai.py` | runtime | Same gate on generate/evaluate | Product AI gate |
| `salesos/backend/app/modules/admin/ai_model_tiers_router.py` | runtime | Echoes Settings; honesty: gated by Settings / Phase 3 | Studio catalog |
| `salesos/backend/app/modules/admin/ai_model_tiers.py` | comment | “Does not enable feature_ai_copilot” | Entitlement ladder |
| `salesos/backend/app/modules/admin/entitlements.py` | comment | “stays False by default” | Stale vs config |
| `salesos/backend/app/modules/admin/repositories.py` | runtime | Seed `ai_copilot` **enabled=False**; comment says Settings=False | **Admin flag ≠ Settings** |
| `salesos/backend/app/modules/tenant_studio/ai_memory_router.py` | runtime | Echoes Settings | Studio |
| `salesos/backend/app/modules/tenant_studio/ai_memory.py` | runtime + comment | Echoes Settings; “remains False” | Stale comment |
| `salesos/backend/app/modules/tenant_studio/ai_memory_store.py` | runtime | Echoes Settings | Studio |
| `salesos/backend/app/modules/tenant_studio/ai_policies_router.py` | runtime + honesty | Echoes Settings; honesty “remains False” | **Inconsistent** |
| `salesos/backend/app/modules/tenant_studio/ai_policies_engine.py` | runtime | **Hardcodes `False`**; finding `…_copilot_false` | **Inconsistent** |
| `salesos/backend/app/modules/tenant_studio/ai_policies.py` | comment | “remains False”; AI-GR-005 text | Stale |
| `salesos/backend/app/modules/tenant_studio/prompt_library_router.py` | runtime + honesty | Echoes Settings; honesty “remains False” | **Inconsistent** |
| `salesos/backend/app/modules/tenant_studio/prompt_library.py` | comment | “remains False” | Stale |
| `salesos/backend/app/modules/gtm/outreach_router.py` | runtime + honesty | Echoes Settings; honesty “remains False” | **Inconsistent** |
| `salesos/backend/app/modules/gtm/outreach_engine.py` | runtime + comment | Warning string `feature_ai_copilot=False` (hardcoded) | **Inconsistent** |
| `salesos/backend/app/modules/gtm/outreach.py` | comment | “remains False” | Stale |
| `salesos/backend/app/modules/gtm/website_intelligence_router.py` | runtime + honesty | Echoes Settings; honesty “remains False” | **Inconsistent** |
| `salesos/backend/app/modules/gtm/website_intelligence_engine.py` | comment | “remains False” | Stale |
| `salesos/backend/app/modules/gtm/website_intelligence.py` | comment | “remains False” | Stale |
| `salesos/backend/app/modules/marketplace_listings/router.py` | runtime | Echoes Settings | Marketplace |
| `salesos/backend/app/modules/load_slo/router.py` | runtime + comment | Echoes Settings; header “False” | Mixed |
| `salesos/backend/app/modules/load_slo/harness.py` | harness | Interpolates Settings | Non-prod |
| `salesos/backend/app/modules/dr_drill/router.py` | runtime + comment | Echoes Settings; header “False” | Mixed |
| `salesos/backend/app/modules/dr_drill/harness.py` | harness | Interpolates Settings | Non-prod |
| `salesos/backend/app/modules/chaos_resilience/router.py` | runtime | **Hardcodes False** in `/chaos/meta` | **Inconsistent** |
| `salesos/backend/app/modules/chaos_resilience/harness.py` | harness | Interpolates Settings | Non-prod |
| `salesos/backend/app/modules/chaos_resilience/handlers.py` | runtime + comment | Echoes Settings; “remains False” | Mixed |
| `salesos/backend/app/modules/chaos_resilience/ai_failover.py` | harness | Echoes Settings | Non-prod |
| `salesos/backend/app/modules/chaos_resilience/ai_failover_router.py` | runtime + comment | Echoes Settings; header “False” | Mixed |
| `salesos/backend/app/modules/chaos_resilience/ai_failover_harness.py` | harness | Echoes Settings | Non-prod |
| `salesos/backend/app/modules/chaos_resilience/llm_regression.py` | harness | Echoes Settings | Non-prod |
| `salesos/backend/app/modules/chaos_resilience/llm_regression_router.py` | runtime + comment | Echoes Settings; header “False” | Mixed |
| `salesos/backend/app/modules/chaos_resilience/llm_regression_harness.py` | harness | Echoes Settings | Non-prod |
| `salesos/backend/runtime/capability_framework/cap_to_kebab_join.yaml` | config | “default False; no decorator registration” | Stale vs config |

### 4.2 Backend tests (assert Settings True)

These are the “~20 files that assert True” — **12 files, 17 asserts**. Names still say False.

| Path | Kind | Current claim | Authority |
|------|------|---------------|-----------|
| `salesos/backend/tests/unit/test_story_11_07_website_intelligence.py` | test | `test_feature_ai_copilot_stays_false` asserts **True** | Phase 3 flip |
| `salesos/backend/tests/unit/test_story_11_08_ai_outreach.py` | test | same | Phase 3 flip |
| `salesos/backend/tests/unit/test_story_12_01_prompt_library.py` | test | same | Phase 3 flip |
| `salesos/backend/tests/unit/test_story_12_02_ai_policies.py` | test | same | Phase 3 flip |
| `salesos/backend/tests/unit/test_story_12_03_ai_memory.py` | test | same | Phase 3 flip |
| `salesos/backend/tests/unit/test_story_12_04_ai_model_tiers.py` | test | `test_copilot_flag_unchanged_false` asserts **True** | Phase 3 flip |
| `salesos/backend/tests/unit/test_story_14_01_load_slo.py` | test | `remains_false` asserts **True** | Phase 3 flip |
| `salesos/backend/tests/unit/test_story_14_02_chaos_resilience.py` | test | Settings True + `out.detail[…]` True | Phase 3 flip |
| `salesos/backend/tests/unit/test_story_14_03_dr_drill.py` | test | `remains_false` asserts **True** | Phase 3 flip |
| `salesos/backend/tests/unit/test_story_14_06_ai_failover.py` | test | Settings True + `out.feature_ai_copilot` True | Phase 3 flip |
| `salesos/backend/tests/unit/test_story_14_07_llm_regression.py` | test | Settings True + out True + meta True (3) | Phase 3 flip |
| `salesos/backend/tests/unit/intelligence/providers/test_openai_base_url.py` | test | comment “remains False”; 2× assert **True** | Phase 3 flip |

No other `salesos/backend/tests/**` files mention `feature_ai_copilot`.

### 4.3 Frontend (runtime + honesty + tests)

| Path | Kind | Current value / claim | Authority |
|------|------|----------------------|-----------|
| `salesos/frontend/src/lib/hooks/useAiCopilotEnabled.ts` | frontend | Dual gate: env `=== "true"` **and** status `=== true` | FE product gate |
| `salesos/frontend/src/app/(dashboard)/layout.tsx` | comment | Documents dual gate | — |
| `salesos/frontend/Dockerfile` | harness | `ARG NEXT_PUBLIC_FEATURE_AI_COPILOT=` (empty = off) | Build-time FE |
| `salesos/frontend/src/lib/i18n/en.json` | frontend | `copilot.disabled_ga` describes `=False` | Copy |
| `salesos/frontend/src/lib/i18n/ar.json` | frontend | Same | Copy |
| `salesos/frontend/src/lib/commands.ts` | comment | “feature_ai_copilot False” | Stale vs Settings |
| `salesos/frontend/src/lib/auth/csrf.ts` | comment | “unchanged” | Neutral |
| `salesos/frontend/src/lib/auth/authSessionHonesty.ts` | honesty | “False”; “Do not enable” | Honesty |
| `salesos/frontend/src/components/v3/V3AiPopup.tsx` | frontend | “Copilot stays gated” | Honesty UI |
| `salesos/frontend/src/app/(dashboard)/studio/{prompt-library,ai-policies,ai-model-tiers,ai-memory}/page.tsx` | comment | “False” | Stale |
| `salesos/frontend/src/app/(dashboard)/gtm/{outreach,website-intelligence}/page.tsx` | comment | “False” | Stale |
| `salesos/frontend/src/features/tenant-studio/{AiPolicies,AiMemory,AiModelTiers,PromptLibrary}Studio.tsx` | frontend | Renders `meta.feature_ai_copilot`; comments say False | Mixed |
| `salesos/frontend/src/features/tenant-studio/{aiPolicies,aiMemory,aiModelTiers,promptLibrary}Honesty.ts` | honesty | “remains False” | **Living FE honesty** |
| `salesos/frontend/src/features/gtm/{Outreach,WebsiteIntelligence}Panel.tsx` | frontend | Renders meta; comments say False | Mixed |
| `salesos/frontend/src/features/gtm/{outreach,websiteIntelligence}Honesty.ts` | honesty | “remains False” | Living FE honesty |
| `salesos/frontend/src/features/marketplace-listings/marketplaceListingsHonesty.ts` | honesty | “enabling feature_ai_copilot” (forbidden list) | Honesty |
| `salesos/frontend/src/lib/api/{aiMemoryStudio,aiModelTiersStudio,aiPoliciesStudio,promptLibrary,outreach,websiteIntelligence,marketplaceListings}.ts` | frontend | Types + comments “remains False” | Client types |
| `salesos/frontend/src/lib/api/__tests__/{aiMemory,aiModelTiers,aiPolicies}Studio.test.ts` | test | **Mocks false**; asserts false | Fixture, not Settings |
| `salesos/frontend/src/lib/api/__tests__/{promptLibrary,outreach,websiteIntelligence,marketplaceListings}.test.ts` | test | **Mocks false** | Fixture |
| `salesos/frontend/src/features/tenant-studio/__tests__/{aiPolicies,aiMemory}Honesty.test.ts` | test | Match `/remains False/` | Coupled to honesty strings |
| `salesos/frontend/src/features/tenant-studio/__tests__/{promptLibrary,aiModelTiers}Honesty.test.ts` | test | Match `/feature_ai_copilot/` | Looser |
| `salesos/frontend/src/features/gtm/__tests__/{outreach,websiteIntelligence}Honesty.test.ts` | test | Match `/feature_ai_copilot/` | Looser |

### 4.4 Harness / CI / deploy (living gates)

| Path | Kind | Current claim | Authority |
|------|------|---------------|-----------|
| `salesos/scripts/fitness-ci-subset.sh` | harness | **FAIL** unless config default False | FF-07 |
| `salesos/scripts/fitness-ci-subset.ps1` | harness | Same | FF-07 |
| `salesos/scripts/wave11-soak-gate.py` | harness | **FAIL** if Settings True | Soak honesty |
| `salesos/scripts/story_14_04_inrepo_pentest_pack.py` | harness | Requires `feature_ai_copilot: bool = False` in config.py | Pentest pack |
| `salesos/scripts/il2a_prod_bounded_soak_local.py` | harness | `feature_ai_copilot_flipped: False` (did-not-flip claim) | Historical probe |
| `salesos/scripts/railway-setup.sh` | harness | Sets `FEATURE_AI_COPILOT=false` | Deploy |
| `salesos/scripts/generate-secrets.sh` | harness | `FEATURE_AI_COPILOT:false` | Deploy |
| `salesos/docker-compose.yml` | comment | “feature_ai_copilot stays False” (freellmapi profile) | Compose honesty |
| `salesos/infra/k8s/configmap.yaml` | harness | `"false"` | K8s |
| `salesos/infra/staging/docker-compose.staging-virtual.yml` | harness | `"false"` | Staging |

### 4.5 Env aliases (close names)

| Path | Kind | Current value | Authority |
|------|------|---------------|-----------|
| `FEATURE_AI_COPILOT` | env alias | Maps to Settings field | Pydantic Settings |
| `NEXT_PUBLIC_FEATURE_AI_COPILOT` | env alias | FE build/runtime dual gate | Next.js |
| Admin key `ai_copilot` | alias | In-memory FeatureFlag, seeded False | Not Settings |

### 4.6 Rules / agent standing text

| Path | Kind | Current claim | Authority |
|------|------|---------------|-----------|
| `AGENTS.md` §6 | document | Default **False** | Stale vs config |
| `AGENTS.md` §15 / §32 / header | document | Flip COMPLETE True; soak FAIL on True | Session history |
| `.cursor/rules/essentials.mdc` | document | Keep default **False** | Workspace rule |
| `.cursor/rules/salesos-master-gate-sequence.mdc` | document | False until Phase 3 Gate | Workspace rule |

### 4.7 Living SoT documents (must stay consistent with the chosen option)

| Path | Kind | Current claim | Authority |
|------|------|---------------|-----------|
| `docs/audit/ga-engineering-audit/AI_HONESTY.md` | document | **False**; do not flip True | **Honesty SoT** |
| `docs/audit/ga-engineering-audit/PHASE3_GATE_EVIDENCE_PACK.md` | document | Flip → **True** complete | Phase 3 evidence |
| `docs/audit/ga-engineering-audit/SALESOS_MASTER_CLOSURE_SEQUENCE.md` | document | False until Phase 3 evidence-closed | Closure order |
| `docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md` | document | False until Phase 3 | Plan |
| `docs/audit/ga-engineering-audit/FINAL_GO_NOGO_ASSESSMENT.md` | document | Flipped to **True** | Assessment (code) |
| `docs/audit/ga-engineering-audit/FITNESS-CI-SUBSET-PLAN.md` | document | FF-07 default False | Fitness |
| `docs/audit/ga-engineering-audit/enterprise-audit-board/{01-CHARTER,02-METHODOLOGY,04-EVIDENCE-STANDARD,05-FITNESS-CATALOG,07-SCORING-MODEL}.md` | document | Default **False**; AIGOV cap if not | EAB |
| `docs/audit/ga-engineering-audit/runbooks/{staging-soak,go-live-checklist,deploy-rollback,ops01-human-execution-pack}.md` | document | Expect False | Ops |
| `docs/ops/{AI_COPILOT_ACTIVATION,GO_LIVE_RUNBOOK,HYPERCARE_RUNBOOK}.md` | document | Default False; activation checks status true | Ops |
| `docs/reports/PROVIDER-EVAL-2026-08-23.md` | document | True in repo ≠ production GO | Provider |
| `docs/reports/OPS-EXECUTION-RUNBOOK-2026-08-24.md` | document | Soak FAIL: flag True vs honesty False | Observed split |
| `docs/current-state/BASELINE_FREEZE.md` / `BASELINE_VALIDATION.md` | document | Flipped / verified **True** | Post-Phase-3 baseline |
| `docs/adr/ADR-LLM-PROVIDER-SELECTION.md` | document | Must stay False in production | ADR |
| `docs/compliance/soc2-type-i/{README,01,02,04,05}*.md` | document | Default False | Compliance |
| `salesos/docs/pentest/{PENTEST_BRIEF,THREAT_MODEL,INTERNAL_TEST_PLAN,VENDOR_HANDOFF_CHECKLIST}.md` | document | Default False; Board to enable | Pentest |

### 4.8 Historical / snapshot documents (do not rewrite as if they were wrong on their date)

These correctly described **False** (or “not flipped”) as of their freeze date (mostly 2026-07-22 … 2026-08-13), or recorded the Phase 3 True flip later. **Option A/B should not mass-edit history.** Add a dated addendum only if PO wants a pointer.

Complete unique paths (excluding `docs/docs/` mirrors):

**Reports:** `docs/reports/{PROGRAM-STATUS-2026-08-12,PROGRAM-STATUS-2026-08-13,P1-CLOSURES-2026-08-12,P1-CLOSURES-2026-08-13,OPS01-DR-GATE-2026-08-12,IL-2B2-LEASE-HARDENING,IL-2A-HTTP-PRODUCTION-GATE,IL-2A-EVALUATE-HTTP-HANG-PROBE,HUMAN-SECRET-ROTATION-CHECKLIST,FREELLMAPI-SALESOS-ASSESSMENT-2026-08-13,FREELLMAPI-E2E-EVIDENCE-2026-08-22,FREELLMAPI-DEPLOY-LOOP-EVIDENCE-2026-08-22,A09-BOUNDED-PROD-IL2A-SOAK-2026-08-12,AI-LIVE-PREVIEW-DECISION-2026-08-22,REMAINING_GAPS}.md`

**Program crumbs / boards:** `docs/program/{DECISION_LOG,PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB,PHASE1_FE_INTEGRATION_HUB_INVENTORY,PHASE1_FE_S11_07_WEBSITE_INTELLIGENCE_CRUMB,PHASE1_FE_S11_08_AI_OUTREACH_CRUMB,PHASE1_FE_S12_01_PROMPT_LIBRARY_CRUMB,PHASE1_FE_S12_02_AI_POLICIES_CRUMB,PHASE1_FE_S12_03_AI_MEMORY_CRUMB,PHASE1_FE_S12_04_AI_MODEL_TIERS_CRUMB,PHASE1_FE_S14_04_05_CSRF_AUTH_SURFACE_CRUMB,PHASE1_FE_SEC_02_DEVOPS_FLAGS_ON_HANDOFF,PHASE1_FE_SEC_02_FLAGS_ON_FIELD_CHECKLIST,PHASE1_FE_TENANT_SURFACE_INVENTORY,PHASE1_FE_VALIDATION_CRUMB,PHASE1_SECURITY_14_04_14_05_DEVOPS_EVIDENCE_PACK,PHASE1_SPRINT25_QA_REGRESSION_CRUMB,PHASE1_STORY_11_07_WEBSITE_INTELLIGENCE_CRUMB,PHASE1_STORY_11_08_AI_OUTREACH_CRUMB,PHASE1_STORY_12_01_PROMPT_LIBRARY_CRUMB,PHASE1_STORY_12_02_AI_POLICIES_CRUMB,PHASE1_STORY_12_03_AI_MEMORY_CRUMB,PHASE1_STORY_12_04_AI_MODEL_TIERS_CRUMB,PHASE1_STORY_13_01_MARKETPLACE_LISTING_CRUMB,PHASE1_STORY_13_02_CERTIFICATION_PIPELINE_CRUMB,PHASE1_STORY_13_04_PUBLISH_PACK_CRUMB,PHASE1_STORY_14_01_LOAD_SLO_CRUMB,PHASE1_STORY_14_02_CHAOS_RESILIENCE_CRUMB,PHASE1_STORY_14_03_DR_DRILL_CRUMB,PHASE1_STORY_14_04_05_BE_SECURITY_SUPPORT_CRUMB,PHASE1_STORY_14_04_PENTEST_CRUMB,PHASE1_STORY_14_05_SOC2_EVIDENCE_CRUMB,PHASE1_STORY_14_06_AI_FAILOVER_CRUMB,PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB,PHASE1_VALIDATION_STREAM_CRUMB,POST_PHASE0_PARALLEL_EXECUTION_PLAN,PRODUCTION_READINESS_CHECKLIST,SPRINT_05_DELIVERY_BOARD,evidence/story-14-04/README}.md` plus `docs/program/SPRINT_PLAN/{Sprint-18,Sprint-20,Sprint-24,Sprint-25}.md` and `docs/program/decisions/DEC-156-METADATA-BASE-MERGE-RESIDUAL.md`

**Audit / EAB history:** `docs/audit/ga-engineering-audit/{APPENDIX-C-FINDINGS-REGISTER,BROWSER_QA_REVALIDATION_2026-08-19,DEC-093-OWNER-LOGIN-FOLLOWUP-CLOSED,EXEC-ARCHITECTURE-PRODUCT-REVIEW-2026-07-30,PAGE_MAP_SALESOS,PROGRESS-REAUDIT-2026-07-29,PROGRESS-WAVE6-7-AI-GATE,PROGRESS-WAVE6-7-DOCS,PROGRESS-WAVE11-SOAK,PROGRESS-WAVE11-SOAK-48H,PROGRESS-WAVE12-PROD-MIGRATE-PREP,PROGRESS-WAVE12-STAGING-UNBLOCK,PROGRESS-WAVE12-TABLETOP,PROGRESS-WAVE13-FULL-UI-CRAWL,PROGRESS-WAVE13-UI-SMOKE,PROGRESS-WAVE14-GO-LIVE,QUARANTINE,SIGN_HERE,completion/STREAM-B-M1,completion/STREAM-B-W2}.md`; EAB history under `enterprise-audit-board/history/EAB-2026-08-06-{001,002,003}/`; A09 staging-parity evidence pack under `completion/evidence/wave-20260808-2/staging-parity/`; `docs/audit/{star-audit/*,production-gap-closure/*,final-release-board/*,final-production-decision/*,evidence-review/*,legacy-reports/*,PAT_REPORT_FINAL,PRODUCTION_VALIDATION_REPORT,10-devops-architecture}.md`

**Other:** `docs/adr/0104-agent-runtime-deferred.md`, `docs/ai/LLM_PROVIDER_QUALIFICATION.md`, `docs/design/salesos-v3/{ai/ai-experience,delivery/legacy-migration,delivery/DESIGN_REVIEW_BRIEF}.md`, `docs/releases/v5.1.0-bootstrap-green/{KNOWN_ISSUES,ARCHITECTURE_STATE}.md`, `docs/releases/v1.0.0-ga/signatures/SIGN_HERE.md`, `docs/vnext/reports/gates/G04_AI_VALIDATION.md`, `docs/ux/UX_ARCHITECTURE.md`, `docs/ops/{STAGING_VERIFICATION_2026-08-08,STAGING_PARITY}.md`, `docs/current-state/EXTERNAL_DEPENDENCY_REGISTER.md`, `salesos/docs/{roadmap/PRODUCTIZATION_ROADMAP,deployment_guide,admin_guide}.md`, `salesos/reports/ENTERPRISE_AUDIT_REPORT_2026-08-08.md`

---

## 5. Option A — keep True; update honesty to match

**Intent:** Treat Phase 3 flip as the new code SoT. Rewrite living honesty so it no longer claims the default is False. **Do not** claim Production GO or live-provider GA.

### 5.1 Files that would change (living only)

**Do not apply.** Listed for PO.

1. `docs/audit/ga-engineering-audit/AI_HONESTY.md` — table default False → True; strike “Do not flip to True”; add: “code default True; `ga_ready` still False; prod env must stay False until PRC.”
2. `AGENTS.md` §6 — False → “code default True; prod templates False; not GA.”
3. `.cursor/rules/essentials.mdc` and `salesos-master-gate-sequence.mdc` — qualify “False” as *production/env* not *Settings default*.
4. Living honesty strings (runtime + FE) that say “remains False” while echoing Settings — list in §5.2.
5. `salesos/scripts/fitness-ci-subset.sh` + `.ps1` — FF-07 must accept `= True` **or** check prod template False instead of config.py.
6. `salesos/scripts/wave11-soak-gate.py` — stop FAIL on True **or** document Phase 3 exception (today it FAILs).
7. `salesos/scripts/story_14_04_inrepo_pentest_pack.py` — `AI_FLAG_MARKERS` → `bool = True`.
8. `docs/audit/ga-engineering-audit/FITNESS-CI-SUBSET-PLAN.md` + EAB `05-FITNESS-CATALOG.md` + `07-SCORING-MODEL.md` — hard cap “default not False → P0” must be rewritten or it immediately opens P0.
9. Soak/go-live runbooks that require Settings False (`staging-soak.md`, `go-live-checklist.md`, `HYPERCARE_RUNBOOK.md`, `GO_LIVE_RUNBOOK.md`, `ops01-human-execution-pack.md`).
10. SOC2 Type I living pages that cite `bool = False` in config.py.
11. Pentest living briefs (`PENTEST_BRIEF`, `VENDOR_HANDOFF_CHECKLIST`, `THREAT_MODEL`, `INTERNAL_TEST_PLAN`).
12. `docs/ops/AI_COPILOT_ACTIVATION.md` — “defaults to False” → “defaults to True; disable via env for prod.”
13. Optional consistency: `chaos_resilience/router.py` and `ai_policies_engine.py` hardcoded False → echo Settings (or keep hardcoded and document as “this surface never enables product AI”).
14. Optional: admin seed `ai_copilot` enabled=False comment (keep seed False; fix comment).
15. FE honesty tests that match `/remains False/` (`aiPoliciesHonesty.test.ts`, `aiMemoryHonesty.test.ts`).
16. `docs/current-state/BASELINE_*` already say True — no change.

**Do not rewrite** dated crumbs / EAB-001…003 history / August program reports.

### 5.2 Proposed diffs (Option A) — exact before/after for living honesty

**`AI_HONESTY.md` §2 table (excerpt):**

```diff
-| `feature_ai_copilot` | `salesos/backend/app/config.py` (`Settings`) | **`False`** | Keep False for GA unless evidence-validated |
+| `feature_ai_copilot` | `salesos/backend/app/config.py` (`Settings`) | **`True`** (Phase 3 code default, 2026-08-19) | **Not GA.** `ga_ready` remains false. Production/staging templates must set `FEATURE_AI_COPILOT=false` until PRC. Provider path remains DEV-only.
```

**`AI_HONESTY.md` L141:**

```diff
- Do **not** flip `feature_ai_copilot` to True.
+ Code default is True (Phase 3). Do **not** market as GA. Do **not** set production env True without PRC + provider qualification.
```

**Honesty strings that must stop saying “remains False” (same substitution everywhere):**

Before: `feature_ai_copilot remains False`  
After: `feature_ai_copilot follows Settings (default True); live LLM / RAG / Production GO not claimed.`

Files:

- `salesos/backend/app/modules/tenant_studio/{ai_policies_router,prompt_library_router,ai_policies,prompt_library,ai_memory}.py`
- `salesos/backend/app/modules/gtm/{outreach_router,outreach,outreach_engine,website_intelligence_router,website_intelligence,website_intelligence_engine}.py`
- `salesos/backend/app/modules/admin/entitlements.py`
- `salesos/backend/app/modules/chaos_resilience/{handlers,ai_failover,ai_failover_harness,llm_regression,llm_regression_harness}.py`
- `salesos/frontend/src/features/tenant-studio/{aiPolicies,aiMemory,aiModelTiers,promptLibrary}Honesty.ts`
- `salesos/frontend/src/features/gtm/{outreach,websiteIntelligence}Honesty.ts`
- `salesos/frontend/src/lib/api/{aiMemoryStudio,aiPoliciesStudio,promptLibrary,outreach,websiteIntelligence}.ts`
- `salesos/frontend/src/lib/auth/authSessionHonesty.ts`

**`outreach_engine.py` warning list:**

```diff
-            "feature_ai_copilot=False",
+            f"feature_ai_copilot={settings.feature_ai_copilot}",
```

**FF-07 (`fitness-ci-subset.sh`):**

```diff
-if rg -n "feature_ai_copilot:\s*bool\s*=\s*False" salesos/backend/app/config.py >/dev/null; then
-  pass "FF-07: feature_ai_copilot defaults False in config.py"
-else
-  fail "FF-07: feature_ai_copilot must default to False in config.py"
-fi
+if rg -n "feature_ai_copilot:\s*bool\s*=\s*True" salesos/backend/app/config.py >/dev/null \
+   && rg -n "FEATURE_AI_COPILOT=false" salesos/.env.production.template >/dev/null; then
+  pass "FF-07: code default True; prod template False; not GA"
+else
+  fail "FF-07: expected Settings True + prod template false"
+fi
```

Mirror the same logic in `.ps1`. **EAB 07-SCORING-MODEL.md** must drop or rewrite the “default not False → cap ≤29 P0” rule, or Option A instantly fails AIGOV.

**Soak gate:**

```diff
-    # Soak candidate expectation: demo_mode False, feature_ai_copilot False
-    if copilot is True:
-        issues.append("feature_ai_copilot=True (AI honesty expects False until validated)")
+    # Soak candidate: demo_mode False. Copilot default may be True (Phase 3);
+    # production soak still requires FEATURE_AI_COPILOT env false if PO so directs.
```

**Pentest pack:**

```diff
-AI_FLAG_MARKERS = ("feature_ai_copilot: bool = False",)
+AI_FLAG_MARKERS = ("feature_ai_copilot: bool = True",)
```

**FE honesty tests** (`aiPoliciesHonesty.test.ts`, `aiMemoryHonesty.test.ts`):

```diff
-    expect(AI_POLICIES_HONESTY).toMatch(/feature_ai_copilot remains False/);
+    expect(AI_POLICIES_HONESTY).toMatch(/feature_ai_copilot follows Settings/);
```

**Not changed under Option A:** `config.py`, `ai.py` / `copilot.py` gate logic, the 12 backend True-assert tests, prod/staging env templates (stay `false`).

---

## 6. Option B — revert default to False; flip tests (recommended)

**Intent:** Restore fail-closed Settings default so AI_HONESTY, FF-07, soak, pentest pack, EAB scoring, prod templates, and honesty strings agree. Lab enablement stays via `FEATURE_AI_COPILOT=true` + FE build-arg (already documented).

### 6.1 Every test / harness that must flip

**Must change (code will fail or stay split if skipped):**

| File | What flips |
|------|------------|
| `salesos/backend/app/config.py` | `True` → `False` + comment (PO-approved apply step; **not done here**) |
| `tests/unit/test_story_11_07_website_intelligence.py` | `is True` → `is False` |
| `tests/unit/test_story_11_08_ai_outreach.py` | same |
| `tests/unit/test_story_12_01_prompt_library.py` | same |
| `tests/unit/test_story_12_02_ai_policies.py` | same |
| `tests/unit/test_story_12_03_ai_memory.py` | same |
| `tests/unit/test_story_12_04_ai_model_tiers.py` | same |
| `tests/unit/test_story_14_01_load_slo.py` | same |
| `tests/unit/test_story_14_02_chaos_resilience.py` | Settings + `out.detail["feature_ai_copilot"]` → False |
| `tests/unit/test_story_14_03_dr_drill.py` | same |
| `tests/unit/test_story_14_06_ai_failover.py` | Settings + `out.feature_ai_copilot` → False |
| `tests/unit/test_story_14_07_llm_regression.py` | Settings + out + meta → False (3 asserts) |
| `tests/unit/intelligence/providers/test_openai_base_url.py` | two `is True` → `is False` |

**Harnesses that already expect False — no flip, they start passing FF-07 / soak / pentest marker:**

- `salesos/scripts/fitness-ci-subset.sh`
- `salesos/scripts/fitness-ci-subset.ps1`
- `salesos/scripts/wave11-soak-gate.py`
- `salesos/scripts/story_14_04_inrepo_pentest_pack.py`

**Frontend tests:** no Settings flip required (they mock false). Honesty tests already expect “remains False”.

**Optional hygiene (not required for correctness):** rename `test_feature_ai_copilot_remains_false` so name matches assert; leave hardcoded chaos/policies False as now-correct.

**Do not change:** `AI_HONESTY.md` (already False), prod templates (already false), FE Decision STUB.

**Do add (small, living):** a one-line dated note on `PHASE3_GATE_EVIDENCE_PACK.md` and `FINAL_GO_NOGO_ASSESSMENT.md` that the 2026-08-19 True flip was **reverted by PO** (only after apply). Historical crumbs stay as written.

### 6.2 Proposed diffs (Option B)

**`config.py`:**

```diff
     feature_search_fuzzy_v2: bool = False
-    # GA honesty (Wave 6): False until AI runtime is evidence-validated.
-    # P3-6 (2026-08-19): Phase 3 gates closed — groundedness, hallucination,
-    # HITL approval, governance audit all passing. Flag flipped to True.
-    # See docs/audit/ga-engineering-audit/PHASE3_GATE_EVIDENCE_PACK.md
-    feature_ai_copilot: bool = True
+    # GA honesty (Wave 6 + AI_HONESTY.md): False until production AI is
+    # evidence-validated. Phase 3 (2026-08-19) flipped True for a code gate;
+    # PO recon 2026-09-12 reverts default. Lab: FEATURE_AI_COPILOT=true.
+    # See docs/reports/AI_FLAG_RECON-2026-09-12.md
+    feature_ai_copilot: bool = False
```

**Each of the 12 test files — representative hunk** (`test_story_12_02_ai_policies.py`):

```diff
 def test_feature_ai_copilot_stays_false() -> None:
-    assert settings.feature_ai_copilot is True
+    assert settings.feature_ai_copilot is False
```

**`test_story_14_07_llm_regression.py` (all three):**

```diff
     assert settings.feature_ai_copilot is False
     assert out.feature_ai_copilot is False
     assert meta["feature_ai_copilot"] is False
```

**`test_story_14_02_chaos_resilience.py`:**

```diff
     assert settings.feature_ai_copilot is False
     assert out.detail["feature_ai_copilot"] is False
```

**`test_openai_base_url.py`:**

```diff
     assert settings.feature_ai_copilot is False
     assert s.feature_ai_copilot is False
```

No other backend test files reference the flag.

---

## 7. Recommended option + why

### FACT

1. Settings default is **True** (`config.py` L162).
2. `AI_HONESTY.md` still mandates **False** and forbids flipping to True.
3. Phase 3 pack (2026-08-19) flipped the code default and 17 test asserts to True.
4. Provider evaluation (2026-08-23): DEV-only; **production NO-GO**; True in repo does not overturn that.
5. Audit / Production GA remains **NO-GO**.
6. FF-07, wave11 soak, and pentest-pack marker still require `bool = False`.
7. Prod/staging/k8s templates pin `FEATURE_AI_COPILOT=false`.
8. Two runtime payloads **hardcode False** while Settings is True.
9. Admin seed `ai_copilot` is False (second flag).
10. Copilot/AI **product** endpoints are ungated at default True (`ga_ready` still False).
11. EAB scoring: default not False → AIGOV cap ≤29 + P0.
12. Workspace rules still say keep False.

### INFERENCE

- The Phase 3 flip was a **code-gate** action, not a production-AI authorization.
- Option A requires rewriting the honesty SoT, EAB hard cap, soak, FF-07, SOC2 citations, and FE honesty tests — a large surface — while leaving product mutate endpoints **on by default** with a DEV-only provider.
- Option B restores a single fail-closed default. Lab preview remains the documented env + FE build-arg path (`AI-LIVE-PREVIEW-DECISION-2026-08-22.md`).
- Leaving the split-brain is worse than either apply: soak/FF-07 fail, honesty strings lie, and default-on copilot is easy to miss in a new environment.

### RECOMMENDATION

**Choose Option B.**

Rationale in one sentence: **AI_HONESTY, EAB AIGOV, soak, FF-07, pentest pack, and production templates all still require False; Phase 3 True was never authorized as GA; the provider is still DEV-only.**

After apply: add a one-line addendum to `PHASE3_GATE_EVIDENCE_PACK.md` that the flag default was reverted by PO (do not silently rewrite the 2026-08-19 evidence).

---

## 8. Pytest / check scope AFTER PO decides (do not run now)

Low-load protocol: **not executed** in this session.

### If Option B

From `salesos/backend`:

```text
pytest -q \
  tests/unit/test_story_11_07_website_intelligence.py \
  tests/unit/test_story_11_08_ai_outreach.py \
  tests/unit/test_story_12_01_prompt_library.py \
  tests/unit/test_story_12_02_ai_policies.py \
  tests/unit/test_story_12_03_ai_memory.py \
  tests/unit/test_story_12_04_ai_model_tiers.py \
  tests/unit/test_story_14_01_load_slo.py \
  tests/unit/test_story_14_02_chaos_resilience.py \
  tests/unit/test_story_14_03_dr_drill.py \
  tests/unit/test_story_14_06_ai_failover.py \
  tests/unit/test_story_14_07_llm_regression.py \
  tests/unit/intelligence/providers/test_openai_base_url.py
```

Then (scripts, not full pytest):

- `salesos/scripts/fitness-ci-subset.sh` (or `.ps1`) — expect FF-07 PASS
- `python salesos/scripts/story_14_04_inrepo_pentest_pack.py` — expect marker PASS
- Optional: wave11 soak `flags.demo_and_copilot` only (not a 48h soak)

### If Option A

- Same 12 backend files should **already** pass (they assert True).
- FE honesty tests that match `remains False` after string edits:
  - `salesos/frontend/src/features/tenant-studio/__tests__/aiPoliciesHonesty.test.ts`
  - `salesos/frontend/src/features/tenant-studio/__tests__/aiMemoryHonesty.test.ts`
- Re-run FF-07 / soak / pentest pack **after** those scripts are rewritten — they **FAIL today** against True.

Do **not** run full `pytest` or `npm run build` unless PO explicitly approves.

---

## 9. Runtime inconsistency summary

**Yes — runtime is inconsistent today.**

| # | Inconsistency | Why it matters |
|---|---------------|----------------|
| 1 | Settings default **True** vs AI_HONESTY / rules **False** | SoT split |
| 2 | Product gates **open** at default True | Accidental enable on any env without override |
| 3 | `/chaos/meta` and AI-policies evaluate **hardcode False** | API lies vs Settings |
| 4 | Router honesty strings say “remains False” while echoing True | User-facing lie |
| 5 | Admin FeatureFlag `ai_copilot` seeded **False** | Two flags, two answers |
| 6 | Tests named `remains_false` assert **True** | Suite documents the split |
| 7 | FF-07 / soak / pentest pack expect **False** | Living gates already red vs config |
| 8 | Prod templates False vs code True | Safe only if every deploy sets the env |

---

## 10. Files changed this session

| Path | Action |
|------|--------|
| `docs/reports/AI_FLAG_RECON-2026-09-12.md` | **Created** (this memo) |

Not edited (per constraints): `app/config.py`, `ai.py`, `copilot.py`, the ~12 True-assert tests, `AGENTS.md`, `AI_HONESTY.md`, `project-audit/**`. No git write. No pytest / npm.

---

## 11. Close aliases (for searchers)

| Alias | Role |
|-------|------|
| `feature_ai_copilot` | Settings field / JSON key / docs |
| `FEATURE_AI_COPILOT` | Env override for Settings |
| `NEXT_PUBLIC_FEATURE_AI_COPILOT` | FE build/runtime gate (AND with status) |
| `ai_copilot` | Admin in-memory FeatureFlag key (seeded False; **not** Settings) |
