# `infrastructure/` — STATUS: PENDING REMOVAL

> **Do not add files here. Do not move `salesos/infra/` here.**

**Classification:** Legacy candidate — empty scaffold, disposition unresolved.
**Authority:** [`ADR-100: Repository Canonicalization`](../docs/adr/0100-repository-canonicalization.md), Gap Analysis §4; `REPOSITORY_HEALTH_GATE_2026-08-05.md` §6–7.
**Marked:** 2026-08-05 (ADR-100 Phase 3 — Legacy Isolation)

## What this is

`infrastructure/cloud/`, `infrastructure/observability/`, and `infrastructure/scripts/` are empty directories with no known origin documented in `migration-log/`. The repository's real, populated infrastructure tree is `salesos/infra/` (Kubernetes manifests, Terraform, Docker, monitoring configs, staging compose files) — referenced by CI, the K8s deployment runbook, and `.engineering/24_REPOSITORY_MANIFEST.json`.

## Why this directory is not being deleted yet

Two possibilities were identified and neither has been confirmed:

1. Dead scaffolding with no purpose — safe to delete.
2. An intended future destination for relocating `salesos/infra/` upward — which would be a **high-blast-radius change** (touches K8s manifests, Terraform state references, CI workflows, and deployment runbooks) requiring its own dedicated ADR and migration-log phase, not a side effect of repository-topology cleanup.

**Default recommendation (per ADR-100):** delete as dead scaffolding, since no migration-log entry documents intent to populate it. This has **not been executed** — repository owner confirmation is required first.

## What happens next

See the **Pending Removal Register** in [`docs/architecture/LEGACY_ISOLATION_REGISTER.md`](../docs/architecture/LEGACY_ISOLATION_REGISTER.md) for the exact unblocking condition and next action.

This file is itself the only content permitted in this directory tree until that decision is made.
