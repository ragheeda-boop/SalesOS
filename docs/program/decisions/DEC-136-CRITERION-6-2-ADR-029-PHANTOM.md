# DEC-136 — ADR-029 phantom / numbering gap disposition (Phase 0 criterion 6.2)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **6.2 READY FOR REVIEW** (Arch/Val PENDING)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / ADR Drift (SalesOS / AQLIYA) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **6.2** · `.engineering/27_ADR_INDEX.md` §4 conflict #2  
> **Authority:** PHASE_0_EXIT_CHECKLIST §6.2 · DEC-135a “Architecture next” (prefer **6.2**) · ARB review protocol  
> **Out of scope this land:** ADR-033/034 status (6.3) · ADR-032 naming (6.4) · ADR-036 multi-index (6.5) · inventing a binding architecture decision for slot 029 · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN · VERIFIED/CLOSED

---

## 1. Decision

Resolve criterion **6.2** by **documenting the numbering gap** (checklist: “Numbering gap closed or documented”) — not by inventing an ADR body with fake architecture content, and not by renumbering ADR-030+.

| Pin | Value |
|---|---|
| Evidence required | Numbering gap closed or documented |
| Observation | No ADR-029 file in `docs/adr/`, `salesos/backend/docs/adr/`, or `engineering-os/adr/`; canonical index had no 029 row (028→030); EOS listed PHANTOM |
| Disposition | **Not Issued** meta-record + index row |
| File | `docs/adr/0029-number-never-issued.md` |
| Criterion state | **READY FOR REVIEW** (Orchestrator VERIFIED/CLOSED only after Arch+Val PASS) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| ADR-029 has an explicit disposition file on disk | **Yes** |
| `docs/adr/index.md` registers ADR-029 with status **Not Issued** (not Accepted) | **Yes** |
| No binding architecture decision invented for 029 | **Yes** |
| ID reuse forbidden (documented) | **Yes** |
| `.engineering/27_ADR_INDEX.md` conflict #2 re-pin | **Residual** — tree untracked (criterion **4.5**); narrative superseded by this DEC |

**Not claimed this land:** Production GO · CI GREEN · VERIFIED/CLOSED · Phase 0 exit · closing 6.3–6.5.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Invent retrospective architecture ADR for 029 | Rejected — no evidence a decision ever existed |
| (b) Renumber 030+ to close gap | Rejected — citation / filename breakage |
| (c) Leave phantom silent | Rejected — fails 6.2 |
| (d) Remove a phantom Accepted index row | N/A — canonical index had **no** 029 row |
| (e) Meta-record Not Issued + index registration | **Approved** — documents the gap |

---

## 3. Validation

| Check | Result |
|---|---|
| `docs/adr/0029-number-never-issued.md` exists | **Yes** · Status Not Issued |
| Index File column path matches disk | **Yes** (`Test-Path`) |
| Git history: no prior ADR-029 body | **Yes** (light search; no `*029*adr*` authoring commit) |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (filesystem + index row; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met.** Arch/Val PENDING for Orchestrator CLOSE.

---

## 4. Records

- Phase 0 criterion **6.2** → **READY FOR REVIEW**
- Phase 0 count remains **30/54** until Orchestrator CLOSE
- ADR Drift Complete remains **1/5** / Open **4** until CLOSE (then Complete **2/5** / Open **3**)
- ADR Drift residual after this land (still OPEN): **6.3** (033/034 status), **6.4** (032 naming), **6.5** (036 all indexes)
- EOS **4.5** / `.engineering/` re-pin of `27_ADR_INDEX.md` §2/§4 conflict #2 = follow-on
- **Not claimed:** Production GO · CI GREEN · VERIFIED/CLOSED · Phase 0 exit

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | ADR-029 Not Issued disposition | `docs/adr/0029-number-never-issued.md` |
| EV-002 | Index registration | `docs/adr/index.md` |
| EV-003 | This DEC | `docs/program/decisions/DEC-136-CRITERION-6-2-ADR-029-PHANTOM.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (disposition file + index + DEC-136 program crumbs) |
| 2 | No auth/DB behavior to undo |
| Expected impact | 6.2 returns OPEN (phantom undocumented); numbering gap reappears as silence |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Future author reuses ADR-029 for a real decision | LOW | Explicitly forbidden in disposition + DEC |
| `.engineering/27` still says PHANTOM until 4.5 re-pin | MEDIUM residual | Documented; index + file are SoT for 6.2 |
| Overclaim VERIFIED/CLOSED | LOW | Land is READY FOR REVIEW only |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 6.2? | **After** Arch PASS + Validation PASS (light: path-exists + Status Not Issued + no Accepted-without-file) → Orchestrator DEC-136a |
| Next PARALLEL | **6.3** (033/034 index↔file status) — docs-only; **6.4** naming; **6.5** after ADR-036 + `27_ADR_INDEX` |
| Do not | Invent binding 029 architecture · claim Production GO / CI GREEN · close 6.3–6.5 in this land |
