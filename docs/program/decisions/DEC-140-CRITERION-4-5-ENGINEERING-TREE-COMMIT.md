# DEC-140 — Commit `.engineering/` tree (Phase 0 criterion 4.5)

> **Status:** **Cursor COMPLETE** / **READY FOR REVIEW** — awaiting Architecture + Validation  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / EOS Audit (SalesOS) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **4.5** · `.engineering/` committed to git (not untracked)  
> **Authority:** PHASE_0_EXIT_CHECKLIST §4.5 · ADR-036 (Engineering Spec layer) · DEC-139 residual  
> **Out of scope this land:** fingerprint re-measure (4.2/4.7) · EvidenceLevel upgrade (4.4) · ARB re-audit (4.1/4.8) · program↔engineering bidirectional refs (9.2) · inventing SoT · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN · Phase 0 exit · VERIFIED/CLOSED

---

## 1. Decision

Resolve criterion **4.5** by **committing the broader EOS v3.1 tree** under `.engineering/` that remained untracked after DEC-139 pinned only `27_ADR_INDEX.md`.

| Pin | Value |
|---|---|
| Evidence required | `.engineering/` committed to git — not untracked |
| Observation | Pre-land: `git ls-files .engineering/` = **1** file (`27_ADR_INDEX.md`); **32** untracked EOS files (`??`); `.gitignore` does not exclude `.engineering/` |
| Disposition | `git add` all `.engineering/**` (33 files total); no content rewrite of fingerprint pin `c89025a`; EvidenceLevel remains **Heuristic** / Revalidation **Pending** |
| Files | Entire `.engineering/` tree · this DEC · program crumbs |
| Criterion state | **READY FOR REVIEW** (not VERIFIED/CLOSED) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| `.engineering/` no longer shows as untracked (`??`) after land | **Yes** (this land) |
| All 33 EOS files tracked (`00`–`32` + JSON) | **Yes** (this land) |
| Secret/credential scan of tree before add | **Yes** — no private keys / API tokens / password assignments found |
| DEC-085 / auth untouched | **Yes** |
| Fingerprint SHA == current HEAD | **No** — residual **4.2** / **4.7** (pin remains `c89025a`; heuristic) |
| Independent ARB re-audit PASS | **No** — residual **4.1** / **4.8** |
| Bidirectional program↔engineering refs | **No** — residual **9.2** (separate criterion) |

**Not claimed:** Production GO · CI GREEN · Phase 0 exit · VERIFIED/CLOSED · closing 4.1–4.4 / 4.6–4.8 / 9.2.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Regenerate fingerprint + re-pin all headers to tip HEAD in same land | Deferred — that is criteria **4.2** / **4.7** (separate evidence); expands blast radius |
| (b) Leave tree untracked; document-only checklist note | Rejected — checklist evidence is “Not untracked” |
| (c) Commit subset only (e.g. JSON runtime) | Rejected — ADR Drift residual explicitly called for broader tree re-pin |
| (d) Claim VERIFIED/CLOSED in this land | Rejected — Arch+Val + Orchestrator gate |
| (e) Commit full tree as-is (heuristic pin preserved) | **Approved** — closes 4.5 evidence gate honestly |

---

## 3. Validation

| Check | Result |
|---|---|
| Pre-land untracked count | **32** (`git ls-files --others --exclude-standard .engineering/`) |
| Pre-land tracked count | **1** (`27_ADR_INDEX.md`) |
| Post-land expected tracked | **33** |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (git track-state + secret scan; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met.** Closed via DEC-140a after Arch+Val PASS.

---

## 4. Records

- Phase 0 criterion **4.5** → **VERIFIED/CLOSED** (DEC-140a)
- Phase 0 count **34/54 → 35/54**
- Residuals (non-blocking for 4.5): **4.1** B1–B7 re-audit · **4.2** fingerprint match · **4.4** EvidenceLevel · **4.7** staleness · **4.8** ARB PASS · **9.2** program↔engineering cross-refs · Eng Stability **8.1–8.3**
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | EOS tree (33 files) | `.engineering/` |
| EV-002 | This DEC | `docs/program/decisions/DEC-140-CRITERION-4-5-ENGINEERING-TREE-COMMIT.md` |
| EV-003 | Checklist / board / DAG crumbs | `PHASE_0_EXIT_CHECKLIST.md` · `SPRINT_05_DELIVERY_BOARD.md` · `EXECUTION_DAG.md` · `DECISION_LOG.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (`.engineering/` returns to untracked except `27`) |
| 2 | No auth/DB behavior to undo |
| Expected impact | 4.5 returns OPEN |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Stale pin `c89025a` vs tip HEAD | LOW | Honest; criteria 4.2/4.7 remain OPEN |
| Encoding mojibake in some Markdown | LOW | Pre-existing in v3.1 correction; not fixed this land (observe-not-fix) |
| Overclaim Production GO / CI GREEN / CLOSED | LOW | Status = READY FOR REVIEW only |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 4.5? | **After** Arch PASS + Validation PASS (light: `git ls-files` / no `??`) → Orchestrator DEC-140a |
| Next PARALLEL | EOS **4.2/4.7** fingerprint re-pin · **4.1/4.8** ARB · Eng Stability **8.1–8.3** · ADR-036 Applied **9.2** |
| Do not | Claim Phase 0 GO · CI GREEN · upgrade EvidenceLevel without measured methods · invent ARB PASS |
