# PERF-001 — Register hang / latency (Railway field)

> **Status:** Field tip-live OK on `8c7d65e` / Active `b95db185` (stale-image false FAIL cleared). Observability follow-up `d4aa0b9` on master (not required for field unblock).  
> **Honesty:** Not Production GO. Do not weaken auth/CSRF/RBAC.

## Field result (2026-08-03)

| Deploy | Tip markers | Register | Notes |
|--------|-------------|----------|-------|
| Prior Active SUCCESS | stale image (not tip) | hang / 499 | False FAIL — SUCCESS ≠ tip-live |
| `b95db185` | `8c7d65e` tip-live | **201 ~2s + token** | load/meta 200; hang probes were stale |

Chicken-egg (no public `/tenants`/invite) stands for alternate mint paths; register path itself is tip-live OK.

## Follow-up tip `d4aa0b9` (nice-to-have, already on master)

`register_enter` before `get_db`, `command_timeout` / `abort_db_session`, bounded checkout/set_config/commit, suspension skip on public identity auth, Redis rate-limit 2s bound. Deploy when convenient — **not a field blocker**.

## Deploy health gate (DevOps-owned) — CLOSED/covered

Backend Health Gate in `deploy.yml` (landed `c0e4f6a`, present on tip `654b33e`) already rejects stale Active: `/health` 200 + `uptime_seconds` < 900 + `/api/v1/load/meta` ≠ 404. Log-stream false-RED closed @ `654b33e`. Optional SHA tip-marker beyond load/meta presence is **not** an open residual. No Production GO.

## Standby

Field tip-live + HTTP harness already PASS. Resume only on BE-caused harness fail. No Production GO.
