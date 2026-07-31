# DEC-044 — STORY-02-01 Option B accepted: revised AC closes at 47 policies

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Supersedes:** [`DEC-DRAFT-STORY-02-01-RLS-72`](DEC-DRAFT-STORY-02-01-RLS-72.md)  
> **Board:** Architecture Review Board + Database + Documentation (SalesOS / AQLIYA)  
> **Human decision:** Option B (“الخيار B”)

---

## Decision

Accept **Option B** from the draft package:

1. **STORY-02-01 closes** under a **revised AC** at **47** policies (`46` + `company_features`), **not** the literal original AC of **72**.
2. **Category B** join / parent-FK policies remain deferred to **Sprint 04** (canonical inventory settlement owned there; target may become 69, 72, or another evidence-backed number).
3. **Eight R-09** ORM tables with no CREATE TABLE migration **wait on DB-05 / R-20** — do not ENABLE RLS on unmigrated tables.
4. **Phase 0 remains NO-GO** until Railway **R-14** (S04-04) and remaining completeness / CI honesty gates clear — revising this story AC does **not** unlock Phase 0 GO (DEC-008).

### Revised STORY-02-01 acceptance criterion

> All Category A tenant-scoped tables that have a CREATE TABLE (or equivalent) migration and are listed in the governed inventory (`ALL_TENANT_TABLES`) have an RLS policy (FORCE + USING/WITH CHECK on `tenant_id`). Target count after this DEC: **47** (includes `company_features`). Original “100% of 72” AC is **retired** for this story.

---

## Alternatives considered

| Option | Outcome |
|---|---|
| A — Pull Category B into STORY-02-01 + settle exact-72 inventory now | Rejected — scope explosion; join-policy design ≠ list append |
| **B — Close at 47 with revised AC; Category B → Sprint 04; R-09 → DB-05** | **Accepted** |
| C — Block until eight R-09 CREATE TABLE migrations land | Rejected — over-blocks safe additive `company_features` work |

---

## Consequence

- Mint this Accepted DEC; mark draft **Superseded**.
- Ship additive Alembic migration enabling RLS on `company_features` only; update generator inventory + adversarial `POLICY_COUNT` 46 → 47.
- Update Sprint-03 / EXECUTION_DAG / R-25 per Option B.
- Do **not** touch Railway. Do **not** enable RLS on the eight R-09 tables.
