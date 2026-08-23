# AI Live Preview decision — 2026-08-22

> **AI Live Preview: GO** (local dev stack only)  
> **AI Production / GA: NO-GO** (unchanged)

## What was enabled (local-only, gitignored `salesos/.env`)

```text
FEATURE_AI_COPILOT=true
OPENAI_BASE_URL=http://host.docker.internal:3101/v1
OPENAI_API_KEY=<FreeLLMAPI unified key, local gateway only>
OPENAI_MODEL=aphrodite/TheDrummer/Cydonia-24B-v4.3   (test1 / AI Horde, pinned)
```

Backend container recreated; runtime verified: flag=True, base_url=gateway.
Production smoke through the real construction path (`copilot.py:_build_coordinator`): finish=stop, Cydonia-24B, valid JSON (`live-preview-smoke-v2`).

## Known limitation (documented, not fixed)

`ProviderFactory.create_from_settings("openai")` falls back to hardcoded `"gpt-4o-mini"` when no explicit model override is passed (factory.py:52). Paths constructing bare `LLMService()` (agent_runtime, RAG service) will request gpt-4o-mini → gateway routing-exhausted under the current single-key pool. The **copilot UI path passes the configured model explicitly and works**. Fix belongs to a separate minimal-wiring change, not this preview.

Embeddings (`text-embedding-3-large`) cannot route through the AI-Horde-only pool → RAG/embedding features are non-functional in this preview. Expected.

## Addendum (same day) — FE build gate fix

The UI gate is dual: `useAiCopilotEnabled` requires `NEXT_PUBLIC_FEATURE_AI_COPILOT=true`
**baked at build time** + backend `/api/v1/copilot/status` returning true with auth.
The runbook (`docs/ops/AI_COPILOT_ACTIVATION.md`) Step 1 does not reach Docker builds
because `frontend/.dockerignore` excludes all `.env*`.

Fix applied:
- `salesos/frontend/Dockerfile`: declared `ARG NEXT_PUBLIC_FEATURE_AI_COPILOT=` (empty
  default = disabled; GA honesty preserved) and passed it into the build-stage ENV.
- Rebuild command (local only):
  `docker compose build --build-arg NEXT_PUBLIC_FEATURE_AI_COPILOT=true frontend && docker compose up -d frontend`

Evidence: compiled hook chunk shows dead-code elimination of the disabled branch and a
direct `/api/v1/copilot/status` fetch; raw `NEXT_PUBLIC_FEATURE_AI_COPILOT` string absent
from client bundles. Rollback = rebuild without the build-arg.

## Kill switches

```powershell
docker stop freellmapi-local                                  # instant: gateway off, AI calls fail fast
# config kill: set FEATURE_AI_COPILOT=false in salesos/.env, then:
docker compose -f C:\Users\raghe\Documents\Muhide\salesos\docker-compose.yml up -d backend
```

## Constraints in force

Demo/synthetic data only · no customer data · no PII · no production business decisions · no agent actions with side effects · test1/AI Horde is NOT a production baseline (see qualification evidence) · paid-provider fallback remains the staging-baseline plan.

## Observability during preview

- SalesOS telemetry UI: `/copilot/telemetry` (calls, success rate, latency p50/p95/p99)
- Gateway analytics dashboard: http://127.0.0.1:3101 (per-request latency/tokens/cost)
- Gateway raw log: `docker logs freellmapi-local -f`
