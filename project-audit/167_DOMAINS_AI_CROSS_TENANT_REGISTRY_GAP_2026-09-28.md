# 167 — `domains/ai`: a single, process-wide `PromptRegistry`/`AIEvaluator` with no tenant concept, correctly permission-gated but not tenant-isolated — documented, not fixed (unlike report 166's marketplace fix, this needs a schema change, not a role-gate swap)

**Read-only.** No files changed — no narrow, unambiguous fix exists here; a real fix requires a schema/product decision. No database or container needed for this investigation.

## 1. Scope

Continuing the `domains/` sweep. `domains/ai` (439 lines: `models.py`, `registry.py`, `service.py`, `evaluator.py`, `schemas.py`), and its sole live consumer, `app/routers/ai.py` (confirmed mounted at `app/boot/routers.py:652`, `/api/v1`).

## 2. What's clean

Unlike report 166's marketplace finding, `app/routers/ai.py`'s router is **not** gated by mere authentication — every one of its 6 endpoints layers `Depends(require_permission_dep("ai", PermissionAction.READ/CREATE/UPDATE))` on top of the shared `_auth = [Depends(verify_token)]`, a real role-based permission check (confirmed via `app/dependencies.py::require_permission()`, which checks `user.role` against `PermissionEnforcer.check(...)`). `/ai/generate`/`/ai/evaluate` (the only endpoints that would execute a real LLM call) additionally require `require_ai_copilot_enabled` — a 403 when `Settings.feature_ai_copilot` is `False` (the default, per this session's extensive AI-honesty history). `OpenAIProvider` is registered with no API key anywhere in this file (`OpenAIProvider()`, all defaults) — `self.client` is `None` whenever `api_key` is falsy, so `generate()` fails closed and returns `""` rather than crashing, independent of the feature flag. `AIEvaluator`'s 5 built-in metric functions and `AIService.generate()`'s template-variable substitution are internally consistent, field-mapping-correct, and match every schema/model exactly.

**File-level code quality: clean.**

## 3. The gap — cross-tenant data sharing, genuinely different in kind from report 166's fix

`PromptRegistry` (`self._templates: dict[str, list[PromptTemplate]]`) and `AIEvaluator` (`self._evaluations: list[AIEvaluation]`) are both purely in-memory, process-wide singletons (`app/routers/ai.py:27-29`, module-level globals, not per-request or per-tenant). Neither `PromptTemplate` nor `AIEvaluation` has a `tenant_id` field anywhere in their dataclass definitions (`domains/ai/models.py`). Every router endpoint takes `tenant_id: str = Depends(get_current_tenant_id)` as a parameter — but this value is **never once used** inside `list_prompts()`/`create_prompt()`/`activate_prompt()`/`evaluate()`/`get_metrics()`/`generate()`; it is captured and silently discarded.

The practical effect: any user whose role carries `ai:read`/`ai:create`/`ai:update` permission (not a rare "admin-only" grant — likely available to "manager" and above per this codebase's role hierarchy) can see, create, or activate prompt templates that are immediately visible to and mutable by every other tenant's similarly-permissioned users on the same process. `get_metrics(prompt_id)` compounds this: since `prompt_id` is a caller-chosen string with no tenant namespacing, two different tenants both naming a prompt e.g. `"welcome-email"` would see each other's evaluation history and scores under that shared key.

## 4. Why this is documented, not fixed — a genuinely different remediation shape than report 166

Report 166's marketplace fix was a **narrow, unambiguous** improvement: swap one dependency (`verify_token` → `require_role_dep("admin")`) with zero schema impact, since every interpretation of the intended design agreed a non-admin user having that power was wrong. This finding is different in kind:

- The permission check here is **already role-based**, not "any authenticated user" — tightening the role further (e.g., to admin-only) would reduce the blast radius but would **not** fix the actual defect, since the registry would still be a single object shared across every tenant regardless of who is allowed to touch it. Two different tenants' admins would still silently corrupt or view each other's prompts.
- A genuine fix requires adding a `tenant_id` field to `PromptTemplate`/`AIEvaluation`, threading it through `PromptRegistry`'s and `AIEvaluator`'s internal dict/list keys and every method, and deciding what "activate" should mean per-tenant vs. globally — a real schema and behavior design, not a one-line dependency swap.
- This module's own in-source documentation already discloses it as non-authoritative ("Domain PromptRegistry — not Studio CAP-089 SoT... dual-capability residual," `EAB-001-P1-DUP-02`) — the durable, tenant-isolated Prompt Library already exists elsewhere (`app/modules/tenant_studio/`, confirmed Postgres-backed with tenant RLS in report 89). It is plausible this entire domain is intended to be retired in favor of that one rather than repaired — a product decision this session should not make unilaterally, matching the established precedent (reports 130/157/166).
- The highest-risk operation (actually calling an LLM) is independently, safely inert today: gated behind `feature_ai_copilot=False` by default, and even if enabled, `OpenAIProvider` has no API key configured anywhere in this wiring.

## 5. Scope and safety

- No files changed. No database or container needed — this is a pure architecture/data-model finding, established by direct inspection of `PromptTemplate`/`AIEvaluation`'s dataclass fields and every consuming method.
- No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted. Flagging this for a deliberate product decision (add tenant scoping vs. retire this domain in favor of the Studio library) rather than resolving it unilaterally.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. Remaining `domains/` candidates: `domains/copilot`, `domains/rag` (`domains/ubom` deferred, explicitly marked DEPRECATED).
