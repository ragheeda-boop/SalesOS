# ADR-001 — Continuous Verification Platform (CVP)

- **Status:** Proposed (post-GA)
- **Date:** 2026-08-07
- **Deciders:** Project Owner
- **Related:** README, ROADMAP, IMPLEMENTATION-PLAN

## Context

Verification is currently manual/pre-release: EAB runs, soak script, read-only audits. To reach Stripe/GitHub-class assurance, verification must run **after every push/merge**, collect evidence, and gate deploys.

## Decision

Adopt a **Continuous Verification Platform** as the target end-state (Phase 3):

1. Run all security tools (SAST/DAST/secret/vuln) on every push.
2. Execute OpenAPI property tests + PostgreSQL/RLS policy checks.
3. Collect all outputs into a single **Evidence Collector**.
4. AI Review Council summarizes into one report.
5. Block deploy automatically on P0.

## Consequences

- **+** Audit becomes continuous; owner sees one evidence bundle per change.
- **+** P0 auto-block reduces human gate fatigue.
- **−** Cost: pipeline maintenance, tool versions, false-positive tuning.
- **−** Requires staging-first discipline; prod-active scans only in windows.

## Alternatives considered

- Keep manual EAB-only: rejected — repeats pre-release-only audit gap.
- Buy managed CVP: possible later; start with open tools (Semgrep/CodeQL/ZAP/k6/OPA).

---

*ADR-001 — verification-platform — 2026-08-07*
