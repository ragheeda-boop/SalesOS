# Findings Recheck — EAB-2026-08-06-002

**Baseline:** [EAB-2026-08-06-001 FINDINGS](../EAB-2026-08-06-001/FINDINGS.md) + [REMEDIATION-PROGRAM-STATUS](../EAB-2026-08-06-001/REMEDIATION-PROGRAM-STATUS.md)  
**Evidence:** [EVIDENCE-LOG.md](./EVIDENCE-LOG.md)  
**Rule:** Disposition from **new executable evidence**, not remediation claims alone.

---

## Summary counts

| New disposition | Count |
|-----------------|------:|
| **Confirmed Fixed** | **9** |
| **Still Partial** | **4** |
| **Still Deferred** | **3** |
| **Regressed** | **0** |
| **Not Proven** | **0** |
| **Total** | **16** |

---

## P0

### EAB-001-P0-SEC-01 — middleware fail-open / missing factory

| Field | Value |
|-------|-------|
| Prior disposition | Fixed (Wave 1; light probe) |
| Evidence result | Factory assignment in `startup.py`; fail-closed **503** in entitlement / suspended / API-key middleware; **39/39** middleware unit tests; live `/api/v1/decisions` → **401** (not skip/200) |
| New disposition | **Confirmed Fixed** |
| Residual | Live 503-without-factory path not chaos-injected; e2e suite blocked by TrustedHost (separate) |

### EAB-001-P0-SEC-02 — lifetime sessions + BYPASSRLS empty password

| Field | Value |
|-------|-------|
| Prior disposition | Fixed (Wave 1+2) |
| Evidence result | `FactoryBoundRepository` / no process-lifetime `_timeline_session` pattern (prior verify + static); `config.py` refuses empty `APP_POSTGRES_PASSWORD` outside allowed ENV; container `JWT_ALGORITHM=RS256` |
| New disposition | **Confirmed Fixed** |
| Residual | Live SQL GUC assertion under load **not validated**; host `.env` HS256 leftover possible (compose pins RS256) |

### EAB-001-P0-FE-01 — blank SSR providers + tokens SoT

| Field | Value |
|-------|-------|
| Prior disposition | Fixed (build not validated) |
| Evidence result | `providers.tsx` no blank `return null`; sync runtime; `globals.css` imports tokens; `npx tsc --noEmit` **exit 0**; targeted decision tests **48/48** |
| New disposition | **Confirmed Fixed** (SSR/tokens intent) |
| Residual | `npm run lint` / `npm run build` fail on ESLint (~528 errors) — **orthogonal** to FE-01 blank-gate; no browser paint evidence |

### EAB-001-P0-DUP-01 — multi decision engines + route collisions

| Field | Value |
|-------|-------|
| Prior disposition | Partial (HTTP remount) |
| Evidence result | OpenAPI + live probes: `/api/v1/decision/*` and `/api/v1/decision-runtime/*` both present; evaluate GET→405 (POST routes live). Engines not deleted; FE package-name twin remains |
| New disposition | **Still Partial** |
| Residual | ≥3 BE engines + FE twin name; clients must follow [DECISION-API-SOT](../EAB-2026-08-06-001/DECISION-API-SOT.md) |

### EAB-001-P0-OPS-01 — DR / WAL / offsite / staging

| Field | Value |
|-------|-------|
| Prior disposition | Deferred |
| Evidence result | `docs/ops/DR-GA-GAPS-CHECKLIST.md` rows 1–5 still **OPEN** / UNSIGNED; no WAL/offsite/staging soak executed this run |
| New disposition | **Still Deferred** |
| Residual | **Launch blocker** for Production GA / cutover |

---

## P1

### EAB-001-P1-DRIFT-01 — MetaData islands

| Field | Value |
|-------|-------|
| Prior disposition | Partial (freeze) |
| Evidence result | Remeasured `MetaData(` → **19** matches / 18 files (not reduced) |
| New disposition | **Still Partial** |

### EAB-001-P1-OPS-02 — dual compose

| Field | Value |
|-------|-------|
| Prior disposition | Fixed (SoT honesty) |
| Evidence result | Root compose quarantine banner; `docs/ops/COMPOSE-SOURCE-OF-TRUTH.md`; runtime used `salesos/` stack healthy |
| New disposition | **Confirmed Fixed** (honesty/SoT) |
| Residual | Dual files remain; merge deferred |

### EAB-001-P1-SEC-03 — Tenant ContextVar reset

| Field | Value |
|-------|-------|
| Prior disposition | Fixed |
| Evidence result | `TenantContextMiddleware` `finally: reset_current_tenant_id`; `database.py` reset helper; covered under middleware unit suite green |
| New disposition | **Confirmed Fixed** |

### EAB-001-P1-ADR-01 — ADR index / Kafka claim

| Field | Value |
|-------|-------|
| Prior disposition | Fixed |
| Evidence result | `docs/adr/0101-…` + `0102-…` exist; index Accepted rows present; Kafka 7.7.2 on running compose |
| New disposition | **Confirmed Fixed** |

### EAB-001-P1-SES-01 — SES baseline

| Field | Value |
|-------|-------|
| Prior disposition | Fixed (stub + waiver) |
| Evidence result | `docs/compliance/SES-BASELINE.md` present |
| New disposition | **Confirmed Fixed** |
| Residual | Full SES pack still thin (waiver territory) |

### EAB-001-P1-LINEAGE-01 — lineage honesty

| Field | Value |
|-------|-------|
| Prior disposition | Fixed (honesty map) |
| Evidence result | Honesty map artifacts present under ga-engineering-audit; `/health` still reports `kafka: in_memory` — pipeline not claimed GA |
| New disposition | **Confirmed Fixed** (honesty disposition) |
| Residual | End-to-end governed pipeline still broken by design |

### EAB-001-P1-DUP-02 — search / webhook / prompt dupes

| Field | Value |
|-------|-------|
| Prior disposition | Partial (doc register) |
| Evidence result | No remount/consolidation evidence this run; OpenAPI still multi-family surfaces |
| New disposition | **Still Partial** |

### EAB-001-P1-AIGOV-01 — AI governance fragmentation

| Field | Value |
|-------|-------|
| Prior disposition | Partial |
| Evidence result | `feature_ai_copilot=False`; FE decision STUB labeled + tests; HTTP SoT remount live; twin package / multi-engine explainability residual |
| New disposition | **Still Partial** |

### EAB-001-P1-DOC-01 — dual bible / superseded GO

| Field | Value |
|-------|-------|
| Prior disposition | Fixed |
| Evidence result | PROJECT_BIBLE GO/NO-GO deferral to audit; AGENTS.md authority chain intact |
| New disposition | **Confirmed Fixed** |
| Residual | Superseded vNext files still on disk (quarantine/banner dependent) |

---

## P2

### EAB-001-P2-FIT-01 — fitness not in CI

| Field | Value |
|-------|-------|
| Prior disposition | Deferred (plan only) |
| Evidence result | No CI fitness subset activated; G-06 remains **0%** |
| New disposition | **Still Deferred** |

### EAB-001-P2-SEC-04 — CSRF bypass under SALESOS_TESTING

| Field | Value |
|-------|-------|
| Prior disposition | Deferred (mitigated) |
| Evidence result | Bypass retained for tests by design; prod/staging pin claims not re-proven beyond prior compose docs; not exercised as fail-open in live probes |
| New disposition | **Still Deferred** (mitigated) |

---

## Matrix (quick)

| ID | Prior → New |
|----|-------------|
| SEC-01 | Fixed → **Confirmed Fixed** |
| SEC-02 | Fixed → **Confirmed Fixed** |
| FE-01 | Fixed → **Confirmed Fixed** |
| DUP-01 | Partial → **Still Partial** |
| OPS-01 | Deferred → **Still Deferred** |
| DRIFT-01 | Partial → **Still Partial** |
| OPS-02 | Fixed → **Confirmed Fixed** |
| SEC-03 | Fixed → **Confirmed Fixed** |
| ADR-01 | Fixed → **Confirmed Fixed** |
| SES-01 | Fixed → **Confirmed Fixed** |
| LINEAGE-01 | Fixed → **Confirmed Fixed** |
| DUP-02 | Partial → **Still Partial** |
| AIGOV-01 | Partial → **Still Partial** |
| DOC-01 | Fixed → **Confirmed Fixed** |
| FIT-01 | Deferred → **Still Deferred** |
| SEC-04 | Deferred → **Still Deferred** |

**Regressions:** none observed against remediation intent.  
**Suite noise:** TrustedHost / Invalid host header impairs e2e + some unit API tests — track as **new residual risk** (not a reopening of SEC-01 fail-open).

---

*Findings Recheck — EAB-2026-08-06-002 — build validated with gaps — no commit*
