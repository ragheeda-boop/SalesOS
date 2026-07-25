# Work Order WO-003 — Wave C: AI Foundation

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: WO-002 (Backend Performance) — ✅ Closed
> **Priority**: P1 — High

---

## Wave ID

WO-003 / WAVE-C

## Objective

Build AI foundation layer: provider abstraction, memory runtime, streaming, cost tracking, prompt registry enhancements, and AI tests. Do NOT implement Agent Runtime — that is future scope.

## Scope

Strictly limited to:

1. **Provider Consolidation** — Anthropic provider implementation alongside existing OpenAI (multi-provider pattern)
2. **Memory Runtime** — Episodic memory (PostgreSQL-backed), working memory (in-memory)
3. **Streaming Layer** — LLM response streaming for chat/copilot endpoints
4. **Cost Tracking** — Token and cost tracking per LLM call, per tenant
5. **Prompt Registry** — Versioned prompts, evaluation criteria, A/B test support
6. **AI Tests** — Backend AI test coverage for existing intelligence module

## Assigned Engineer

`ai-engineer`

## Assigned Reviewer

`security-reviewer` (for guardrails/safety) + `performance-reviewer` (for cost/streaming)

## Expected Deliverables

| Deliverable | Description |
|-------------|-------------|
| Anthropic provider | Implement `AnthropicProvider` following the provider protocol |
| Provider factory update | `factory.py` supports OpenAI + Anthropic, switchable per config |
| Episodic memory | PostgreSQL-backed agent memory (conversation history) |
| Working memory | In-memory session context |
| Streaming support | SSE streaming for LLM responses |
| Cost tracker | Per-call token/cost tracking, per-tenant aggregation |
| Prompt Registry v2 | Versioned prompts, evaluation criteria fields |
| AI tests | ≥ 30% coverage on intelligence module |
| `SPRINT0_WAVE_C_REPORT.md` | Final report documenting all changes |

## Quality Gates

| Gate | Criteria |
|------|----------|
| G-C.1 | Anthropic provider returns correct responses in test mode |
| G-C.2 | Provider selection is configurable (OpenAI / Anthropic) via settings |
| G-C.3 | Episodic memory persists across agent sessions (verified by test) |
| G-C.4 | Streaming responses deliver tokens progressively, not batched |
| G-C.5 | Cost tracker records: model, tokens (prompt + completion), estimated cost, tenant_id |
| G-C.6 | Prompt Registry supports version tracking + evaluation criteria |
| G-C.7 | AI test coverage ≥ 30% on intelligence module (pytest-cov) |
| G-C.8 | All existing tests still pass |

## Stop Condition

Wave C is complete when all deliverables are produced and quality gates pass.

## Constraints

- Do NOT implement Agent Runtime — that remains "PLANNED FOR RT3"
- Do NOT implement multi-agent orchestration
- Do NOT modify frontend code
- Do NOT implement Data Fabric connectors
- All changes must be backward-compatible

## Dependencies

WO-002 (Backend Performance) — ✅ Closed. BodyCache, pagination, N+1 fixes all in place.

---

**Engineering OS Authorization**: ✅ Approved
