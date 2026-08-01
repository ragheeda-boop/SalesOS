# DEC-091 — JWT audience enforcement verify; consumption remains OPEN

**Date:** 2026-08-01  
**Status:** Accepted  
**Product:** SalesOS  
**Owners:** Backend / Security  
**Related:** STORY-02-03 (`2379e5f`); Phase 0 DEC-008 gate GO (DEC-086); `EXECUTION_DAG.md` JWT consumption track

---

## Context

Board lists **JWT audience consumption** as READY / PARALLEL after STORY-02-03 groundwork landed. Phase 0 (DEC-008) exit = GO under DEC-086. Need an honest close-or-keep decision with fresh evidence on `salesos-api` vs `salesos-owner-platform` enforcement.

## Decision

1. **STORY-02-03 groundwork** remains **DONE** at `2379e5f` (`jwt_audience=salesos-api`, `jwt_owner_audience=salesos-owner-platform`; owner mint/verify helpers; cross-audience reject tests).
2. **JWT audience consumption** remains **OPEN / READY / PARALLEL** — do **not** CLOSE. No router dependency uses `decode_owner_*`; Owner Platform endpoints do not exist yet (EPIC-04). Tenant API path `verify_token` → `decode_access_token` → `decode_token(audience=settings.jwt_audience)` enforces **`salesos-api`** only (owner tokens rejected).
3. Re-validation (this session, tip `9cfc890`): host `poetry run pytest tests/unit/test_jwt_audience_split.py -q` → **7 passed** / 0 failed (**light validated**). Prior swarm Docker evidence (`deae7de` / SWARM_VALIDATION) still stands for JWT+write-protection **15 passed**.
4. **Production GA / External pilot = NO-GO** unchanged. **CI GREEN not met.** Do not claim production GO.

## Alternatives considered

- (a) CLOSE consumption because Sprint-04 AC wording ("token type exists, unused by any endpoint") is already met by groundwork — rejected; board/DAG treat endpoint wiring as a separate READY track for EPIC-04.
- (b) Implement Owner Platform auth deps now — rejected; out of scope for this verify gate; no Owner surface to consume against.

## Evidence

| Check | Result |
|---|---|
| Config audiences distinct | `salesos-api` ≠ `salesos-owner-platform` |
| Tenant decode rejects owner token | covered by `test_tenant_decoder_rejects_owner_token` |
| Owner decode rejects tenant token | covered by `test_owner_decoder_rejects_tenant_token` |
| Endpoint owner consumption | **absent** — keep OPEN |
| Narrow pytest | **7/7 PASS** (host Poetry) |

## Follow-ups

- EPIC-04 / Owner Admin: wire `decode_owner_access_token` into owner-only deps; add adversarial HTTP cross-audience tests; then CLOSE consumption on board.
