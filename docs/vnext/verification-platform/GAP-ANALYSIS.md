# Verification Platform — Gap Analysis

**Method:** verified against the repo as of 2026-08-07 (CI workflows + compose + tests).
**Vocabulary:** Not Yet Implemented (NOT "missing") — these are **Future Capabilities**, not GA defects.

---

## Implemented today

| Layer | Tool | Where | Notes |
|-------|------|-------|-------|
| Secrets | Gitleaks | `.github/workflows/security-scan.yml` | Blocking (continue-on-error removed) |
| Vuln/Secrets/IaC/SBOM | Trivy | `security-scan.yml` + `deploy-production.yml` | fs + config + SBOM (SPDX) SARIF |
| Python deps | pip-audit | `security-scan.yml` | `--strict`, named ignore PYSEC-2026-1325 |
| JS deps | npm audit | `security-scan.yml` | `--audit-level=moderate` |
| Python SAST | Bandit | `security-scan.yml` | SARIF |
| Generic SAST | Semgrep | `security-scan.yml` | `--config=auto` (Phase 2: harden) |
| SARIF consumption | CodeQL upload-action | `ci.yml`, `security-scan.yml` | Consumes Bandit/Semgrep/Trivy SARIF |
| Forbidden files | custom check | `security-scan.yml` | `*.env`/`*.key`/`*.pem` etc. |
| Monitoring | Prometheus + Grafana + Alertmanager + Loki + OTel | `salesos/docker-compose.yml` (GA-P2-03) | incl. exporters, `prometheus-token` guard |
| RLS (custom) | `tests/integration/test_adversarial_rls_story_04_01.py` | backend tests | 🔵 Existing Alternative for pgTAP |
| API contract | `tests/contract/test_openapi_contract.py` | backend tests | 🔵 Existing Alternative for Schemathesis |
| Config guard | `.semgrepignore`, `.trivyignore`, `.gitleaks.toml` | repo root | scoped scans |

## Not Yet Implemented (Future Capabilities)

| Layer | Tool | Phase | Notes |
|-------|------|-------|-------|
| Advanced SAST | CodeQL analysis (own rules) | 2 | Currently SARIF consumer only |
| SAST hardening | Semgrep curated rules | 2 | RBAC/RLS/SSRF custom rules |
| OpenAPI property testing | Schemathesis | 2 | Drive from live openapi.json |
| DB policy tests | pgTAP | 2 | RLS/policy unit tests in PG |
| DAST | OWASP ZAP | 3 | CSRF/Auth/SSRF active testing |
| Load | k6 | 3 | Scripted scenarios + soak regression |
| Chaos | LitmusChaos / Gremlin | 3 | Staging first |
| Uptime/alerting | Better Stack | 3 | External SaaS |
| Policy as Code | OPA + Conftest | 3 | Gate Docker/Terraform/YAML |
| Error capture | Sentry | 3 | Runtime exceptions |
| DB audit | pgAudit | 3 | DB activity audit trail |

## Status summary

| Status | Count | Items |
|--------|:-----:|-------|
| ✅ Implemented | 10 | Gitleaks, Trivy, pip-audit, npm audit, Bandit, Semgrep, SARIF consumer, forbidden-files, Prometheus/Grafana/OTel, config guards |
| 🔵 Existing Alternative | 2 | custom RLS tests, openapi contract test |
| 🟡 Planned (Phase 2) | 4 | CodeQL analysis, Semgrep hardening, Schemathesis, pgTAP |
| 🟡 Planned (Phase 3) | 7 | ZAP, k6, Chaos, Better Stack, OPA/Conftest, Sentry, pgAudit |
| ⚪ Deferred | — | (none active) |
| 🔴 Required (before current GA) | **0** | — |

> None of the Not Yet Implemented items are required for the current release decision.

---

*docs/vnext/verification-platform/GAP-ANALYSIS.md — 2026-08-07 — repo-verified.*
