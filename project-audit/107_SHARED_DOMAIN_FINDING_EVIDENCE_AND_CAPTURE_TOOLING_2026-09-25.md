# 107 — Shared-domain finding, reviewer evidence, and decision-capture tooling (2026-09-25)

**Context:** the owner's directive "يلا الكل" after report 106.
**What was done:**
- Machine evidence and suggestions added to the review workbooks.
- A tool to capture the human decisions.
- A second systematic finding, measured by dry run only.

**No decision was recorded, no real run was made, and no gate was opened.**

## 1. What was not done and why

The workbook decision columns were **left empty**. G3 is under the government-ID hard veto (report 91 §4.2). G4 and G5 require human review. Report 91 retired machine-generated dispositions labelled as human (the older `phase7a_capture_p1_evidence_review.py` pattern). The machine output below is marked `NOT A DECISION`.

## 2. Evidence added to the workbooks

`scripts/phase7a_enrich_gate_workbooks.py` uses local files only. It adds:
- domains and names per source;
- the relation between the domains (single, alias with the same base, or different bases);
- `machine_suggestion (NOT A DECISION)` with a reason.

| File | LIKELY_CORRECT | NEEDS_HUMAN |
|---|---:|---:|
| G4 field conflict (663) | 30 | 633 |
| G4 weak identity (491) | 0 | 491 |
| G4 corroboration sample (288) | 92 | 196 |
| G5 spot check (50) | 10 | 40 |

## 3. Decision-capture tooling

`scripts/phase7a_capture_gate_workbooks.py`:
- Dry run by default; `--apply` to write.
- Records a row only when it has a **decision, a reviewer name and a date**, and never reads the suggestion column.
- Rejects invalid decision values.
- Mapping:
  - G3 `CONFIRMED_VALID_CR / NOT_A_CR / UNRESOLVED_ESCALATE` → SHORT_CR dispositions.
  - G4 `CORRECT / MATERIAL_ERROR / CANNOT_VERIFY` → P1 `CONFIRM / ESCALATE / REVIEW`.
  - G5: computes the material error rate against the 2% threshold. There is no per-row write; stratum acceptance is a PO signature.
- Current dry-run output: 0 to record (all rows unfilled). Nothing was written.

## 4. Second systematic finding: domains that do not belong to the entity count as identity

Under OPTION C a "real domain" is an identity signal, but the current filter (`is_real_domain`) catches only a fixed list.

**Source map:** **494 domains** are each used by 5 or more distinct Master Accounts. They fall into these groups:

| Type | Examples (distinct accounts) |
|---|---|
| Platform | `muqawil.org` (3,708: every Suppliers row) |
| Misspelled free mail | `gamil.com` 485, `gmal.com` 74, `gmali.com` 65, `gmial.com` 54, `hotmal.com` 36 |
| Disposable/spam mail | `webxio.pro` 349, `webxios.pro` 291, `inboxmail.life`, `boxmail.lol`, `firemailbox.club`, `emailax.pro` |
| Registration agents (SFDA) | `ajlaarabian.com` 259, `5boxes.co` 177, `whs.sa` 122 |
| Placeholders/social/portals | `not.com`, `non.com`, `example.org`, `google.com`, `twitter.com`, `instagram.com`, `maps.app.goo.gl` |
| Telco/ISP mail | `stc.com.sa`, `awalnet.net.sa`, `mail.net.sa` |
| **Possibly legitimate groups** (risk) | `balsharafgroup.com` 47, `almaladh.com` 39, `tamergroup.com` 35, `mas-logistics.sa` 35, `rabiyah.com` 53 |

`muqawil.org` alone is behind **298 of the 663** G4 field conflicts.

### Dry run: `--shared-domain-threshold 5` on top of the NCNP rule (0 writes, safety 0)

Artifacts: `phase6_dry_run_domsh5_20260925_*`, `phase6_domsh5_20260925_comparison.json`.

| Measure | Now (`+EXCL_NCNP`) | With the rule |
|---|---:|---:|
| Accounts changed | — | 8,315 (10,680 domain choices changed) |
| SALES_READY | 5,689 | 5,839 |
| SALES_READY_WITH_REVIEW | 36,034 | 29,175 |
| P1 / P2 / P3 | 6,883 / 43,204 / 546 | 6,321 / 36,224 / **147** |
| P1 field conflict (full review) | 663 | **326** |
| P1 weak identity (full review) | 491 | **117** |
| P1 corroboration | 5,729 | 5,878 |

Main transitions:
- **6,885 SRWR → INSUFFICIENT_DATA.** Their only identity was a shared domain.
- 410 P3 and 388 P1 drop to P4.
- 169 are promoted to SALES_READY: the conflict disappears once the platform domain is removed. They remain blocked by G4.

### Effect on the workbooks already prepared

| File | Rows changing class under the rule |
|---|---|
| G4 field conflict | 331 of 663 |
| G4 weak identity | 381 of 491 (→ INSUFFICIENT_DATA) |
| G4 corroboration sample | 1 of 288 |
| **G5 spot check** | **8 of 50 (16%) → INSUFFICIENT_DATA.** These would count as real-world errors and fail the stratum for a known cause. |

## 5. Recommendations (need a PO decision)

1. **Adopt the shared-domain rule before any G4/G5 human review starts.** It removes about 711 full G4 reviews and prevents a known cause of G5 failure.
2. **Threshold 5 plus a group allowlist.** Legitimate groups that share one domain across branches would lose identity. Proposal: a reviewed allowlist, currently about 5–10 candidate domains, drawn from the §4 list after a short human pass.
3. After approval:
   - real run under a new version (`…+DOMSH5`), same method as report 106 (backup, one transaction, supersede, not delete);
   - regenerate the G4/G5 workbooks and the P2 sample.
4. **G3 (5 accounts) can start now.** It is not affected by the domain rule.

## 6. Verification

- Unit tests (Phase 6/7): 131 passed.
- Ruff clean.
- Dry run: safety counters 0, READ ONLY.
- Capture dry run: 0 writes.

Gates remain **OPEN**. Production is **NOT APPROVED**.
