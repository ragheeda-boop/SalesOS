# Test Strategy — The Full Pyramid

> **Context:** Current test-to-source ratio is Grade D (13.8%, 277 test files / 2,009 source files per `CANONICAL_ARCHITECTURE.md` §14/§17). This strategy does **not** attempt to retroactively fix that number across the entire existing codebase before GA — that would consume the whole program. It fixes it **going forward** (new code only) and adds the specific new test categories a commercial multi-tenant platform requires that a single-tenant app never needed.

---

## 0. Coverage Gates (the mechanism, not just the pyramid)

| Gate | Threshold | Enforced where | Since |
|---|---|---|---|
| New/changed line coverage | ≥80% | CI, diff-coverage tool, blocks merge | Sprint 2 |
| Existing (pre-Phase-0) code coverage | No new requirement — tracked, not blocked | Reporting dashboard only | Sprint 2 |
| Cross-tenant regression suite | 100% pass, every PR touching a tenant-scoped table | CI, blocks merge | Sprint 1 (P0 fixes), permanent from Sprint 3 |
| Contract test suite | 100% of new API surface covered | CI, blocks merge | Sprint 3 onward |

**Implementation (STORY-03-03, Sprint 02):** `scripts/check_diff_coverage.py`
— a self-contained script (no new third-party dependency; `diff-cover` was
considered and passed over so `poetry.lock` doesn't churn for a small,
fully-controllable piece of logic), wired into `.github/workflows/ci.yml`'s
`test-backend` job as a step that runs only `if: github.event_name ==
'pull_request'` (a push directly to main/develop has no base to diff
against). Independent of, not a replacement for, the existing repo-wide
`--cov-fail-under=85` gate in the same job — that one is unchanged and stays
on. Scopes to the same `app/`, `domains/`, `sdk/`, `runtime/`,
`intelligence/` prefixes the existing coverage command already covers, and
deliberately excludes test files themselves from the gate (a PR's new test
code "covering itself" isn't the signal this gate is for). Unit-tested in
`tests/unit/test_check_diff_coverage.py` (19 tests: hunk-parsing regex,
Cobertura XML parsing, scope/test-file filtering, end-to-end `analyze()`)
and separately verified by hand against a real historical 35-file commit
(`be1bb2b`) — that run caught two real bugs before either reached CI: a
`UnicodeDecodeError` from relying on the platform-default subprocess
encoding against this Arabic-first codebase's actual file contents, and a
path-prefix mismatch between plain `git diff` (repo-root-relative) and
`coverage.xml` (working-directory-relative), fixed with `git diff
--relative`.

---

## 1. Unit Tests

**Scope:** Pure functions, business logic, individual service methods, in isolation from DB/network.

| Area | Priority examples | Owner |
|---|---|---|
| Subscription state machine (every transition) | trial→active, active→past_due, past_due→suspended, suspended→reactivated, any→churned | Backend |
| Proration calculation | Every upgrade/downgrade direction × every billing-cycle-position | Backend |
| Entitlement evaluation logic | Plan × capability matrix, cache invalidation on plan change | Backend |
| `FieldMappingConfig` drift detection | Simulated field rename/removal produces a loud alert, not a silent null | Backend |
| Anti-Corruption Layer stages (Mapper/Validator/Transformer/Normalizer/ConflictResolver) | Each stage tested independently with malformed-input cases | Backend |
| `TaskCaseExtension` JSON Schema validation per `case_type` | financing/insurance/generic each validated against their own schema | Backend |
| Scoring Rule evaluation engine | Fail-safe fallback to platform default on rule error | Backend |
| Workflow Builder canvas-to-execution-graph compiler | Every node type (condition, action, branch) compiles correctly | Backend |

**Target:** ≥80% coverage on all new code (gate above); unit tests run in <3 minutes total in CI (fast feedback is the point of this layer).

---

## 2. Integration Tests

**Scope:** Real database, real Redis, mocked external services (Stripe, Odoo, AI providers) via recorded fixtures.

| Area | Priority examples | Owner |
|---|---|---|
| Tenant provisioning → suspension → deletion full lifecycle | State + access verified at every transition | Backend |
| Stripe webhook idempotency | Same webhook delivered twice produces one billing state change, not two | Backend |
| RLS policy enforcement | Direct DB-level query with wrong tenant context denied, even bypassing application code | Backend |
| Odoo adapter sync cycle | Against a recorded/mocked XML-RPC fixture set (27,264-record scale sample) | Backend |
| Custom Object/Field definition across concurrent tenants | 5 simulated tenants defining fields simultaneously, verify isolation | Backend |
| AI Memory storage and retrieval | Conversation-scoped read/write round-trip | AI/Backend |

**Target:** Runs against an ephemeral, seeded multi-tenant test database (≥5 synthetic tenants) in CI, <15 minutes total.

---

## 3. Contract Tests

**Scope:** API schema conformance — does the actual response match the documented OpenAPI schema, and does every `SourceConnector` adapter conform to the published interface.

| Area | Priority examples | Owner |
|---|---|---|
| OpenAPI schema validation | Every endpoint added since Phase 1 validated against its documented schema on every CI run | Backend |
| `SourceConnector` interface conformance | `OdooAdapter` and the second connector both pass an identical conformance suite — this is the direct proof the framework generalizes | Backend |
| Odoo XML-RPC response shape | Mocked/sandboxed Odoo instance in CI, closing the exact gap `ARB_META_REVIEW.md` §9 flagged as missing from the original ARB | Backend |
| Marketplace listing conformance | Certification pipeline's automated contract-testing stage | Backend |

**Target:** Zero schema drift between documentation and implementation — a failing contract test is treated as a P0 CI failure, not a warning.

---

## 4. API Tests

**Scope:** Black-box, HTTP-level tests against a running instance — the layer that would catch "the unit tests all pass but the endpoint actually returns 500."

| Area | Priority examples | Owner |
|---|---|---|
| Full request/response cycle per endpoint, including auth/entitlement gating | Valid token + wrong plan → 403 with clear entitlement-denied body, not a generic 500 | QA |
| Rate limiting (CAP-078) | Confirm per-tenant rate limits actually throttle at the gateway | QA |
| Idempotency keys on mutating endpoints (billing, provisioning) | Duplicate request with the same idempotency key produces one effect | QA |

**Target:** Runs in a staging environment resembling production topology (not just localhost), nightly + pre-release.

---

## 5. Playwright (End-to-End UI)

**Scope:** Real browser, real UI, critical user journeys.

| Journey | Priority | Owner |
|---|---|---|
| Self-service signup → provision → first Company 360 view | P0 | QA/Frontend |
| Studio: add a custom field → see it render on Company page | P0 | QA/Frontend |
| Studio: build a workflow in the no-code canvas → activate → observe execution | P0 | QA/Frontend |
| Integrations Studio: connect Odoo → test → map fields → schedule → monitor | P0 | QA/Frontend |
| GTM: define ICP → run Lead Discovery → enrich a result → launch a sequence | P0 | QA/Frontend |
| Marketplace: browse → install a connector listing | P1 | QA/Frontend |
| Owner Console: view tenant list, billing status | P1 | QA/Frontend |
| Subscription: upgrade plan mid-cycle, confirm proration reflected in UI | P0 | QA/Frontend |

**Target:** Runs against a full staging deploy on every merge to `main` and mandatorily before every phase-gate release; flaky-test quarantine process defined (a test failing intermittently is fixed or quarantined within 1 sprint, not left red indefinitely).

---

## 6. Load Testing

**Scope:** Sustained, realistic traffic simulation.

| Scenario | Target | Tooling |
|---|---|---|
| 50 concurrent simulated tenants, mixed CRM + GTM + Studio traffic | p95 ≤300ms, p99 ≤800ms on core CRM endpoints, sustained 2 hours | k6 or Locust |
| Connector sync load | ≥5,000 records/hour sustained per connection | Custom harness against mocked Odoo fixture |
| Billing webhook burst | 100 webhooks/minute burst, zero dropped/misprocessed | k6 |

**Target:** Executed in Phase 6 (Sprint 23) as the primary validation gate before Release Candidate.

---

## 7. Stress Testing

**Scope:** Push past expected limits to find the actual breaking point and confirm graceful degradation (not silent corruption) beyond it.

| Scenario | Expected behavior at failure |
|---|---|
| 2× the load-test tenant count (100 simulated tenants) | Graceful backpressure (queuing/rate-limiting), not data corruption or crash |
| Database connection pool exhaustion | Clear error responses, automatic recovery once load subsides, no connection leak |
| Sustained AI provider latency spike | Requests queue and eventually time out cleanly, no cascading failure into unrelated services |

**Target:** Executed once in Phase 6, results documented even if the system "passes" (know the actual ceiling, don't just confirm the floor).

---

## 8. Chaos Testing

**Scope:** Deliberate fault injection into a running (non-production or shadow-production) environment.

| Injected fault | Expected behavior |
|---|---|
| Kill primary AI provider connection | Failover to secondary provider within 30 seconds (per `PRODUCTION_READINESS_CHECKLIST.md`) |
| Kill a connector's external endpoint (simulate Odoo unreachable) | Sync retries with backoff, alerts loudly, does not corrupt partially-synced data |
| Database primary failover | Application reconnects automatically, in-flight requests fail cleanly and are retryable, no silent data loss |
| Redis (entitlement cache) unavailability | Falls back to a DB read (slower, but correct) rather than failing open/closed incorrectly |

**Target:** Each drill produces a written postmortem regardless of outcome (practice postmortems, per `MASTER_EXECUTION_PLAN.md` principle 8), executed in Phase 6 (Sprint 23).

---

## 9. Security Testing

**Scope:** Continuous automated scanning + point-in-time manual/external review.

| Layer | Mechanism | Cadence |
|---|---|---|
| SAST | Static analysis in CI | Every PR |
| Dependency vulnerability scan | `pip-audit`/`npm audit`-equivalent | Every PR (blocking from Sprint 2) |
| Cross-tenant adversarial suite | Purpose-built test harness (Sprint 1 template, extended every epic) | Every PR touching a tenant-scoped table |
| Entitlement-bypass suite | Full plan × capability matrix | Every PR touching entitlement logic, full run weekly |
| Secrets-in-logs audit | Automated log-scrubbing scan | Weekly |

---

## 10. Penetration Testing

**Scope:** External, adversarial, human-led — the one test category deliberately *not* automated, because it's designed to find what automation misses.

| Item | Detail |
|---|---|
| Timing | Phase 6, Sprint 24 — deliberately after internal hardening, not instead of it |
| Scope | Full tenant-facing surface + Owner Console + Integration Hub + Marketplace certification pipeline |
| Firm/team | External firm preferred; internal dedicated red-team exercise as fallback if budget/timeline forces it |
| Exit bar | Zero unresolved criticals; highs triaged with fix-by date or explicit CTO risk acceptance |
| Re-test | Any critical finding is re-tested by the same reviewer post-fix, not just closed on the fixing engineer's word |

---

## 11. Tenant Isolation Testing

**Scope:** The single most important test category this platform has, given the Decision Center IDOR precedent — treated as its own pyramid layer, not folded into "security" generically.

| Test | Detail |
|---|---|
| RLS bypass attempt | For every tenant-scoped table, attempt cross-tenant read/write with a valid-but-wrong-tenant JWT — must fail at the DB layer even with a hypothetical application bug |
| Owner/Tenant audience cross-use | Owner token against tenant endpoint and vice versa — both must be rejected |
| AI Memory cross-tenant leakage | Including provider-level prompt-cache leakage, not just DB-level |
| Studio config isolation | 5 concurrent tenants defining conflicting-looking custom fields/objects, verify zero collision |
| Support impersonation boundary | Impersonation grant scoped to exactly the consented tenant, cannot pivot to a second tenant within the same grant |

**Target:** 100% pass, run on every PR touching any tenant-scoped surface, permanently — not a pre-GA-only exercise.

### 11.1 Reusable Cross-Tenant Regression Harness (STORY-01-04, Sprint 02)

Every domain was independently hand-writing the same create-as-tenant-A /
read-as-tenant-B pair (see `domains/decision_center/tests/test_postgres_repo.py`,
written to close GA-P0-SEC-01 in Sprint 01/02). `tests/support/tenant_isolation.py`
extracts that pattern once:

- `assert_cross_tenant_read_blocked(create_as, read_as, tenant_a=, tenant_b=)`
  — for `get_x(id, tenant_id) -> X | None`-shaped methods.
- `assert_cross_tenant_listing_excludes(create_as, list_as, identify=, tenant_a=, tenant_b=)`
  — for `list_x(tenant_id) -> list[X]`-shaped methods.

Both are two-sided by design: they fail if tenant B can see tenant A's
record, **and** fail if tenant A can't see its own — a helper that "passes"
only by hiding everything from everyone is isolation failing in the other
direction, not a fix. Failures raise `CrossTenantIsolationViolation` (not a
bare `AssertionError`) with both tenant identifiers, the record key, and
the leaked value in the message, so a CI failure here is legible without
opening the test file.

Not a pytest fixture — plain async functions, called from inside a test —
because what needs isolating differs per domain (a repository method, a
service method, a router function called directly) and no single fixture
shape covers all of them without hiding what's actually being asserted.

**Real consumers (not just demos):**
- `tests/unit/test_decision_center_harness_demo.py` — Decision Center,
  proving the harness agrees with the existing hand-written coverage.
- `tests/unit/test_meeting_brief_tenant_isolation.py` — a second,
  independently-discovered cross-tenant IDOR (`POST /meetings/{id}/brief`
  in `app/routers/meetings.py`, missing the tenant check every sibling
  endpoint in `app/routers/opportunities.py` already had), found while
  picking a real demonstration target for this story and fixed under the
  Sprint Execution Contract's small-fix carve-out — see
  `docs/program/RISK_REGISTER.md`.

**Verified catch:** the harness was run against `get_decision` with its
tenant_id predicate temporarily deleted (simulating the general regression
class, not one specific historical diff) — it failed loudly with the exact
leaked record. It was also run against a revert to the *original*
pre-Sprint-01 JSONB-path query shape — that one still passed, a genuinely
informative negative result recorded in the test file's docstring: for
well-formed metadata the two query shapes isolate identically, meaning the
dedicated indexed column's real value is robustness against malformed
metadata, not a difference observable via this kind of black-box replay.

---

## 12. AI Evaluation

**Scope:** Quality/correctness of AI outputs, distinct from infrastructure correctness.

| Area | Method |
|---|---|
| ICP scoring accuracy | Backtest against real historical won/lost Opportunity data, precision/recall reported |
| AI Outreach copy quality | Human review sample (≥20 generated messages per release) scored against a rubric (relevance, brand-voice adherence, factual grounding) |
| PII scrubbing effectiveness | Manual audit of ≥100 real InteractionNote samples post-scrub, zero PII leakage tolerance |
| Guardrail effectiveness (`AI-GR-001`-`006`) | Adversarial prompt-injection test set run against every guardrail-protected endpoint |

---

## 13. LLM Regression Testing

**Scope:** Detect silent quality degradation when an underlying model version changes (provider-side updates are outside SalesOS's control but must not silently degrade tenant-facing output).

| Mechanism | Detail |
|---|---|
| Golden-output test set | A fixed set of prompts with human-scored "acceptable" reference outputs, re-run against every model update |
| Automated similarity scoring | Flags any output that drifts significantly from the golden reference for human review |
| Alerting | A failed LLM regression run blocks promoting a new default model tier to production until reviewed |

**Target:** Established in Phase 6 (Sprint 25), running continuously post-GA against every provider model update.

---

## 14. Acceptance Tests

**Scope:** Business-readable, tied directly to `PRODUCT_ROADMAP.md` phase acceptance criteria and `PRODUCTION_READINESS_CHECKLIST.md` items — the layer that answers "is this feature actually done" in terms a non-engineer stakeholder can verify.

| Mechanism | Detail |
|---|---|
| Given/When/Then scenarios | Written per epic in `PROGRAM_PLAN.md`'s Definition of Done, executed at each phase gate |
| CPO/Program Director sign-off | Required at every phase Go/No-Go gate per `PRODUCT_ROADMAP.md`, based on acceptance test results, not engineering self-attestation alone |
| Traceability | Every acceptance test traces back to a specific story ID (`STORY-{EPIC}-{NN}`), which traces to an epic, which traces to a phase, which traces to a business goal — no orphan tests |
