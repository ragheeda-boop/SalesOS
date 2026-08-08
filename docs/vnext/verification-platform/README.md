# Verification Platform — Vision (vNext)

> **Category:** Backlog / Future Capability for the **next release**.
> **NOT** part of current GA governance. Do not read these documents as GA requirements.
> **Phase:** Engineering CLOSED (current GA); this platform is post-GA.

---

## Purpose

A **continuous, evidence-driven verification platform** that turns audit from a pre-release activity into an always-on process — every push/merge runs security tools, executes OpenAPI + RLS checks, collects evidence, and gates deploys.

Single-owner reality: this is a **capability backlog**, not a governance SoT. The Enterprise Audit Board and current release artifacts remain the authority for the **current** GA decision.

## Status vocabulary

| Status | Meaning |
|--------|---------|
| ✅ **Implemented** | Exists and works today |
| 🟡 **Planned** | Scheduled after GA (Phase 2 / Phase 3) |
| 🔵 **Existing Alternative** | An existing substitute already fulfills the goal partially |
| ⚪ **Deferred** | Deliberately deferred (no active plan) |
| 🔴 **Required** | Required before this release (currently none in this backlog) |

## Phasing

| Phase | Name | Scope |
|-------|------|-------|
| **1** | Release GA (current) | **Frozen** — no tooling added |
| **0** | Post-GA sequence (owner decision 2026-08-07) | GA → Postmortem → Lessons Learned → **v1.0.1** → then Verification Platform (see ROADMAP) |
| **2** | Verification Platform Foundation | Semgrep hardening, CodeQL, Gitleaks, Trivy, Schemathesis, pgTAP |
| **3** | Continuous Verification Platform (CVP) | k6, OWASP ZAP, Chaos, Better Stack, OPA, Conftest |

## Documents

- [ROADMAP.md](./ROADMAP.md) — execution phases
- [GAP-ANALYSIS.md](./GAP-ANALYSIS.md) — implemented vs not-yet-implemented
- [CAPABILITY-MAP.md](./CAPABILITY-MAP.md) — capability → tool → status
- [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md) — post-GA plan
- [MATURITY-MODEL.md](./MATURITY-MODEL.md) — maturity scale (L0–L5) + tool placement
- [SUCCESS-METRICS.md](./SUCCESS-METRICS.md) — KPI report card
- [ADR/](./ADR/) — architecture decision records (ADR-001 CVP, ADR-002 SAST, ADR-003 DAST, ADR-004 Chaos)

---

*docs/vnext/verification-platform — 2026-08-07 — backlog for next release; not GA governance.*
