# Agent Reach → Fact Review Proposal Bridge — 2026-09-21

## Result

Added an internal adapter at `salesos/backend/app/modules/agent_reach/fact_proposals.py` and registered `POST /api/v1/facts/proposals/from-agent-reach` in the authenticated Fact Review API. An authorized human can select already-persisted Agent Reach evidence and submit a proposed value; the route creates a reviewable proposal only. It does not apply a value to Company or Contact records. The full Agent Reach/provider router remains unregistered.

## Guardrails implemented

- The requested tenant must match PostgreSQL's current `app.tenant_id`; the evidence query is tenant-scoped and excludes expired evidence.
- The target Company must belong to the same tenant. Its Arabic or English canonical name must exactly match the evidence company name after Unicode NFKC normalization, case folding, and whitespace normalization. No fuzzy name match is attempted.
- Evidence must have a supported Agent Reach channel, a UUID, and a timezone-aware collection timestamp.
- Source URLs require HTTPS and syntactically valid IDNA DNS labels; credentials, nonstandard ports, local/special literal IPs, ambiguous numeric IP spellings, and local-only hostnames are rejected. Query strings and fragments are stripped before persistence.
- Raw Agent Reach payloads are not copied. Titles and summaries are length-capped.
- Every observation is scored as `CITED_CLAIM`, confidence level `UNKNOWN`, and fixed input confidence `0.40`; the producer cannot promote it to an official or verified source.
- A deterministic token makes an identical tenant/company/field/value/evidence proposal idempotent. The actor is attributed as `agent_reach:evidence:<id>`.
- The new route requires both `agent_reach:READ` and `master-data-review:CREATE`. The existing default role matrix grants these capabilities to `admin`; ordinary `user` is denied. It gets the creator ID from the verified JWT and records the proposal as human-authored, so the existing self-review prohibition applies. Client-supplied actor fields are rejected.

## Verification

- Focused regression across bridge/service/router/authz/contracts and both related PostgreSQL integrations: **66 passed**.
- PostgreSQL proof used `salesos_test` with a role that is neither superuser nor `BYPASSRLS`. Integration fixtures and test signing keys are rolled back or held under pytest `tmp_path`.
- Cases cover idempotent retries, evidence classification and raw-payload exclusion, URL sanitization, tenant isolation, wrong-company evidence, expired evidence, invalid channel/URL/time metadata, JWT-derived creator identity, ordinary-user denial, proposer self-review denial, independent review, and unchanged Company data.
- OpenAPI registration contract **1/1 passed**; Ruff (`E4,E7,E9,F,I`) and `compileall` passed. Pytest emitted one upstream Starlette/httpx deprecation warning.
- Existing Agent Reach router/security regression also passed **35/35**; the provider-facing router remains absent from app registration. The combined run of proposal, bridge, authorization, Agent Reach security and OpenAPI tests finished **102/102 passed**.
- The route is user-invoked and proposal-only. It does not expose provider execution or make Agent Reach/Minder an automated caller.

## Boundaries and remaining work

The human caller supplies the proposed field and value; the cited page summary does not independently prove that value. The Fact Review queue and a second human reviewer remain the quality gate. The route authenticates and authorizes the human request, but it is not a service identity for Minder and does not budget or authorize provider execution. Host validation checks syntax and literal IP classification without DNS resolution; any future fetch must add DNS pinning and egress controls. No provider was called, no schema or production data was changed, no CRM field was applied, and no deploy/staging/commit action occurred.

Browser decision interaction remains unverified: this turn found no listener on `localhost:3102`, the in-app browser returned `ERR_CONNECTION_REFUSED`, and the `agent-browser` CLI was not installed. No browser action was claimed. The integration now redirects the test JWKS key directory itself to pytest `tmp_path`; the existing application key files' timestamps were unchanged. Next work: start a current-source UI/API test environment when its dependencies are available, verify decision interaction against the authenticated API, then define a distinct trusted Minder producer identity and permission/budget gate before automating proposal creation. Specify ownership, freshness, conflict, and supersession policy before any CRM apply; keep apply in a separate atomic service with its own audit/retry proof. Phase 7 remains BLOCKED, production remains NOT APPROVED, and the roadmap remains **46%** (last census 52/113; this focused task did not re-census).

## Scoped Minder service principal + RLS correction — 2026-09-21

The human-only endpoint above has been extended with a narrow service-authentication option for Minder proposal creation. `POST /api/v1/facts/proposals/from-agent-reach` accepts either an authorized human JWT or a validated API key bound to an active `agent_reach_service` user. The service role grants exactly `agent_reach:READ` and `master-data-review:CREATE`; the key must contain exactly those two scopes, identify its key/user/tenant, and send the matching `X-Tenant-Id`. Service proposals are attributed as `agent` with both service-user and API-key identity. Human callers remain JWT-attributed and the author still cannot review their own proposal.

The end-to-end PostgreSQL integration inserts temporary scoped keys and calls through the actual `ApiKeyMiddleware`, tenant context, tenant RLS, service-role authorization, persisted evidence bridge, and proposal service. It exposed and fixed middleware ordering: tenant context must wrap API-key lookup because `api_keys` itself is RLS-protected. `ApiKeyMiddleware` now exposes the validated key ID to downstream authorization. Wrong-tenant key use, extra scopes, service-role JWT authentication on either proposal route, and human-JWT use of the agent route are denied. A separate application-stack test locks the middleware order. Default CSRF still applies; server callers must send the standard matching cookie and token headers. The complete focused run passed **123/123** on `salesos_test`; Ruff, compileall, and `git diff --check` passed. One upstream Starlette/httpx deprecation warning remains. Test key/user/fact rows rolled back; no provider or production calls occurred.

This establishes a proposal-only producer boundary, not a live Minder integration. No service account or credential was provisioned. The provider router remains unregistered; provider price/cost caps and durable spend accounting are undefined; the proposed field/value is still a cited claim for human review. Service account provisioning, a cost-budget policy, source-to-value checks, browser decision action, field ownership/freshness/conflict/supersession policy, separate atomic CRM apply, and Phase 7/PO gates remain open. Production is NOT APPROVED and roadmap remains **46%** (last complete census 52/113; not re-censused).

## Browser reviewer decision update — 2026-09-21

The browser decision limitation above is superseded for the isolated human review path. A reason-gated approval from the current V3 page reached the signed-JWT/RBAC/tenant-RLS API on `salesos_test`; the Approved state, reviewer, timestamp, and reason event were verified, while Company stayed unchanged. All synthetic DB rows were removed and checked at zero. Normal production login was not tested. See [report 28](28_FACT_REVIEW_BROWSER_DECISION_2026-09-21.md). Minder provisioning/budgets, evidence-to-value validation, ownership/freshness/conflicts/supersession, atomic CRM apply, and Phase 7 gates remain open; roadmap remains **46%**.
