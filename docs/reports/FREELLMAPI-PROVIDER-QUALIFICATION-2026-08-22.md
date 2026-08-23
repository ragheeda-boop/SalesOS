# FreeLLMAPI Provider Qualification — run 1: test1 — 2026-08-22

**Classification:** **production no-go** (unchanged)  
**Gate context:** E2E Gate **CLOSED** (`FREELLMAPI-E2E-EVIDENCE-2026-08-22.md`) → this file starts **Provider Qualification** → then Staging → Production Review.  
**Scope:** single provider run against the already-configured operator key `test1`. Providers `qual-a/b/c` deferred (operator will supply later).

---

## 1. Candidate under test

```text
Provider label: test1
Platform:       AI Horde (free community pool)
Model:          aphrodite/TheDrummer/Cydonia-24B-v4.3
Path:           SalesOS LLMService → Factory → AsyncOpenAI → host.docker.internal:3101/v1 → FreeLLMAPI v0.6.9 → AI Horde
```

## 2. Protocol (as approved)

| Item | Value |
|------|-------|
| Requests | 5 total = 1 warm-up + 4 measured, 20 s gaps |
| Prompt | same synthetic JSON prompt as E2E |
| max_tokens | 100 |
| Route | `LLMService.chat()` always (production path) |
| request_ids | `qual-test1-1..5` |
| Retry policy | none per-attempt; internal `ReliableProvider` retries monitored via gateway logs |

## 3. Results (measured requests)

| # | finish | latency (client) | upstream (gateway) | tokens in/out | JSON valid |
|---|--------|------------------|--------------------|---------------|------------|
| warm-up | stop | 4893 ms | 4433 ms | 26/17 | ✅ |
| measure-1 | stop | 13173 ms | 13151 ms | 26/17 | ✅ |
| measure-2 | stop | 4955 ms | 4931 ms | 26/17 | ✅ |
| measure-3 | stop | 6110 ms | 6094 ms | 26/17 | ✅ |
| measure-4 | stop | 5685 ms | 5669 ms | 26/17 | ✅ |

Gateway-side correlation: exactly 5 `start`/`ok` pairs for the window, token counts match client usage on every request → **zero hidden retries**, source-of-response intact.

## 4. Verdict vs acceptance thresholds

| Criterion | Threshold | Actual | Verdict |
|-----------|-----------|--------|---------|
| Success rate | ≥ 4/5 | 5/5 | ✅ PASS |
| JSON validity | ≥ 90% | 100% | ✅ PASS |
| Latency p50 | < 3 s | ≈ 5.9 s | ❌ FAIL |
| Latency p95/max | < 8 s | 13.2 s outlier | ❌ FAIL |
| Model stability (in-run) | consistent | consistent | ✅ PASS |
| Rate-limit behavior | record only | none observed | n/a |

## 5. Qualification decision

```text
test1 / AI Horde / Cydonia-24B → QUALIFIED FOR DEV PLAYGROUND ONLY
                                 NOT RECOMMENDED AS STAGING BASELINE
Reason: latency SLA failure (p50 ~2x threshold, 13 s tail)
        + known model-churn risk (406 incident recorded in E2E evidence §4)
```

What this provider **did prove**: integration path stability across a burst of 5 sequential requests, perfect structured-output compliance this session, no rate-limit interference at this volume.

## 6. Qualification matrix status

| Provider | Label | Status |
|----------|-------|--------|
| AI Horde | `test1` | ⚠️ Dev-only (this document) |
| TBD (Groq/OpenRouter/Google candidates) | `qual-a/b/c` | ⏳ Awaiting operator keys |

## 7. Next

1. Operator adds 2–3 stable-provider keys (`qual-a/b/c`) via dashboard.
2. Same protocol runs per provider; winner becomes **Staging baseline** candidate.
3. ToS/cost/commercial-use review per provider remains a human decision (agent can gather public data on request).

Production remains **NO-GO** throughout.
