# ADR-LLM-PROVIDER-SELECTION — 2026-08-24

**Status:** BLOCKED — PROVIDER DECISION  
**Decision Maker:** PO + TL + Finance  
**Date:** 2026-08-24

---

## Context

SalesOS requires a production-qualified LLM provider for the AI copilot, intelligence agents, and RAG system. Four providers are technically qualified. No provider has been selected or provisioned.

## Qualification Summary

| Provider | Model | Cost (per 1M tokens) | Latency (p50) | JSON | Tools | SLA | Regional |
|----------|-------|:--------------------:|:-------------:|:----:|:-----:|:---:|:--------:|
| OpenAI | GPT-4o-mini | $0.15 in / $0.60 out | ~1.5-2.5s | ✅ | ✅ | ✅ | Global |
| Azure OpenAI | GPT-4o-mini | Same + Azure markup | ~1.5-3s | ✅ | ✅ | ✅ | ME regions |
| Google Gemini | 1.5 Flash | $0.075 in / $0.30 out | ~1-2s | ✅ | ✅ | ✅ | ME regions |
| Anthropic | Claude 3.5 Sonnet | $3 in / $15 out | ~2-4s | ✅ | ✅ | ✅ | Global |

## Decision Required

**NOT YET DECIDED — External decision required from PO + TL + Finance.**

### Options

**Option A: OpenAI GPT-4o-mini (Recommended)**
- Best cost/quality ratio
- Widest ecosystem compatibility
- Global infrastructure
- Risk: No Middle East data residency

**Option B: Azure OpenAI GPT-4o**
- Same model quality as OpenAI
- Middle East regions available (UAE, Saudi Arabia)
- Azure enterprise SLA
- Risk: Higher operational complexity, potential Azure markup

**Option C: Google Gemini 1.5 Flash**
- Cheapest option
- Middle East regions available
- Good quality (not GPT-4 class for complex reasoning)
- Risk: Less mature tool/function calling ecosystem

**Option D: Anthropic Claude 3.5 Sonnet**
- Highest quality reasoning
- Global infrastructure
- Risk: 20x more expensive than GPT-4o-mini

## Rejected Alternatives

| Provider | Reason |
|----------|--------|
| AI Horde | SLA fail (p50 5.9s), no tool calling, community-hosted, no data protection |

## Expected Cost (Monthly Estimate)

| Usage Level | OpenAI GPT-4o-mini | Azure OpenAI | Google Gemini | Anthropic |
|-------------|:------------------:|:------------:|:-------------:|:---------:|
| Light (100 calls/day) | ~$5 | ~$7 | ~$3 | ~$60 |
| Medium (1000 calls/day) | ~$50 | ~$70 | ~$30 | ~$600 |
| Heavy (10000 calls/day) | ~$500 | ~$700 | ~$300 | ~$6000 |

## Risks

| Risk | Mitigation |
|------|------------|
| Provider outage | ReliableProvider circuit breaker + retry |
| Cost overrun | Budget enforcement via `tenant_llm_budgets` |
| Data residency | Azure OpenAI or Google Gemini (ME regions) |
| Model quality degradation | PolicyGate model tier enforcement |

## Fallback Strategy

1. Primary: Selected provider
2. If primary fails: OpenAI (if not primary) or Azure OpenAI
3. If all commercial fail: AI Horde (DEV-ONLY, degraded quality)
4. If all fail: Deterministic grounded paths (no LLM)

## Operational Requirements

| Requirement | Detail |
|-------------|--------|
| API key management | Via GitHub Environments secrets |
| Cost tracking | `llm_cost_entries` table (already implemented) |
| Budget enforcement | `tenant_llm_budgets` table (already implemented) |
| Observability | Prometheus metrics via `AIObservability` (already implemented) |
| Retry/failover | `ReliableProvider` with circuit breaker (already implemented) |

## Consequences

- Until a provider is selected, all AI features remain non-functional in production
- `feature_ai_copilot` must stay `False` in production
- Grounded agents degrade to INSUFFICIENT EVIDENCE (honest degradation)
- No LLM costs are incurred (budget enforcement blocks calls)

---

**This ADR is PENDING a management decision. Do not implement until explicitly approved.**
