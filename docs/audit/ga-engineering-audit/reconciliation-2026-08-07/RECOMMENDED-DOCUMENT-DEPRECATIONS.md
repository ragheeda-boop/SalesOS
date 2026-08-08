# Recommended Document Deprecations

**Pack:** Enterprise Reconciliation Audit — 2026-08-07  
**Mode:** Recommendations only — **do not apply** in this reconciliation (no rewrites of living governance).  
**Purpose:** Tell humans which texts to fence, supersede, or stop citing as current.

---

## A. Fence as HISTORICAL (keep, but banner “not current SoT”)

| Document / section | Why | Replace-with while current |
|--------------------|-----|----------------------------|
| Audit baseline Security **48** / PR **38** when cited as “GA audit remains” beside 2026-08-07 ops | Baseline is real history; citing it as concurrent board score creates RC-P0-03 | EAB-003 SCORECARD (**~81** / **~53**) + explicit **production no-go** |
| `SIGN_HERE.md` closed evidence “Alembic head **0040**” / pytest **1548/0** as *live* identity | Superseded by later probes/EAB suites | `d1a8c35e7f09` evidence; EAB-003 **2009/0** + **2492/0** (dated) |
| `GA_STATUS.md` #1 staging “409 behind / DEBUG=true / shared JWT” **present tense** | Contradicts 2026-08-07 ROW4/DIFF | `OPS01-ROW4-STATUS.md` + `STAGING-vs-PRODUCTION-DIFF.md` |
| `STAGING-VERIFICATION.md` / `SOAK-READINESS.md` (2026-08-06) parity failure as *current* | Pre-parity snapshot | Dated ROW4 (2026-08-07) |
| `PRODUCTION-VERIFICATION.md` Neo4j OFFLINE — **if** post-repair health JSON is later deposited | Until then it remains Authoritative for last verified artifact | Post-repair health JSON (missing today) |
| Wave10 local DR OPEN narratives when arguing prod-path drills | Scope confusion | OPS-01 evidence JSON |
| `docs/vnext/reports/GO_NO_GO_DECISION.md`, `GA_CHECKLIST.md` | Already superseded | ga-engineering-audit + SIGN_HERE |

---

## B. Mark INCORRECT-AS-CURRENT (stop citing for decisions)

| Claim / phrase | Location | Why |
|----------------|----------|-----|
| Offsite/WAL/PITR **DONE** = cutover CLOSED | `GA_STATUS.md` #7 (as CLOSED) | Conflicts DR checklist OPEN / SIGN_HERE OPEN (**RC-P0-01**) |
| DR EAB-003 “archive **Still off**” / offsite “**NOT done**” *as fact denial* | `DR-GA-GAPS-CHECKLIST.md` EAB-003 block | Contradicts linked evidence JSON (**RC-P0-02**) — update or retract block |
| “Production **READY with conditions**”; Readiness **~96%**; Verification **100%**; Security **98%** | `OPS01-ROW4-STATUS.md` §2/§7 | Conflicts mandatory production no-go + EAB scores (**RC-P1-05**, RC-P0-03) |
| Soak “**not started**” (after 2026-08-07T14:10:06Z start) | `OPS01-ROW4-STATUS.md` §1–2 | Conflicts same-file §5–6 + loop JSON (**RC-P1-02**) |
| Alembic **0051** as live prod revision id | `GA_STATUS.md` | Evidence shows `d1a8c35e7f09` (**RC-P1-06**) |
| Local **140-loop** soak as the cloud Row 4 completeness story | `SIGN_HERE.md` open #1 | Dual SoT with `ops01-staging` (**RC-P1-03**) |
| APPENDIX / Principal “Use Security **72**” as EAB score | APPENDIX-B lineage | Never adopted by EAB SCORECARDs |

---

## C. Recommended SUPERSESSION actions (human edit later — not done here)

1. **Single OPS-01 disposition statement** attached to EAB-003 + PROGRAM-STATUS: split “manual drills proven (evidence)” vs “cutover rows CLOSED (DR checklist + ink)” — eliminate DONE∩OPEN.
2. **Refresh `DR-GA-GAPS-CHECKLIST` EAB-003 block** to match evidence **or** explicitly state residual = automation/sign-off only (if humans accept DONE\* semantics).
3. **Refresh `SIGN_HERE` open #7** DR language to match chosen disposition; keep CTO NO-GO until Row 4/5 close.
4. **Refresh `GA_STATUS` scoreboard** Security/PR to EAB-003 with historical baseline footnote; remove or banner stale staging #1.
5. **Point soak SoT** solely to `SOAK-GATE-CHECKLIST` + `ops01-staging` evidence; demote Wave11 local 140-loop to Historical.
6. **Deposit or retract** Neo4j “connected” claims: require prod health JSON under evidence/.
7. **Fence TL draft greens** in SIGN_HERE as non-authoritative until TL signs.

---

## D. Do NOT deprecate (still required)

| Document | Reason |
|----------|--------|
| `SIGN_HERE.md` | CTO NO-GO ink + TL UNSIGNED gate |
| `DR-GA-GAPS-CHECKLIST.md` | Cutover CLOSED? SoT (needs repair, not deletion) |
| EAB-001/002/003 history packs | Immutable run history — amend via new notes, not silent rewrite |
| `AI_HONESTY.md` | Marketing honesty SoT |
| `PROD-MIGRATION-RISK.md` + `PRODUCTION-CUTOVER-PACKAGE.md` | Migration class + unexecuted playbook |
| OPS-01 evidence JSON/MD | Executable facts |

---

## E. Optional: README one-line pointer

Prefer **zero** edits outside this folder. If humans later want a pointer, add one line under `docs/audit/ga-engineering-audit/README.md` → `reconciliation-2026-08-07/` — **not applied** in this pack.

---

*Chair synthesis — RECOMMENDED-DOCUMENT-DEPRECATIONS — reconciliation-2026-08-07*
