# 05 — Fitness Catalog | كتالوج دوال اللياقة

**Pack:** Enterprise Audit Board v2.1  
**Role:** Checkable fitness functions + drift metrics ideas  
**Status:** **Proposed / not validated** until a run or CI wires them

Waivers require: ticket ID + expiry date + owner.

---

## 1. Architecture fitness functions

| ID | Rule | Suggested check |
|----|------|-----------------|
| FF-01 | No module imports upward layer | Static import linter / arch unit test |
| FF-02 | No circular deps (stated method) | Import graph cycle detect |
| FF-03 | Every capability has ADR **or** explicit DEBT/DEC ticket | Capability register join |
| FF-04 | Every public API has contract/schema | OpenAPI / pydantic / contract tests |
| FF-05 | Every published event has ≥1 consumer **or** quarantine note | Event catalog |
| FF-06 | Every service has CODEOWNERS / owner | CODEOWNERS + compose service list |
| FF-07 | `feature_ai_copilot` default **False**; FE decision package **STUB** honesty | Config + [AI_HONESTY.md](../AI_HONESTY.md) gate |
| FF-08 | Tenant GUC / RLS non-bypass unless documented exception | Session middleware audit |
| FF-09 | Dual compose / orphan `MetaData()` must be flagged | Compose diff + MetaData grep count |
| FF-10 | Middleware needing `db_session_factory` fails closed if unset | Code + narrow tests (approved) |
| FF-11 | FE build must verify (not succeed-instead-of-verify) | CI gate (approved) |
| FF-12 | Superseded GO docs must not be cited as authority | Doc link audit |
| FF-13 | Decision Traceability: sample ADRs have complete hop coverage or explicit gap IDs | DTM table (Axis 40) |
| FF-14 | AI Governance: no product path imports FE Decision STUB for evaluate/explain | Import / provider wiring check |

---

## 2. Drift metrics (Axis 41) | مقاييس الانحراف

Measure over time (board-to-board). First run establishes baseline; subsequent runs compute delta.

| Metric ID | Metric | Definition (sketch) |
|-----------|--------|---------------------|
| DM-01 | ADR–impl mismatch count | `#` Accepted ADRs with status `partial` \| `conflicting` \| `unimplemented` |
| DM-02 | Orphan ADR count | Accepted/Proposed ADRs with no capability + no code pointer |
| DM-03 | Orphan capability count | Shipped capabilities with neither ADR nor DEBT/DEC |
| DM-04 | Dual-engine count | Distinct implementations of same capability (decision, forecast, sync, …) |
| DM-05 | Dual-compose divergence | Services defined differently in root vs `salesos/` compose |
| DM-06 | Orphan MetaData island count | Distinct `MetaData()` constructions outside canonical Base |
| DM-07 | Bible–audit claim delta | Count of bible maturity claims contradicted by audit evidence |
| DM-08 | DTM break count | Hops missing in Decision Traceability Matrix samples |
| DM-09 | Superseded-doc citation count | Live docs still citing quarantined GO artifacts |
| DM-10 | AI honesty breach count | Marketing/UI/API paths implying GA AI while flags/stubs say otherwise |

**Drift score formula sketch:** see [07-SCORING-MODEL.md](./07-SCORING-MODEL.md) §Drift.

---

## 3. Engineering economics signals (feed Axis 42)

Not pass/fail fitness — **signals** for cost bands:

| Signal | Suggests higher cost when… |
|--------|----------------------------|
| No capability SoT | Adding Capability → High/Extreme |
| Hard-coded locale strings | Adding دولة → High |
| Tenant bootstrap undocumented | Adding Tenant → High |
| Dual lockfiles / dual Next majors | Framework upgrade → Extreme |
| Orphan MetaData + multi-head Alembic risk | DB change → High/Extreme |
| No module boundary / shared tables | Deleting Module → Extreme |

---

## 4. Execution note

Prefer static checks under low-load. CI wiring and full suite gates require explicit approval. Until run: all FF/DM results = **not validated**.

---

*Fitness Catalog — Enterprise Audit Board v2.1*
