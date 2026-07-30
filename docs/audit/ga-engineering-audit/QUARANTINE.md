# QUARANTINE / Dead Code Register — SalesOS / AQLIYA

**Purpose:** Track removed, superseeded, or quarantined code to prevent re-introduction.
**Authority:** ga-engineering-audit.
**Last updated:** 2026-07-30 (Wave 22 remediation).

---

## Removed files

| File | Removed in | Reason | Verification |
|------|------------|--------|-------------|
| `backend/app/middleware_setup.py` | P0 #4 (2026-07-30) | Dead code; duplicate of `boot/middleware.py` | grep for imports → 0 matches |
| `backend/app/routers/router_registry.py` | P1 #14 (2026-07-30) | Orphan duplicate of `boot/routers.py`; 151 lines; no imports | grep for `router_registry` → 0 matches; contained 3 security regressions (no auth on notifications, MCP, GraphQL) |
| `cookies.txt` (root) | P0 #1 (2026-07-30) | Leaked credentials file | gitignored; deleted; git history contains prior versions |
| `login.json` (root) | P0 #1 (2026-07-30) | Leaked credentials file | gitignored; deleted |
| `salesos/railway-status.json` | P0 #1 (2026-07-30) | Infrastructure status file | gitignored; deleted |

## Superseeded documentation (retained for history with SUPERSEDED banners)

| File | Verdict | Banner applied |
|------|---------|----------------|
| `docs/vnext/reports/GO_NO_GO_DECISION.md` | Claims GO — **false** (audit says NO-GO) | Yes (2026-07-22) |
| `docs/vnext/reports/GA_CHECKLIST.md` | Claims 15/15 PASS — **false** | Yes (2026-07-22) |
| `docs/vnext/reports/PRODUCTION_READINESS_REPORT.md` | Claims NO-GO (consistent) | Yes (2026-07-22) |
| `docs/vnext/reports/OPEN_ISSUES.md` | Superseeded by APPENDIX-C | Yes (2026-07-22) |
| `docs/vnext/reports/FINAL_RELEASE_NOTES.md` | GA shipping claims — do not use | Yes (2026-07-22) |
| `docs/vnext/reports/gates/G04_AI_VALIDATION.md` | Claims PASS 98% — **false** | Yes (2026-07-22) |

## Deleted code patterns (do not restore)

1. **`jwt.encode(payload, secret, algorithm="HS256")`** — removed across 13 files (tests, configs, docs, K8s, docker-compose). Use `create_access_token()` / `create_rs256_token_payload()` instead.
2. **Raw f-string SQL queries** — 19 sites audited. All guarded by hardcoded allowlists. If new SQL patterns are added, use the same allowlist pattern, not raw interpolation.
3. **Middleware in `routers/router_registry.py`** — all router registration goes through `boot/routers.py`. Do not create a second registry.
4. **Empty `__init__.py` files** — all package markers should have explicit `__all__` exports.

## Integrity rules

- Do not re-create `router_registry.py` or `middleware_setup.py`
- Do not revert `jwt_algorithm` to `HS256` in `config.py` or any `.env`
- Do not remove `feature_ai_copilot=False` guard without concurrent AI audit wiring
- Do not remove SUPERSEDED banners from vNext reports
