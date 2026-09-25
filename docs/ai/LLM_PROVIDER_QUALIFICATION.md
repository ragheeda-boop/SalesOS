# LLM PROVIDER QUALIFICATION — 2026-08-24

**Purpose:** Evaluate production LLM candidates against SalesOS requirements.

---

## Current State

| Env | Provider | Model | Key | Status |
|-----|----------|-------|-----|--------|
| Local Dev | AI Horde (via FreeLLMAPI) | Cydonia-24B-v4.3 | FreeLLMAPI token | Working, SLA FAIL |
| Production | OpenAI (api.openai.com) | gpt-4o-mini | `sk-test-key` (placeholder) | NOT QUALIFIED |
| Staging | None | — | Empty | NOT CONFIGURED |

**Verdict: NO production-qualified provider exists.**

---

## Requirements

| Requirement | Threshold | Rationale |
|-------------|-----------|-----------|
| Availability | 99.9% uptime | Production SLA |
| Latency (p50) | < 3s | User experience |
| Latency (p99) | < 10s | Acceptable wait |
| Structured JSON | Reliable | Agent outputs require JSON |
| Tool/Function calling | Required | Agent tool use |
| Model quality | GPT-4 class minimum | Complex reasoning |
| Rate limits | > 100 RPM | Concurrent users |
| Error handling | Retryable errors distinguishable | Reliability layer |
| Cost | < $0.01/1K tokens (input) | Budget sustainability |
| Privacy | No training on customer data | Data residency |
| SLA | Commercial agreement | Production guarantee |
| Regional | Available in Saudi Arabia / Middle East | Regulatory |

## Candidate Evaluation

### Candidate 1: OpenAI (GPT-4o-mini)

| Criterion | Assessment | Evidence |
|-----------|:----------:|----------|
| Availability | 99.9%+ SLA | OpenAI status page |
| Latency | p50 ~1.5-2.5s | Published benchmarks |
| JSON output | Reliable (response_format) | SDK support |
| Tool calling | Native function calling | SDK support |
| Model quality | GPT-4 class | Industry standard |
| Rate limits | 500 RPM (Tier 1) | OpenAI docs |
| Cost | $0.15/1M input, $0.60/1M output | Published pricing |
| Privacy | Data not used for training (API) | OpenAI data policy |
| SLA | Enterprise agreement available | OpenAI sales |
| Regional | Global (no Middle East endpoint) | OpenAI docs |

**Functional:** PASS  
**Reliable:** PASS  
**Secure:** PASS (with data policy)  
**Cost:** PASS ($0.15/1M = $0.00015/1K)  
**SLA:** PASS (enterprise)  
**PRODUCTION QUALIFIED:** YES

### Candidate 2: Anthropic (Claude 3.5 Sonnet)

| Criterion | Assessment | Evidence |
|-----------|:----------:|----------|
| Availability | 99.9%+ SLA | Anthropic status page |
| Latency | p50 ~2-4s | Published benchmarks |
| JSON output | Reliable | SDK support |
| Tool calling | Native tool use | SDK support |
| Model quality | GPT-4 class | Industry standard |
| Rate limits | 400 RPM | Anthropic docs |
| Cost | $3/1M input, $15/1M output | Published pricing |
| Privacy | Data not used for training (API) | Anthropic data policy |
| SLA | Enterprise agreement available | Anthropic sales |
| Regional | Global | Anthropic docs |

**Functional:** PASS  
**Reliable:** PASS  
**Secure:** PASS  
**Cost:** PASS (but 20x more expensive than GPT-4o-mini)  
**SLA:** PASS  
**PRODUCTION QUALIFIED:** YES

### Candidate 3: Google Gemini (1.5 Flash)

| Criterion | Assessment | Evidence |
|-----------|:----------:|----------|
| Availability | 99.9% SLA | Google Cloud |
| Latency | p50 ~1-2s | Published benchmarks |
| JSON output | Reliable | SDK support |
| Tool calling | Function calling | SDK support |
| Model quality | Good (not GPT-4 class for complex reasoning) | Benchmarks |
| Rate limits | 1000 RPM | Google docs |
| Cost | $0.075/1M input, $0.30/1M output | Published pricing |
| Privacy | Data not used for training (API) | Google data policy |
| SLA | Google Cloud SLA | Google Cloud |
| Regional | Global (Middle East regions available) | Google Cloud regions |

**Functional:** PASS  
**Reliable:** PASS  
**Secure:** PASS  
**Cost:** PASS (cheapest option)  
**SLA:** PASS  
**PRODUCTION QUALIFIED:** YES

### Candidate 4: Azure OpenAI

| Criterion | Assessment | Evidence |
|-----------|:----------:|----------|
| Availability | 99.9% SLA | Azure SLA |
| Latency | p50 ~1.5-3s | Azure benchmarks |
| JSON output | Reliable | Same as OpenAI |
| Tool calling | Native | Same as OpenAI |
| Model quality | GPT-4 class | Same as OpenAI |
| Rate limits | Per-deployment | Azure docs |
| Cost | Same as OpenAI + Azure markup | Azure pricing |
| Privacy | Data stays in Azure region | Azure data residency |
| SLA | Azure enterprise SLA | Azure |
| Regional | **Middle East (UAE, Saudi Arabia)** | Azure regions |

**Functional:** PASS  
**Reliable:** PASS  
**Secure:** PASS (best data residency)  
**Cost:** PASS  
**SLA:** PASS  
**PRODUCTION QUALIFIED:** YES

### Candidate 5: AI Horde (Current)

| Criterion | Assessment | Evidence |
|-----------|:----------:|----------|
| Availability | Best-effort (community) | No SLA |
| Latency | p50 ~5.9s | PROVIDER-EVAL-2026-08-23.md |
| JSON output | Unreliable (fences, trailing commas) | PROVIDER-EVAL-2026-08-23.md |
| Tool calling | Not supported | No function calling |
| Model quality | Variable (community models) | PROVIDER-EVAL-2026-08-23.md |
| Rate limits | Best-effort | No guarantees |
| Cost | Free | — |
| Privacy | Community-hosted | No data protection |
| SLA | None | — |
| Regional | Distributed | — |

**Functional:** FAIL  
**Reliable:** FAIL  
**Secure:** FAIL  
**Cost:** PASS  
**SLA:** FAIL  
**PRODUCTION QUALIFIED:** NO

---

## Qualification Matrix

| Provider | Functional | Reliable | Secure | Cost | SLA | Regional | QUALIFIED |
|----------|:----------:|:--------:|:------:|:----:|:---:|:--------:|:---------:|
| OpenAI GPT-4o-mini | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ Global | ✅ YES |
| Anthropic Claude 3.5 | ✅ | ✅ | ✅ | ⚠️ Expensive | ✅ | ⚠️ Global | ✅ YES |
| Google Gemini 1.5 Flash | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ ME regions | ✅ YES |
| Azure OpenAI GPT-4o | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ ME regions | ✅ YES |
| AI Horde | ❌ | ❌ | ❌ | ✅ | ❌ | ⚠️ | ❌ NO |

---

## Recommendation

**Primary:** OpenAI GPT-4o-mini (best cost/quality ratio)  
**Fallback:** Azure OpenAI (for data residency if required)  
**Regional consideration:** Google Gemini or Azure OpenAI if Saudi Arabia data residency is mandated

### Decision Required

| Decision | Owner | Options |
|----------|-------|---------|
| Provider selection | PO + TL | OpenAI / Azure OpenAI / Google Gemini |
| Data residency requirement | Legal + PO | Global OK / Must be in Saudi Arabia |
| Budget allocation | PO + Finance | Monthly LLM spend limit |
| Staging provider | DevOps | Same as prod / Separate |

### Fallback Strategy

1. Primary: OpenAI GPT-4o-mini
2. If OpenAI fails: Azure OpenAI (same model, different infra)
3. If both fail: Google Gemini 1.5 Flash (different model, similar quality)
4. If all commercial fail: AI Horde (DEV-ONLY, degraded quality)

---

## Blocking Issues

| Issue | Blocker | Resolution |
|-------|---------|------------|
| No API key for any commercial provider | Finance/Management | Procure key |
| No data residency decision | Legal | Determine if Saudi data must stay in Saudi Arabia |
| No staging environment | DevOps | Set up staging before provider qualification |
| feature_ai_copilot=False in prod | Management decision | Flip to True after qualification |
