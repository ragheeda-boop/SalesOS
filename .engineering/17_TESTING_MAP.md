---
EngineeringOS: v3
GeneratedAt: 2026-08-01T20:10:52Z
RepositoryCommit: 9fa8e9f
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Measured
Revalidation: Active (DEC-142)
---

# 17 â€” TESTING MAP

> Where tests live, how they run, and what is verified. **Validation honesty labels apply (AGENTS.md Â§5): nothing in this file claims a passed suite without evidence.**

## 1. Backend tests (`salesos/backend/tests/`, 220 files via `git ls-files` test_*/_test.py method)

| Pillar | Dir (as-built) | Scope |
|---|---|---|
| Unit | `tests/unit/` | single-module behavior |
| Contract | `tests/contract/` | API contracts, frozen-interface rules (Rule 4 search) |
| Integration | `tests/` + `tests/test_integration.py` | API + DB integration |
| E2E | `tests/e2e/` | backend e2e |
| Evaluation | `tests/evaluation/` | eval harness |
| Support | `tests/support/` | fixtures (incl. mock keypair) |
| Architecture | `tests/test_architecture.py` | **5 arch rules** (SDK-import, kernel-commercial) |

Fixtures: `tests/conftest.py` + support. SQLi sinks from SEC report are located under `app/` and are NOT covered by green tests (no evidence of passing coverage).

## 2. Frontend tests (`salesos/frontend/`)

| Pillar | Config | Scope |
|---|---|---|
| Unit | `jest.config.js` | component/feature `__tests__` |
| E2E | `playwright.config.ts` (+ visual via `tests/visual/`) | **31 Playwright specs** |
| Storybook | `.storybook/` | component gallery |

## 3. CI wiring

- Backend unit+integration in `ci.yml` (approval required to run locally; CI owns it).
- **e2e CI job has NO services (DB/Redis)** â†’ Playwright e2e cannot pass in CI (SEC/CI finding).
- Coverage gate: `scripts/check-coverage.py` exists (threshold unverified).
- Arch gate: `scripts/arch-compliance.py` + `tests/test_architecture.py`.

## 4. Known test-honesty gaps (observe only)

- No test exercises `/api/v1/capabilities` or the decorator registry (see `29` Â§4 #6).
- SQLi sinks untested for injection.
- No recorded evidence in this bootstrap of any full-suite pass (labels: **not validated**).

## 5. When this file changes

- On test add/pillar change. Mirror `12` (CI), `30` (report).
