# ADR-002 — SAST: Semgrep hardening + CodeQL

- **Status:** Proposed (post-GA, Phase 2)
- **Date:** 2026-08-07
- **Deciders:** Project Owner
- **Related:** GAP-ANALYSIS (SAST rows), IMPLEMENTATION-PLAN §2.1–2.2

## Context

Today: Semgrep runs `--config=auto` and CodeQL only consumes SARIF (no own analysis). The codebase's top concerns — RBAC/tenant-scoping/SSRF — are not covered by generic rules.

## Decision

1. **Semgrep:** replace `--config=auto` with curated rule packs + **custom rules** for RBAC role-check consistency, missing tenant-scope on queries, and SSRF-prone URL fetching.
2. **CodeQL:** add a dedicated analysis workflow (Python): auth bypass, SQL injection, insecure deserialization. Keep SARIF ingestion.

## Consequences

- **+** Rules match the actual risk surface (tenant isolation, RBAC).
- **+** CodeQL provides deep dataflow analysis Semgrep cannot.
- **−** Custom rule authoring + false-positive tuning effort (M).
- **−** Two engines to maintain.

## Alternatives considered

- Keep auto-only Semgrep: rejected — misses project-specific RBAC/tenant bugs.
- Single engine: rejected — Semgrep (pattern) + CodeQL (dataflow) are complementary.

---

*ADR-002 — verification-platform — 2026-08-07*
