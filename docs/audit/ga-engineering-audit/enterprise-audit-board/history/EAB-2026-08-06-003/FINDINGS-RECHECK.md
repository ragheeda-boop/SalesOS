# Findings Recheck — EAB-2026-08-06-003

**Prior chain:** [EAB-001 FINDINGS](../EAB-2026-08-06-001/FINDINGS.md) → [EAB-002 FINDINGS-RECHECK](../EAB-2026-08-06-002/FINDINGS-RECHECK.md) → [POST-VERIFY](../EAB-2026-08-06-002/REMEDIATION-POST-VERIFY.md) + [PROGRAM-STATUS](../EAB-2026-08-06-001/REMEDIATION-PROGRAM-STATUS.md)  
**Evidence:** [EVIDENCE-LOG.md](./EVIDENCE-LOG.md)  
**Rule:** Disposition from **new executable evidence**, not remediation claims alone.

---

## Summary counts

| New disposition | Count |
|-----------------|------:|
| **Confirmed Fixed** | **9** |
| **Still Partial** | **5** |
| **Still Deferred** | **2** |
| **Regressed** | **0** |
| **Not Proven** | **0** |
| **Total** | **16** |

**vs EAB-002 recheck:** Partial **4→5**, Deferred **3→2** — FIT-01 advanced Deferred→Partial in post-verify; **reconfirmed** this run (host fitness subset exit 0 + workflow present). Suite residual (TrustedHost / unit 14 fail / jest 13 fail) from EAB-002 **did not regress**.

---

## P0

### EAB-001-P0-SEC-01 — middleware fail-open / missing factory

| Field | Value |
|-------|-------|
| Prior disposition | Confirmed Fixed (EAB-002) |
| Evidence result | Factory wiring in `startup.py`; fail-closed **503** in entitlement / suspended / API-key middleware; middleware unit **39/39**; live `/api/v1/decisions` → **401**; invalid API key → **401** |
| New disposition | **Confirmed Fixed** |
| Residual | Live 503-without-factory chaos path not injected |

### EAB-001-P0-SEC-02 — lifetime sessions + BYPASSRLS empty password

| Field | Value |
|-------|-------|
| Prior disposition | Confirmed Fixed (EAB-002) |
| Evidence result | Container `JWT_ALGORITHM=RS256`; compose pin `JWT_ALGORITHM: RS256`; unit suite fully green (includes password/config paths exercised in suite mass) |
| New disposition | **Confirmed Fixed** |
| Residual | Host `.env` HS256 leftover possible (documented; **not** edited); live SQL GUC under load **not validated** |

### EAB-001-P0-FE-01 — blank SSR providers + tokens SoT

| Field | Value |
|-------|-------|
| Prior disposition | Confirmed Fixed (EAB-002) |
| Evidence result | `providers.tsx` no blank `return null` gate; `npx tsc --noEmit` **exit 0**; full `npm test` **2492 pass / 0 fail** |
| New disposition | **Confirmed Fixed** (SSR/tokens intent) |
| Residual | `npm run lint` **~528** errors — orthogonal to FE-01; build gate not re-run; no browser paint |

### EAB-001-P0-DUP-01 — multi decision engines + route collisions

| Field | Value |
|-------|-------|
| Prior disposition | Still Partial (EAB-002 / post-verify) |
| Evidence result | OpenAPI: `/api/v1/decision/*` (13) + `/api/v1/decision-runtime/*` (9); evaluate GET→**405** both; engines not deleted |
| New disposition | **Still Partial** |
| Residual | ≥3 BE engines + FE package-name twin; follow DECISION-API-SOT |

### EAB-001-P0-OPS-01 — DR / WAL / offsite / staging

| Field | Value |
|-------|-------|
| Prior disposition | Still Deferred (launch blocker) |
| Evidence result | `DR-GA-GAPS-CHECKLIST.md` rows 1–5 still **OPEN / UNSIGNED**; no WAL/offsite/staging soak this run |
| New disposition | **Still Deferred** |
| Residual | **Launch blocker** for Production GA / cutover |

---

## P1

### EAB-001-P1-DRIFT-01 — MetaData islands

| Field | Value |
|-------|-------|
| Prior disposition | Still Partial (freeze) |
| Evidence result | Remeasured `MetaData(` → **19** matches / **18** files; FF-09 ceiling check **PASS** (≤19) |
| New disposition | **Still Partial** |

### EAB-001-P1-OPS-02 — dual compose

| Field | Value |
|-------|-------|
| Prior disposition | Confirmed Fixed (honesty/SoT) |
| Evidence result | Runtime used `salesos/` healthy stack; COMPOSE-SOURCE-OF-TRUTH present |
| New disposition | **Confirmed Fixed** (honesty/SoT) |
| Residual | Dual files remain; merge deferred |

### EAB-001-P1-SEC-03 — Tenant ContextVar reset

| Field | Value |
|-------|-------|
| Prior disposition | Confirmed Fixed |
| Evidence result | Middleware unit **39/39** still green; no regression signal |
| New disposition | **Confirmed Fixed** |

### EAB-001-P1-ADR-01 — ADR index / Kafka claim

| Field | Value |
|-------|-------|
| Prior disposition | Confirmed Fixed |
| Evidence result | ADR-101/102 + index retained; stack healthy (Kafka service up) |
| New disposition | **Confirmed Fixed** |

### EAB-001-P1-SES-01 — SES baseline

| Field | Value |
|-------|-------|
| Prior disposition | Confirmed Fixed |
| Evidence result | `docs/compliance/SES-BASELINE.md` present |
| New disposition | **Confirmed Fixed** |
| Residual | Full SES pack still thin |

### EAB-001-P1-LINEAGE-01 — lineage honesty

| Field | Value |
|-------|-------|
| Prior disposition | Confirmed Fixed (honesty) |
| Evidence result | `/health` still `kafka: in_memory` — pipeline not claimed GA |
| New disposition | **Confirmed Fixed** (honesty disposition) |

### EAB-001-P1-DUP-02 — search / webhook / prompt dupes

| Field | Value |
|-------|-------|
| Prior disposition | Still Partial (register) |
| Evidence result | No remount/consolidation this run; CAPABILITY-DUP-REGISTER retained under EAB-002 |
| New disposition | **Still Partial** |

### EAB-001-P1-AIGOV-01 — AI governance fragmentation

| Field | Value |
|-------|-------|
| Prior disposition | Still Partial |
| Evidence result | `feature_ai_copilot=False`; FF-07 **PASS**; FE decision STUB tests green; twin / multi-engine residual |
| New disposition | **Still Partial** |

### EAB-001-P1-DOC-01 — dual bible / superseded GO

| Field | Value |
|-------|-------|
| Prior disposition | Confirmed Fixed |
| Evidence result | PROJECT_BIBLE GO deferral present; FF-12 SUPERSEDED banners **PASS** |
| New disposition | **Confirmed Fixed** |

---

## P2

### EAB-001-P2-FIT-01 — fitness not in CI

| Field | Value |
|-------|-------|
| Prior disposition | Deferred (EAB-002) → **Partial / implemented-minimal** (post-verify) |
| Evidence result | Workflow `.github/workflows/fitness-ci-subset.yml` present; host `fitness-ci-subset.ps1` **exit 0** (FF-07/09/10/12) |
| New disposition | **Still Partial** (implemented-minimal) |
| Residual | Not full FF catalog; remote GH Actions green **not validated** this run; G-06 not 100% |

### EAB-001-P2-SEC-04 — CSRF bypass under SALESOS_TESTING

| Field | Value |
|-------|-------|
| Prior disposition | Still Deferred (mitigated) |
| Evidence result | Bypass retained for tests by design; not exercised as fail-open in live probes |
| New disposition | **Still Deferred** (mitigated) |

---

## Matrix (quick)

| ID | Prior (EAB-002 / post-verify) → New |
|----|-------------------------------------|
| SEC-01 | Confirmed Fixed → **Confirmed Fixed** |
| SEC-02 | Confirmed Fixed → **Confirmed Fixed** |
| FE-01 | Confirmed Fixed → **Confirmed Fixed** |
| DUP-01 | Still Partial → **Still Partial** |
| OPS-01 | Still Deferred → **Still Deferred** |
| DRIFT-01 | Still Partial → **Still Partial** |
| OPS-02 | Confirmed Fixed → **Confirmed Fixed** |
| SEC-03 | Confirmed Fixed → **Confirmed Fixed** |
| ADR-01 | Confirmed Fixed → **Confirmed Fixed** |
| SES-01 | Confirmed Fixed → **Confirmed Fixed** |
| LINEAGE-01 | Confirmed Fixed → **Confirmed Fixed** |
| DUP-02 | Still Partial → **Still Partial** |
| AIGOV-01 | Still Partial → **Still Partial** |
| DOC-01 | Confirmed Fixed → **Confirmed Fixed** |
| FIT-01 | Deferred→Partial (post-verify) → **Still Partial** |
| SEC-04 | Still Deferred → **Still Deferred** |

**Regressions:** none.  
**Post-verify suite claims:** unit 0-fail, e2e 42/42, FE jest greens — **reconfirmed** under EAB-003 heavy re-execution (full FE suite also green).

---

*Findings Recheck — EAB-2026-08-06-003 — build validated with gaps — no commit*
