# Code Quality Audit

> **Audit Date**: 2026-07-16
> **Scope**: `salesos/backend/**/*.py`, `salesos/frontend/src/**/*.{ts,tsx}`, `salesos/frontend/packages/**/*.{ts,tsx}`
> **Files Inspected**: 1,403 Python files + 7,022 TypeScript/TSX files
> **Tooling**: grep/ripgrep pattern scan, file size analysis

---

## Executive Summary

The codebase demonstrates **strong overall code quality** with minimal outright violations:

| Category | Count | Severity |
|----------|-------|----------|
| TODO comments | 4 | 🟡 Low |
| FIXME comments | 0 | 🟢 None |
| HACK comments | 0 | 🟢 None |
| XXX comments | 0 | 🟢 None |
| `print()` in production code | 1 | 🟡 Low |
| `console.log`/`console.debug` | 1 | 🟡 Low |
| `Any` type annotations (Python) | 284 | 🟡 Medium |
| `any` type annotations (TS) | 4 | 🟡 Low |
| `# type: ignore` | 0 | 🟢 None |
| `@ts-ignore` | 0 | 🟢 None |
| `@deprecated` markers | 0 | 🟢 None |
| NoQA/F401 (model registration) | 11 | 🟢 Intentional |
| Files > 500 lines | 18 | 🟡 Medium |
| Commented-out imports | 8 | 🟡 Low |
| Technical Debt markers (TD-*) | 0 in code | 🟢 Tracked externally |

**Overall Assessment**: The codebase is clean with respect to commented-out code, suppression annotations, and debug logging. The main areas for attention are file size complexity (many files exceed 500 lines), Python `Any` type proliferation, and residual `print()` calls in scripts/tools.

---

## 1. TODO Comments

### Backend

| File | Line | Comment |
|------|------|---------|
| `app/modules/commercial/commercial.py` | 281 | `# TODO(D-005): Replace hardcoded demo input with real pipeline data.` |
| `app/modules/commercial/commercial.py` | 329 | `# TODO(D-005): Replace hardcoded demo analytics input with real data pipeline.` |
| `app/modules/commercial/commercial.py` | 451 | `# TODO(D-005): Replace hardcoded demo analytics input with real pipeline data.` |
| `app/modules/commercial/commercial.py` | 493 | `# TODO(D-005): Replace hardcoded "Today" summary values (12.4M, 89%, "Healthy")` |

**Severity**: 🟡 Low — All four TODOs reference a single tracked issue (D-005) and are confined to one file.

### Frontend

**None found** in production `src/` or `packages/` directories.

---

## 2. FIXME Comments

**None found** anywhere in the scanned codebase.

---

## 3. HACK Comments

**None found.**

---

## 4. XXX Comments

**None found.**

---

## 5. Deprecated Markers

### Backend

| File | Line | Context |
|------|------|---------|
| `kernel/feature_registry.py` | 18 | `DEPRECATED = "deprecated"` — Enum value, intentional |
| `app/modules/identity/security.py` | 14 | `deprecated="auto"` — Passlib bcrypt config, intentional |

### Frontend

**None found.**

---

## 6. `console.log` / `console.debug`

### Frontend

| File | Line | Code |
|------|------|------|
| `src/lib/monitoring.ts` | 126 | `console.debug('[Monitor]', full.type, full)` |

This is a moderate concern — `console.debug` in a monitoring utility may be intentional for diagnostics but should ideally use a proper logging framework.

---

## 7. `print()` in Python

### Total: 130 occurrences across the codebase

#### By File (non-production scripts excluded when appropriate)

| File | Count | Nature |
|------|-------|--------|
| `demo/pilot_seed.py` | 34 | CLI demo tool — acceptable |
| `infra/cli.py` | 20 | CLI application — acceptable |
| `infra/benchmark/run.py` | 19 | Benchmark CLI — acceptable |
| `demo/reset.py` | 18 | Demo helper — acceptable |
| `scripts/prod_audit.py` | 18 | Audit script — acceptable |
| `demo/seed_data.py` | 12 | Seed data generator — acceptable |
| `demo/seed_graph.py` | 6 | Graph seeder — acceptable |
| `infra/config.py` | 2 | Configuration docstring — acceptable |
| `demo/demo_data_generator.py` | 1 | Acceptable |

### 🔴 Production Code `print()`

| File | Line | Code |
|------|------|------|
| `app/modules/monitoring/metrics.py` | 18 | `print(metrics.generate())` |

**Action Required**: This `print()` call in production monitoring code should be replaced with structured logging.

---

## 8. `Any` Type Annotations (Python)

### Total: 284 occurrences

#### Top Files by `Any` Usage

| File | Count | Impact |
|------|-------|--------|
| `kernel/grounding.py` | 14 | High — core kernel module |
| `infra/database/fakes.py` | 9 | Test utility — acceptable |
| `infra/benchmark/data_generator.py` | 7 | Benchmark tool — acceptable |
| `kernel/pagination.py` | 6 | Medium — API pagination surface |
| `kernel/reasoning.py` | 6 | Medium — AI reasoning module |
| `app/modules/monitoring/audit.py` | 4 | Low — audit |
| `infra/benchmark/runner.py` | 4 | Benchmark tool |
| `app/main.py` | 4 | Medium — application entry point |
| `kernel/graph.py` | 3 | Low |
| `infra/database/database.py` | 3 | Low |
| `kernel/guardrails.py` | 3 | Low |
| `app/application/object_viewer.py` | 3 | Low |
| `kernel/capability_registry.py` | 2 | Low |
| `kernel/telemetry.py` | 2 | Low |
| Others | ~200 | Scattered |

**Key Files Requiring Attention**:
- `kernel/grounding.py` (14 `Any` uses)
- `kernel/pagination.py` (6 `Any` uses, impacts API contracts)
- `kernel/reasoning.py` (6 `Any` uses)

---

## 9. `any` Type in TypeScript

### Total: 4 occurrences

| File | Line | Code |
|------|------|------|
| `src/__tests__/end-to-end.test.tsx` | 7 | `const store = { opps: [] as any[], tasks: [] as any[] }` |
| `src/__tests__/end-to-end.test.tsx` | 16 | `jest.fn((url: string, data: any) => {...})` |
| `src/__tests__/end-to-end.test.tsx` | 30 | `jest.fn((url: string, data?: any) => {...})` |
| `src/__tests__/end-to-end.test.tsx` | 34 | `const opp = store.opps.find((o: any) => o.id === oppMatch[1])` |

All 4 are in test utility code — acceptable.

---

## 10. Type Suppression Annotations

### `# type: ignore` (Python): **0 found**
### `@ts-ignore` (TypeScript): **0 found**
### `noqa: F401` (Python): 11 occurrences in `database.py` (intentional model registration imports)

**Excellent** — no type-safety escapes in production code.

---

## 11. Files Exceeding 500 Lines

### Backend (13 files)

| File | Lines | KB | Risk |
|------|-------|----|------|
| `runtime/knowledge_graph_runtime/__init__.py` | 1,087 | 52.3 | 🔴 High — largest source file |
| `tests/e2e/test_critical_paths.py` | 931 | 37.5 | 🟡 Medium — test file |
| `domains/commercial/infrastructure/postgres_repositories.py` | 861 | 47.0 | 🔴 High — need refactoring |
| `app/modules/decision/engine.py` | 774 | 30.5 | 🔴 High — core engine |
| `app/main.py` | 773 | 38.1 | 🔴 High — app bootstrap |
| `runtime/data_fabric_runtime/__init__.py` | 681 | 31.0 | 🟡 Medium |
| `app/modules/company/service.py` | 665 | 29.9 | 🟡 Medium |
| `runtime/feature_store/features.py` | 648 | 25.8 | 🟡 Medium |
| `app/modules/admin/router.py` | 621 | 34.0 | 🟡 Medium |
| `app/modules/entity_resolution/service.py` | 614 | 26.0 | 🟡 Medium |
| `app/application/dashboard/services/decision_provider.py` | 593 | 26.7 | 🟡 Medium |
| `app/modules/decision/router.py` | 531 | 21.3 | 🟡 Medium |
| `app/modules/identity/service.py` | 524 | 22.5 | 🟡 Medium |

### Frontend (5 files)

| File | Lines | KB | Risk |
|------|-------|----|------|
| `src/lib/api.ts` | 1,240 | 38.0 | 🔴 High — monster API client |
| `src/app/(dashboard)/graph/page.tsx` | 931 | 38.2 | 🔴 High — monolithic page |
| `src/lib/api/types.ts` | 667 | 16.6 | 🟡 Medium — type definitions |
| `src/components/employee-360-view.tsx` | 547 | 31.4 | 🟡 Medium — component |
| `src/components/pipeline-kanban.tsx` | 516 | 19.4 | 🟡 Medium — component |

### Packages (None > 500 lines)

---

## 12. Commented-Out Code

### Backend: 8 commented import statements

All in `infra/database/database.py` — import model registrations that use `# noqa: F401`. These are pattern-conformant (models need to be imported to register with SQLAlchemy) and the `noqa` suppression is appropriate.

### Frontend: None found

---

## 13. Technical Debt Markers

**No `TD-*` or "Technical Debt" markers found in code.** Technical debt is tracked externally in `memory/technical-debt.md` per Engineering Constitution Article 2.3.

---

## 14. Most Problematic Files

### Priority 1 — Refactor Candidates (Complexity Risk)

| Rank | File | Lines | Issues |
|------|------|-------|--------|
| 1 | `frontend/src/lib/api.ts` | 1,240 | Monolithic API client, single-file bottleneck |
| 2 | `backend/runtime/knowledge_graph_runtime/__init__.py` | 1,087 | Massive init file, likely doing too much |
| 3 | `backend/app/main.py` | 773 | All-in-one app bootstrap |
| 4 | `backend/app/modules/decision/engine.py` | 774 | Core engine needs modularization |
| 5 | `backend/domains/commercial/infrastructure/postgres_repositories.py` | 861 | Repository pattern sprawl |
| 6 | `frontend/src/app/(dashboard)/graph/page.tsx` | 931 | Monolithic page component |

### Priority 2 — Type Safety

| File | `Any` Count | Issue |
|------|-------------|-------|
| `backend/kernel/grounding.py` | 14 | Replace `Any` with proper generics |
| `backend/kernel/pagination.py` | 6 | API surface type safety |
| `backend/kernel/reasoning.py` | 6 | AI module type safety |

### Priority 3 — Production Debug Artifacts

| File | Line | Issue |
|------|------|-------|
| `backend/app/modules/monitoring/metrics.py` | 18 | `print()` in production |
| `frontend/src/lib/monitoring.ts` | 126 | `console.debug` in production |

### Priority 4 — Technical Debt (D-005)

- `backend/app/modules/commercial/commercial.py` — 4 TODOs referencing D-005 (hardcoded demo values)
- Fix should replace hardcoded values with real pipeline data

---

## 15. Prioritized Remediation List

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| P0 | Refactor `frontend/src/lib/api.ts` (1,240 lines) | 3 days | High — maintainability, testability |
| P0 | Refactor `backend/runtime/knowledge_graph_runtime/__init__.py` (1,087 lines) | 3 days | High — modularity |
| P1 | Replace `Any` types in `kernel/grounding.py`, `pagination.py`, `reasoning.py` | 2 days | Medium — type safety |
| P1 | Refactor `backend/app/main.py` into modular startup | 1 day | Medium — boot clarity |
| P1 | Refactor `backend/app/modules/decision/engine.py` (774 lines) | 2 days | Medium — testability |
| P2 | Replace `print()` with logging in `metrics.py` | 0.5 day | Low — production hygiene |
| P2 | Replace `console.debug` with structured logging in `monitoring.ts` | 0.5 day | Low — production hygiene |
| P3 | Resolve D-005 TODOs in `commercial.py` | 1 day | Low — demo code |
| P3 | Audit remaining files >500 lines for extraction opportunities | 1 day | Medium — ongoing |

---

## 16. Summary Statistics

| Metric | Value |
|--------|-------|
| Python files scanned | 1,403 |
| TypeScript/TSX files scanned | 7,022 |
| Total `print()` calls | 130 (1 in production) |
| Total `console.log`/`console.debug` | 1 |
| Total Python `Any` annotations | 284 |
| Total TypeScript `any` | 4 (test only) |
| Total `# type: ignore` | 0 |
| Total `@ts-ignore` | 0 |
| Total TODOs | 4 |
| Total FIXMEs | 0 |
| Total HACKs | 0 |
| Files > 500 lines (backend) | 13 |
| Files > 500 lines (frontend) | 5 |
| Commented-out import blocks | 8 (intentional model registration) |

---

## 17. Conclusion

SalesOS codebase is in **good health**. Key strengths:

- **Zero** `# type: ignore` or `@ts-ignore` escapes in production code
- **Zero** FIXME, HACK, or XXX annotations
- **Zero** TSX HACK/XXX patterns
- **Zero** deprecated function/method usages
- **Zero** Technical Debt markers in code (tracked externally)
- All `print()` calls are concentrated in CLI/demo/benchmark tools (129/130)
- All `any` in TypeScript are in test utilities (4/4)

Primary improvement areas center on **file size management** (18 files > 500 lines) and **Python type safety** (284 `Any` annotations, especially in kernel modules). Addressing the 3 highest-priority refactors (api.ts, knowledge_graph_runtime __init__, main.py) would yield the largest maintainability gains.
