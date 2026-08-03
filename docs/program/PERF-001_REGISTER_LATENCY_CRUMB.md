# PERF-001 — Register hang / latency (Railway field)

> **Status:** OPEN (cancellable-wait tip shipping)  
> **Honesty:** Not Production GO. Do not weaken auth/CSRF/RBAC.

## Field evidence (tip `8c7d65e` / deploy `b95db185` tip-live after stale-image redeploy)

- HTTP **499** (60–180s); hang ~30s+ **with or without** `tenant_id` (no skip pivot)
- **Last step = NONE** on earlier probes — zero lines: `register_ok` / `register_timeout` / `steps=` / `set_config` / `tenant_insert` / `create_user`
- DB: no new users/tenants; `deleted_at` + `provisioning_status` present
- Ruled out: hash/save/audit/publish/tokens; missing columns; completed tenant_insert
- Chicken-egg: `/tenants` + invite are 401; no public signup alternate

**Likely:** pre-first `_mark` — uncancellable `set_config`|`tenant_insert`, or `get_db`/middleware before handler.

## Tip fix (post-`8c7d65e`)

1. `register_enter` in `get_register_db` **before** pool checkout / set_config
2. Per-step `register_step` + stdout flush; `register_timeout step=…` on fail
3. App engine `command_timeout=10`; `abort_db_session` (asyncpg terminate)
4. Bounded `get_db` checkout / ContextVar set_config / commit
5. Suspension skip on public identity auth; Redis rate-limit 2s bound
6. Explicit register commit; no same-session side-effect `create_task`

## DevOps probe

Expect `register_enter` then `register_step` / `register_ok` or `register_timeout step=…` / **503** within ~10s (not silent 499).  
**Do not claim field fix until tip-live register result is reported.**
