# ADR-0030: Unified LLM Provider Architecture

**Status**: Accepted
**Date**: 2026-07-16
**Author**: AI Platform Architect
**Supersedes**: Fragmented `AIProvider` (domains/ai), `LLMProvider` (intelligence/providers), `LLMService` (intelligence/agents)

## Context

The SalesOS AI Platform has three overlapping LLM abstractions:

1. **`intelligence/providers/`** — `LLMProvider` Protocol, `ChatRequest`/`ChatResponse`, `OpenAIProvider`, `ProviderFactory`
2. **`domains/ai/service.py`** — `AIProvider` ABC (different interface), `OpenAIProvider` (duplicate), `DecisionPlatformProvider`
3. **`intelligence/agents/llm.py`** — `LLMService` (standalone OpenAI wrapper with no protocol/abstraction)

This fragmentation causes:
- No single provider interface that all consumers can rely on
- Duplicate OpenAI client initialization (3 places)
- No streaming support anywhere
- No vendor lock-in protection (only OpenAI wired)
- Cost tracking not wired into any provider
- No failover/fallback chain

## Decision

Consolidate all LLM provider access into `intelligence/providers/` under a single unified protocol:

### Architecture

```
intelligence/providers/
├── __init__.py                 # Public exports
├── protocol.py                 # Enhanced LLMProvider Protocol (streaming, structured, tools)
├── base.py                     # Dataclasses: ChatRequest, ChatResponse, StreamEvent, etc.
├── openai_provider.py          # OpenAI (chat, streaming, structured, tools)
├── anthropic_provider.py       # Anthropic Claude (chat, streaming, structured, tools)
├── gemini_provider.py          # Google Gemini (chat, streaming, structured)
├── azure_provider.py           # Azure OpenAI (chat, streaming, structured)
├── ollama_provider.py          # Ollama local (chat, streaming)
├── factory.py                  # ProviderFactory with registry, failover chain
├── router.py                   # Intelligent query routing by complexity/cost
└── cost_tracker.py             # Cost tracking wired into every provider call
```

### Unified Interface

```python
class LLMProvider(Protocol):
    async def chat(self, request: ChatRequest) -> ChatResponse: ...
    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]: ...
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse: ...
```

### Migration Path

1. `domains/ai/service.py` `AIProvider` ABC → delegate to `intelligence.providers.LLMProvider`
2. `intelligence/agents/llm.py` `LLMService` → wrap `intelligence.providers.LLMProvider`
3. All agent code → use unified provider via `ProviderFactory.create()` or `get_provider()`

## Consequences

### Positive
- Single interface for all LLM operations across the platform
- 5 providers supported: OpenAI, Anthropic, Gemini, Azure, Ollama
- Streaming support built into every provider
- Cost tracking automatically wired into every LLM call
- Provider failover chain for resilience
- Query routing by complexity for cost optimization
- No vendor lock-in

### Negative
- Existing provider calls in agents and AI service need migration
- Additional dependencies: `anthropic`, `google-generativeai` SDKs
- Testing needs mock providers for each new provider

### Neutral
- `domains/ai/service.py` retains its `AIProvider` ABC as a domain-level concept, but delegates LLM work to the unified provider layer

## Compliance

- CI enforces: no direct OpenAI/Anthropic SDK imports outside `intelligence/providers/`
- All LLM calls must go through `LLMProvider` interface
- All providers must implement both `chat()` and `chat_stream()`
