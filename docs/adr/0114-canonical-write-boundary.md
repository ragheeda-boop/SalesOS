# ADR-0114: Canonical Write Boundary — FactRecorder + UBOM

**Status:** ACCEPTED
**Date:** 2026-08-09
**Phase:** P2 (Tools + Evidence + Write Path)

---

## Context

SalesOS has 20+ enrichment fields on `CompanyObject` and `ContactObject` that agents
could populate. Agents must never directly mutate canonical data — they must pass through
a governed write boundary with field classification, human-ownership protection, dismissal
guard, and band-based auto-apply.

## Decision

### Governed Write Boundary

```
Agent
  │
  └── WRITE
        │
        ├── Canonical Fact → FactRecorder (authoritative boundary)
        │     ├── fence check (lease_generation)
        │     ├── idempotency check
        │     ├── humanOwns() check
        │     ├── dismissal guard
        │     ├── band decision (VERIFIED→APPLIED, PROBABLE→PROPOSED)
        │     └── UBOM mutation (same transaction)
        │
        └── Other Business Mutation → Governed Tool/Repository (Phase 3)
```

**No agent may access domain ORM/repositories directly.**

### Field Classification

`BusinessObject.is_agent_updatable(field_name)` classifies fields:

**Identity fields (agent NEVER writes):**
`id`, `tenant_id`, `cr_number`, `created_at`, `updated_at`, `is_golden_record`,
`parent_company_id`, `source_ids`, `embedding`

**Enrichment fields (agent CAN write if VERIFIED):**
`city`, `region`, `industry`, `website`, `employees_count`, `annual_revenue`,
`activity_description`, `legal_form`, `latitude`, `longitude`, `phone`, `email`,
`address`, `capital`, `incorporation_date`, `confidence_score`

### FactRecorder Rules

1. **Never overwrite human-set fields.** If a user manually set a field (tracked
   via audit log or `source` column), agent facts are rejected.

2. **Never re-offer a dismissed fact.** Once a human dismisses `(entity_type, entity_id,
   field, value)`, the same combination is permanently blocked.

3. **Never write below POSSIBLE band.** Evidence score < 0.30 → fact is not stored.

4. **VERIFIED facts auto-apply.** Score >= 0.85 AND has primary source → create
   `canonical_facts` row with status=APPLIED + update UBOM field (single tx).

5. **PROBABLE/POSSIBLE facts are proposed.** Create `canonical_facts` row with
   status=PROPOSED + create `approval_request`. Do NOT update UBOM field.

6. **Supersession.** New APPLIED fact supersedes previous APPLIED fact on the
   same `(entity_type, entity_id, field)`. Previous → SUPERSEDED.

### Data Model

```
evidence_records (source of truth for evidence)
    └── fact_evidence (join table)
          └── canonical_facts (proposed/applied facts)
                └── UBOM objects (CompanyObject, ContactObject)
```

`canonical_facts` contains an `evidence_snapshot` JSONB column as an immutable
audit projection only — NOT the source of truth for evidence.

## Relationship with Security Boundary

ADR-0115 defines the security authorization chain (Auth → RBAC → PDP → Tool permissions).
The write path flows through two sequential gates:
1. **ToolDispatcher** (ADR-0115) — security gating: PDP, RBAC, tool-permission checks
2. **FactRecorder** (this ADR) — data integrity gating: field classification, humanOwns,
   dismissal guard, band-based auto-apply

Both gates must pass for a write to reach UBOM.

## Consequences

- Human-set fields are protected from agent overwrites.
- Dismissed facts never re-surfaced (data quality).
- Provenance tracked via `fact_evidence` → `evidence_records` → `agent_runs`.
- Not in Phase 1 — read-only agent only. Write path is Phase 2.

## Related

- ADR-0113: Evidence Architecture
- ADR-0115: Agent Security Boundary

---

## Implementation reconciliation addendum (2026-09-21)

- The original UBOM target is deprecated by ADR-021 and `domains/ubom` is dead code. Future implementation must target the active tenant-scoped SQLAlchemy models in `app/modules/company/models.py` and `app/modules/contact/models.py`; it must not revive the duplicate UBOM mapper registry.
- The application currently has durable `approval_requests`, but that generic workflow is not a canonical fact ledger: it does not store normalized fact state, evidence joins, dismissal guards, or apply an approved value to a company/contact in the same transaction. Do not treat approval metadata as a replacement for `canonical_facts`.
- Approval actor identity now comes from the verified JWT dependency, and approval reads/decisions verify the request tenant in the service. Focused route/service tests cover actor attribution and cross-tenant rejection.
- Company REST/GraphQL create and update paths now pass the verified actor into the audit trail. Other service/bulk mutation paths can still lack an actor, and field-level ownership semantics are not yet unified. No fact may auto-apply until human ownership, dismissal, idempotency, and transactional supersession are enforced by the actual write boundary.
- At the time of the initial reconciliation no schema migration or database write had been made. The schema-only checkpoint below initially recorded no test migration; the later FactRecorder and reviewer addenda supersede that interim state and document the `salesos_test`-only migration and integration proof.

## Fact ledger schema slice (2026-09-21)

- Added tenant-scoped `evidence_records`, `canonical_facts`, `fact_evidence`, and `canonical_fact_events` SQLAlchemy models plus additive Alembic revision `s2t3u4v5w6x7`.
- Evidence-to-fact and event-to-fact foreign keys include `tenant_id`; the join table cannot connect evidence across tenants. RLS is enabled and forced on all four tables.
- Open-proposal and dismissed-value partial unique indexes provide database-level duplicate guards. Status and subject type are constrained; the dismissed row remains the durable suppression record.
- At this schema-only checkpoint, the implementation was groundwork: no proposal writer or review transition existed yet, and no migration had then been applied. The later addenda below record subsequent `salesos_test` work. No production migration or CRM auto-apply is authorized by this checkpoint.
- Offline migration rendering across the full existing chain is currently blocked by pre-existing revision `0028_enrichment_performance.py`, which calls SQLAlchemy inspection against Alembic's offline `MockConnection`. The new revision itself is separately rendered and inspected in the implementation record.

## Proposal-only FactRecorder vertical slice (2026-09-21)

- Added `FactProposalService.propose()` as a tenant-scoped, proposal-only writer. It requires the request tenant to match `app.tenant_id`, verifies the company/contact exists under that tenant, validates the ADR-0114 field registry and classified evidence, and fingerprints both the idempotency token and request payload.
- Evidence, fact, evidence links, and the `PROPOSED` event are inserted in the caller's transaction. PostgreSQL uniqueness handles concurrent retries; the service never commits and never updates Company or Contact. An exact retry returns the existing fact; a changed request reusing its key, an already-open duplicate, or a dismissed value fails closed.
- Added unit and PostgreSQL integration coverage. The integration test is pinned to `salesos_test` and uses the configured application role (verified `rolsuper=false`, `rolbypassrls=false`). It uses an outer rollback, proves the canonical company field stays unchanged, checks retry/dismissal/tenant-scope behavior, and leaves no fixture rows behind.
- Applied revision `s2t3u4v5w6x7` online to `salesos_test` only; the database now reports that revision and all four new tables have ENABLE/FORCE RLS plus tenant policies. No production migration was run.
- Remaining after the proposal service: proposal/agent integration, field ownership ledger, freshness/version semantics, and an approved-fact transactional CRM apply path. The schema's `APPLIED` status is not reachable through this service.

## Human review transition slice (2026-09-21)

- Added `FactReviewService.decide()` with an explicit `APPROVE`, `REJECT`, or `DISMISS` decision for `PROPOSED` facts only. It requires the requested tenant to match `app.tenant_id`, locks the fact row, requires a verified reviewer identity and non-empty reason, updates the fact decision fields, and appends one `REVIEW_DECIDED` event in the caller-owned transaction.
- Exact retries by the same reviewer with the same decision and reason are idempotent. Conflicting decisions and retries fail closed. Dismissed values remain blocked by the proposal service. No Company or Contact field is written; `APPROVED` does not mean applied.
- Unit tests cover the decision map, validation, scope, one-way transition, exact retry, and conflicting retry. PostgreSQL integration on `salesos_test` verifies approve/dismiss, the audit event, dismissal suppression, tenant isolation, and unchanged CRM data under the configured non-superuser/non-`BYPASSRLS` application role; the outer test transaction rolls back.
- This is a service boundary only; a future caller must derive `reviewer_id` from authenticated identity and enforce tenant permission. CRM apply remains unavailable until ownership, freshness, supersession, and atomic apply policy are implemented. The subsequent API addendum below records the registered reviewer routes.

## Authenticated Fact Review API slice (2026-09-21)

- Registered `GET /api/v1/facts/proposals` and `POST /api/v1/facts/{fact_id}/decision`. Reads require `master-data-review:READ`; decisions require `master-data-review:UPDATE`. The existing role matrix grants that resource to administrators, not ordinary users. Rate limiting is applied at the router.
- Registered `POST /api/v1/facts/proposals` for manual human proposals, protected by `master-data-review:CREATE`. The request rejects client-supplied actor fields; the handler fixes `actor_type=human` and derives `actor_id` from the verified JWT subject.
- The decision handler takes reviewer identity only from `get_current_user_id` (verified JWT dependency), tenant only from `get_current_tenant_id`, and the database session from the tenant-context-aware `get_db_session`. The service rechecks the database tenant GUC and locks the proposal before transition.
- Responses explicitly report `crm_applied: false`. The read endpoint exposes proposal/evidence context with bounded pagination and a constrained status filter. Route tests exercise request/response contracts and assert the configured permission dependencies; OpenAPI registration is verified. The PostgreSQL ASGI integration overrides auth/RBAC dependencies to isolate handlers, so live JWT verification and permission enforcement remain unverified end to end.
- Added an internal V3 screen at `/v3/fact-review`, linked from the existing internal review queue without adding a customer-nav destination. It lists proposals, evidence and status; asks for a reason; submits approve/reject/dismiss; and states that approval does not update CRM. Its initial verification-pending state is superseded by the verification addendum below.
- Remaining: Minder/Agent Reach producer integration, verified frontend/browser flow, tenant-role acceptance, field ownership/freshness/supersession policy, and transactional application of approved values to Company/Contact. The manual endpoint is admin-gated; the API cannot apply CRM values.

## Fact Review frontend verification addendum (2026-09-21)

- Reused an existing isolated C: verification copy after confirming matching SHA-256 hashes for the frontend package manifest, lockfile, Jest configuration, and TypeScript configuration. Copied only the changed/new Fact Review frontend files into that copy; no environment files or credentials were included.
- Focused TypeScript check for the Fact Review page/client and transitive imports passed. Focused Jest passed **2 suites / 5 tests**. The browser smoke used Chromium and a synthetic token plus mocked API: the route returned HTTP 200, rendered the proposal and evidence, submitted an approval reason, and rendered reviewer state with **0** console/page errors and failed API requests.
- The project-wide `npm run typecheck` still fails with 88 existing diagnostics in decision-platform/revenue-execution contracts and screens; it reports none in the Fact Review page/client. The current full Next build was not run. The browser flow does not establish live JWT/RBAC enforcement or API/database persistence.
- A locked npm install on the FAT32 D: volume was stopped with about 1.1 GB free; it left a partial ignored `salesos/frontend/node_modules` tree. Automatic command review rejected removal, so it was left untouched. The existing incomplete dependency directory was also preserved; `package-lock.json` is unchanged.
- No production database, provider, deployment, staging, commit, or index staging was used. Phase 7 remains BLOCKED; production remains NOT APPROVED.

## Human-submitted evidence classification hardening (2026-09-21)

- The admin-gated manual proposal route treats submitted evidence as unverified input: it overwrites client `evidence_kind` with `web.cited_claim` and `confidence_level` with `unknown` before the scoring/persistence service runs. Caller-supplied numeric confidence is informational and is not the ADR-0113 weight.
- This prevents a human proposal client from self-asserting primary registry or government-source status. It remains a proposal requiring a separate reviewer. Internal agent producers will need an independently reviewed classifier and must not reuse the human endpoint's identity or source claims.
- Unit scope covering the Fact ledger/proposal/review/router and ADR-0113 scoring: **40/40 PASS**; `salesos_test` integration: **1/1 PASS**, confirming a claimed official registry item persists as a 0.40 POSSIBLE cited claim with unknown descriptive confidence, with transaction rollback. Ruff E9/F and compile pass.
- No canonical Company/Contact update, provider call, production DB write, or deployment is added by this hardening.

## Agent Reach Fact Review bridge — 2026-09-21

The internal `AgentReachFactProposalBridge` transfers persisted Agent Reach evidence into the proposal-only FactRecorder service. It requires tenant GUC agreement, same-tenant company and evidence, unexpired evidence, exact normalized company-name agreement, and safe HTTPS source syntax. It always assigns `CITED_CLAIM` / `UNKNOWN`; the caller-supplied field/value still requires human review. The adapter has no API route or production caller and does not authenticate the producer or enforce its permissions/budget. It does not apply approved values to Company/Contact. Future source fetching must use DNS pinning/egress controls; this proposal adapter makes no DNS lookup or provider request. Focused regression is 42/42 on `salesos_test`, with test fixtures rolled back.

## Authenticated Agent Reach proposal route update (2026-09-21)

- `POST /api/v1/facts/proposals/from-agent-reach` now lets an authenticated human create a Fact Review proposal from evidence already stored in `agent_evidence`. It requires `agent_reach:READ` and `master-data-review:CREATE`; only the default admin role has both. The full Agent Reach provider router is still not mounted.
- The route takes its creator identity from the verified JWT subject and target tenant from the authenticated request context. It rejects client-supplied actor metadata and creates a proposal only. The source stays classified `CITED_CLAIM` / `UNKNOWN`; a second reviewer is required, and the proposal author cannot approve it. The response is `crm_applied=false`.
- Signed RS256/JWT/RBAC/tenant RLS integration on `salesos_test` verifies admin allow, ordinary-user deny, self-review deny, independent review allow, source-payload exclusion, and unchanged Company data. Focused regression passes **66/66**; OpenAPI contract **1/1**; fixtures roll back. This is not an automated Minder identity or provider execution path.
- The preceding adapter-only status remains historically accurate for its checkpoint but is superseded on route existence by this update. Open: browser decision action against the API; automated Minder identity, budget and source-to-value validation; field ownership, freshness, conflicts/supersession; separate atomic apply with audit/retry guarantees. No production migration or CRM apply is authorized here.

## Minder proposal producer authorization addendum (2026-09-21)

The Agent Reach proposal endpoint accepts either a human JWT or an API key validated by `ApiKeyMiddleware` and bound to an active `agent_reach_service` user. This role grants only `agent_reach:READ` and `master-data-review:CREATE`; the key must have exactly those two scopes. The service actor includes the service user ID and API-key ID and remains `agent`, so a human reviewer is required. `TenantContextMiddleware` runs before API-key lookup because `api_keys` has tenant RLS; the request's `X-Tenant-Id` must match the key's tenant. The API-key caller still follows the standard CSRF cookie/header check.

PostgreSQL integration verifies this full proposal-only path on `salesos_test` using the actual API-key middleware and a non-superuser/non-BYPASSRLS role. No service key was provisioned and no provider was called. This does not supply provider pricing, a durable spend budget, or evidence-to-value proof. It does not authorize CRM application; field ownership, freshness, conflict, supersession, and a separate atomic apply policy remain prerequisites.
