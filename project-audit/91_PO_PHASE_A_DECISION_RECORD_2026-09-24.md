# 91 — PO Phase-A Decision Record: register acceptance, Phase 7 scope release, P2 sampling parameters (2026-09-24)

## Purpose

Records the PO's three Phase-A gate decisions verbatim, the constraints attached to each, and the standing invariants that remain in force regardless of them. This document **changes no code and writes no database**; it only records decisions a human decision-maker made in-session on 2026-09-24.

Decisions supersede prior framings where explicitly stated. They do **not** supersede the safety invariants listed in §3, which were read to the PO before decision A2 and remain unconditional.

---

## 1. Decision A1 — Capability-register methodology (gate G1)

**Accepted (PO, 2026-09-24).**

- The 132-row reconciled register (`project-audit/57_CAPABILITY_REGISTER_RECONCILIATION_2026-09-23.md` §2) is adopted as the single row-level source of truth for SalesOS capability tracking.
- **124/132 = 93.9%** becomes the operational complete fraction.
- The historical **89/113 = 78.8%** scalar is retired from active tracking and reclassified as a historical figure (an unaudited running total whose membership was never row-audited). It remains in the record (`AGENTS.md` header history, report 57 §4) for traceability, but is no longer the operative denominator.
- Bare-scalar tracking stops; further reporting is row-level against the 132-row register.

## 2. Decision A2 — Phase 7 scope (gate G7)

**SUPERSEDES the 2026-08-29 Option B (implementation-planning only).**

The PO opened **Phase 7 implementation** in scope, effective immediately, **with explicitly accepted and tracked risk**. The review gates G2 (2,661 P3 pairs) and G3 (36 short-CR accounts) are **not** closed by decision; the PO acknowledged this before choosing, and the choice is recorded as "open implementation now with accepted/tracked risk."

What this authorizes:
- Phase 7 code implementation, feature engineering, and DB work scoped to the Phase 7 roadmap, informed by the Phase 6 evidence outputs (enrichment/quality/readiness reviews, entity-resolution improvements, sales-readiness segments).
- Normal engineering lifecycle for Phase 7 work: design → implementation → migration(s) → tests → evidence reports, following the repository's established conventions (single Alembic head, `tenant_isolation_<table>` RLS + FORCE + GUC-pinned stores, honest degradation, proof-first reporting).

What this does **NOT** authorize (standing invariants, reaffirmed in §3):
- Automatic merging of any fuzzy candidate under any condition (the 2,661 P3 pairs remain `final_review_required=YES`; never auto-merge, including perfect-score pairs).
- Automatic adjudication of any government identifier (the 36 short-CR accounts require individual human judgment; no batch rule).
- Production ingestion / production DB writes / Apollo / external API calls.
- Opening the production-readiness gate (G8), which remains not-open.

**Risk acknowledgment (tracked):** the PO accepts that Phase 7 implementation proceeds while the human review populations (2,661 pairs + 36 short-CR) remain pending, and that any Phase 7 work consuming Phase 6 outputs must treat those populations as un-reviewed. The mitigation is that Phase 7 work consuming identity/quality/readiness data must not assume those accounts are adjudicated, and cannot auto-resolve them.

## 3. Decision A3 — P2 sampling parameters (gate G5)

**Accepted as proposed (PO, 2026-09-24).**

For the P2 tier (46,736 accounts, by definition single-source with no cross-source corroboration):
- **3%** random sample of the `SALES_READY_WITH_REVIEW`-eligible P2 subset.
- **1%** random sample of the remaining P2 subset (`ENRICHMENT_REQUIRED` and any other non-ready remainder).
- **No P2 account is treated as sales-usable until its stratum's sample has passed review with the PO-set acceptance threshold** (threshold remains PO-set; draft 2% referenced in decision record §2.2 applies to the P1 Tier-B spot-check, not yet to P2 unless the PO adopts it).
- Sampling is stratified by readiness (usable-proximity), not uniform.

---

## 4. Standing invariants (unconditional, not superseded by A1–A3)

1. **Never auto-merge** any fuzzy candidate; P3 pairs stay human-only (contract + ADR-0104).
2. **Never auto-adjudicate** a government identifier (CR) ambiguity (government-ID hard veto).
3. **No production writes, no production DB access, no Apollo, no external API calls** by any work performed under these decisions.
4. **Source immutability** of MUHIDE source rows/raw payload; corrections only via provenance/derived values/conflicts/audit.
5. **Global-ID stability**: existing G-C/G-P IDs never change, regenerate, recycle, or reassign.
6. **Only `salesos_test` DB scope** for any DB work (production `salesos` forbidden).
7. **Phase 7 does not start on data that requires the still-pending human reviews** to be safe — it may build tooling/systems around it but may not assume adjudication and may not resolve the pending populations itself.
8. **AI honesty labels** unchanged; no demo-only code promoted to production claims.

---

## 5. Register row effect

The accepted register (report 57 §2) is **unchanged by A1–A3**: 124/132 COMPLETE proposed; the 8 BLOCKED rows (40, 46, 52, 53, 59, 60, 131, 132) stay BLOCKED *as completion* even though A2 unblocks Phase 7 *implementation*. In particular row 40 (Review Queue / Phase 7-A/B/C) is not promoted by A2 — the human review work is still outstanding; only the code-implementation blocker on Phase 7 is lifted. Promoting any row still requires its own evidence + closure report.

## 6. Explicit production statement

**Production is NOT approved. ** G8 (production-readiness gate) was not part of A1–A3, was not asked, and is not answered by this record. Nothing here authorizes production ingestion or deployment.

---

## Sign-off

| Field | Value |
|---|---|
| Decided by | Ragheb (PO) |
| Decided at | 2026-09-24 |
| Decisions | A1 accepted · A2 Phase 7 implementation opened with tracked risk · A3 sampling accepted |
| Constraints | §3 invariants read back and reaffirmed before A2 |
| Artifacts | Decision recorded; register totals in headers updated per A1; gate index updated |
| Attestation | AGENT-EXECUTED per explicit user directive 2026-09-24 (verbatim: "افتح التنفيذ الآن مع تباع المخاطر") |