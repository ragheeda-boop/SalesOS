# ADR-0116: Tool/Capability Architecture — CapabilityRegistry Extension

**Status:** ACCEPTED
**Date:** 2026-08-09
**Phase:** P2 (Tools + Evidence + Write Path)

---

## Context

Comp AI CRM has 28 typed tools with structured input/output schemas. SalesOS has a
CapabilityRegistry (`sdk/capability_registry.py`) that already declares system capabilities
with typed metadata, execution strategies, and AI declarations. Agents need tool discovery
and governed execution without a second capability system.

## Decision

### Extend CapabilityRegistry (not replace it)

Add two fields to `AIDeclaration`:

```python
@dataclass
class AIDeclaration:
    semantic_search: bool = False
    similar_companies: bool = False
    copilot: bool = False
    rag: bool = False
    classification: bool = False
    agent_available: bool = False      # NEW: Can agents use this capability?
    agent_tool_name: str | None = None # NEW: Tool name when exposed to agents
    agent_sensitive: bool = False      # NEW: Requires human approval for writes?
```

### ToolRegistry (reads CapabilityRegistry)

```
CapabilityRegistry (existing)
  Capability(name="company_search", type=SEARCH, ai=AI(agent_available=True, agent_tool_name="company.lookup"), ...)
        │
        ▼
ToolRegistry (new, Phase 2)
  Tool(name="company.lookup", capability_name="company_search", handler=..., permissions=["company:read"])
  Tool(name="company.enrich", capability_name="company_enrich", handler=..., permissions=["company:write"])
        │
        ▼
ToolDispatcher (new, Phase 2)
  Before every tool call:
    1. Resolve tool from ToolRegistry
    2. Check budget via BudgetTracker.spend()
    3. If write tool: check PDP
    4. If automated + sensitive: block
    5. Execute handler with timeout
    6. Record agent_action with idempotency_key
```

### Three Separated Concepts

| Concept | Responsibility | Phase |
|---------|---------------|:-----:|
| **Agent** | Business intelligence (analysis, decisions) | P1 |
| **Agent Runtime** | Execution infrastructure (state, lease, budget) | P1 |
| **Tool** | Controlled capability (read/write boundaries) | P2 |

### Initial Tool Set

**Read tools (Phase 2):**
`company.lookup`, `company.list`, `contact.lookup`, `opportunity.read`,
`graph.query_relationships`, `source.balady_lookup`, `source.cr_lookup`,
`intelligence.feature_scores`, `intelligence.signals_read`

**Write tools (Phase 2):**
`company.update_enrichment`, `contact.update_info`, `opportunity.create_note`,
`fact.record`

**Write tools (Phase 3, with approval):**
`opportunity.create`, `company.merge_propose`

### Tool Declaration

```python
@dataclass
class ToolDeclaration:
    name: str                      # "company.lookup"
    capability_name: str            # References CapabilityRegistry
    description: str                # For agent preamble
    input_schema: type[BaseModel]   # Pydantic model
    output_schema: type[BaseModel]  # Pydantic model
    required_permissions: list[str] # e.g., ["company:read"]
    is_write: bool                  # Does this tool modify data?
    is_sensitive: bool              # Requires human approval if automated?
    cost_units: int                 # Budget cost (0 = free)
    handler: Callable               # Async function
```

## Consequences

- Single source of truth: CapabilityRegistry for all capability declarations.
- Tools are typed (Pydantic), not arbitrary function calls.
- Tool availability is per-tenant (Phase 3: `agent_capabilities` table).
- Missing/unavailable tools degrade gracefully (Comp AI pattern: `unavailable()` message).
- Not in Phase 1 — Tool architecture is Phase 2.

## Related

- ADR-0111: Task Queue (Phase 1)
- ADR-0114: Canonical Write Boundary (Phase 2)
