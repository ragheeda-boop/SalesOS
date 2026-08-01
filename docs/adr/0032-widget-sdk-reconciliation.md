# ADR-032: Widget SDK Reconciliation

**Status**: Proposed
**Date**: 2026-07-17
**Author**: Architecture Review Board (Sprint 0) — registry naming bridge (Phase 0 criterion 6.4)
**Alias**: ADR-0032 (historical `engineering-os` filename / vNext citations)
**Canonical body**: `engineering-os/adr/ADR-0032-widget-sdk-reconciliation.md`
**Authority**: `PHASE_0_EXIT_CHECKLIST` §6.4 · DEC-138

---

## Naming (criterion 6.4)

Phase 0 exit criterion **6.4** requires: *ADR-032/0032 naming unified — single naming convention across `docs/adr/` and `engineering-os/adr/`*.

| Form | Value | Role |
|------|-------|------|
| Registry / citation ID | **ADR-032** | Canonical across indexes and program docs (`ADR-NNN`, 3-digit) |
| `docs/adr/` filename | `0032-widget-sdk-reconciliation.md` | Matches product-root peers (`0030`…`0035`) |
| `engineering-os/adr/` filename | `ADR-0032-widget-sdk-reconciliation.md` | Historical on-disk name (**alias** of ADR-032; not a second decision) |
| Title (both) | Widget SDK Reconciliation | Unchanged |

**Decision:** One decision, one registry ID (**ADR-032**). `ADR-0032` is an allowed historical alias for the submodule filename and legacy citations; it must not be treated as a distinct ADR number.

Submodule rename of `ADR-0032-*` → `ADR-032-*` is **out of scope** this land (docs-only; avoids submodule pointer churn while `engineering-os` carries unrelated dirty work).

---

## Status honesty (adjacent, not a new Accepted claim)

The canonical body header is `**Status**: Proposed`. This bridge matches that status. Index ✅ Accepted without ARB file-header acceptance is **not** re-asserted here. vNext D-016 “Approved” remains a separate program decision record and does **not** by itself flip this ADR to Accepted.

---

## Body

Architecture Context / Decision / Consequences live in the canonical body:

→ [`engineering-os/adr/ADR-0032-widget-sdk-reconciliation.md`](../../engineering-os/adr/ADR-0032-widget-sdk-reconciliation.md)

Do not duplicate or invent a second binding decision text in this bridge.

---

## Consequences

- Registry consumers cite **ADR-032**; searches for ADR-0032 resolve to the same decision via Alias.
- `docs/adr/` and index use the unified **ADR-032** / `0032-*` convention; submodule filename retained as documented alias.
- Auth / CSRF / RBAC / DEC-085 untouched. **Production GO not claimed. CI GREEN not met.**
