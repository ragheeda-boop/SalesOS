# Wave A Security Review Report

> **Reviewer**: Security Reviewer
> **Date**: 2026-07-16
> **Status**: Approved

## Quality Gate Results

| Gate | Result | Evidence |
|------|--------|----------|
| G-A.1 | ✅ | `webhooks/router.py:24` — `dependencies=[Depends(verify_token), Depends(get_current_tenant_id)]` at router level, covering all 6 routes (list/create/get/update/delete subscriptions + delivery logs + retry). No bypass paths found. |
| G-A.2 | ✅ | `graphql/schema.py:14-31` — `get_context()` validates JWT via `decode_access_token()` (same function as FastAPI `verify_token` in `dependencies.py:11-17`). Both code paths converge at `service.py → jwks.py`. Additional hardening: QueryDepthLimiter(max_depth=8), MaxTokensLimiter(max_token_count=500), GraphiQL disabled in production (`schema.py:41`). |
| G-A.3 | ✅ | `identity/jwks.py:103-110` — JWKS returns single RS256 key (`kty: RSA`, `alg: RS256`, `kid: v2-rs256`) with non-empty `n` and `e` fields. Old empty HS256 entry removed. Key generated at 4096-bit RSA. |
| G-A.4 | ✅ | All Neo4j Cypher values use `$param` syntax. Structural elements (labels, rel types, property keys) validated via `_validate_cypher_identifier()` regex `^[A-Za-z_][A-Za-z0-9_]*$` in both `sdk/graph.py:23-27` and `knowledge_graph_runtime/__init__.py:31-34`. SQL queries remain using `text()` with `:param` binding — out of scope for SEC-016. |
| G-A.5 | ✅ | `.env.example` — No real default credentials. `GRAFANA_PASSWORD=CHANGE_ME_USE_STRONG_PASSWORD`, `POSTGRES_PASSWORD=CHANGE_ME_IN_PRODUCTION`, `NEO4J_PASSWORD=CHANGE_ME_IN_PRODUCTION`, `JWT_SECRET_KEY=CHANGE_ME_USE_OPENSSL_rand_hex_32`. All placeholders. |
| G-A.6 | ✅ | See findings and verdict below. |

## Findings

### No blocking issues found

All 6 security tasks (SEC-001, SEC-003, SEC-004, SEC-016, SEC-005, API Key ADR) have been correctly implemented and verified.

### Observations (non-blocking)

1. **HS256 fallback for legacy tokens** (`jwks.py:146-153`): The `decode_token` function falls back to HS256 symmetric verification for tokens signed before the RS256 migration. This is acceptable as a transitional measure but should be removed once all legacy tokens expire (max 7 days for refresh tokens). Recommend tracking in Technical Debt Register with a removal deadline.

2. **RS256 private key stored on disk** (`jwks.py:14-16`): Keys are stored in `_keys/rsa_private.pem` with `0o600` permissions. Adequate for development/staging but must be moved to a secrets vault (HashiCorp Vault, AWS Secrets Manager, or Kubernetes Secrets) before GA production launch.

3. **`_validate_cypher_identifier` duplication**: Both `sdk/graph.py` and `knowledge_graph_runtime/__init__.py` define identical functions. Consider consolidating into a shared utility in `sdk/` for Wave B or a future refactor sprint.

4. **SQL f-string queries outside scope**: Several SQL queries across the codebase use f-strings for table names and WHERE clause construction (notably `activity_runtime/__init__.py:228`). These are not Neo4j/Cypher queries and thus outside SEC-016 scope, but should be reviewed in a future security pass.

### ADR-0031 Assessment

| Criterion | Verdict |
|-----------|---------|
| Decision clarity | Clear — JWT vs API key comparison across 6 factors |
| Soundness | Correct — admin CRUD benefits from JWT's tenant scoping, audit trail, and key rotation |
| Completeness | Comprehensive — acknowledges future incoming webhook receiver would benefit from API keys |
| **Overall** | **Accept** — no change required |

## Recommendations

1. **Schedule HS256 fallback removal**: Add a calendar reminder or ticket for 7 days post-deployment to remove the HS256 legacy fallback path (`jwks.py:146-153`).
2. **Plan vault migration**: Create a task in the Technical Debt Register to move RS256 private key to production secrets vault before GA launch.
3. **Consolidate `_validate_cypher_identifier`**: Refactor into a shared `sdk/cypher.py` utility to eliminate code duplication.
4. **SQL injection audit**: Schedule a separate security pass to audit all SQL f-string patterns for potential injection vectors.

## Verdict

**Approved** — All 6 quality gates pass. The Wave A Security Hardening work meets the required security standards. No blocking issues found. The 4 observations above are non-blocking and should be tracked for future sprints.

### Closure Checklist

| Item | Status |
|------|--------|
| All 6 deliverables produced | ✅ |
| Security reviewer approves | ✅ |
| WO-001 ready for closure | ✅ |
| Remaining risks documented | ✅ (in this report + SPRINT0_WAVE_A_REPORT.md) |
