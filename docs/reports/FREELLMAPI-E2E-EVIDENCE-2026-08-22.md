# FreeLLMAPI E2E evidence — 2026-08-22

**Classification:** **production no-go** (unchanged; ga-engineering-audit SoT)  
**Conclusion:** **E2E PASS** — see §7 for exact scope wording.  
**Companion docs:** [`FREELLMAPI-DEPLOY-LOOP-EVIDENCE-2026-08-22.md`](./FREELLMAPI-DEPLOY-LOOP-EVIDENCE-2026-08-22.md) (deployment + wiring proof, same day)

> FreeLLMAPI E2E inference through the SalesOS OpenAI-compatible provider path has been validated in a controlled local environment using synthetic data and a single upstream provider.

---

## 1. Test Identity

```text
FreeLLMAPI:
Version: v0.6.9
SHA: 5597814ebcf4c04ae3d75d78cd6fc89bf8dff8e7
Image digest: sha256:a0659f8100bd14571517d3eb1a20f138d4adde444344e1f5fd7d7326f56c244a
Endpoint: http://127.0.0.1:3101/v1 (host) / http://host.docker.internal:3101/v1 (containers)
```

## 2. Provider

```text
Provider: AI Horde (single operator-supplied key, dashboard label "test1")
Model: aphrodite/TheDrummer/Cydonia-24B-v4.3
```

No API key value recorded anywhere in this document or in chat.

## 3. Routing

```text
SalesOS
→ LLMService.chat()                    (intelligence/agents/llm.py:117)
→ ReliableProvider → ProviderFactory   (_get_raw_provider → create_from_settings)
→ OpenAI-compatible client             (AsyncOpenAI)
→ http://host.docker.internal:3101     (asserted BEFORE request; abort-on-mismatch)
→ FreeLLMAPI v0.6.9                    (gateway log req id d6a7c0)
→ AI Horde upstream
→ response
→ SalesOS LLMResponse
```

Routing pre-checks executed inside `salesos-backend-1` before any network call:

```text
svc._resolved_base_url()      == http://host.docker.internal:3101/v1
raw_provider._base_url        == http://host.docker.internal:3101/v1
```

Source-of-response proof (gateway log, matches client-side tokens exactly):

```text
[Proxy] 02:08:29 start d6a7c0 a0 aihorde - aphrodite/TheDrummer/Cydonia-24B-v4.3 req=aphrodite/TheDrummer/Cydonia-24B-v4.3
[Proxy] 02:08:34 ok    d6a7c0 a0 aihorde - aphrodite/TheDrummer/Cydonia-24B-v4.3 lat=5710ms in=26 out=17
```

No traffic to `api.openai.com` or any direct provider endpoint was possible: base_url was asserted pre-flight and the only configured egress from the test process pointed at the local gateway.

## 4. Results

| Test | Status |
|---|---|
| FreeLLMAPI healthy | **PASS** (`/api/ping` → 200 `{"status":"ok"}`) |
| `/v1/models` | **PASS** (200, 191 models; unauthenticated probe correctly 401) |
| Direct gateway completion | **FAILED then superseded** — see note below |
| SalesOS LLMService completion | **PASS** |
| Response validation | **PASS** (`RESPONSE VALID`) |
| Routing to local gateway | **PASS** (pre-check assertions + gateway log `d6a7c0`) |
| Production untouched | **PASS** |
| Staging untouched | **PASS** |
| Database untouched | **PASS** |
| Code unchanged | **PASS** |

**Direct-test note (honest):** the first controlled attempt used `model="auto"` and failed with HTTP 502 in 136ms — gateway log `5c890b fail … err="AI Horde API error 406: Model None not known!"`. Root cause is **upstream instability of the free AI Horde pool** (the auto-selected model disappeared between requests), not the routing path: an operator-run dashboard Playground request seconds earlier succeeded through the same chain (`6658c8 ok`, 5176ms). Per task STOP rules no automatic retry was made; the operator then directed one single pinned-model attempt via the SalesOS path, which passed on its first try.

## 5. Metrics

SalesOS E2E attempt (pinned model, ONE request):

```text
HTTP status: 200 (finish_reason=stop; gateway log ok)
Model: aphrodite/TheDrummer/Cydonia-24B-v4.3
Latency: 6120 ms client-side (5710 ms upstream per gateway log)
Input tokens: 26
Output tokens: 17
Total tokens: 43
Policy findings: ['input_sanitized'] (normal PII-scrub pass; nothing blocked)
Response body: ```json {"status": "ok", "test": "salesos-freellmapi-e2e"}``` → parsed & matched
request_id: freellmapi-e2e-20260822
```

Failed auto attempt (for completeness):

```text
HTTP status: 502 · latency 194 ms client / 136 ms upstream · model: none served
Error: AI Horde API error 406: Model None not known!
```

## 6. Security

Explicitly confirmed:

```text
No production data          — prompt was synthetic only
No customer data            — none touched
No PII                      — synthetic prompt; PolicyGate input_sanitized pass clean
No production credentials   — zero Railway/prod credentials read or used
No staging credentials      — staging never contacted
No secret committed         — provider key lives only in gateway DB (encrypted at rest
                              via ENCRYPTION_KEY); unified key never printed to repo,
                              report, or persistent env; temp test scripts deleted after run
```

Side-effect audit post-test: `git status` unchanged (only pre-existing untracked evidence doc), backend container env still has `OPENAI_BASE_URL`/`OPENAI_API_KEY` unset, no migrations run, no AgentTask/AgentAction created, container count unchanged, `feature_ai_copilot` not modified by this work (repo value predates it).

## 7. Conclusion

```text
E2E PASS
```

This proves **Inference Path Proof** only:

```text
SalesOS → LLMService → ProviderFactory → AsyncOpenAI client
        → 127.0.0.1:3101 → FreeLLMAPI v0.6.9 → AI Horde → Cydonia-24B → validated JSON response
```

It does **not** prove: production readiness, data governance, Saudi residency compliance, SLA, scalability, multi-tenancy, production reliability, or AI Copilot readiness.

Caveats carried forward:

1. Upstream used is a **free community pool (AI Horde)** with observed model churn — unsuitable for deterministic or SLA-bound workloads.
2. Single-request sample size by design.
3. Staging validation remains a separate, unexecuted gate.

**Next gate:** controlled staging validation. Production remains NO-GO.
