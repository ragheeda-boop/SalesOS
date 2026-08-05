# Release Checklist — v5.1.0-rc1

**Version:** v5.1.0-rc1 (Release Candidate 1)  
**Predecessor:** [v5.1.0-bootstrap-green](../v5.1.0-bootstrap-green/BOOTSTRAP_GREEN_REPORT.md)  
**ADR-102 Hardening applied:** 21 fixes across 6 domains  
**Date:** 2026-08-06  
**Validation:** not validated

---

## ADR-102 Hardening Applied (21 fixes)

### Quality (6)
| # | Fix | Detail |
|---|-----|--------|
| 1 | ESLint modernization | Removed `ignoreDuringBuilds`, promoted 6 rules `warn` → `error` |
| 2 | Prettier baseline | `.prettierrc` created (100w, 2-space, semicolons, single quotes); `format`/`format:check` scripts added |
| 3 | Ruff upgrade | `^0.4` → `^0.11`, added PL/RUF/PERF rule sets, target py312 |
| 4 | Mypy strictness | `ignore_missing_imports=false`, 6 strictness flags enabled, `domains/` added to files |
| 5 | Coverage threshold | `fail_under` 55 → 65, `branch=true` |
| 6 | EditorConfig | `.editorconfig` — UTF-8, LF, trailing whitespace, language-specific indents |

### Dependencies (3)
| # | Fix | Detail |
|---|-----|--------|
| 7 | Poetry unification (K4) | Docker pinned to Poetry 2.4.1, `poetry-core>=2.0` |
| 8 | Docker image pinning | 5 services pinned from `:latest` to specific versions |
| 9 | Kafka version standardization | All 4 compose files → `bitnami/kafka:3.6.2` |

### Security (3)
| # | Fix | Detail |
|---|-----|--------|
| 10 | JWT algorithm unification (K5) | RS256 enforced at boot via startup validator |
| 11 | TrustedHostMiddleware | Added to backend middleware stack, configured via `ALLOWED_HOSTS` |
| 12 | Content Security Policy | CSP and COOP headers added in `next.config.js` |

### CI/CD (3)
| # | Fix | Detail |
|---|-----|--------|
| 13 | deploy.yml fix | Fixed `needs.health-check` → `needs.deploy-backend-health-gate` |
| 14 | release-gates.yml | Created — typecheck, lint, test, security, build, healthcheck gates |
| 15 | docker-smoke.yml | Added `concurrency` group to prevent overlapping runs |

### Observability (3)
| # | Fix | Detail |
|---|-----|--------|
| 16 | MetricsTracker deprecation | Deprecated duplicate; callers migrated to canonical instance |
| 17 | Alert rule cleanup | Commented out 4 undeployed-exporter rules |
| 18 | Uptime alerts | Added BackendDown, FrontendDown, DatabaseDown alerts |

### Cross-cutting (3)
| # | Fix | Detail |
|---|-----|--------|
| 19 | next.config.js hardening | ESLint fix + CSP/COOP headers (already counted in Quality/Security) |
| 20 | pyproject.toml hardening | Ruff + Mypy + Coverage (already counted in Quality) |
| 21 | docker-compose.yml hardening | Image pinning + JWT RS256 (already counted in Dependencies/Security) |

> **Note:** Fixes 19–21 are rollup entries for multi-touch files. Distinct atomic changes = 21 across 18 files.

---

## Verification Gates

### Gate 1: Quality
- [ ] ESLint runs during build (no `ignoreDuringBuilds`)
- [ ] Prettier format check passes
- [ ] TypeScript typecheck: 0 errors
- [ ] Ruff lint passes
- [ ] Mypy type check passes
- [ ] Coverage >= 65%

### Gate 2: Build
- [ ] Backend Docker image builds
- [ ] Frontend Docker image builds
- [ ] Docker Compose up succeeds

### Gate 3: Services
- [ ] 14 services healthy
- [ ] Backend /health: `database=connected`
- [ ] Frontend HTTP 200

### Gate 4: Integration
- [ ] Login flow works
- [ ] Company list loads
- [ ] Search works

### Gate 5: Security
- [ ] JWT algorithm = RS256 (validated)
- [ ] TrustedHostMiddleware active
- [ ] CSP headers present
- [ ] No secrets in tracked files

### Gate 6: Observability
- [ ] Prometheus scraping /metrics
- [ ] Alertmanager healthy
- [ ] Grafana dashboards accessible

---

## Decision

- [ ] **GO** — All gates pass. Proceed to UX Architecture.
- [ ] **NO-GO** — One or more gates fail. Remaining issues logged below.

**Remaining Issues:**

| # | Gate | Description | Severity |
|---|------|-------------|----------|
|   |      |             |          |

---

## Next Milestone

**UX Architecture** — UX/UI Modernization per ADR-101 / ADR-102 roadmap.
