# 163 — `sdk/theme_sdk::ThemeTokenSet.to_css_variables()` silently dropped every typography token; closes the `sdk/*_sdk/` plugin-SDK sweep

**Read-only in scope of production/salesos_test.** Pure unit-level fix; no database container needed.

## 1. Scope

Continuing directly from report 162. Checked the remaining `sdk/*_sdk/` plugin-scaffolding subdirectories flagged in report 161: `widget_sdk`, `backend_sdk`, `integration_sdk`, `plugin_sdk`, `theme_sdk`, `frontend_sdk`, `company_sdk`.

## 2. The bug

`ThemeTokenSet` declares 8 fields (`colors`, `typography`, `radius`, `elevation`, `spacing`, `motion`, `breakpoints`, `icons`). `merge()` correctly iterates all 8 when combining two token sets. `to_css_variables()` — the method that actually generates the theme's output CSS — independently duplicated the same category list but with `"typography"` omitted, leaving 7 entries. Any typography tokens set via `ThemeBuilder.with_typography(...)` were silently absent from the generated stylesheet, with no error or warning; `merge()` (right next to it in the same class) demonstrates this was almost certainly a copy-paste omission between two independently-maintained copies of the same list, not an intentional exclusion.

## 3. Reachability

`grep -rln "ThemeBuilder\|create_theme\|ThemeTokenSet\|to_css_variables"` across `app/`, `domains/`, `runtime/`, `intelligence/`, `mcp_server/`, `tests/` (excluding the module itself): zero matches. Dead code, zero prior test coverage — matching this session's established "correctly-designed-but-unwired, genuine internal defect" pattern. Fixed anyway, since the omission is unconditional and silent, and would surface as a real design-system defect (missing font-related CSS variables) the instant this SDK is wired to a real theme-building caller.

## 4. Fix

Extracted a single shared `_TOKEN_CATEGORIES` module-level constant (the complete, correct 8-item list) and used it in both `to_css_variables()` and `merge()`, replacing their two independently-maintained copies — closing off the exact drift mechanism that caused the bug, not just the immediate symptom.

## 5. Verification — genuine red→green

New `tests/unit/test_theme_sdk_token_categories.py` (3 tests): one drives the real `ThemeBuilder`/`create_theme()` public API and asserts typography tokens appear in the built theme's `"css"` output; one constructs a `ThemeTokenSet` with all 8 categories populated and asserts every one appears (including a same-key-in-two-categories check, since `radius` and `breakpoints` both use key `"sm"` in the test — proving both categories' entries are independently emitted, not merely one satisfying the assertion for both); one is a regression guard confirming the refactor didn't change `merge()`'s already-correct behavior.

Scoped `git stash push -- salesos/backend/sdk/theme_sdk/__init__.py` (reverting only the fix): the first two tests failed with the exact predicted `AssertionError: missing '--tw-font: Inter;' in generated CSS` (and the equivalent for the multi-category test); the third (merge-only) test correctly still passed, since that method was never buggy. `git stash pop` restored the fix; all 3 re-confirmed PASS.

## 6. Other 6 files in this sweep — confirmed clean

`widget_sdk`, `backend_sdk`, `integration_sdk`, `plugin_sdk`, `frontend_sdk`, `company_sdk` (`interfaces.py`) are all pure dataclass/fluent-builder/ABC-interface definitions with no async logic, no raw SQL, no duplicated category lists, and no I/O of any kind — read in full, no defects found.

## 7. Regression

New test file: 3/3 PASS. Ruff (`--select E4,E7,E9,F,I`): 0 findings on both files. `python -m py_compile` and `git diff --check`: clean.

## 8. Scope and safety

- Two files touched: `salesos/backend/sdk/theme_sdk/__init__.py` (fix + explanatory comment), `salesos/backend/tests/unit/test_theme_sdk_token_categories.py` (new).
- No database or container needed. No production/`salesos_test` write. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.

## 9. `sdk/*_sdk/` plugin-SDK sweep — closed

| File | Result |
|---|---|
| `agent_sdk/__init__.py` | **1 bug fixed** — `asyncio.run()` from a sync method (report 162) |
| `theme_sdk/__init__.py` | **1 bug fixed** — missing typography category (this report) |
| `widget_sdk`, `backend_sdk`, `integration_sdk`, `plugin_sdk`, `frontend_sdk`, `company_sdk` | **Clean** |

## 10. Loop status

Continuing the standing 24-hour continuous-loop authorization. The `sdk/` tree (root files, `sdk/events/`, `sdk/pagination.py`, `sdk/graph.py`, `sdk/search.py`, and all `sdk/*_sdk/` plugin scaffolding) is now comprehensively swept across reports 155-163. Pivoting to a fresh file family for the next tick — candidates: `domains/` subdirectories not yet individually reviewed this session, or a repeat of the report-98-style raw-SQL sweep restricted to files added since that report's original run (fact ledger, provider spend, Agent Reach, MA-proposal-staging, Phase 7 review queue — none of which existed when report 98 first ran, and confirmed in report 174/§ AGENTS.md history that a later re-run found 0 new candidates, but that predates several subsequent additions this session).
