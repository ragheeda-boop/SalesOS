# ADR-104: Agent Runtime — Defer to v2.0

**Status**: ACCEPTED
**Date**: 2026-08-07
**Author**: STAR Audit / Architecture
**Related**: D-05, ADR-101, ADR-102
**Supersedes**: nothing

---

## Context

The MASTER_BLUEPRINT.md describes Agent Runtime as a full lifecycle (plan → execute → learn → adapt). The STAR audit (D-05) found only a **placeholder string** — `agent_runtime = "placeholder"` in config.

Current SalesOS has:
- AI Copilot (gated, search-only, `feature_ai_copilot=False`)
- Basic AI guardrails (injection protection, PII scrubbing)
- OpenAI provider integration

None of these constitute an Agent Runtime. The gap is total.

## Decision

**Defer Agent Runtime to v2.0.** Remove from v1.0 scope.

### Rationale
1. **No foundation exists** — Agent Runtime requires: planning engine, execution loop, learning system, tool integration
2. **AI Copilot is gated** — The simpler AI feature is disabled by default; building agents before copilot ships is premature
3. **Dependencies** — Agent Runtime requires: Event Bus (in-memory), AI Memory (basic), Knowledge Graph (offline), Tool Registry (not built)
4. **Risk** — Autonomous agents in a B2B SaaS product require extensive safety testing; shipping未经验证的 agents is a liability

### What stays in v1.0
- AI Copilot (search-only, gated)
- AI guardrails (injection, PII, output validation)
- OpenAI provider integration

### What moves to v2.0
- Planning engine
- Execution loop
- Learning system
- Tool integration
- Agent lifecycle management

## Consequences

- **Positive:** v1.0 AI scope is clear and manageable; copilot can ship without agent complexity
- **Negative:** "AI-native" marketing claim becomes inaccurate for v1.0
- **Risk:** If agents become table stakes in B2B SaaS, v2.0 delivery timeline is critical

## Evidence

- D-05: STAR Audit found placeholder string
- `salesos/backend/app/config.py` — `agent_runtime = "placeholder"`
- `salesos/backend/app/modules/` — no agent-related module
