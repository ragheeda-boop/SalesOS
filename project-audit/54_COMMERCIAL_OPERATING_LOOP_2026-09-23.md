# Commercial Operating Loop 54 — 2026-09-23

## Purpose

Close verified gaps in the seller feedback loop and Customer Success evidence without modifying the production database, calling a provider, or advancing Phase 7 canonical data.

## Delivered changes

| Area | Change | Boundary retained |
|---|---|---|
| Seller outcome | `action_outcomes` can carry one optional, tenant-owned opportunity ID and an idempotency key. The company NBA page now presents only the current company's opportunities as an explicit optional selector. | This records a relationship; it does not assert attributed revenue or create a CRM opportunity. |
| Customer Success | Tenant-scoped NPS and CSAT response API, persistence, validation, idempotency and v3 survey panel. NPS/CSAT are derived only from recorded responses. | Invitation count, response rate, onboarding, adoption, support, health, renewal and expansion are not modeled. `response_rate` remains `null` with an explicit reason. |
| Stakeholders | Opportunity-contact endpoints now require opportunity UPDATE/READ permissions, validate both parent records in the authenticated tenant, and constrain stakeholder roles to commercial values. | This is an opportunity stakeholder edge, not a general people-to-people relationship graph. |
| Runtime permissions | Migration `r4s5t6u7v8w9` grants only the parent reads required by these workflows to `salesos_app`, while FORCE RLS remains the row boundary. | No blanket privilege grant was introduced. |
| Meeting and search | Meeting briefing reads are tenant-scoped; opportunity search suggestions use a bounded field whitelist. | No live OAuth/calendar provider or external search provider was enabled. |

## Verification

The final verification used a fresh ephemeral `pgvector/pgvector:pg16` database. Migrations ran from zero to `r4s5t6u7v8w9`; fixtures were seeded by the owner connection and all workflow assertions used the non-superuser `salesos_app` runtime role.

```text
39 passed in 1.16s
```

The run includes tenant-isolated stakeholder parent checks, NPS/CSAT response idempotency and aggregation, action-outcome opportunity links, meeting intelligence scope tests, and opportunity-search tests. Python compilation and Alembic head resolution also pass.

The first restricted-role run exposed missing table privileges for `commercial_opportunities`, `companies`, and `contacts`. The narrow grant migration above corrects that deploy-time defect. Tests were rerun with the restricted role after the correction; a result produced with the owner role was not accepted as RLS evidence.

## Deliberate non-claims

- Local frontend dependencies remain incomplete, so TypeScript, Next build, Jest, and authenticated browser evidence were not refreshed here.
- No external provider, CRM apply, staging connector, production migration, deployment, commit, or push occurred.
- Phase 7 remains capture-only/test-only. No Global ID, source payload, or canonical Master Data value changed.
- The capability census remains **88/113 = 77.9% (78%)**. This loop improves partial capabilities; it does not close the Customer Success lifecycle, end-to-end outcome-to-revenue attribution, provider operation, or production gates needed to claim 90%.

## Next code-reachable work

1. Add a reviewed, tenant-scoped relationship graph for person-to-person influence and lifecycle evidence; keep opportunity stakeholders as its existing bounded slice.
2. Add durable customer lifecycle inputs before deriving a Customer Health score: invitations, onboarding milestones, product-use events, support and renewal data.
3. Restore the frontend toolchain in a clean D: checkout, then run TypeScript, Jest, Next build, and an authenticated browser journey against the current backend.

Production remains **NOT APPROVED**.
