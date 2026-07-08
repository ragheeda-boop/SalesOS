# SalesOS — QUALITY GATE

> **معايير قبول الكود — الفحص الآلي قبل الدمج**
> Version 1.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## Purpose

Every pull request must pass all quality gates before merge. These gates are **automated** (run in CI) and **mandatory**. No exceptions without documented CTO override.

---

## GATE 1: Architecture Compliance

### Automated Checks
- [ ] **No cross-domain imports** — Arch test verifies domain isolation
- [ ] **No circular dependencies** — Arch test detects circular imports
- [ ] **No infrastructure imports in domain layer** — Domain is pure Python
- [ ] **No SDK bypass** — Cross-cutting concerns go through SDK
- [ ] **Capability template followed** — New capabilities match template
- [ ] **No Frozen Interface modification** — (requires ADR)

### Manual Review
- [ ] Follows Runtime Architecture execution model
- [ ] Follows 4-layer architecture (Kernel → Platform → Business → App)
- [ ] Events registered in Event Catalog
- [ ] Capability registered in Capability Catalog

---

## GATE 2: Code Quality

### Automated
- [ ] **Ruff** — All rules pass
- [ ] **Black** — Formatting applied (line length 100)
- [ ] **mypy** — Strict mode passes. No `Any` without justification
- [ ] **No debug/print statements** — Automated search
- [ ] **No hardcoded secrets** — `.gitguard` or equivalent scan
- [ ] **No TODO/FIXME without ticket number** — `TODO(SALES-NNN)`
- [ ] **Security scan** — `bandit` passes (Python), `npm audit` passes (JS/TS)

### Manual Review
- [ ] Google-style docstrings on public API
- [ ] Structured logging (not print)
- [ ] Error messages follow RFC 7807

---

## GATE 3: Testing

### Automated
- [ ] **Unit tests pass** — All existing + new tests
- [ ] **Coverage** — >85% on new business logic
- [ ] **No flaky tests** — Tests are deterministic
- [ ] **Architecture constraint tests pass** — Domain isolation, import rules
- [ ] **Integration tests pass** — Against PostgreSQL (if applicable)

### Manual Review
- [ ] Tests use InMemoryRepository for unit tests
- [ ] No test depends on external services (API, DB, Network)
- [ ] Test <1 second each (unit suite <30s total)

---

## GATE 4: Events & Telemetry

### Automated
- [ ] **Domain events emitted** — Every mutation produces an event
- [ ] **Structured logging** — JSON logs with all required fields
- [ ] **Feature flag** — New features default OFF
- [ ] **Audit trail** — User mutations logged

### Manual Review
- [ ] Event type registered in Event Catalog
- [ ] Consumer map updated if new event consumed
- [ ] Feature flag documented with removal date

---

## GATE 5: Observability

### Automated
- [ ] **Tracing instrumented** — OpenTelemetry spans for new capability
- [ ] **Metrics registered** — Prometheus counters + histograms
- [ ] **No silent execution** — Every path produces observable output

### Manual Review
- [ ] SLA targets documented for new capability
- [ ] Error scenarios handled with proper status codes
- [ ] Timeout configured for new capability
- [ ] Circuit breaker configured (or justified not needed)

---

## GATE 6: AI Quality (if applicable)

### Automated
- [ ] **Eval results attached** — Accuracy, hallucination rate, confidence calibration
- [ ] **Semantic Cache used** — Query passes through cache before LLM
- [ ] **Cost tracked** — Token count logged to AI Governance

### Manual Review
- [ ] Prompt registered in AI Catalog
- [ ] Model registered in AI Catalog
- [ ] Guardrails enabled (PII detection, content filtering)
- [ ] Fallback model configured
- [ ] Budget tracking configured

---

## GATE 7: Documentation

### Automated
- [ ] **CHANGE LOG updated** — `PROJECT_STATUS.md` change log
- [ ] **OpenAPI schema** — Auto-generated from Pydantic

### Manual Review
- [ ] `CAPABILITY_CATALOG.md` updated (if new/modified capability)
- [ ] `EVENT_CATALOG.md` updated (if new events)
- [ ] `AI_CATALOG.md` updated (if new AI assets)
- [ ] `DATA_CONTRACTS.md` updated (if new integration)
- [ ] `DECISION_LOG.md` updated (if architectural decision)
- [ ] `PROJECT_STATUS.md` updated (completion %, debt)
- [ ] README updated (if project structure changed)
- [ ] ADR written (if architectural change)
- [ ] `MASTER_BLUEPRINT.md` updated (if architecture changed)

---

## GATE 8: UX & Accessibility (if UI)

### Automated
- [ ] **RTL layout verified** — Arabic UI renders correctly
- [ ] **Responsive design** — Mobile + desktop breakpoints work
- [ ] **Accessibility scan** — aXe or equivalent passes

### Manual Review
- [ ] Loading states shown during data fetch
- [ ] Error states handled gracefully
- [ ] Empty states have helpful messages
- [ ] All text is localizable (i18n)
- [ ] Keyboard navigation works
- [ ] Screen reader compatible

---

## GATE SUMMARY TABLE

```
Gate                     │ Auto  │ Manual │ Blocking │
─────────────────────────┼───────┼────────┼──────────┤
1: Architecture          │   6   │   4    │   ✅     │
2: Code Quality          │   7   │   2    │   ✅     │
3: Testing               │   5   │   3    │   ✅     │
4: Events & Telemetry    │   5   │   3    │   ✅     │
5: Observability         │   3   │   4    │   ✅     │
6: AI Quality (if AI)    │   3   │   5    │   ✅     │
7: Documentation         │   2   │   9    │   ✅     │
8: UX & Accessibility    │   3   │   6    │   ✅     │
                         │       │        │          │
TOTAL: 40+ checks        │  34   │  36    │ Mandatory│
```

---

## CI PIPELINE (GitHub Actions)

```yaml
name: Quality Gate
on: [pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ruff check .
      - run: black --check .
      - run: mypy --strict src/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: salesos_test
          POSTGRES_PASSWORD: test
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/ --cov=src/ --cov-fail-under=85

  arch-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/architecture/ --no-header -q

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: bandit -r src/ --confidence-level high
      - run: npm audit --audit-level=high  # if frontend changes

  ai-eval:
    runs-on: ubuntu-latest
    if: contains(github.event.pull_request.labels.*.name, 'ai')
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/run_ai_eval.py --report
```

---

## CTO OVERRIDE PROCESS

If a gate must be bypassed:

1. Create an issue documenting the reason
2. Assign to CTO for review
3. CTO approves (or rejects) with written rationale
4. Override recorded in `DECISION_LOG.md`
5. Technical debt created in `PROJECT_STATUS.md` Section 6
6. Override expires after 30 days — must be resolved

---

*This quality gate is binding on all SalesOS development. Every PR must pass all applicable gates. No exceptions without documented CTO override.*
