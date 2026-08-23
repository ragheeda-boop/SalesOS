# FreeLLMAPI deploy + SalesOS dev loop — evidence — 2026-08-22

**Classification:** **production no-go** (unchanged; ga-engineering-audit SoT)  
**Product:** SalesOS (`salesos/`)  
**Validation honesty:** **build validated** (live local proofs below; no generation, no staging)  
**Supersedes residuals:** [`FREELLMAPI-SALESOS-ASSESSMENT-2026-08-13.md`](./FREELLMAPI-SALESOS-ASSESSMENT-2026-08-13.md) §7 items 1 (partially) — see Updated residuals.

> Principle: AI assists. Humans decide. Evidence governs.  
> This is a **local/staging gateway deployment + wiring proof**, not live AI, not GA.

---

## 1. Verdict

FreeLLMAPI **v0.6.9** deployed as a **standalone local container** on the operator machine and proven reachable end-to-end from the running SalesOS dev stack through every layer of the OpenAI-compatible shim — **with zero file changes to SalesOS and zero service restarts** (one-off `docker exec` probes only).

## 2. Deployment evidence

| Check | Result | Label |
|-------|--------|-------|
| Source pin | clone @ `5597814ebcf4c04ae3d75d78cd6fc89bf8dff8e7`, tag `v0.6.9` — `git rev-parse HEAD` match | **verified** |
| Image | `ghcr.io/tashfeenahmed/freellmapi:v0.6.9`, digest `sha256:a0659f8100bd…` | **verified** |
| Container | `freellmapi-local` — Up (**healthy**) | **verified** |
| Port | `127.0.0.1:3101->3001/tcp` — **localhost bind only**, not LAN-exposed | **verified** |
| Health | `GET http://127.0.0.1:3101/api/ping` → **200** `{"status":"ok"}` | **verified** |
| Auth enforced | `/v1/models` without key → **401** | **verified** |
| Auth accepted | `/v1/models` with unified key → **200, 191 models** | **verified** |
| Encryption key | generated locally, stored in untracked temp `.env.local`; never committed | **verified** |
| Work dir | `%TEMP%\opencode\freellmapi-v069\` (compose: `freellmapi.local.yml`) | **verified** |

**Port deviation (3001 → 3101):** host port 3001 is occupied by `salesos-grafana-1` (3001→3000). Operator approved alternative port. Container-internal port remains 3001; only the host publish moved. The SalesOS compose definition (`salesos/docker-compose.yml:430`) keeps `127.0.0.1:3001` — if that profile is ever used instead, the Grafana conflict applies there too.

## 3. SalesOS dev-loop evidence (from inside `salesos-backend-1`)

Executed as a single one-off process via `docker exec -i` with env injected per-process (`OPENAI_BASE_URL`, unified key). Running backend service untouched.

| Stage | Layer | Proof |
|-------|-------|-------|
| 1 | Network reachability container→gateway | urllib GET `{BASE}/models` → **200, 191 models** |
| 2 | `sdk.config.sdk_settings.openai_base_url` | resolved == `http://host.docker.internal:3101/v1`; `resolve_openai_base_url()` matches |
| 3 | `ProviderFactory.create_from_settings("openai")` → `OpenAIProvider` | `_base_url` == gateway URL (factory.py:46 path; NOT raw `create()`) |
| 4 | Live call through SalesOS provider layer (`AsyncOpenAI` client) | `client.models.list()` → **200, 191 models** |
| 5 | Agent entry `intelligence.agents.llm.LLMService._get_raw_provider()` | `_base_url` inherited == gateway URL |

Unit-test parity: stages 3/5 mirror `tests/unit/intelligence/providers/test_openai_base_url.py::test_factory_passes_openai_base_url` / `test_llm_service_inherits_app_openai_base_url` — here proven **live against a real OpenAI-compatible server**, mocked there.

## 4. Explicit non-claims

- Live LLM **generation** — **NOT exercised** (zero provider keys loaded; any real completion needs an operator-loaded provider key = separate human decision)
- Staging proof (`OPENAI_BASE_URL` on staging backend) — **NOT run**
- `feature_ai_copilot` — **not modified by this work**
- SalesOS files changed by this work — **none** (no code, no env, no migrations, no schema)
- Railway / prod deploy of FreeLLMAPI — **NO** (forbidden)
- FreeLLMAPI integrated as product dependency — still **shim + local sidecar only**

## 5. Updated residuals (vs 2026-08-13 assessment §7)

1. ~~Compose sidecar image pull / health not validated~~ → **CLOSED (dev, standalone)** — this document. Repo-profile variant (`--profile freellmapi`) still unproven and blocked by Grafana port conflict unless remapped.
2. **Staging proof** — still open (needs approval; staging compose intentionally has no sidecar).
3. App `Settings` inheritance — already wired (`ad2b227`); re-proven live at stage 5.
4. Policy/budget/observability unchanged; empty `base_url` still means official OpenAI default if a key is present.
5. Production NO-GO — unchanged.
6. **Generation E2E** — new residual: prove one completion through the shim after operator loads a provider key (human-gated).

## 6. Operations cheat-sheet

```powershell
# location
Set-Location "$env:TEMP\opencode\freellmapi-v069"
docker logs freellmapi-local -f                 # logs (unified API key + setup code appear once)
docker stop freellmapi-local                    # stop
docker start freellmapi-local                   # start
docker compose -f freellmapi.local.yml down     # remove (keeps volume)
```

SalesOS usage (when desired): set `OPENAI_BASE_URL=http://host.docker.internal:3101/v1` (+ unified key as `OPENAI_API_KEY`) on the backend environment. Do not commit either value.

**Authority:** executable evidence above + ga-engineering-audit. This file does not overturn Production Readiness / Security scores or the NO-GO classification.
