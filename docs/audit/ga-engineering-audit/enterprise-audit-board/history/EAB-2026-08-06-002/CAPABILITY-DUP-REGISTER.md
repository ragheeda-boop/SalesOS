# Capability Duplicate Register — EAB-2026-08-06-002 (+ EAB-003 + Stream B M1)

**Date:** 2026-08-08 (Completion Program Stream B M1)  
**Finding:** EAB-001-P1-DUP-02  
**Disposition:** **Partial (narrowed)** — workflow webhook remount **resolved**; search experimental **quarantined**; prompt dual-registry **quarantine comments + OpenAPI tags** strengthened (still not consolidated)  
**Validation:** light validated (doc/router quarantine; fitness unrelated)  
**Does not change:** Production GA **NO-GO** / evidence-based GO not claimed

Cross-links:

- Decision HTTP SoT: [../EAB-2026-08-06-001/DECISION-API-SOT.md](../EAB-2026-08-06-001/DECISION-API-SOT.md)
- Structural pack: [../EAB-2026-08-06-003/REMEDIATION-STRUCTURAL.md](../EAB-2026-08-06-003/REMEDIATION-STRUCTURAL.md)
- Stream B M1: [../../../completion/STREAM-B-M1.md](../../../completion/STREAM-B-M1.md)

---

## Precedence rules (general)

1. **Documented mount order wins** for overlapping *families*; prefer the router named as primary in this register.
2. **No silent remount** without DEC + OpenAPI regression check (workflow remount is the exception recorded here).
3. Dual *capability* without path overlap is **honest residual**, not an HTTP collision.
4. Clients must not invent a single “Search/Webhook/Prompt” mega-API until consolidation lands.

---

## Search

| Role | Module | Mount | Paths / notes |
|------|--------|-------|---------------|
| **Primary runtime** | `runtime.search_runtime.router` | `/api/v1` (first) | `GET /search`, `/search/suggest`, `/search/similar/{id}`, `/search/metrics`, `POST /search/ai` |
| **API / experimental** | `app.routers.search` | `/api/v1` (second) | `GET /search/analytics`, `/search/semantic`, `POST /search/similar` — OpenAPI **`deprecated=True`**, tag **Search (experimental)** |
| Collision status | — | — | **No path overlap** with runtime list above (dual capability) |
| Remount this pass | — | — | **Quarantined** (EAB-003); fold later via DEC |

**Client guidance:** Prefer runtime list/suggest for product search UX; treat experimental analytics/semantic as alternate until a DEC consolidates.

---

## Webhooks

| Role | Module | Mount | Notes |
|------|--------|-------|-------|
| **Subscriptions (Hub SoT)** | `app.modules.webhooks.router` | `/api/v1/webhooks` | Tenant webhook subscriptions / deliveries |
| **Workflow endpoints** | `app.routers.workflows` | `/api/v1/workflow/webhooks*` | **Remounted EAB-003** from `/api/v1/webhooks*` — prefix collision **resolved** |
| Stripe | `app.modules.billing.stripe_router` | `/api/v1` | Signature-verified public webhook; CSRF-exempt by design |
| Employee | `domains.employee.webhook_handler` | `/api/v1` | `/webhooks/google-calendar`, `/webhooks/microsoft-calendar` — keep |
| Collision status | — | — | Workflow vs Hub **fixed**; Stripe/employee distinct ingress |

**Client guidance:** Use `/api/v1/webhooks/subscriptions*` for Hub CRUD; use `/api/v1/workflow/webhooks*` for workflow endpoint CRUD.

---

## Prompt / AI library surfaces

| Role | Module | Mount | Notes |
|------|--------|-------|-------|
| **Studio prompt library** | `tenant_studio.prompt_library_router` | `/api/v1` + `/studio/prompt-library` | Tag **AI Studio (experimental; prompt dual-registry)**; meta.honesty cites DUP-02 |
| Domain AI prompts HTTP | `app.routers.ai` | `/api/v1/ai/prompts*` | Separate registry; list OpenAPI describes dual; **generate/evaluate gated + OpenAPI deprecated** (AIGOV-01) |
| Other registries | `intelligence.prompts` residual | code | Not HTTP SoT |
| Remount / consolidate | — | — | **Not done** — quarantine only; DEC required for single SoT |

**Client guidance:** Treat studio library as experimental; do not market as single governed prompt SoT.

---

## Related decision engines (pointer only)

Decision multi-engine HTTP SoT is **not** re-registered here — see DECISION-API-SOT.md (DUP-01).

---

## Finding status

| ID | Status after Stream B M1 |
|----|--------------------------|
| **EAB-001-P1-DUP-02** | **Partial (narrowed)** — webhook remount Fixed (prior); search quarantined (prior); prompt dual-registry quarantine **strengthened**; consolidation Deferred |

*Capability Dup Register — EAB-002 + EAB-003 + Stream B M1 — production no-go unchanged — no commit*
