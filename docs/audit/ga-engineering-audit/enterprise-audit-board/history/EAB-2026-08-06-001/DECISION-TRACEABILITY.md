# Decision Traceability Matrix — EAB-2026-08-06-001 (Axis 40)

**Legend:** ✓ present | △ partial | ✗ break/missing | STUB | n/a  
**Sample only** — not full capability inventory.  
**Validation:** light validated

| Decision ID | Vision | Bible | Cap | ADR/DEC | Impl | API | UI | Tests | Runtime | Monitoring | Break notes | Finding IDs |
|-------------|:------:|:-----:|:---:|:-------:|:----:|:---:|:--:|:-----:|:--------:|:----------:|-------------|-------------|
| Decision Center | ✓ | △ | ✓ | △ DEC/ADR | ✓ | △ | ✓ | △ | △ | ✗ | Long-lived `_dc_session`; **HTTP SoT** `/api/v1/decisions*` (Stream C) | EAB-001-P0-DUP-01 partial, EAB-001-P0-SEC-02 |
| Decision Platform HTTP | ✓ | △ | ✓ | △ | ✓ | ✓ | △ | △ | △ | ✗ | Sole owner `/api/v1/decision/*` after Runtime remount | EAB-001-P0-DUP-01 partial |
| Decision Runtime (DIE) | △ | △ | ✓ | △ | ✓ | △ | △ | △ | △ | ✗ | Remounted `/api/v1/decision-runtime` (engines retained) | EAB-001-P0-DUP-01 partial |
| FE `@salesos/decision-platform` | △ | △ | ✓ | ADR-033 Proposed | **STUB** | n/a | STUB | △ | ✗ | ✗ | Twin labeled private; same name residual | EAB-001-P0-DUP-01, EAB-001-P1-AIGOV-01 partial |
| Search | ✓ | ✓ | ✓ | △ | ✓ | △ | ✓ | △ | △ | ✗ | Dual routers; paths non-colliding (DUP-02 doc) | EAB-001-P1-DUP-02 partial |
| Auth / SSO | ✓ | ✓ | ✓ | DEC-RS256 | ✓ | ✓ | ✓ | △ | △ | △ | CSRF/JWT strong; factory fail-open undermines | EAB-001-P0-SEC-01 |
| Entity Resolution | ✓ | ✓ | ✓ | ADR-025 | ✓ | ✓ | △ | △ | △ | ✗ | Not default post-import hop | EAB-001-P1-LINEAGE-01 |
| Graph / KG | ✓ | ✓ | ✓ | ADR-028 | ✓ | ✓ | ✓ | △ | △ | ✗ | Neo4j in compose; completeness open | EAB-001-P1-LINEAGE-01 |
| AI / Copilot | ✓ | △ | ✓ | AI_HONESTY | △ | ✓ gate | ✓ gate | △ | △ | △ | Flag False; not GA | EAB-001-P1-AIGOV-01 |
| Webhooks | ✓ | △ | ✓ | ADR-031 | ✓ | △ | △ | △ | △ | ✗ | Multi families / SSRF history | EAB-001-P1-DUP-02 |
| Comm Hub | △ | △ | △ | △ | △ | △ | △ | △ | △ | ✗ | Progress docs exist; end-to-end not validated | — |

**G-05:** 0/8 primary rows fully ✓ across all hops → **~0% completion**.

---

*DTM — EAB-2026-08-06-001*
