# DEC-125 — Webhook SSRF URL allowlist (Phase 0 criterion 1.2)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion 1.2 = **READY FOR REVIEW** (Architecture PENDING · Validation PENDING). Only Execution Orchestrator may mark VERIFIED/CLOSED.  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Security P0 (SalesOS / AQLIYA)  
> **Story / risk:** GA-P0-SEC-02 / PROD-W2-002 / STORY-01-02 / Phase 0 Exit Criterion **1.2**  
> **Authority:** PHASE_0_EXIT_CHECKLIST §1.2 · PRODUCTION_PLAN PROD-W2-002 · DEC-085 `set_config` · ARB review protocol (Cursor ≠ CLOSED)  
> **Out of scope this land:** CSRF X-API-Key (1.3) · Railway R-14 (2.3) · staging SSRF pentest · frontend · `.ai/` org design · Criterion CLOSED/VERIFIED claims · Production GO

---

## 1. Decision

Accept webhook outbound URL allowlist (public HTTPS + DNS/IP public-only + pinned dial) as **Cursor COMPLETE** for criterion **1.2**, with HTTP + Integration Hub regressions added.

| Pin | Value |
|---|---|
| Finding | GA-P0-SEC-02 — outbound webhook to `sub.url` / workflow webhook without SSRF guard |
| App fix (prior Sprint 01 / Wave 2) | `app/modules/webhooks/url_safety.py` HTTPS-only, blocked metadata hosts, RFC1918/link-local/loopback/reserved IP deny, DNS check, `_PinnedIPBackend` |
| This land | (1) Workflow router maps `UnsafeWebhookURLError` → **400** (was 500); (2) Slack Integration Hub caller reuses `analyze_webhook_url` + pinned transport; (3) HTTP contract + unit + Slack regressions |
| DEC-085 | **Intact** (`get_db` still `set_config`; not touched) |
| Criterion state | **READY FOR REVIEW** (not CLOSED / not VERIFIED) |

**Allowlist semantics (existing pattern, enforced):** outbound destinations must be **HTTPS** to a host that is not localhost/metadata and whose resolved IPs are **public** (non-private, non-link-local, non-loopback, non-reserved). Delivery dials **pre-validated IPs only**.

---

## 2. Validation

| Check | Result |
|---|---|
| Narrow Docker pytest | **32 passed** (65 deselected), ~31s |
| Nodes | unit SSRF · workflow adversarial SSRF-01..07 · HTTP contract (hub + workflow) · Slack Integration Hub |
| Command | `docker compose exec -T backend poetry run pytest tests/contract/test_webhook_ssrf.py tests/unit/test_webhooks.py::TestWebhookSSRF domains/marketplace/tests/test_internal_plugins.py::TestSlackPlugin domains/workflow/tests/test_phase13.py -k "ssrf or SSRF or TestWebhookSSRF or test_send_blocks or test_send_pins or test_rejects or test_valid_https or test_hub or test_workflow_webhook" -q` |
| Production / Railway / staging pentest | **Not run** |
| Label | **build validated** (narrow Docker pytest) |

**Production GO not claimed. CI GREEN not met. Criterion CLOSED not claimed. Staging SSRF pentest still OPEN.**

---

## 3. Records

- Phase 0 criterion **1.2** → **READY FOR REVIEW** (Cursor COMPLETE)
- Assigned next: Architecture Reviewer (independent review sign)
- Prior notes: Sprint 01 service-layer fix + Wave 2 pin redesign already in tree; checklist 1.2 remained ⬜ pending HTTP + Integration Hub re-verify
- **Not claimed:** Criterion CLOSED · VERIFIED · Production GO · CI GREEN · staging pentest PASS

---

## 4. Evidence Package

| ID | Artifact | Location / command |
|----|----------|-------------------|
| EV-001 | URL allowlist | `app/modules/webhooks/url_safety.py` |
| EV-002 | Hub delivery pin | `app/modules/webhooks/service.py` `_attempt_delivery` |
| EV-003 | Workflow create/update | `domains/workflow/service.py` + `app/routers/workflows.py` 400 mapping |
| EV-004 | Integration Hub Slack | `domains/marketplace/plugins/slack.py` `send_slack_notification` |
| EV-005 | New HTTP contract | `tests/contract/test_webhook_ssrf.py` |
| EV-006 | Prior unit / adversarial | `tests/unit/test_webhooks.py::TestWebhookSSRF`, `domains/workflow/tests/test_phase13.py` SSRF-01..07 |
| EV-007 | Slack SSRF tests | `domains/marketplace/tests/test_internal_plugins.py` |
| EV-008 | pytest output | **32 passed**, 65 deselected (Docker `poetry run pytest` narrow SSRF suite) |
| EV-009 | Screenshots | N/A |
| EV-010 | CI artifacts | Field CI PENDING (OpenCode / Validator) |

---

## 5. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (workflows 400 mapping, Slack pin, contract/unit tests, DEC-125 docs) |
| 2 | Core `url_safety.py` / webhook module delivery pin remain (pre-existing); do not remove |
| Expected impact | Lose HTTP/Slack Integration Hub coverage + 400 mapping; allowlist core unchanged |

---

## 6. Risk

| Surface | Level | Note |
|---------|-------|------|
| Application | LOW | Allowlist is deny-private (public HTTPS), not a static SaaS domain list — intentional for tenant webhooks |
| Runtime | LOW | Staging cloud SSRF pentest still OPEN (Wave 12 residual) |
| Integration Hub | LOW | Slack path now shares allowlist; other marketplace plugins without outbound HTTP not in this land |
| Database | N/A | No schema / DEC-085 / R-14 changes |
