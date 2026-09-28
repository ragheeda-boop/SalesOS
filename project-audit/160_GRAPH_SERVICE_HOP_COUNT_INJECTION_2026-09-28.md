# 160 — `sdk/graph.py::shortest_path()`: `max_hops` interpolated into Cypher unvalidated, unlike every other dynamic value in the file

**Read-only in scope of production/salesos_test.** Pure unit-level fix (mocked Neo4j driver); no database container needed. `sdk/pagination.py` also reviewed this tick and confirmed clean.

## 1. Scope

Continuing the sweep into unreviewed `sdk/` root files. `sdk/pagination.py` (the keyset codec involved in reports 80/81's earlier `search_runtime`/`PostgresSearchRepository` bugs) was re-checked directly for its current 6 real call sites — all pass a genuinely UUID-primary-key model (`Company`, `User`, `EmployeeSignalModel`, each confirmed against its actual column definition: `BaseModel.id: PG_UUID(as_uuid=True)`, `EmployeeSignalModel.id: UUID(as_uuid=True)`). **No bug found** — `build_keyset_condition()`'s `UUID(cursor_id)` assumption holds for every current caller.

`sdk/graph.py` (`GraphService`, a Neo4j abstraction) was reviewed next.

## 2. The gap

Every dynamic Cypher fragment in this file except one goes through `_validate_cypher_identifier()` (a regex allowlist: `^[A-Za-z_][A-Za-z0-9_]*$`) before being f-string-interpolated into a query — labels, relationship types, property keys are all guarded this way, consistently, across `create_node`, `find_node`, `create_relationship`, `find_related`, `shortest_path`, and `run_community_detection`.

`shortest_path()`'s `max_hops` parameter was the one exception: `[*..{max_hops}]` (Cypher's variable-length path syntax, which has no bound-parameter form — Neo4j does not support parameterizing a path-length bound) was interpolated directly with no validation at all, despite `max_hops: int = 6` being *type-hinted* as `int` — a hint Python does not enforce at runtime. A caller passing an unvalidated string (e.g., sourced from user input, the moment this module is ever wired to a real caller) would have that string land verbatim inside the query text — the same class of risk `_validate_cypher_identifier()` exists specifically to close for every other dynamic value in the file.

## 3. Reachability

`grep -rln "GraphService\|\.shortest_path(" app/ domains/ runtime/ intelligence/ mcp_server/` (excluding the module itself): the only hit is `app/startup.py:259`, which constructs an entirely different, unrelated `RelationshipGraphService` class — not this file's `GraphService`. `app/startup.py` is itself confirmed dead code (never imported anywhere, per reports 132/139/140/148/153). `GraphService` has **zero** live callers. This is consistent with the codebase's own governance record — ADR-108 explicitly keeps Neo4j offline (per this session's AGENTS.md §10) — this is deliberately parked infrastructure, not an accidental gap.

## 4. Fix — narrow, matches the file's own existing pattern

Zero prior test coverage existed for this file at all. Added `_validate_hop_count()`, mirroring `_validate_cypher_identifier()`'s role: rejects non-`int` (including `bool`, since `bool` is a subclass of `int` in Python and would otherwise silently pass an `isinstance(x, int)` check) and out-of-range values (bounded `1..15`) before `shortest_path()` builds its query string. `run_community_detection()`'s `label` parameter was already correctly guarded and needed no change.

## 5. Verification — genuine red→green

New `tests/unit/test_graph_service.py` (14 tests, using a minimal fake Neo4j driver — no real database needed): parametrized rejection of injection-shaped strings, floats, booleans, `None`, and out-of-range ints; acceptance of the valid `1..15` range; an end-to-end proof that a malicious `max_hops` value passed to `shortest_path()` never reaches the driver's `.run()` call at all; and a proof that a valid `max_hops` is correctly interpolated into the query text.

Scoped `git stash push -- salesos/backend/sdk/graph.py` (reverting only the fix): the test module failed to even *import* — `ImportError: cannot import name '_validate_hop_count' from 'sdk.graph'` — the exact predicted failure, since the function didn't exist before this change. `git stash pop` restored the fix; all 14 tests re-confirmed PASS.

## 6. Regression

New test file: 14/14 PASS in isolation. Ruff (`--select E4,E7,E9,F,I`): caught one unused import (`MagicMock`, left over from an earlier draft of the test) — fixed immediately, 0 findings after. `python -m py_compile` and `git diff --check`: clean. No pre-existing test file for `sdk/graph.py` existed to regress.

## 7. Scope and safety

- Two files touched: `salesos/backend/sdk/graph.py` (fix + explanatory comment), `salesos/backend/tests/unit/test_graph_service.py` (new).
- No database or container needed — the fix and its verification are both pure Python-level validation, exercised against a fake driver.
- No production/`salesos_test` write. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted. Does not change or challenge ADR-108's "keep Neo4j offline" decision in any way — this hardens dead code ahead of any future wiring decision, matching the established precedent (reports 121/123/126/127/130/131/135/156/158), rather than proposing to activate the module.

## 8. Loop status

Continuing the standing 24-hour continuous-loop authorization. Remaining unreviewed `sdk/` root files: `sdk/search.py` (5 DB-indicator hits from an initial scan), `sdk/queue.py`, `sdk/vector.py`, `sdk/telemetry.py` (all showed 0 DB-touching indicators in the initial scan — likely pure in-memory/utility code, lower priority). `sdk/search.py` is the next candidate.
