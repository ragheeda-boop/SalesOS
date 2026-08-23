# Provider Evaluation — FreeLLMAPI / AI Horde — 2026-08-23

**Agent:** Agent-D (synthesis from existing evidence; no new provider runs)  
**Sources:**  
- [`FREELLMAPI-DEPLOY-LOOP-EVIDENCE-2026-08-22.md`](./FREELLMAPI-DEPLOY-LOOP-EVIDENCE-2026-08-22.md)  
- [`FREELLMAPI-E2E-EVIDENCE-2026-08-22.md`](./FREELLMAPI-E2E-EVIDENCE-2026-08-22.md)  
- [`FREELLMAPI-PROVIDER-QUALIFICATION-2026-08-22.md`](./FREELLMAPI-PROVIDER-QUALIFICATION-2026-08-22.md)

**Classification:** **production no-go** (unchanged; ga-engineering-audit SoT)

---

## Executive verdict

| Gate | Status | Honest label |
|------|--------|--------------|
| Deploy + wiring | **PASS** | build validated (local sidecar v0.6.9, SalesOS OpenAI shim reachable) |
| E2E inference (1 request) | **PASS** | light validated (synthetic prompt, pinned model) |
| Provider qualification (`test1`) | **FAIL SLA** | Dev playground only — not staging baseline |
| Staging provider path | **NOT RUN** | not validated |
| Production GO | **NO-GO** | production no-go |

**Recommended operator action:** add 2–3 stable-provider keys (`qual-a/b/c`); re-run qualification protocol; human ToS/commercial-use review per winner.

---

## What was proven

1. **Routing integrity** — SalesOS `LLMService.chat()` → `ReliableProvider` → `AsyncOpenAI` → `host.docker.internal:3101/v1` → FreeLLMAPI v0.6.9 → AI Horde; pre-flight `base_url` assertions; gateway log correlation (`d6a7c0`).
2. **Structured output** — pinned `aphrodite/TheDrummer/Cydonia-24B-v4.3` returned parseable JSON on SalesOS path (E2E §5).
3. **Burst stability** — qualification run: 5/5 success, 100% JSON validity, zero hidden retries (qual doc §3).
4. **Safety boundaries** — no prod/staging credentials, no customer data, no secrets committed (E2E §6).

---

## What failed or remains open

| Issue | Evidence | Impact |
|-------|----------|--------|
| Latency SLA | p50 ≈ 5.9 s (threshold &lt; 3 s); max 13.2 s (threshold &lt; 8 s) | **FAIL** — unsuitable for interactive copilot SLA |
| Model churn | AI Horde 406 `Model None not known!` on `auto` route (E2E §4) | **FAIL** — free pool nondeterministic |
| Unparseable JSON storms | AGENTS.md §20 — Cydonia-24B frequent malformed JSON in live copilot | **DEV ONLY** — product degrades honestly but UX poor |
| Generation not exercised in deploy loop | Deploy doc §4 — wiring only until operator loads key | **OPEN** at 2026-08-22; closed by E2E same day |
| Staging `OPENAI_BASE_URL` | Deploy doc §5 residual #2 | **OPEN** |
| `qual-a/b/c` candidates | Qual doc §6 — awaiting operator keys | **OPEN** |

---

## Qualification matrix (as of 2026-08-22)

| Provider label | Upstream | Model | Status |
|----------------|----------|-------|--------|
| `test1` | AI Horde | Cydonia-24B-v4.3 | ⚠️ **Dev playground only** (latency + churn) |
| `qual-a` | TBD (Groq/OpenRouter/Google) | TBD | ⏳ Awaiting keys |
| `qual-b` | TBD | TBD | ⏳ Awaiting keys |
| `qual-c` | TBD | TBD | ⏳ Awaiting keys |

---

## GO / NO-GO decision record

```text
STAGING BASELINE PROVIDER:  NO-GO (no qualified candidate)
PRODUCTION LLM PROVIDER:    NO-GO
DEV / LOCAL PLAYGROUND:     CONDITIONAL GO (test1 only, synthetic data, no SLA claim)

Reason: Only evidence is a free community pool with SLA failure, model churn,
        and observed JSON reliability issues in copilot paths. No stable
        commercial provider has been qualified.
```

---

## Relationship to SalesOS AI gates

- `feature_ai_copilot` may be `True` in repo for Phase 3 gate evidence — **does not** overturn provider NO-GO for production.
- Grounded intelligence agents (Phase 1–3B) intentionally degrade to INSUFFICIENT / UNKNOWN when provider fails — honest per `AI_HONESTY.md`.
- Replacing DEV-only Horde path remains **P2 human-blocked** (DevOps — no alternative provider available per AGENTS.md §24).

---

## Next gates (human-owned)

1. Operator supplies `qual-a/b/c` keys via FreeLLMAPI dashboard.
2. Repeat qualification protocol (5 requests, 20 s gaps, same JSON prompt, `LLMService.chat()` path).
3. Winner → staging validation (`OPENAI_BASE_URL` on staging backend) — separate gate, not executed.
4. ToS / residency / commercial-use sign-off per provider — outside agent scope.

**Production remains NO-GO** until ga-engineering-audit overturned with evidence.
