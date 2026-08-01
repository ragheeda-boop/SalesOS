# ADR-029: Number Never Issued

**Status**: Not Issued
**Date**: 2026-08-01
**Author**: Backend Lead / Architecture (Phase 0 criterion 6.2 disposition)
**Authority**: `PHASE_0_EXIT_CHECKLIST` §6.2 · DEC-136 · `.engineering/27_ADR_INDEX.md` conflict #2

---

## Context

EOS ADR index (`.engineering/27_ADR_INDEX.md`) recorded **ADR-029** as a **PHANTOM**: no title, no file under `docs/adr/`, `salesos/backend/docs/adr/`, or `engineering-os/adr/`, and no row in the canonical product index `docs/adr/index.md` (sequence jumps **028 → 030**).

Filesystem and git history checks (2026-08-01) found **no** prior ADR-029 body and **no** evidence a decision was drafted then deleted. The gap is a **numbering hole**, not a lost Accepted decision.

Phase 0 exit criterion **6.2** requires: *ADR-029 phantom resolved — numbering gap closed or documented*.

---

## Decision

**Document the numbering gap. Do not invent an architectural decision for slot 029.**

| Pin | Value |
|---|---|
| Disposition | **Not Issued** — permanent numbering reservation |
| Binding architecture | **None** (no Context/Decision/Consequences body beyond this meta-record) |
| Index action | Register this file in `docs/adr/index.md` with status **Not Issued** |
| Reuse of ID | **Forbidden** — do not assign a new decision to ADR-029 later |
| Next free product-root ID after 028 | Continues at **ADR-030** (already Accepted); this record only closes the phantom narrative |

### Alternatives rejected

| Option | Verdict |
|---|---|
| (a) Invent a retrospective architecture ADR for 029 | Rejected — dishonest; no evidence of a prior decision |
| (b) Renumber ADR-030+ downward to close the gap | Rejected — breaks citations and file names |
| (c) Leave phantom undocumented | Rejected — fails 6.2 evidence |
| (d) Meta-record: Not Issued + index row | **Approved** — matches “numbering gap … documented” |

---

## Consequences

- Consumers searching for ADR-029 find an explicit **Not Issued** disposition instead of silence or a false Accepted claim.
- ADR Drift conflict #2 (029 phantom) is dispositioned for checklist **6.2**; Orchestrator CLOSE remains separate (Arch+Val).
- Residual ADR Drift items **6.3–6.5** unchanged.
- Auth / CSRF / RBAC / DEC-085 untouched. **Production GO not claimed. CI GREEN not met.**
