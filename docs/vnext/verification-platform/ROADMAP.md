# Verification Platform — Roadmap

**Scope:** post-GA capability roadmap. Current release (GA) is **frozen**; nothing here blocks or gates it.

---

## Phase 1 — Release GA (current) — FROZEN

- No tooling added. No changes to `docs/audit` governance.
- Release freeze until `2026-08-10T14:10Z`; soak + maintenance window + owner decision in flight.

## Phase 0 — Post-GA sequence (owner decision 2026-08-07)

Verification Platform does **not** start immediately after GA. Fixed order:

```
Production GA
   ↓
Postmortem (GA retrospective)
   ↓
Lessons Learned (recorded)
   ↓
v1.0.1 (first patch release)
   ↓
Verification Platform vNext (this roadmap, Phase 2 → Phase 3)
```

Rationale: the first release always surfaces lessons worth recording before building the next platform. This keeps release work and platform work separated.

## Phase 2 — Verification Platform Foundation

Trigger: after GA decision (owner), during steady-state.

| Item | Capability | Effort | Notes |
|------|-----------|--------|-------|
| Semgrep hardening | SAST (custom rules: RBAC/RLS/SSRF) | M | Move from `--config=auto` to curated rule packs + custom RBAC/tenant rules |
| CodeQL | Advanced SAST in CI | M | Add CodeQL analysis workflow (not only SARIF upload) |
| Gitleaks | Secret detection | S | Already running; harden config beyond stub |
| Trivy | Container + IaC + SBOM | S | Already running; add image scanning on every deploy image |
| Schemathesis | OpenAPI property-based testing | M | Drive from prod/staging `openapi.json`; detect unexpected cases |
| pgTAP | PostgreSQL / RLS policy tests | M | Test RLS + policies in DB (complement existing custom adversarial tests) |

Exit criteria: every push runs the foundation suite; SARIF artifacts land in GitHub code scanning; RLS/OpenAPI checks run in CI.

## Phase 3 — Continuous Verification Platform (CVP)

Trigger: Phase 2 stable + owner approval.

| Item | Capability | Effort | Notes |
|------|-----------|--------|-------|
| k6 | Load / soak tests | M | Scripted scenarios against staging; soak regression gate |
| OWASP ZAP | DAST (CSRF, Auth, SSRF) | M | Baseline + full scan scheduled; prod-safe active scan only in window |
| LitmusChaos (or Gremlin) | Chaos engineering | L | Kill Redis, drop DB, restart workers — on staging first |
| Better Stack | Uptime / alerting / logs | S | `/health` monitoring + on-call routing |
| OPA + Conftest | Policy as Code | M | Gate Docker/Terraform/YAML before deploy |
| Sentry | Error/exception capture | S | Runtime stack traces |

Exit criteria: single evidence collector aggregates all tool outputs; CVP blocks deploy on P0; AI Review Council consumes one report.

## Not Yet Implemented (explicit)

All Phase 2/3 items are **Not Yet Implemented** as of 2026-08-07 — none are GA blockers.

---

*docs/vnext/verification-platform/ROADMAP.md — 2026-08-07*
