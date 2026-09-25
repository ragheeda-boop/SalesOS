# 104 — PO decision record: G3/G4/G5 recommendations (2026-09-25)

**Signed:** Ragheed Almadani (PO) — 25/09/2026. Signature given in the session chat: "اوافق على الكل ودى توقيقي ragheed almadani 25/09/2026".
**Source:** recommendations in [report 103](103_G3_G4_G5_GATE_ANALYSIS_AND_RECOMMENDATIONS_2026-09-25.md).

## Approved decisions

| # | Decision |
|---|---|
| G3-1 | An NCNP number is not a commercial registration. For the 34 NCNP accounts among the 36, the CR anchor is removed as a derived value (the source is unchanged) and the number is kept as an NCNP registration identifier. The 2 SOCPA accounts are reviewed individually by a human. |
| G3-2 | Add a source-aware rule that excludes NCNP values from CR anchors in derived classification, then run a Phase 6 dry run to measure the effect before any real run. |
| G4-1 | Full review of the 666 field conflicts and 489 weak-identity accounts. A 5% sample of the 5,753 corroboration accounts, stratified by source. Any P1 whose only anchor is NCNP moves to full review. If the sample error exceeds 2%, the full 5,753 are reviewed. |
| G5-1 | Neither stratum is accepted on the internal-consistency 0%. The error is redefined as real-world error, measured by a ~50-account spot check stratified by source. |
| G5-2 | G3-2 is applied before the G5 error is measured. |

## Open (not answered by this signature)

- **G5-3 (product):** are non-profits and government bodies part of the sales ICP? Report 103 posed this as a question, not a proposed answer. It stays open until answered explicitly.

## Unchanged

- The decisions approve the **method**. They close no gate. G3/G4/G5 close only with a closure report once the approved method has been executed.
- Report 91 invariants apply in full: no auto-merge, source immutability, Global-ID stability, `salesos_test` only, no production writes. Production is **NOT APPROVED**.
