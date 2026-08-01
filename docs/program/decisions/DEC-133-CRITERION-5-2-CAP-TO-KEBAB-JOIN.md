# DEC-133 — CAP-### → kebab join map (Phase 0 criterion 5.2)

> **Status:** **Accepted** — Criterion **5.2 VERIFIED/CLOSED** (DEC-133a; Arch+Val PASS @ `81b593f`)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Capability Drift (SalesOS / AQLIYA) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **5.2** · DEBT-ARC-003 / E-21 · unblocked by DEC-132a (5.1 SoT)  
> **Authority:** PHASE_0_EXIT_CHECKLIST §5.2 · DEC-132 role matrix (catalog join via 5.2) · ARB review protocol  
> **Out of scope this land:** Criterion **5.3** `validate_capability_registries.py` exit 0 · registering new decorator capabilities · deleting secondary registries · auth/CSRF weaken · DEC-085 `set_config` · Production GO · CI GREEN

---

## 1. Decision

Land a machine-readable **join map** from docs `CAP-###` inventory to decorator SoT kebab IDs so automation can join the product catalog to the runtime registry.

| Pin | Value |
|---|---|
| Join map | `salesos/backend/runtime/capability_framework/cap_to_kebab_join.yaml` |
| Path pin | `CAPABILITY_CAP_TO_KEBAB_JOIN_MAP` in `runtime/capability_framework/__init__.py` |
| SoT (unchanged) | Decorator framework kebab IDs (DEC-132) |
| Catalog role | Secondary product inventory — join only; not runtime SoT |
| Criterion state | **VERIFIED/CLOSED** (DEC-133a) |

### Coverage (honest residual)

| Metric | Count |
|---|---|
| Catalog CAP-001..040 | 40 |
| Direct joins (`join: direct`) | 10 |
| Unmapped catalog (`join: unmapped`) | 30 |
| Decorator SoT IDs | 13 |
| Decorator-only (no primary CAP) | 3 (`event-runtime`, `activity-intelligence`, `marketplace`) |

**Direct joins:** CAP-001→`identity`, CAP-002→`company`, CAP-003→`search`, CAP-004→`timeline`, CAP-005→`data-fabric`, CAP-006→`feature-store`, CAP-007→`knowledge-graph`, CAP-009→`workflow`, CAP-016→`decision-engine`, CAP-037→`capability-framework`.

**Not claimed this land:** 40/40 decorator registration · validate exit 0 · Production GO · CI GREEN.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Embed CAP-### into every decorator `@Capability` | Rejected this land — expands runtime surface; needs broader Arch DEC |
| (b) Name-heuristic only (slugify catalog titles) | Rejected — fragile (e.g. Recommendation ≠ decision-engine) |
| (c) Explicit YAML join map + validate hook | **Approved** — automation join key; partial coverage documented |
| (d) Wait for full 4-way sync (5.3) before any map | Rejected — 5.2 unblocks 5.3; checklist separates them |

---

## 3. Validation

| Check | Result |
|---|---|
| Join map present + YAML parse | **Yes** |
| Every CAP-001..040 keyed exactly once | **Yes** (validate hook) |
| Every `runtime_id` for `join: direct` ∈ decorator SoT | **Yes** (validate hook) |
| Every decorator SoT ID = direct join ∪ `decorator_only` | **Yes** (validate hook) |
| `--join-map-only` exit 0 | **Yes** — host: `python scripts/validate_capability_registries.py --join-map-only` → exit 0; 40 caps / 10 direct / 30 unmapped / 3 decorator-only / 13 SoT |
| Full `validate_capability_registries.py` exit 0 | **No** — criterion **5.3** still OPEN (SDK/YAML drift unchanged; host SDK import blocked by missing sqlalchemy) |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (join-map integrity only; no claim of 5.3 exit 0) |

**Production GO not claimed. CI GREEN not met.**

**Orchestrator CLOSE (DEC-133a):** Arch PASS + Validation PASS (light) @ `81b593f` → criterion **5.2 VERIFIED/CLOSED**; Phase 0 **28/54**; Capability Drift **3/4**. Residual **5.3** OPEN. Non-blocking: CAP-037→`capability-framework` semantic-join refine. **Production GO not claimed. CI GREEN not met.**

---

## 4. Records

- Phase 0 criterion **5.2** → **VERIFIED/CLOSED** (DEC-133a)
- Residual **5.3** remains OPEN (validate exit 0)
- **5.1** / **5.4** remain CLOSED (DEC-132a / DEC-131a)
- Phase 0 **27/54 → 28/54**
- Non-blocking residual: CAP-037→`capability-framework` semantic-join refine (does not re-open 5.2)
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit · 5.3 exit 0

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | Join map YAML | `salesos/backend/runtime/capability_framework/cap_to_kebab_join.yaml` |
| EV-002 | Path pin | `CAPABILITY_CAP_TO_KEBAB_JOIN_MAP` in `runtime/capability_framework/__init__.py` |
| EV-003 | Validate hook | `salesos/backend/scripts/validate_capability_registries.py` (`validate_cap_to_kebab_join_map`) |
| EV-004 | Catalog banner | `docs/CAPABILITY_CATALOG.md` |
| EV-005 | This DEC | `docs/program/decisions/DEC-133-CRITERION-5-2-CAP-TO-KEBAB-JOIN.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (YAML + pin + validate hook + DEC-133 program crumbs) |
| 2 | No auth/DB behavior to undo |
| Expected impact | Lose CAP↔kebab automation join only; 5.1 SoT designation remains |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| 30 unmapped CAP cards | HIGH residual (documented) | Expected — catalog ≫ decorator; 5.2 allows honest null |
| CAP-016→decision-engine / CAP-037→capability-framework | MEDIUM | Semantic joins; CAP-037 refine = **non-blocking** residual (5.2 CLOSED) |
| Overclaim 5.3 exit 0 / Production GO | LOW | 5.2 CLOSED; 5.3 still OPEN |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 5.2? | **Done** — DEC-133a (Arch+Val PASS @ `81b593f`) |
| Next | **5.3** — reorient `validate_capability_registries.py` / sync so exit 0 means “secondaries ⊆ / aligned to SoT (+ join map)” |
| Do not | Treat unmapped CAP as failure for 5.2; invent decorator IDs to force 40/40; claim Production GO / CI GREEN / validate exit 0 from this land |
