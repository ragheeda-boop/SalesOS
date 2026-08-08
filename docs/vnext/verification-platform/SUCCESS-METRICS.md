# Success Metrics (KPIs)

The single report card for the verification platform. Review quarterly against these targets; report the current number beside each row.

| KPI | Target | Current (2026-08-07) | Baseline source |
|-----|:------:|:--------------------:|-----------------|
| P0 escaped to production | **0** | 0 (tracked from GA) | release-gates / deploy logs |
| Mean verification time | **< 15 min** | not measured yet | CI timings (P2: Schemathesis/pgTAP) |
| Automated evidence | **> 95%** | low (manual evidence today) | EAB evidence dirs |
| Manual review time | **< 30 min** | not measured yet | EAB run reports |
| False positive rate | **< 5%** | not measured yet | SARIF review backlog |
| Security coverage | **> 95%** | partial (SAST ✅ / DAST 🟡) | GAP-ANALYSIS map |
| API contract coverage | **100%** | partial (contract test 🔵) | `test_openapi_contract.py` |
| RLS policy coverage | **100%** | partial (adversarial tests 🔵) | `test_adversarial_rls_story_04_01.py` |

## Rules

1. **Never claim a KPI met** without command/log/artifact evidence (validation-honesty labels apply).
2. Targets are **post-GA** — none gate the current release.
3. Update `Current` column only at quarterly review with evidence links.

---

*docs/vnext/verification-platform/SUCCESS-METRICS.md — 2026-08-07*
