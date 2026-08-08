# DEC-134 — SoT-oriented capability validate exit 0 (Phase 0 criterion 5.3)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **5.3 VERIFIED/CLOSED** (DEC-134a; Arch+Val PASS @ `6a98999`)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Capability Drift (SalesOS) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **5.3** · DEBT-ARC-003 / E-21 · unblocked by DEC-132a (5.1) + DEC-133a (5.2)  
> **Authority:** PHASE_0_EXIT_CHECKLIST §5.3 · DEC-132/133 “Architecture next” (secondaries ⊆ SoT via join map) · ARB review protocol  
> **Out of scope this land:** Deleting secondary SDK/YAML/catalog entries · registering new decorator capabilities · auth/CSRF weaken · DEC-085 `set_config` · Production GO · CI GREEN · claiming VERIFIED/CLOSED (Orchestrator)

---

## 1. Decision

Reorient `validate_capability_registries.py` so **exit 0** means the **SoT-oriented gate** (joined secondaries ⊆ decorator SoT via the CAP→kebab join map) — **not** false 4-way identity equality across catalog / decorator / SDK / YAML.

| Pin | Value |
|---|---|
| Canonical SoT | Decorator framework kebab IDs (DEC-132; unchanged) |
| Join key | `cap_to_kebab_join.yaml` (DEC-133; unchanged integrity rules) |
| Default validate mode | SoT-oriented subset gate → exit **0** on pass |
| Light path | `--join-map-only` → 5.2 integrity (unchanged) |
| Diagnostic | `--legacy-equality` → historical 4-way check; exit **2** on mismatch (not the close gate) |
| Criterion state | **VERIFIED/CLOSED** (DEC-134a) |

### Gate definition (honest)

| Check | Fail? |
|---|---|
| Join map integrity (5.2 rules) | **Yes** → exit 1 |
| Catalog CAP via join map: `direct` ⇒ `runtime_id` ∈ SoT; `unmapped` allowed | Covered by join map |
| SDK / YAML IDs that normalize to a SoT kebab | Must ⊆ SoT (joined subset) |
| SDK / YAML IDs outside SoT | **INFO residual** — not failure |
| SoT IDs absent from SDK/YAML (`decorator_only` / partial mirrors) | **INFO residual** — not failure |
| 4-way identity equality | **Not required** for exit 0 |

**Not claimed this land:** Production GO · CI GREEN · VERIFIED/CLOSED · Phase 0 exit · deleting secondaries · inventing decorator IDs to force 40/40.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Keep 4-way equality as exit 0 | Rejected — false until dishonest mass delete / invent |
| (b) Delete SDK/YAML extras to force equality | Rejected — dishonest; out of scope |
| (c) SoT-oriented subset via join map | **Approved** — matches DEC-132/133 Architecture next |
| (d) Claim BLOCKED until full convergence | Rejected — checklist evidence is validate exit 0 under an honest gate |

---

## 3. Validation

| Check | Result |
|---|---|
| Default `validate_capability_registries.py` exit 0 | **Yes** — host exit **0** (full catalog+YAML+SDK+SoT+join); Docker exit **0** (SoT+join+SDK; catalog/YAML not mounted in backend-only container) |
| Mode | SoT-oriented (source parse; no `runtime` / SDK import — avoids `runtime/__init__` hang) |
| Counts (host) | SoT 13 · SDK 21 (aligned 3 / residual 18) · YAML 22 (aligned 5 / residual 17) · join 40/10/30/3 |
| `--join-map-only` exit 0 | **Yes** (5.2 intact) |
| `--legacy-equality` | Exit **2** (diagnostic; not 5.3 gate) |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (script exit evidence; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met.** Closed via Orchestrator DEC-134a after Arch+Val PASS.

---

## 4. Records

- Phase 0 criterion **5.3** → **VERIFIED/CLOSED** (DEC-134a; Arch PASS + Validation PASS @ `6a98999`)
- **5.1** / **5.2** / **5.4** remain CLOSED (DEC-132a / DEC-133a / DEC-131a) — Capability Drift cluster **COMPLETE 4/4**
- Phase 0 **28/54 → 29/54**
- Residual (non-blocking INFO): secondary SDK/YAML extras + CAP unmapped + CAP-037 semantic-join refine; ADR Drift / other Phase 0 clusters unchanged
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | SoT-oriented validate | `salesos/backend/scripts/validate_capability_registries.py` |
| EV-002 | Sync helper reorient (diagnostic) | `salesos/backend/scripts/sync_capability_registries.py` |
| EV-003 | Join map note | `salesos/backend/runtime/capability_framework/cap_to_kebab_join.yaml` |
| EV-004 | SoT module docstring | `salesos/backend/runtime/capability_framework/__init__.py` |
| EV-005 | This DEC | `docs/program/decisions/DEC-134-CRITERION-5-3-SOT-ORIENTED-VALIDATE.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (validate/sync + DEC-134 program crumbs) |
| 2 | No auth/DB behavior to undo |
| Expected impact | 5.3 returns OPEN; 5.1/5.2/5.4 unchanged |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Gate weaker than 4-way equality | MEDIUM accepted | Intentional — equality was dishonest; residual extras documented |
| Overclaim Production GO / CI GREEN | LOW | CLOSED for 5.3 only; Phase 0 still NO-GO |
| Import hang via `runtime` package | MITIGATED | Source-parse path avoids `runtime/__init__.py` stack import |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 5.3? | **DONE** — DEC-134a @ `6a98999` |
| Residual after CLOSE | Optional backlog (INFO): tighten secondary alias map (`company-360`→`company`); CAP-037 semantic-join refine; do not require 4-way equality |
| Do not | Delete secondaries · claim Production GO / CI GREEN · reopen 5.1–5.3 without superseding DEC |
