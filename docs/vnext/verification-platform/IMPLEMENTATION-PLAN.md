# Verification Platform — Implementation Plan (post-GA)

**Trigger:** only after the current release decision (owner) and the change freeze lift.
**Rule:** never bundles into a release; each item is its own work package with its own approval. **No P0 here.**

---

## Phase 2 — Foundation (sequence)

### 2.1 Semgrep hardening
- Replace `--config=auto` with curated rule packs.
- Add custom rules for the patterns this codebase cares about: RBAC role check consistency, tenant-scoping (missing `get_current_tenant_id` on queries), SSRF-prone URL fetching.
- Wire findings into code scanning SARIF (already in place).
- **Accept:** new rules have zero false-positive noise gate on the 3 RBAC-critical domains.

### 2.2 CodeQL (own analysis)
- Add a dedicated CodeQL workflow (currently only SARIF upload consumed).
- Python analysis: auth bypass, SQL injection, insecure deserialization.
- **Accept:** code scanning shows CodeQL results alongside Bandit/Semgrep/Trivy.

### 2.3 Gitleaks hardening
- Move from stub config to a maintained `.gitleaks.toml` (custom entropy + block-list tokens).
- Keep blocking behavior.

### 2.4 Trivy image scanning
- Extend deploy workflows to scan the built images (`backend`, `frontend`, `migrate`) for CRITICAL/HIGH.
- Keep SBOM generation (already present).

### 2.5 Schemathesis
- Add a CI job that pulls prod/staging `openapi.json` and runs property-based tests against staging (never prod).
- Watch: CSRF/tenant-header injection during schema-driven tests; run under staging creds only.
- **Accept:** 0 unexpected server errors on a stable schema diff.

### 2.6 pgTAP
- Add DB-level tests for RLS policies + roles (complement `test_adversarial_rls_story_04_01.py`).
- Run against staging DB or scratch Postgres (never prod writes).

---

## Phase 3 — CVP (sequence)

### 3.1 k6
- Script core journeys (login → list → read → write on staging).
- Add soak-regression scenario to CI (shorter than 72h; the 72h remains the gate).

### 3.2 OWASP ZAP
- Baseline scan on staging per push; full active scan scheduled weekly.
- Active scan against prod only inside a maintenance window (owner-approved).

### 3.3 Chaos (LitmusChaos first, Gremlin if prod-class needed)
- Staging-only: kill Redis, drop DB connection, restart workers; assert recovery + evidence.
- Never on prod without owner-approved window.

### 3.4 Better Stack
- `/health` uptime monitor + log shipping + on-call route.

### 3.5 OPA + Conftest
- Policy as Code: gate compose/terraform/YAML against required policies (no `:latest`, secrets rules, RLS config).

### 3.6 Sentry
- SDK + ingestion; capture exceptions in staging first.

### 3.7 Evidence Collector + AI Review Council
- Single pipeline that aggregates all tool SARIF/reports → one evidence bundle → AI Review Council summary → owner gate.
- CVP blocks deploy on P0 automatically (target for the platform's end state).

---

## Sequencing guardrails

1. **Each item is independently reversible** — no coupled mega-deploy.
2. **Staging-first, prod-only-with-owner-window** for any active testing (ZAP/Chaos/k6).
3. **No new SoT docs** — this backlog lives in `docs/vnext/verification-platform/`; findings feed EAB runs, they do not replace them.
4. **Never marked 🔴 Required** for the current release.

---

*docs/vnext/verification-platform/IMPLEMENTATION-PLAN.md — 2026-08-07*
