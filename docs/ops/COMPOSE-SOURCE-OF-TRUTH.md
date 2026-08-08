# Compose Source of Truth — SalesOS

**Date:** 2026-08-06  
**Finding:** EAB-001-P1-OPS-02  
**Validation:** light validated (docs + Grep/Read)  
**GA claim:** **None** — this document does not assert production readiness.

---

## Decision (DEC-style)

| Role | Path | Status |
|------|------|--------|
| **Authoritative local/dev stack** | `salesos/docker-compose.yml` | **SoT** — use this for SalesOS local bring-up |
| **Production overlay (non-cloud)** | `salesos/docker-compose.prod.yml` | Authoritative prod *compose shape* for compose-based deploys |
| **Staging overlay** | `salesos/infra/staging/docker-compose.staging.yml` | Staging parity work; not a substitute for signed soak |
| **Test overlay** | `salesos/docker-compose.test.yml` | CI/test only |
| **Frontend-only helper** | `salesos/frontend/docker-compose.yml` | Narrow FE helper — not platform SoT |
| **Repo-root compose** | `docker-compose.yml` (workspace root) | **LEGACY / QUARANTINED** — do not treat as SalesOS SoT |

**Rationale:** Dual compose stories (root vs `salesos/`) caused Celery/event-bus/port confusion (EAB). Merging stacks is out of scope for this wave (too large). Honesty fix = declare one SoT and quarantine the rest.

---

## Operator rules

1. From a clean machine: `cd salesos && docker compose up --build -d` (not repo root).
2. Do **not** invent parity between root and `salesos/` — they may diverge (ports, Celery, Kafka profile, monitoring mounts).
3. `EVENT_BUS_TYPE` defaults to **`in_memory`** even when Kafka containers exist — Kafka in compose ≠ Kafka event bus in use.
4. Staging/prod cutover still requires [DR-GA-GAPS-CHECKLIST.md](./DR-GA-GAPS-CHECKLIST.md) items CLOSED with human signatures.

---

## Footguns (sharp edges)

| Footgun | Truth |
|---------|--------|
| Root compose header once said “Canonical” | Quarantined; banner points here |
| Root postgres often on host `6432` | `salesos/` uses `5432` + PgBouncer `6432` — do not mix stacks on one host without port review |
| Kafka image | Authoritative stacks use `confluentinc/cp-kafka:7.7.2` (not bitnami 3.6.2) |
| Celery | Present on some root/prod stories; may be absent on local `salesos/` — check the file you actually started |
| Merging dual compose | **Deferred** — explicit human program; not this wave |
| MinIO `objectstore` profile | Optional local object store for **drill rehearsal** only — starting MinIO ≠ offsite DR closed; never commit real keys; `S3_BUCKET` often empty on `backup` |
| `backup` profile | Manual: `docker compose --profile backup run --rm backup backup-db` — volume `backup_data` is single-host; not offsite |
| Primary WAL | Stock postgres has `archive_mode=off` — do not claim PITR from compose alone |

---

## Related

- [DR_RUNBOOK.md](./DR_RUNBOOK.md) — DR procedures (gaps remain OPEN)
- [DR-GA-GAPS-CHECKLIST.md](./DR-GA-GAPS-CHECKLIST.md) — cutover blockers
- [RUNTIME_STACK.md](./RUNTIME_STACK.md)
- EAB finding: `EAB-001-P1-OPS-02`
