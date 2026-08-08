# ADR-003 — DAST: OWASP ZAP

- **Status:** Proposed (post-GA, Phase 3)
- **Date:** 2026-08-07
- **Deciders:** Project Owner
- **Related:** GAP-ANALYSIS (DAST), IMPLEMENTATION-PLAN §3.2

## Context

SAST (Semgrep/CodeQL) and runtime probes catch code-level issues, but **runtime** attacks (CSRF bypass, auth flow, SSRF through live routes) need an active scanner against the deployed app.

## Decision

Adopt **OWASP ZAP**:

1. **Baseline scan** on staging per push (passive + safe active).
2. **Full active scan** weekly on staging.
3. **Active scan against prod only inside an owner-approved maintenance window.**

## Consequences

- **+** Detects CSRF/Auth/SSRF issues SAST misses.
- **−** Active scans can be noisy / generate load → staging-first, prod-in-window only.
- **−** Needs CSRF/tenant-header-aware configuration to avoid false positives on this app's middleware.

## Alternatives considered

- Burp Suite: commercial, heavier; ZAP is open-source and CI-friendly.
- Keep manual probes only: rejected — not continuous.

---

*ADR-003 — verification-platform — 2026-08-07*
