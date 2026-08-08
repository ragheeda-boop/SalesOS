# Enterprise Audit Board — Runs Index

**Pack:** v2.2  
**Rule:** One row per pack-based run. No invented scores.

| Run ID | Date | Scope | Type | Overall | Prod Readiness | Drift | AI Gov | Maturity | Path | Status |
|--------|------|-------|------|---------|----------------|-------|--------|----------|------|--------|
| EAB-2026-08-06-001 | 2026-08-06 | SalesOS (`salesos/`) + governance docs | Baseline | ~46 / **production no-go** | ~41 | raw 129 / score **0** | ~39 | **L2** | [EAB-2026-08-06-001/RUN-REPORT.md](./EAB-2026-08-06-001/RUN-REPORT.md) | **closed** |
| EAB-2026-08-06-002 | 2026-08-06 | SalesOS — verify vs EAB-001 remediations | **Verification Run** | ~51 / **production no-go** | ~49 | raw 122 / score **0** | ~43 | **L2** | [EAB-2026-08-06-002/RUN-REPORT.md](./EAB-2026-08-06-002/RUN-REPORT.md) | **closed** |
| EAB-2026-08-06-003 | 2026-08-06 | SalesOS — verify vs EAB-002 + post-verify | **Verification Run** | ~54 / **production no-go** | ~53 | raw 122 / score **0** | ~44 | **L2** | [EAB-2026-08-06-003/RUN-REPORT.md](./EAB-2026-08-06-003/RUN-REPORT.md) | **closed** |

**Sibling (not indexed as EAB run):** [PRINCIPAL-AUDIT-BOARD-2026-08-06.md](../../PRINCIPAL-AUDIT-BOARD-2026-08-06.md)

### Comparison (EAB-001 → EAB-002 → EAB-003)

| Axis | Baseline | EAB-002 | EAB-003 | Δ (002→003) |
|------|--------:|--------:|--------:|------------:|
| Production Readiness (39) | ~41 | ~49 | ~53 | **+4** |
| Security (30) | ~70 | ~78 | ~81 | **+3** |
| AI Governance (43) | ~39 | ~43 | ~44 | **+1** |
| Drift raw / score (41) | 129 / 0 | 122 / 0 | 122 / 0 | raw **0**; score unchanged |
| Classification | production no-go | production no-go | production no-go | unchanged (OPS-01 Deferred) |

---

*Runs Index — Enterprise Audit Board v2.2 — EAB-003 Verification Run registered 2026-08-06*
