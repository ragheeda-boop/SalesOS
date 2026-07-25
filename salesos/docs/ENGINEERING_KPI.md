# SalesOS — Engineering KPIs

> **Sprint 0.5 Deliverable: Platform Freeze**
> Date: 2026-07-17 | Status: 🧊 IMMUTABLE (baseline)
>
> Key Performance Indicators for measuring engineering execution.
> All future sprints report against these baselines.

---

## 1. Architecture Compliance KPI

| KPI | Baseline | Target | Measurement | Frequency | Owner |
|-----|----------|--------|-------------|-----------|-------|
| Overall Compliance Score | 85% | ≥ 95% | `scripts/arch-compliance.ps1` | Per sprint | Chief Architect |
| Identity Compliance | 100% | ≥ 95% | Compliance script | Per sprint | Backend Engineer |
| Widget SDK Compliance | 70% | ≥ 95% | Compliance + file scan | Per sprint | Frontend Engineer |
| Company Compliance | 95% | ≥ 95% | Compliance script | Per sprint | Backend Engineer |
| Search Compliance | 88% | ≥ 95% | Compliance script | Per sprint | Backend Engineer |
| Scoring Compliance | 92% | ≥ 95% | Compliance script | Per sprint | Backend Engineer |
| CRM Compliance | 88% | ≥ 95% | Compliance script | Per sprint | Frontend Engineer |
| AI Compliance | 82% | ≥ 95% | Compliance script | Per sprint | AI Engineer |
| Timeline Compliance | 78% | ≥ 95% | Compliance script | Per sprint | Backend Engineer |
| Workflow Compliance | 48% | ≥ 95% | Compliance script | Per sprint | Workflow Engineer |

**Trend target**: +1% per sprint until 95% reached (target: Sprint 12)

---

## 2. Technical Debt KPI

| KPI | Baseline | Target | Measurement | Frequency | Owner |
|-----|----------|--------|-------------|-----------|-------|
| Critical TD Items | 1 | 0 | Technical Debt Register | Per sprint | CTO |
| High TD Items | 6 | ≤ 3 | Technical Debt Register | Per sprint | Chief Architect |
| Total Active TD | 12 | ≤ 10 | Technical Debt Register | Per sprint | Engineering Team |
| TD Resolution Rate | — | ≥ 2 resolved/sprint | Technical Debt Register | Per sprint | Engineering Team |
| TD Aging (Critical) | 0 days | ≤ 30 days | Register date stamps | Per sprint | CTO |
| TD Aging (High) | 0 days | ≤ 60 days | Register date stamps | Per sprint | Chief Architect |

**Trend target**: Net debt reduction every sprint. Zero critical debt by Sprint 1. Zero high debt by Sprint 3.

---

## 3. Quality KPI

| KPI | Baseline | Target | Measurement | Frequency | Owner |
|-----|----------|--------|-------------|-----------|-------|
| Unit Test Coverage | 93% | ≥ 85% (maintain) | `pytest --cov` | Per sprint | QA Engineer |
| Integration Coverage | 70% | ≥ 70% (maintain) | `pytest --cov` | Per sprint | QA Engineer |
| E2E Coverage | 60% | ≥ 60% (maintain) | Playwright report | Per sprint | QA Engineer |
| Total Tests | 2,110+ | ≥ 2,000 (maintain) | Test runner count | Per sprint | QA Engineer |
| Test Pass Rate | 100% | 100% | CI pipeline | Per commit | CI/CD |
| New Feature Coverage | — | ≥ 85% for new code | `pytest --cov` | Per PR | Code Reviewer |
| Coverage Regression | 0% | ≤ -1% per release | Comparison vs baseline | Per release | QA Engineer |

**Trend target**: Maintain 100% pass rate. No coverage regression > 1% per release.

---

## 4. Performance KPI

| KPI | Baseline | Target | Measurement | Frequency | Owner |
|-----|----------|--------|-------------|-----------|-------|
| GET /companies/{id} p95 | 6ms | < 100ms | `benchmark/run.py` | Per release | Performance Reviewer |
| POST /search p95 | 6ms | < 100ms | `benchmark/run.py` | Per release | Performance Reviewer |
| GET /dashboard p95 | 88ms | < 200ms | `benchmark/run.py` | Per release | Performance Reviewer |
| GET /timeline p95 | 100ms | < 100ms | `benchmark/run.py` | Per release | Performance Reviewer |
| POST /decision/evaluate p95 | 30ms | < 100ms | `benchmark/run.py` | Per release | Performance Reviewer |
| Partial Search p95 | < 50ms | < 100ms | `benchmark/run.py` | Per release | Performance Reviewer |
| HTTP Load Test p95 | BLOCKED | All budgets met | Load test script | Post-S1 | Performance Reviewer |
| Lighthouse Performance | Not measured | > 90 | Lighthouse CI | Per release | QA Engineer |
| Lighthouse Accessibility | Not measured | > 95 | Lighthouse CI | Per release | QA Engineer |

**Trend target**: All endpoints within 2x budget at all times. HTTP load testing unblocked by end of Sprint 1.

---

## 5. Security KPI

| KPI | Baseline | Target | Measurement | Frequency | Owner |
|-----|----------|--------|-------------|-----------|-------|
| Security Posture | 10/10 | ≥ 9.5/10 | `scripts/security-audit.ps1` | Per release | Security Reviewer |
| Critical Vulnerabilities | 0 | 0 | Trivy + Bandit + Semgrep | Per commit | CI/CD |
| High Vulnerabilities | 0 | 0 | Dependency audit | Per commit | CI/CD |
| Auth Coverage | 100% | 100% | Route scan | Per release | Security Reviewer |
| Secrets in Code | 0 | 0 | GitLeaks | Per commit | CI/CD |

**Trend target**: Zero tolerance for all security violations.

---

## 6. Velocity KPI

| KPI | Baseline | Target | Measurement | Frequency | Owner |
|-----|----------|--------|-------------|-----------|-------|
| Sprint Velocity | 58 pts/sprint | ≥ 50 pts/sprint | Sprint tracking | Per sprint | Sprint Planner |
| Planned Points | 60 pts | ≥ 50 pts | Sprint planning | Per sprint | Sprint Planner |
| Scope Change | +3 pts | ≤ +5 pts | Sprint tracking | Per sprint | Product Director |
| Velocity Trend | — | Stable or improving | 3-sprint rolling avg | Per sprint | Engineering Team |
| Unplanned Work | — | ≤ 20% of sprint | Sprint retrospective | Per sprint | Engineering Team |

**Trend target**: Predictable velocity within ±10% per sprint.

---

## 7. Documentation KPI

| KPI | Baseline | Target | Measurement | Frequency | Owner |
|-----|----------|--------|-------------|-----------|-------|
| Documentation Score | 9.5/10 | ≥ 9/10 | Engineering Dashboard | Per release | Documentation Engineer |
| CHANGELOG Updated | ✅ | Always current | File check | Per release | Changelog Manager |
| ADR Compliance | 8 ADRs | All changes via ADR | ADR directory | Per release | Chief Architect |
| API Docs Updated | ✅ | Always current | Portal check | Per release | Backend Engineer |
| README Updated | ✅ | Always current | Per-package check | Per release | Documentation Engineer |

---

## 8. Executive Summary Dashboard

```
KPI DASHBOARD (Baseline: 2026-07-17)
═══════════════════════════════════════

ARCHITECTURE     ████████░░  85%    🟡 Target: 95%
TEST COVERAGE    █████████░░ 93%    🟢 Target: ≥ 85%
SECURITY         ████████████ 10/10 🟢 Target: ≥ 9.5/10
PERFORMANCE      ████████░░  8.2/10 🟡 Target: 9/10
TECH DEBT        ████████░░  12     🟡 Target: ≤ 10
VELOCITY         █████████░░ 58/s   🟢 Target: ≥ 50/s
DOCUMENTATION    █████████░░ 9.5/10 🟢 Target: ≥ 9/10
PROD READINESS   █████████░░ 9/10   🟢 Target: ≥ 9/10
```

---

## 9. KPI Change Protocol

1. **KPIs are measured** at baseline and tracked per sprint
2. **KPI regression** > 5% triggers review by Chief Architect
3. **KPI regression** > 10% triggers sprint halt and remediation
4. **New KPIs** may be added by ADR only
5. **KPI targets** are frozen — changing a target requires ADR
6. **All KPIs** are reported in the ENGINEERING_DASHBOARD at each sprint end
