# Verification Platform — Capability Map

Maps the problems you care about to tools and their current status. **Future capabilities are Not Yet Implemented — none are current-GA requirements.**

| Capability | Primary tool(s) | Status | Existing alternative |
|------------|-----------------|:------:|----------------------|
| SAST (RBAC/RLS/SSRF) | Semgrep (curated) | ✅ (auto) → 🟡 (hardened P2) | Bandit (generic Python) |
| Advanced SAST | CodeQL | 🔵 (SARIF consumer) → 🟡 (own analysis P2) | — |
| Secret leakage | Gitleaks + Trivy fs | ✅ | — |
| Container/IaC vulns | Trivy (image + config) | ✅ | — |
| Python deps | pip-audit | ✅ | — |
| JS deps | npm audit | ✅ | — |
| DAST (CSRF/Auth/SSRF) | OWASP ZAP | 🟡 (P3) | manual probes (read-only audit 08-07) |
| OpenAPI edge cases | Schemathesis | 🟡 (P2) | 🔵 `test_openapi_contract.py` |
| DB policy / RLS | pgTAP | 🟡 (P2) | 🔵 custom adversarial RLS tests |
| DB activity audit | pgAudit | 🟡 (P3) | audit_logs table |
| Load / soak | k6 | 🟡 (P3) | 🔵 `wave11-soak-gate.py` (health loop) |
| Chaos (stop Redis/DB/workers) | LitmusChaos / Gremlin | 🟡 (P3) | — |
| Uptime / alerting / logs | Better Stack | 🟡 (P3) | ✅ Prometheus + Grafana + Loki (self-hosted) |
| Error/exception capture | Sentry | 🟡 (P3) | backend structured logs |
| Policy as Code (Docker/Terraform/YAML) | OPA + Conftest | 🟡 (P3) | — |
| Evidence collection → board | Evidence Collector + EAB | ✅ (manual today) → 🟡 (automated CVP P3) | `evidence/` dirs + EAB run reports |
| Deploy gate on P0 | CVP auto-block | 🟡 (P3) | manual owner decision today |

---

## Mapping to known incident classes

| Problem | Tool chain | Status today |
|---------|------------|:------------:|
| RBAC / Tenant Escape | Semgrep + pgTAP + Schemathesis | Partial (Semgrep auto, custom RLS tests, contract test) |
| SSRF | OWASP ZAP + Semgrep | ZAP Not Yet Implemented (P3) |
| Secret leak | Gitleaks + Trivy | ✅ |
| Production downtime | Better Stack + Grafana + Sentry | Grafana ✅; Better Stack/Sentry 🟡 |
| Soak failure | k6 + Better Stack + Sentry | soak-gate script ✅; k6/etc 🟡 |
| RLS silent bypass | pgTAP + custom integration | Custom ✅; pgTAP 🟡 |
| CSRF bypass | OWASP ZAP + Schemathesis | Manual probe ✅; automated 🟡 |
| WAL / Backup integrity | automated restore tests + pgAudit | Restore drills ✅ (ops01-pitr); pgAudit 🟡 |
| Evidence integrity | OPA + Conftest + EAB | EAB manual ✅; OPA/Conftest 🟡 |

---

*docs/vnext/verification-platform/CAPABILITY-MAP.md — 2026-08-07*
