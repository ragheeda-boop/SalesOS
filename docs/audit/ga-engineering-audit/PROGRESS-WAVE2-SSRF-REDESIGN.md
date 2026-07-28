# PROGRESS — Wave 2 SSRF redesign closeout (code)

**Date:** 2026-07-28  
**Related:** [PROGRESS-WAVE2-RESIDUALS.md](./PROGRESS-WAVE2-RESIDUALS.md), [runbooks/staging-ssrf-pentest.md](./runbooks/staging-ssrf-pentest.md)  
**Validation:** light validated (unit path); staging pentest **OPEN**  
**Production secure:** **false**

## Code changes

1. Delivery always calls `analyze_webhook_url(..., resolve_dns=True)`.
2. Delivery refuses empty `allowed_ips` (no hostname-only dial).
3. `_PinnedIPBackend` accepts multiple IPs and fails over on connect errors.
4. `build_pinned_async_transport` takes `tuple[str, ...] | str`.
5. Unit coverage: multi-IP failover test in `tests/unit/test_webhooks.py`.

## Still OPEN (ops)

- Staging cloud pentest per `runbooks/staging-ssrf-pentest.md` — **BLOCKED** on credentials/VPS
- Full redesign away from httpx private `_pool` coupling — deferred; pin path remains defense-in-depth

## Honesty

Does **not** flip GA to GO. Security residual “staging pentest” remains until executed on live staging.
