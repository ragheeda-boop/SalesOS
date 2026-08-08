# DEC-135 — ADR-025/026/027/028 index path correction (Phase 0 criterion 6.1)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **6.1 VERIFIED/CLOSED** (DEC-135a; Arch+Val PASS @ `4997ae4`)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / ADR Drift (SalesOS) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **6.1** · `.engineering/27_ADR_INDEX.md` §4 conflict #1  
> **Authority:** PHASE_0_EXIT_CHECKLIST §6.1 · DEC-134a “Architecture next” (ADR Drift **6.x**) · ARB review protocol  
> **Out of scope this land:** ADR-029 phantom · ADR-033/034 status · ADR-032 naming · ADR-036 multi-index · inventing new ADR bodies · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN

---

## 1. Decision

Resolve criterion **6.1** by **index correction to existing files** (checklist: “files exist OR index corrected”) — not by inventing ADR bodies.

| Pin | Value |
|---|---|
| Evidence required | No index entry claiming Accepted without a file |
| Disposition | **Files exist** under `salesos/backend/docs/adr/` with `**Status:** Accepted` |
| Index action | Register explicit **File** paths for ADR-025..028 in `docs/adr/index.md`; add location row for `salesos/backend/docs/adr/` |
| Dates | Align index dates to file headers (`2026-07-12`) — prior index dates `2026-07-01`..`04` were location-unknown placeholders |
| Criterion state | **VERIFIED/CLOSED** (DEC-135a) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| ADR-025..028 each have a readable file path in `docs/adr/index.md` | **Yes** |
| Each path exists on disk | **Yes** (host `Test-Path`) |
| Each file header `**Status:** Accepted` | **Yes** |
| No Accepted row without a file for 025..028 | **Yes** |
| `.engineering/27_ADR_INDEX.md` re-pin | **Residual** — tree untracked (criterion **4.5**); conflict #1 narrative superseded by this DEC |

**Not claimed this land:** Production GO · CI GREEN · VERIFIED/CLOSED · Phase 0 exit · closing 6.2–6.5.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Leave index Accepted with “no file” (engineering-os phantom) | Rejected — fails 6.1 evidence |
| (b) Downgrade index to Proposed / remove rows | Rejected — files already Accepted; dishonest |
| (c) Duplicate/copy ADRs into `docs/adr/` or `engineering-os/adr/` | Rejected — duplicate SoT; out of scope |
| (d) Index correction pointing at `salesos/backend/docs/adr/` | **Approved** — matches checklist “files exist OR index corrected” |

---

## 3. Validation

| Check | Result |
|---|---|
| `salesos/backend/docs/adr/0025-entity-resolution.md` | exists · Status Accepted |
| `salesos/backend/docs/adr/0026-hybrid-search.md` | exists · Status Accepted |
| `salesos/backend/docs/adr/0027-feature-store.md` | exists · Status Accepted |
| `salesos/backend/docs/adr/0028-knowledge-graph-integration.md` | exists · Status Accepted |
| Index File column paths match disk | **Yes** |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (filesystem + header Status; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met.** Closed via Orchestrator DEC-135a after Arch+Val PASS.

---

## 4. Records

- Phase 0 criterion **6.1** → **VERIFIED/CLOSED** (DEC-135a)
- Phase 0 **29/54 → 30/54**
- ADR Drift Complete **0 → 1** / Open **5 → 4**
- ADR Drift residual: **6.2** (029 phantom), **6.3** (033/034 status), **6.4** (032 naming), **6.5** (036 all indexes)
- EOS **4.5** / `.engineering/` re-pin of `27_ADR_INDEX.md` §2/§4 conflict #1 = follow-on (do not claim 4.5 from this land)
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | Canonical ADR-025 | `salesos/backend/docs/adr/0025-entity-resolution.md` |
| EV-002 | Canonical ADR-026 | `salesos/backend/docs/adr/0026-hybrid-search.md` |
| EV-003 | Canonical ADR-027 | `salesos/backend/docs/adr/0027-feature-store.md` |
| EV-004 | Canonical ADR-028 | `salesos/backend/docs/adr/0028-knowledge-graph-integration.md` |
| EV-005 | Corrected index | `docs/adr/index.md` |
| EV-006 | This DEC | `docs/program/decisions/DEC-135-CRITERION-6-1-ADR-025-028-INDEX.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (index + DEC-135 program crumbs) |
| 2 | No auth/DB behavior to undo |
| Expected impact | 6.1 returns OPEN (Accepted-without-file narrative); ADR files unchanged |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Title wording drift (index short title vs file H1) | LOW residual | Non-blocking; IDs + paths authoritative |
| `.engineering/27` still says NO FILE until 4.5 re-pin | MEDIUM residual | Documented; index + files are SoT for 6.1 |
| Overclaim VERIFIED/CLOSED | LOW | Closed honestly via DEC-135a after Arch+Val PASS |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 6.1? | **Done** — DEC-135a (Arch PASS + Validation PASS light) |
| Next PARALLEL | **6.3** (033/034 index↔file status) or **6.2** (029 phantom doc) — both docs-only; **6.5** after ADR-036 + `27_ADR_INDEX` |
| Do not | Duplicate ADR bodies · claim Production GO / CI GREEN · close 6.2–6.5 in this land |
