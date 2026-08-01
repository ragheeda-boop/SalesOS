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

# 19 â€” EXECUTION STRATEGY

> How to sequence work toward GA given the frozen no-go posture. Authority: `docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md` (Waves 0â€“14). This file is a pointer + prioritization aid, NOT a license to proceed ahead of Human gates.

## 1. Priority axis

| Priority | Theme | Evidence gate |
|---|---|---|
| P0 | Close critical security findings (SQLi, CI secrets, deploy outputs) | Security score rises; gitleaks green |
| P0 | Unblock CI-08 (GHCR) and CI-09 (VPS/SSH) | CI run evidence |
| P0 | Fix e2e CI services so e2e can actually run | Playwright green in CI |
| P1 | Enable refresh-token families (password reset, refresh rotation) when approved — verify live enabled-state first (T-013) | Migration verified, security tests |
| P1 | Replace decision STUB with Decision Center APIs | feature_ai_copilot gates still honest |
| P1 | Align capability registries (4-way) | registry drift check passes |
| P2 | Implement stubbed runtimes (workflow, agent, simulation) | capability tests green |
| P2 | Replace 11 empty FE packages | build unaffected, e2e green |
| P3 | ADR index cleanup (Human-owned) | consistency report accepted |

## 2. Strategy notes

- Work in **waves** per PRODUCTION_PLAN; do not jump ahead of Human gates.
- Keep **parallel ready** agents on independent clusters (see `31` Â§2) even when CI is blocked (DEC-107).
- Every change carries a validation label (AGENTS.md Â§5). No silent "fixed".
- Security middleware, auth, RLS, audit logging, evidence gates: never weakened without approval (AGENTS.md Â§4).

## 3. When this file changes

- When waves/priorities change (Human authority). Mirror `20`, `30`, `21`.
