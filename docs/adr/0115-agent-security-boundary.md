# ADR-0115: Agent Security Boundary — PDP + Sandbox + RBAC

**Status:** ACCEPTED
**Date:** 2026-08-09
**Phase:** P3 (Governance + Approval + Signals)

---

## Context

Agents executing autonomously need a multi-layer security boundary to prevent:
cross-tenant access, direct database access by the LLM, unrestricted network calls,
PDP bypass, RBAC bypass, and silent sensitive writes.

SalesOS already has: RS256 JWT, RBAC (5 roles), PDP (PolicyEngine), multi-tenancy (RLS),
and a PluginSandbox for marketplace plugins.

## Decision

### Authorization Chain

```
1. Authentication (existing)       →  RS256 JWT / API key → user_id, tenant_id
2. TenantContextMiddleware (existing) → ContextVar → RLS on all tables
3. RBAC check (existing)           →  require_permission(resource, action)
4. Agent Policy check (new)        →  automated? sensitive? budget OK? enabled?
5. PDP Evaluation (existing, ext)  →  PolicyEngine: DNC, government, custom policies
6. Tool-level permissions (new)    →  Tool declares required permissions; ToolDispatcher checks
7. Action execution or rejection
```

### Security Invariants

| # | Invariant | Enforcement |
|---|-----------|-------------|
| 1 | No cross-tenant access | RLS on all Agent* tables + tenant_id ContextVar |
| 2 | No direct DB credentials to agent | Tools use typed APIs; agent never receives DATABASE_URL |
| 3 | No unrestricted network access | Agent sandbox denies egress; only registered tools make HTTP calls |
| 4 | No agent bypass of PDP | ToolDispatcher calls PolicyEngine before every write tool |
| 5 | No agent bypass of RBAC | Agent identity has role; permissions checked at tool dispatch |
| 6 | No silent sensitive writes | Automated sessions blocked from sensitive actions; PROBABLE facts require approval |
| 7 | All actions auditable | `agent_actions` table + EventRuntime events |
| 8 | Idempotent side effects | `UNIQUE(tenant_id, idempotency_key)` on `agent_actions` |

### Agent Sandbox

- **Network:** deny-all egress. Tools are the ONLY egress path.
- **Database:** no DATABASE_URL in agent environment. Tools call internal services.
- **Filesystem:** no write access. Read-only workspace.
- **Environment:** only explicitly allowed vars (`tenant_id`, `session_id`, `user_id`).
- **Timeout:** per-task via Celery `time_limit`.
- **Budget:** per-task tool call cap.

The existing PluginSandbox (for marketplace plugins) is NOT reused — it lacks network
isolation and credential isolation. A dedicated AgentSandbox is built in Phase 3.

### Action Classification

| Classification | Automated Session | Human Session |
|:---|---:|:---:|
| INFORMATIONAL (read) | AUTO_EXECUTE | AUTO_EXECUTE |
| NON-SENSITIVE WRITE (enrichment) | AUTO_PROPOSE | AUTO_PROPOSE |
| SENSITIVE WRITE (business-impacting) | REQUIRE_APPROVAL | REQUIRE_APPROVAL |
| IRREVERSIBLE (destructive) | ALWAYS_BLOCK | REQUIRE_APPROVAL |

## Consequences

- Agents have the same security posture as human users (RBAC + PDP).
- Automated sessions cannot perform sensitive writes unattended.
- Sandbox prevents credential leakage and network exfiltration.
- Security gating is in Phase 3. Phase 1 is read-only (no writes, no PDP needed).

## Related

- ADR-0114: Canonical Write Boundary
- ADR-0112: Agent State Machine
- Existing: `runtime/policy_runtime/`, `runtime/plugin_sandbox/`, `sdk/permissions.py`
