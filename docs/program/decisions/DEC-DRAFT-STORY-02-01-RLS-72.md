# DEC-DRAFT — STORY-02-01 RLS “72-table” AC vs inventory reality

> **Status:** **DRAFT** — for human resolution. Not Accepted. Not executed.  
> **Date:** 2026-08-01  
> **Board:** Architecture Review Board + Documentation (SalesOS / AQLIYA program)  
> **Stop condition:** Database Team Alpha **STOPPED** on STORY-02-01 — no further RLS migration shipped pending this package.  
> **Authority chain:** Sprint-03 STORY-02-01 AC → R-09 / R-20 / DB-05 → DEC-008 / DEC-013 → this package → human accept/reject → (if accepted) numbered DEC entry in `DECISION_LOG.md`.  
> **Out of scope:** Shipping Alembic migrations, editing `ALL_TENANT_TABLES` production policy sets, or claiming Phase 0 GO.

---

## 1. Decision required

Human owners must choose how STORY-02-01 closes relative to the stated acceptance criterion **“100% of 72 tenant-scoped tables have an RLS policy”**, given Team Alpha’s inventory evidence that **72 is not achievable as a Category-A-only (direct `tenant_id`) rollout on current migrations**.

| Fact | Evidence (Team Alpha stop — 2026-08-01) |
|---|---|
| Policies live today | **46** — `ALL_TENANT_TABLES` / migration `0afbf3e6ae53` |
| Sprint AC target | **72** → **gap 26** |
| ORM models with `tenant_id` | **55** |
| Missing from RLS list | **9** of those 55 |
| Additive-safe now | **`company_features` only** — `CREATE TABLE` present (`0002_feature_store` / related) |
| Blocked (R-09 / no CREATE TABLE migration) | **8** of the 9 missing ORM tables |
| Remainder of gap to 72 | **Category B** join / parent-FK policies (script already defers to Sprint 04) |
| Canonical “exactly 72” inventory | **Not pinned in code** — arithmetic check: 55 Category A + ~14 Category B ≈ **69**, not 72 |

**Implication:** Hitting the literal AC of 72 requires either (a) inventing/settling a Category B inventory that closes the arithmetic gap, or (b) revising the AC. Continuing as if 72 is a Category-A migration story will produce false completeness.

---

## 2. Options

### Option A — Pull Category B into STORY-02-01 now + settle canonical 72 inventory

Expand STORY-02-01 scope immediately to design and ship Category B (join / parent-keyed) policies **and** publish a single authoritative inventory that totals exactly 72 (or formally redefines 72).

Includes: naming every Category B table/policy, policy templates beyond `tenant_id = current_setting(...)`, adversarial coverage for join isolation, and resolving the 55+14≠72 arithmetic in writing before more DDL.

### Option B — Split: close STORY-02-01 at 46 + `company_features` (47) with revised AC; Category B → Sprint 04; R-09 tables wait on DB-05

1. **STORY-02-01 (Sprint 03):** allow additive policy for **`company_features` only** → policies **47**; revise story AC to “all Category A tables that have a CREATE TABLE migration and are listed in the governed inventory.”  
2. **Category B join policies:** remain deferred to **Sprint 04** (already foreshadowed in `generate_rls_policies.py`). Sprint 04 must include an explicit story to settle the canonical inventory (target count may become 69, 72, or another evidence-backed number — not assumed).  
3. **Eight R-09 drift tables:** **no RLS until** CREATE TABLE (or equivalent) migrations land under **DB-05 / R-20** (and historical R-09). Do not ENABLE RLS on tables that do not exist in the migration chain.

### Option C — Block STORY-02-01 until R-09 CREATE TABLE migrations land for the 8 drift tables, then resume

Hold all STORY-02-01 completion (including the safe `company_features` add) until DB-05 delivers CREATE TABLE for the eight missing ORM tables; then resume Category A rollout toward 55 before addressing Category B / the 72 gap.

---

## 3. Pros / cons

| | Option A | Option B | Option C |
|---|---|---|---|
| **Pros** | Single story owns “complete RLS”; forces inventory truth now; may unlock literal “72” narrative if Category B is designed carefully | Matches evidence; preserves scope discipline (local story / local drift); unblocks honest PARTIAL close; Category B stays where script already deferred it; R-09 not papered over with RLS-on-ghost-tables | Maximizes Category A coverage before any AC revision; avoids shipping “47 of 72” optics |
| **Cons** | Scope explosion mid-sprint; Category B design is architecture work, not a list append; risks shipping join policies without settled inventory; delays other Sprint 03 close-out | Does **not** satisfy original AC of 72 without formal revision; Phase 0 still NO-GO; leaves ~8+ Category B gaps explicit | Blocks safe additive work (`company_features`); couples STORY-02-01 to multi-sprint DB-05; Calendar slip with little security gain vs B (those 8 tables are not migratable today) |
| **Migration risk** | High — new policy classes + inventory churn | Low — at most one additive Category A table | Medium — waits on large schema program before any close |
| **Honesty vs DEC-008** | Can claim progress only after Category B + inventory settled | Honest PARTIAL; requires **AC revision** so “complete” is not falsely claimed | Honest block; still does not solve Category B or 72 arithmetic |

---

## 4. Explicit recommendation

### Recommend: **Option B**

**Rationale (ARB + Documentation):**

1. **Evidence over aspiration.** Policies are 46; only `company_features` is additive-safe. The other eight ORM gaps are R-09/DB-05 problems (no CREATE TABLE), not missing `ENABLE ROW LEVEL SECURITY` lines.  
2. **Category B is a different design class.** Parent-FK / join isolation was already deferred to Sprint 04 in `scripts/generate_rls_policies.py`. Pulling it into STORY-02-01 (Option A) conflates “complete Category A where tables exist” with “invent join-policy architecture.”  
3. **72 is not pinned.** 55 + 14 ≈ 69. Forcing “exactly 72” without a settled inventory invites fake tables or double-counting. Sprint 04 should own the canonical count.  
4. **Option C over-blocks.** Waiting on eight CREATE TABLE migrations before adding the one safe table or revising AC does not improve Railway R-14 or Phase 0 exit; it only stalls documented progress.

### Phase 0 impact (explicit — do not soft-pedal)

Under **recommended Option B**, even after STORY-02-01 closes at **47** with a **revised AC**:

| Gate | Status |
|---|---|
| Phase 0 exit | Remains **NO-GO** |
| Railway R-14 (S04-04) | Still **OPEN** — unchanged by this package |
| “100% of 72” as originally written | **Unmet** unless AC is formally revised; incomplete 72 coverage remains a gate fact |
| DEC-008 zero partial credit | Still binds — revised story AC ≠ Phase 0 GO |

**Acceptance of B should mint** a numbered DEC that: (1) revises STORY-02-01 AC to Category-A-migrated-only (target **47** after `company_features`); (2) assigns Category B + canonical inventory settlement to Sprint 04; (3) keeps the eight drift tables behind DB-05/R-20; (4) restates Phase 0 **NO-GO** until Railway + revised completeness criteria + CI honesty are met.

---

## 5. What engineering MAY continue pending Accept

| May continue | Must not |
|---|---|
| Docs / inventory drafts for Category B (design only) | Ship Alembic RLS migrations for the 8 R-09 tables |
| DB-05 / R-20 schema reconciliation planning | Claim STORY-02-01 COMPLETE against original 72 AC |
| Sprint 03 non-RLS stories already in flight | Claim Phase 0 GO or “RLS complete on 72 tables” |
| Adversarial suite work on the existing 46 (and later 47) | Enable RLS on non-existent / unmigrated tables |

**Stop preserved until Accepted:** Database Team Alpha does not ship further STORY-02-01 DDL beyond what this package authorizes after Accept.

---

## 6. Decision record (human fill-in)

| Field | Value |
|---|---|
| Chosen option | ☐ A  ☐ B  ☐ C |
| Authorizing role(s) | Program Director / Chief Architect / Backend Lead: ________ |
| Date | ________ |
| If B: revised STORY-02-01 AC text | ________ |
| If B: Sprint 04 Category B story ID | ________ |
| Follow-on DEC ID when Accepted | DEC-042 (proposed; confirm free ID at accept time — DEC-041 is CI-21) |
| Evidence pointer | Team Alpha stop package / this DRAFT |

---

## 7. Immediate program effects (unchanged until Accepted)

- `SPRINT_PLAN/Sprint-03.md` — STORY-02-01 **PARTIAL / STOPPED** pending this decision.  
- `RISK_REGISTER.md` — **R-25** (72-table AC unachievable without Category B design + inventory pin); R-09 / R-20 unchanged as blockers for the 8 tables.  
- `EXECUTION_DAG.md` — STORY-02-01 **WAITING** on architecture decision (this package).  
- Phase 0 exit — **NO-GO** (Railway + incomplete 72 / unrevised AC).  
- This file — **DRAFT only**; pointer in `DECISION_LOG.md` as DRAFT (not Accepted).

**Validation status of this package:** docs-only; **not validated** as executed RLS work. **No Alembic migrations** created under this draft.
