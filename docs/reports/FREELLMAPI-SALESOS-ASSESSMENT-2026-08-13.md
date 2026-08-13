# FreeLLMAPI × SalesOS assessment — 2026-08-13

**Classification:** **production no-go** (unchanged)  
**Product:** SalesOS (`salesos/`)  
**AI flag:** `feature_ai_copilot` remains **False**  
**Live LLM:** **not called** (this assessment is read-only; follow-on wiring is unit-tested with mocks)  
**Alembic:** **not run** (`upgrade head` not performed)

> **Principle:** AI assists. Humans decide. Evidence governs.  
> Do not market this as live AI, copilot GA, or a production LLM path.

---

## 1. Verdict

**Not integrated** (pre-wiring read-only scan: **zero** repo references to FreeLLMAPI / `freellmapi` / the v0.6.9 SHA).

**Valid path (inferred from upstream docs, not from SalesOS runtime proof):** point the existing OpenAI provider at a **self-hosted** FreeLLMAPI instance via OpenAI-compatible `base_url` (`OPENAI_BASE_URL` → `AsyncOpenAI(base_url=…)`). Do **not** call live external LLM providers from this repo’s agents. Do **not** deploy FreeLLMAPI to Railway production. Do **not** flip `feature_ai_copilot`.

Follow-on in the same change-set (after this assessment): a **dev/staging-capable shim** — settings field, factory pass-through, env placeholders, optional compose profile. That is wiring, not integration proof, not live AI.

---

## 2. Method (what was actually checked)

| Check | Result | Label |
|-------|--------|-------|
| Repo grep `FreeLLMAPI` / `freellmapi` / SHA `5597814ebcf4c04ae3d75d78cd6fc89bf8dff8e7` (pre-wiring) | No matches | **verified** |
| `OpenAIProvider` already accepts `base_url` | Yes (`openai_provider.py`) | **verified** |
| Factory `config_map["openai"]` passed `base_url` from settings (pre-wiring) | No — only `api_key` + `model` | **verified** |
| `feature_ai_copilot` default | `False` in `app/config.py` | **verified** |
| Upstream tag `v0.6.9` git SHA | `5597814ebcf4c04ae3d75d78cd6fc89bf8dff8e7` | **verified** (GitHub API, 2026-08-13) |
| SalesOS talks to a running FreeLLMAPI | Not exercised | **not validated** |
| Staging proof of the shim | Not run | **not validated** |

---

## 3. SHA verification (v0.6.9)

| Field | Value |
|-------|--------|
| Upstream | [tashfeenahmed/freellmapi](https://github.com/tashfeenahmed/freellmapi) |
| Tag | `v0.6.9` |
| Commit | `5597814ebcf4c04ae3d75d78cd6fc89bf8dff8e7` |
| Commit message | `release: v0.6.9 (#774)` |
| Date (commit) | 2026-08-07T07:03:14Z |
| Evidence | GitHub API `GET /repos/tashfeenahmed/freellmapi/git/commits/5597814…` and `GET /repos/…/tags` — tag object SHA matches |

**Observation (not a recommendation):** tag `v0.7.0` exists on the same repo (`b81fde193d9aff145864080b6dbeac5e6717f199`) as of this assessment. This work pins **v0.6.9** as specified. No upgrade claim.

---

## 4. What FreeLLMAPI is (upstream; inferred for SalesOS)

Labeled **inferred** from upstream README / `docs/install.md` at tag v0.6.9 — not from SalesOS runtime:

- Self-hosted OpenAI-compatible proxy (`POST /v1/chat/completions`, `GET /v1/models`, embeddings, etc.).
- Default listen: `http://localhost:3001`; OpenAI clients use `base_url=http://localhost:3001/v1`.
- Published image: `ghcr.io/tashfeenahmed/freellmapi` with release tags `v*.*.*`.
- Upstream states it aggregates **free-tier** provider keys behind one unified key, with routing/failover.

**Honesty implication:** hosting the container locally does **not** by itself prevent those keys from calling third-party LLM APIs. SalesOS policy for this work: do not call live external LLM providers. Operators must not load live provider keys into the sidecar for any claimed “offline” or “no live LLM” path.

---

## 5. SalesOS integration path (valid, minimal)

| Layer | Action | Status after follow-on wiring |
|-------|--------|-------------------------------|
| `sdk/config.py` | `openai_base_url: str = ""` | wired |
| Factory openai `config_map` | pass `base_url` (`""` → `None`) | wired |
| `.env.example` / production templates | `OPENAI_BASE_URL=` placeholder only | wired |
| Compose | optional `--profile freellmapi` on **dev** compose; **not** on prod overlay | wired (dev); staging proof residual |
| `feature_ai_copilot` | stays **False** | unchanged |
| Copilot / RAG product APIs | still gated / not claimed live | unchanged |

`OpenAIProvider` already constructed `AsyncOpenAI(..., base_url=base_url)`. The gap was factory/settings, not the client constructor.

---

## 6. Explicit non-claims

- Production / GA **GO** — **NO**
- Live AI / copilot — **NO**
- FreeLLMAPI **integrated** as a product dependency — **NO** (shim only)
- Railway / prod deploy of FreeLLMAPI — **NO** (forbidden)
- Staging end-to-end proof (`OPENAI_BASE_URL` → healthy sidecar → mocked or local completion) — **NO**
- Alembic migrate / `upgrade head` — **not run**
- Calling Groq / Google / OpenAI / other live providers through the shim — **not done, not allowed for this work**

---

## 7. Residual

1. **Compose sidecar** — optional profile on `salesos/docker-compose.yml` only. Default `docker compose up` does not start it. Image pull / health of `ghcr.io/tashfeenahmed/freellmapi:v0.6.9` is **not validated** in this change-set. `FREELLMAPI_ENCRYPTION_KEY` must be supplied by the operator (never committed).
2. **Staging proof** — staging compose does **not** run the sidecar. Pointing a staging backend at `OPENAI_BASE_URL` and recording a non-prod loop is **not validated**.
3. **App `Settings` vs SDK settings** — copilot/RAG paths that use `app.config.settings` (not `sdk_settings`) do not automatically inherit `openai_base_url`. Out of scope for this minimal factory shim.
4. **Policy / budget / observability** — unchanged; empty `base_url` still means the official OpenAI default if a key is present. Do not set production keys + empty URL and call that “FreeLLMAPI”.
5. **Production NO-GO** — unchanged (ga-engineering-audit).

---

## 8. Authority

Executable evidence + [`docs/audit/ga-engineering-audit/`](../audit/ga-engineering-audit/) + [`AI_HONESTY.md`](../audit/ga-engineering-audit/AI_HONESTY.md).  
This file does not overturn Production Readiness / Security scores or the 2026-07-22 **NO-GO**.
