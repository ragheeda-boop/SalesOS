# DEC-132 — Capability registry single source of truth (Phase 0 criterion 5.1)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **5.1 VERIFIED/CLOSED** via DEC-132a (Arch PASS + Validation PASS light @ `8e105fe`)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Capability Drift (SalesOS) — Architecture-adjacent SoT packaging  
> **Story / risk:** Phase 0 Exit Criterion **5.1** · DEBT-ARC-003 / E-21 · EXEC-ARCHITECTURE-PRODUCT-REVIEW #9/#17  
> **Authority:** PHASE_0_EXIT_CHECKLIST §5.1 · audit “pick one registry as SoT” · ARB review protocol  
> **Out of scope this land:** Criterion **5.2** CAP-###→kebab join map · **5.3** `validate_capability_registries.py` exit 0 · deleting secondary registries · auth/CSRF weaken · DEC-085 `set_config` · Production GO · CI GREEN

---

## 1. Decision

Designate **one** registry as the canonical **runtime** source of truth for SalesOS capabilities.

| Pin | Value |
|---|---|
| Canonical SoT | Decorator framework — `salesos/backend/runtime/capability_framework` |
| Identity scheme | kebab-case IDs (`identity`, `data-fabric`, `decision-engine`, …) |
| HTTP surface | `GET /api/v1/capabilities` (contract-tested under DEC-131 / criterion 5.4) |
| Machine pins | `CAPABILITY_REGISTRY_SOT`, `CAPABILITY_REGISTRY_SOT_PATH`, `CAPABILITY_ID_SCHEME` in `__init__.py` |
| Criterion state | **CLOSED** (DEC-132a) |

### Role matrix (honest residual)

| Registry | Role after DEC-132 |
|---|---|
| Decorator framework | **Canonical runtime SoT** |
| SDK `CapabilityRegistry` | Secondary — module/type registration; must converge to SoT IDs |
| Governance YAML (`engineering-os/kernel/capability-registry.yaml`) | Secondary — governance mirror; must converge to SoT IDs |
| Docs `CAPABILITY_CATALOG.md` (`CAP-###`) | Product/planning inventory — **not** runtime SoT; join via criterion **5.2** |

**Not claimed this land:** 4-way sync complete · validate exit 0 · CAP-### present in backend · Production GO · CI GREEN.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Catalog (`CAP-###`) as SoT | Rejected for *runtime* — `CAP-###` absent from backend; no live HTTP identity |
| (b) SDK registry as SoT | Rejected — naming differs from API kebab IDs; no `/api/v1/capabilities` surface |
| (c) Governance YAML as SoT | Rejected — submodule, naming drift (`crm`, `company-360`), structural fence bug |
| (d) Decorator framework as SoT | **Approved** — live API + 5.4 tests; kebab scheme; matches audit “pick one” |

---

## 3. Validation

| Check | Result |
|---|---|
| SoT pins present in `runtime/capability_framework/__init__.py` | **Yes** (`decorator-framework` / `kebab-case`) |
| Catalog banner records secondary role | **Yes** (`docs/CAPABILITY_CATALOG.md`) |
| Validate script documents SoT + prints pins | **Yes** (exit behavior **unchanged** — still non-zero until 5.3) |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (docs + pin inspection; no full 4-way sync claim) |

**Production GO not claimed. CI GREEN not met.**

**Orchestrator CLOSE (DEC-132a):** Arch PASS + Validation PASS (light) @ `8e105fe` → criterion **5.1 VERIFIED/CLOSED**; Phase 0 **27/54**; Capability Drift **2/4**. Residuals **5.2–5.3** OPEN. **Production GO not claimed. CI GREEN not met.**

---

## 4. Records

- Phase 0 criterion **5.1** → **VERIFIED/CLOSED** (DEC-132a)
- Residuals **5.2** (CAP-### map) · **5.3** (validate exit 0) remain OPEN
- **5.4** remains CLOSED (DEC-131a)
- Phase 0 **26/54 → 27/54**
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit · validate exit 0

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | SoT pins | `salesos/backend/runtime/capability_framework/__init__.py` (`CAPABILITY_REGISTRY_SOT*`) |
| EV-002 | Module docstring | Same file — DEC-132 designation |
| EV-003 | Catalog role banner | `docs/CAPABILITY_CATALOG.md` |
| EV-004 | Validate SoT header + print | `salesos/backend/scripts/validate_capability_registries.py` |
| EV-005 | This DEC | `docs/program/decisions/DEC-132-CRITERION-5-1-CAPABILITY-SOT.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (pins + docs + DEC-132 program crumbs) |
| 2 | No auth/DB behavior to undo |
| Expected impact | Lose formal SoT designation only; 4-way drift unchanged |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Secondary registries still diverge | HIGH residual | Expected — closes designation only; 5.2/5.3 own convergence |
| Future dual-write to SDK “as SoT” | MEDIUM | Forbidden without a superseding DEC |
| Overclaim CLOSED | LOW | CLOSED = SoT designation only; 5.2/5.3 still OPEN |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 5.1? | **Done** — Arch PASS + Val PASS (light) → DEC-132a CLOSED |
| Next | **5.2** — build `CAP-###` → kebab join map against decorator IDs; **5.3** — reorient validate/sync so exit 0 means “secondaries ⊆ / aligned to SoT” |
| Do not | Delete SDK/YAML this sprint without dedicated DEC; claim validate exit 0 from this land; claim Production GO / CI GREEN |
