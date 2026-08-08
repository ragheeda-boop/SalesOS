# Verification Maturity Model

A single scale to answer *"where are we?"* — not just *"how many tools?"*.

```
Level 0  Manual
Level 1  Static Analysis
Level 2  Continuous Security
Level 3  Runtime Verification
Level 4  Continuous Verification
Level 5  Autonomous Enterprise Verification
```

## Level definitions

| Level | Name | Meaning |
|:-----:|------|---------|
| **0** | Manual | Verification by hand; evidence ad hoc; human-only gates |
| **1** | Static Analysis | SAST/secrets/vuln scans run in CI on push (not continuous, not policy-gated) |
| **2** | Continuous Security | Scans run continuously + contract/DB-policy checks; evidence collected per change |
| **3** | Runtime Verification | Live monitoring, error capture, load & uptime observability on running systems |
| **4** | Continuous Verification | Deploy auto-blocked on P0; chaos + policy-as-code; single evidence pipeline |
| **5** | Autonomous Enterprise Verification | AI Review Council + EAB consume one automated report; owner makes final call |

## Tool → level map (current + planned)

| Capability | Level | Status today |
|------------|:-----:|:------------:|
| Gitleaks | L1 | ✅ Implemented |
| Semgrep | L1 | ✅ (auto) → L2 curated (P2) |
| Bandit | L1 | ✅ Implemented |
| Trivy | L1 | ✅ Implemented |
| pip-audit / npm audit | L1 | ✅ Implemented |
| CodeQL (own analysis) | L1→L2 | 🔵 SARIF consumer → 🟡 (P2) |
| Schemathesis | L2 | 🟡 (P2) |
| pgTAP | L2 | 🟡 (P2) |
| OpenAPI contract test | L2 | 🔵 Existing alternative |
| Custom RLS adversarial tests | L2 | 🔵 Existing alternative |
| Sentry | L3 | 🟡 (P3) |
| Better Stack | L3 | 🟡 (P3) |
| k6 | L3 | 🟡 (P3) |
| Prometheus + Grafana + Loki | L3 | ✅ Implemented (self-hosted) |
| OWASP ZAP | L2→L3 | 🟡 (P3) |
| OPA / Conftest | L4 | 🟡 (P3) |
| Chaos (LitmusChaos) | L4 | 🟡 (P3) |
| Evidence Collector | L4 | 🟡 (P3) — manual `evidence/` today |
| AI Review Council | L5 | 🟡 (P3) |
| Enterprise Audit Board | L5 | ✅ Manual today → automated (P3) |

## Current position

**Level 1.5 ≈ today** — static analysis implemented; continuous/contract/DB-policy not yet automated. Target after Phase 2 → **L2+**; after Phase 3 (CVP) → **L4**; AI Council/EAB automation → **L5**.

> Track this file. One year from now you should be able to state a number (e.g. "we are at Level 2.8"), not just a tool count.

---

*docs/vnext/verification-platform/MATURITY-MODEL.md — 2026-08-07*
