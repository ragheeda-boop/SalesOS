# IL-2A — live evaluate HTTP hang probe (2026-08-12)

**Scope:** Railway `responsible-comfort` / production · deploy SHA `4f52f68` · API `salesos-production-96c0.up.railway.app` · tenant `326e0825-…172b`  
**Decisions cited:** `9804dd5b-…`, `29ae975c-…` (both `recommend_call`, no new AgentTask)  
**This note:** read-only prod probe for fix sister. No secrets. No alembic. No `feature_ai_copilot`.

## Verdict

| Question | Answer |
|----------|--------|
| Same-request vs two-request (80ms log vs 20–60s WARN)? | **Two-request.** Fast evaluate (~77–137ms, often **no** client `X-Request-ID`) creates the decision row; a second evaluate (**with** `request_id`) hangs and WARNs ~20–60s later. |
| Do response headers arrive on the hang? | **No.** Railway HTTP: `499`, `txBytes=0`, detail `client has closed the request before the server could send a response`. Connection stayed open upstream until client abort (~25s in sampled case). |
| AgentTask within 10–30s? | **Never** for these decisions (and **`decision.created` store count = 0 all-time**). |
| Is `create_task` publish in the running image? | **Yes** — `/app/runtime/decision_runtime/__init__.py:108` `asyncio.get_running_loop().create_task(_run())`, safety timeout **60s**. Router still `return result` (no Starlette `BackgroundTasks` on this SHA). |

## Evidence (short)

1. **Image / SHA:** production SalesOS active deploy commit `4f52f688…`; container file matches `create_task` + `_EVENT_PUBLISH_SAFETY_TIMEOUT_SECONDS = 60.0`.
2. **Paired app logs (same user/tenant):** e.g. `15:12:29Z` evaluate steps + middleware `latency_ms=106.5` (no `request_id`) → decision `9804dd5b` `created_at=15:12:29.913Z`; then middleware WARN `request_id=cbe0a058-…` `latency_ms=24845` with **no** second evaluate step cluster. Similar pairs at `15:05:51` (~137ms / ~59300ms → decision `29ae975c`) and `15:11:13` (~77ms / ~19888ms).
3. **Edge HTTP (hang only in recent buffer):** `POST …/decision/evaluate` → **499**, `totalDuration≈25024`, **`txBytes=0`**.
4. **AgentTask / events:** `9804dd5b` company `2f3b1426-…` → **0** `agent_tasks`; `29ae975c` company `eb67ce55-…` → only **older COMPLETED** research tasks (10:45Z / 14:16Z), none after the evaluate. `domain_events`: **`decision.created` count = 0**; newest row in table is **2026-08-08** (bus type env `in_memory` → `EventRuntime` + Postgres store).
5. **ASGI note:** `AuditMiddleware` does post-response DB work after `send` (can delay stack unwind). `RequestLoggingMiddleware` is *inside* Audit and timestamps handler+inner only — so a **60s WARN with no evaluate steps** is a **second** request stuck **before** `decision_runtime.evaluate enter`, consistent with **pool checkout starvation** while the first request’s background `publish` (up to **60s** `wait_for`) holds connections (`pool_timeout=30` already documented as 499-class). Not a BaseHTTPMiddleware body-buffer of the NBA JSON on the fast path.

## Top fix hypothesis (for sister)

1. **Primary (AgentTask never):** `EventRuntime.publish` **store path fails or early-returns before fan-out** (`except Exception: return lifecycle` skips subscribers) — explains **zero** `decision.created` rows and **no** IL-2A `AgentTask`. Fix append/`id`/payload and **still fan-out in-process on store failure** (or fail loud with metrics).  
2. **Primary (HTTP 499 / no headers):** Background `create_task(publish)` still **contends the shared async DB pool** for up to ~60s; a **retry/parallel evaluate** then blocks in middleware/deps **before** the route → **no headers**, client 20–60s timeout. Isolate publish (separate pool / queue / shorter bounded fan-out) and/or defer with `call_soon` so the NBA response flush wins the event loop; do **not** move hang onto Starlette `BackgroundTasks` without proving edge flush (tasks run before the ASGI call fully returns).  
3. **Hygiene:** Make audit logging non-blocking; emit `event_publish_*` / IL-2A fields so Railway JSON `message` is not empty.

**Validation:** **PASS** on live prod — see [`IL-2A-HTTP-PRODUCTION-GATE.md`](./IL-2A-HTTP-PRODUCTION-GATE.md) (deploy `9304265`, light validated). Hang-fix SHAs listed there (`69c6e835`, non-blocking publish, fail-open store).
