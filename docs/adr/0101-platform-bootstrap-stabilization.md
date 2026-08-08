# ADR-101: Platform Bootstrap & Stabilization

**Status**: ACCEPTED  
**Date**: 2026-08-05  
**Author**: Principal Platform Engineer  
**Related**: ADR-100 (Repository Canonicalization); ADR-102 (Engineering Hardening)  
**Evidence pack:** [docs/releases/v5.1.0-bootstrap-green/](../releases/v5.1.0-bootstrap-green/)  
**Validation:** light validated (Docker Compose green). **Does not** change Production GA **NO-GO**.

---

## Context

After ADR-100 repository canonicalization, the platform still needed a clean install → build → Docker → healthcheck cycle. Agents and humans lacked a single accepted record that local compose could reach a green bootstrap without inventing production readiness.

---

## Decision

Accept **Green Bootstrap** (`v5.1.0-bootstrap-green` / `5.1.0-rc1`) as the platform stabilization baseline:

| Gate | Outcome (session evidence) |
|------|----------------------------|
| Docker Compose up | **14/14** services healthy (postgres, pgbouncer, neo4j, redis, zookeeper, kafka, schema-registry, backend, frontend, prometheus, grafana, alertmanager, postgres-exporter, redis-exporter) |
| TypeScript typecheck | **0** errors |
| Backend health | DB / cache / graph / redis connected |
| Frontend | HTTP 200 on `:3000` |
| Alembic | Migrations applied on local compose (head recorded in release pack) |

**Authoritative compose for this bootstrap:** `salesos/docker-compose.yml` (see [COMPOSE-SOURCE-OF-TRUTH.md](../ops/COMPOSE-SOURCE-OF-TRUTH.md)).

Known non-blocking issues at accept (later addressed or tracked in ADR-102): ESLint build bypass, Poetry Docker vs lock mismatch, JWT algorithm ambiguity in dev `.env`, Kafka available but `EVENT_BUS_TYPE` default `in_memory`.

---

## Consequences

**Positive:** Repeatable local green bootstrap; release pack under `docs/releases/v5.1.0-bootstrap-green/`; AGENTS.md session tag `v5.1.0-bootstrap-green`.

**Risks / honesty:**

- Bootstrap green ≠ production GO (audit remains **production no-go**).
- Quality bypasses present at ADR-101 accept were intentionally left for ADR-102.
- Dual root vs `salesos/` compose remained a footgun until OPS SoT docs (EAB Stream D).

## Next

ADR-102 Engineering Hardening → UX architecture / Phase 1 (see release + ADR-102).

## References

- [BOOTSTRAP_GREEN_REPORT.md](../releases/v5.1.0-bootstrap-green/BOOTSTRAP_GREEN_REPORT.md)
- [ARCHITECTURE_STATE.md](../releases/v5.1.0-bootstrap-green/ARCHITECTURE_STATE.md)
- [SERVICE_MATRIX.md](../releases/v5.1.0-bootstrap-green/SERVICE_MATRIX.md)
