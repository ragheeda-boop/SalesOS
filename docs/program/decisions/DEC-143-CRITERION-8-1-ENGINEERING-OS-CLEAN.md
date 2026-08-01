# DEC-143 — engineering-os submodule clean (Phase 0 criterion 8.1)

> **Status:** **READY FOR REVIEW** (Cursor COMPLETE — Arch + Validation + Orchestrator CLOSE pending)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Engineering Stability (SalesOS / AQLIYA) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **8.1** · `engineering-os/` submodule clean  
> **Authority:** PHASE_0_EXIT_CHECKLIST §8.1 · `.engineering/27_ADR_INDEX.md` conflict #11 · DEC-142 residual  
> **Out of scope this land:** Eng Stability **8.2** / **8.3** · EOS **4.1/4.8** ARB · inventing capability SoT · submodule remote push · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN · Phase 0 exit · VERIFIED/CLOSED

---

## 1. Decision

Resolve criterion **8.1** by restoring a **clean** `engineering-os/` working tree at the already-pinned submodule SHA, discarding **malformed unreviewed** local drift in `kernel/capability-registry.yaml`.

| Pin | Value |
|---|---|
| Submodule SHA (unchanged) | `b82b9fb` / `b82b9fbee2781fa72357a61fe8dfc8a25b8de3bf` |
| Dirty path (pre-land) | `engineering-os/kernel/capability-registry.yaml` (+365 lines) |
| Disposition | **Discard** — restore to HEAD (`git restore`) |
| Rationale | Append sat **outside** the documented YAML fenced block (after closing fence at workflow `frozen: false`); EOS conflict #11 = “Unreviewed governance drift”; Capability Drift cluster already **CLOSED** (DEC-134a) with YAML as **secondary** SoT |
| Parent gitlink | **Unchanged** — still `b82b9fb` (no submodule commit / no push) |
| Criterion state | **READY FOR REVIEW** (not VERIFIED/CLOSED) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| `engineering-os/` working tree clean | **Yes** — `git status` empty inside submodule; parent `git submodule status` no leading `+`/`-`/`U`; no `m` dirty flag |
| Submodule pin matches recorded SHA | **Yes** — `b82b9fb` |
| No invent of new capability registry SoT | **Yes** — no commit of unreviewed append; decorator SoT remains DEC-132 |
| DEC-085 / auth untouched | **Yes** |
| Submodule remote advanced / pushed | **N/A** — no submodule commit |
| Agent coordination at scale (8.2) | **No** — residual **8.2** |
| Arch rules green in CI (8.3) | **No** — residual **8.3** (`test_architecture` not in workflows; gate is `arch-compliance.ps1`) |

**Not claimed:** Production GO · CI GREEN · Phase 0 exit · VERIFIED/CLOSED · closing 8.2 / 8.3 / 4.1 / 4.8.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Commit malformed append as-is inside submodule | Rejected — content outside YAML fence; unreviewed governance drift |
| (b) Move append inside fence + commit + update parent gitlink | Rejected this land — expands secondary YAML SoT without Arch review; prefers submodule push for clone fetchability (user: prefer not push) |
| (c) Docs-only checklist note while tree stays dirty | Rejected — 8.1 requires no uncommitted changes |
| (d) Claim VERIFIED/CLOSED in this land | Rejected — Arch+Val + Orchestrator gate |
| (e) Discard malformed unreviewed drift; keep pin `b82b9fb` | **Approved** |

---

## 3. Validation

| Check | Result |
|---|---|
| Pre: dirty | `M kernel/capability-registry.yaml` (+365); parent ` m engineering-os` |
| Post: clean | submodule `git status --short` empty; `git submodule status` → ` b82b9fb… engineering-os (heads/main)` |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (git working-tree evidence only; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met.**

---

## 4. Records

- Phase 0 criterion **8.1** → **READY FOR REVIEW** (this DEC)
- Phase 0 remains **39/54** until Orchestrator CLOSE (DEC-143a)
- Residuals (non-blocking for 8.1): Eng Stability **8.2** / **8.3** · EOS **4.1** / **4.8** ARB · CI-08/CI-09 ops
- `.engineering/27_ADR_INDEX.md` conflict #11 → **RESOLVED (DEC-143)**
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit · VERIFIED/CLOSED

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | Clean submodule pin | `engineering-os` @ `b82b9fb` |
| EV-002 | Conflict #11 resolve note | `.engineering/27_ADR_INDEX.md` |
| EV-003 | This DEC | `docs/program/decisions/DEC-143-CRITERION-8-1-ENGINEERING-OS-CLEAN.md` |
| EV-004 | Checklist / board / DAG crumbs | `PHASE_0_EXIT_CHECKLIST.md` · `SPRINT_05_DELIVERY_BOARD.md` · `EXECUTION_DAG.md` · `DECISION_LOG.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (docs / conflict note) |
| 2 | Re-apply discarded YAML append only if Arch explicitly re-approves structured in-fence update |
| Expected impact | 8.1 returns OPEN if working tree dirtied again |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Loss of uncommitted capability stubs | LOW | Unreviewed + malformed (outside fence); secondary YAML SoT; can re-land via reviewed submodule commit later |
| Overclaim CLOSED / Production GO | LOW | Status = READY FOR REVIEW only |
| Historical EOS prose still says “DIRTY” in older catalogs | LOW | Bootstrap snapshots; conflict #11 is the living conflict register |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 8.1? | **After** Arch PASS + Validation PASS (light: submodule clean @ `b82b9fb`) → Orchestrator DEC-143a |
| Next PARALLEL | Eng Stability **8.2** / **8.3** · EOS **4.1/4.8** ARB |
| Do not | Claim Phase 0 GO · CI GREEN · invent ARB PASS · weaken auth / DEC-085 · silently commit unreviewed YAML expansions |
