# ARB Evidence Pack — Phase 0 Criteria 4.1 & 4.8

> **Role of this document:** Decision-ready briefing for **independent ARB** only.  
> **Authority:** [PHASE_0_EXIT_CHECKLIST.md](PHASE_0_EXIT_CHECKLIST.md) §4 · [DEC-151](decisions/DEC-151-PHASE-0-GOVERNANCE-FREEZE.md) Governance Freeze · prior EOS FAIL audit `.engineering/32_EOS_VALIDATION_AUDIT.md`  
> **Scribe:** program/ARB preparation (Cursor) — **2026-08-02**  
> **Pack tip at assembly:** `5fafbe9` (`5fafbe9c55c8e3017891944a3005b05dce3a99e1`) — DEC-151 land  
> **Status of 4.1 / 4.8:** **CLOSED** via DEC-153 — ARB **PASS** / **PASS** (report `.engineering/34_EOS_REAUDIT_2026-08-02.md`; first land `74f698b` / corroboration tip `d973cba`)

---

## 0. Explicit request to ARB

**Return PASS or FAIL only** for each criterion below (and optionally a short CRITICAL finding list if FAIL).

| Criterion | Required ARB return |
|-----------|---------------------|
| **4.1** | **PASS** or **FAIL** — “All B1–B7 findings resolved” |
| **4.8** | **PASS** or **FAIL** — “Independent ARB re-audit = PASS” (new validation report with **no CRITICAL** findings) |

**Forbidden for non-ARB agents (including this scribe):** inventing PASS/FAIL, claiming Independent Audit PASS, Phase 0 COMPLETE, or Production GO.

**Allowed after ARB returns:** Orchestrator may record VERIFIED/CLOSED only when ARB evidence exists.

---

## 1. Exact acceptance criteria (checklist)

Source: `docs/program/PHASE_0_EXIT_CHECKLIST.md` §4 EngineeringOS Audit Pass.

| # | Criterion | Evidence required (verbatim) | Pre-ARB status |
|---|-----------|------------------------------|----------------|
| **4.1** | All B1–B7 findings resolved | **ARB re-audit returns PASS** | ✅ CLOSED — Independent **PASS** (DEC-153) |
| **4.8** | Independent ARB re-audit = PASS | **New validation report with no CRITICAL findings** | ✅ CLOSED — Independent **PASS**, CRITICAL **0** (DEC-153) |

Owner: OpenCode / **ARB**. Reference: `.engineering/32_EOS_VALIDATION_AUDIT.md`, `.engineering/00_PROJECT_CONSTITUTION.md`.

### Related §4 rows (context — already measured/closed; not substitutes for 4.1/4.8)

| # | Criterion | Status | Close evidence |
|---|-----------|--------|----------------|
| 4.2 | Fingerprint matches pinned commit | ✅ CLOSED (DEC-142a) @ `637d051` | Pin `9fa8e9f`; Alembic `a4f7c29e1b80`; migrations **69** |
| 4.3 | No invented surfaces | ✅ VERIFIED (ARB 2026-08-01; B4) | Filesystem / API catalog |
| 4.4 | EvidenceLevel justified | ✅ CLOSED (DEC-142a) | **Measured** (not “Repository Verified”) |
| 4.5 | `.engineering/` committed | ✅ CLOSED (DEC-140a) @ `5b2e4c2` | Tree tracked (now **35** files at tip) |
| 4.6 | Lock protocol verified | ✅ VERIFIED (ARB 2026-08-01; B6) | `21` mirrors `22` |
| 4.7 | Staleness protocol active | ✅ CLOSED (DEC-142a) | `measure_fingerprint.py` + Revalidation **Active** |

**Honesty:** Closing 4.2–4.7 did **not** auto-close 4.1/4.8. Historical ARB FAIL in `32` remains on disk; superseded for 4.1/4.8 verdict only by `.engineering/34_EOS_REAUDIT_2026-08-02.md`.

---

## 2. Original B1–B7 blockers (must re-verify)

Source of numbering: `.engineering/32_EOS_VALIDATION_AUDIT.md` (Verdict **FAIL**, 2026-08-01). Do not rewrite that file.

| ID | Finding (summary) | Severity | Claimed remediation path |
|----|-------------------|----------|--------------------------|
| **B1** | Fingerprint Alembic head false at claimed pin (`e4b9…` absent; real pin head `b110…`) | CRITICAL | Re-measure / re-pin → DEC-142 → head `a4f7c29e1b80` @ pin `9fa8e9f` |
| **B2** | Framework version false (`FastAPI 0.111` vs `>=0.136.0,<0.142.0`) | CRITICAL | Fingerprint + catalogs corrected (v3.1 / DEC-142) |
| **B3** | Structural counts false at claimed commit | CRITICAL | Re-derived via `measure_fingerprint.py` / `23` methods |
| **B4** | Invented CRM API (`modules/crm`, `/api/v1/crm`) | CRITICAL | Removed from `14_API_CATALOG.md`; note retained as B4 fix |
| **B5** | Database catalog unsafe vs live Alembic graph | CRITICAL | `13_DATABASE_CATALOG.md` rewritten / head aligned (v3.1 → DEC-142) |
| **B6** | Bootstrap write lock never released on `.engineering/**` | CRITICAL | Lock `free` in `22_FILE_LOCKS.json`; `21` mirror note |
| **B7** | Evidence-level overclaim (“Repository Verified”) | CRITICAL | Downgraded to **Measured** (DEC-142); **not** self-certified Repository Verified |

**Scribe note (non-verdict):** `.engineering/30_ENGINEERING_BOOTSTRAP_REPORT.md` §2 swaps B5/B6 labels vs audit `32`. ARB should use **audit `32` numbering** above.

---

## 3. Artifact index (paths + SHAs)

### 3.1 Tip / program pins (at pack assembly)

| Artifact | Path | Commit / blob SHA |
|----------|------|-------------------|
| Pack assembly tip | `HEAD` | `5fafbe9` / `5fafbe9c55c8e3017891944a3005b05dce3a99e1` |
| Phase 0 checklist | `docs/program/PHASE_0_EXIT_CHECKLIST.md` | blob `677ea64e3d44504c444d79bbef1eeb81af1e5a21` @ tip |
| Governance freeze | `docs/program/decisions/DEC-151-PHASE-0-GOVERNANCE-FREEZE.md` | blob `c4f1a696dce134c7674dcb622504bdcb407b3a70` |
| This pack | `docs/program/ARB_PHASE0_4_1_4_8_EVIDENCE_PACK.md` | *(SHA after land commit)* |
| Delivery board | `docs/program/SPRINT_05_DELIVERY_BOARD.md` | tip-relative (crumb added this land) |
| Execution DAG | `docs/program/EXECUTION_DAG.md` | tip-relative (crumb added this land) |

### 3.2 Historical FAIL + correction DECs

| Artifact | Path | Commit / blob SHA |
|----------|------|-------------------|
| Independent FAIL audit (do not rewrite) | `.engineering/32_EOS_VALIDATION_AUDIT.md` | blob `b3606dcdfad2ae1d7eb7ee82a035e838a1468449` @ tip |
| EOS claimed pin at FAIL | (audit field) | `3749c30` / `3749c301c97ed8dff5dba1d3fc447a91e766be8f` |
| Live HEAD at FAIL | (audit field) | `0156121` |
| Commit `.engineering/` (4.5) | DEC-140 / land `5b2e4c2` | DEC blob `98d67758c8f5fba136a78a74528046e47942518b` |
| Fingerprint re-pin (4.2/4.4/4.7) | DEC-142 / CLOSE `637d051` | DEC blob `79537287053e2661ee06f439af04db95db671fe0` |
| Measurement tip (DEC-142) | fingerprint pin | `9fa8e9f` / `9fa8e9fc4536d02a1f6a081f9b5bf49c6f59d56e` |

### 3.3 EOS surfaces ARB should sample

| ID | Path | Tip blob SHA | Why |
|----|------|--------------|-----|
| EV-FP | `.engineering/23_PROJECT_FINGERPRINT.json` | `c48dd56deef9cd8a087af15131f1c2b803e822a0` | B1–B3 / B7 |
| EV-MS | `.engineering/measure_fingerprint.py` | `55f06b129da8f79f4f9c77003566df84c87c2df7` | 4.7 protocol / re-measure |
| EV-DB | `.engineering/13_DATABASE_CATALOG.md` | `85eaa17c4c7292ed4cc48e45fff7f15365206e96` | B5 |
| EV-API | `.engineering/14_API_CATALOG.md` | `10b35ae08a4b3fd8ed1a9cd07840d468040f2eb5` | B4 |
| EV-LK | `.engineering/22_FILE_LOCKS.json` | `bdc21e6e1aec3729096fa8b18096288b30b8ac8f` | B6 |
| EV-RT | `.engineering/21_RUNTIME_STATE.json` | tip tree | B6 mirror |
| EV-BS | `.engineering/30_ENGINEERING_BOOTSTRAP_REPORT.md` | `23477a4d37335f2f99d02ef7b8c67858afd622d0` | v3.1 correction narrative + §8 AC |
| EV-MF | `.engineering/24_REPOSITORY_MANIFEST.json` | tip tree | B3/B4 structural |
| EV-BR | `docs/program/ENGINEERING_LAYER_BRIDGE.md` ↔ `.engineering/33_PROGRAM_LAYER_BRIDGE.md` | DEC-141a | Layer pointers only |

Full tree: `.engineering/` (**35** tracked files at tip `5fafbe9`).

### 3.4 Suggested independent re-measure commands (ARB executes)

```text
git rev-parse HEAD
git rev-parse HEAD:.engineering/23_PROJECT_FINGERPRINT.json
python .engineering/measure_fingerprint.py
# optional corroboration (non-prod):
# docker compose exec backend alembic heads
```

Compare output to `_metadata.repository_commit` / counts in `23`. Material drift since pin `9fa8e9f` is expected (many program commits); ARB decides whether drift is **disqualifying CRITICAL** or acceptable under Active revalidation protocol.

---

## 4. Measured vs Open (scribe inventory — not an ARB verdict)

### Measured / program-closed (do not treat as 4.1/4.8 PASS)

| Item | State |
|------|--------|
| `.engineering/` in git | Measured — DEC-140a CLOSED |
| Fingerprint re-pin @ `9fa8e9f` | Measured — DEC-142a CLOSED |
| EvidenceLevel **Measured** + Revalidation Active | Measured — DEC-142a CLOSED |
| Invented CRM row removed (catalog claim) | ARB-confirmed RESOLVED (B4) |
| Bootstrap lock released | ARB-confirmed RESOLVED (B6) |
| Eng Stability 8.1–8.3 | CLOSED / CLOSED CONDITIONAL (orthogonal) |
| Phase 0 scoreboard | **51/54 NO-GO** (DEC-153 closed 4.1/4.8; DEC-152 3.9 CONDITIONAL) |

### ARB-closed (this pack)

| Item | State |
|------|--------|
| **4.1** B1–B7 resolved | **CLOSED — PASS** (DEC-153) |
| **4.8** New independent report, 0 CRITICAL | **CLOSED — PASS** (`.engineering/34_EOS_REAUDIT_2026-08-02.md`) |
| New validation report artifact | Present — do not overwrite historical FAIL `32` |
| Official EOS adoption as SoT | Measured SoT with Active revalidation — **not** Production GO |

### Explicit non-claims by this pack

1. No Phase 0 COMPLETE / Phase 0 GO (score **51/54**; hard OPEN **3.7**).  
2. No Production GO / full CI GREEN (Stages 1–7).  
3. No “Repository Verified” upgrade invented here (EvidenceLevel stays **Measured**).  
4. Fingerprint pin `9fa8e9f` ≠ tip — disclosed; Active revalidation; non-CRITICAL.

---

## 5. Decision worksheet (ARB fills)

### 5.1 Criterion 4.1 — B1–B7 resolved

| Finding | ARB PASS? | CRITICAL remaining? | Notes |
|---------|-----------|---------------------|-------|
| B1 | ☑ PASS | ☐ N | tip head `a4f7c29e1b80` (69 revs; pin has file) |
| B2 | ☑ PASS | ☐ N | FastAPI `>=0.136.0,<0.142.0` |
| B3 | ☑ PASS | ☐ N | modules/domains/runtime/pages/migrations/tests match tip |
| B4 | ☑ PASS | ☐ N | no CRM module/route; catalog B4 fix only |
| B5 | ☑ PASS | ☐ N | catalog head `a4f7c29e1b80` / 69 |
| B6 | ☑ PASS | ☐ N | lock `free`; `21.locked_files=[]` |
| B7 | ☑ PASS | ☐ N | Measured only (0 live Repository Verified) |

**4.1 overall:** ☑ **PASS** ☐ FAIL — see `.engineering/34_EOS_REAUDIT_2026-08-02.md`

### 5.2 Criterion 4.8 — Independent re-audit

| Gate | Result |
|------|--------|
| New validation report path | `.engineering/34_EOS_REAUDIT_2026-08-02.md` |
| Report commit SHA | first land `8ff782f` / close `d973cba` (`d973cba302a76a470141d954ba36c61cd39163d5`); measurement corroboration this pack update |
| CRITICAL findings count | **0** |
| **4.8 overall** | ☑ **PASS** ☐ FAIL |

**PASS rule (checklist):** new report **and** CRITICAL count = **0**.  
**FAIL** if any CRITICAL remains, or if no new independent report is produced.

---

## 6. Governance constraints (DEC-151)

While Governance = FROZEN:

- Completing **4.1 / 4.8** with honest ARB evidence is **allowed** and does **not** require thaw.
- Cursor / Orchestrator must **not** invent PASS to clear the freeze inventory.
- Phase 0 remains **NO-GO** until all hard OPEN criteria (residual **3.7**) meet checklist evidence — ARB PASS on 4.1/4.8 alone is not Production GO.

---

## 7. Deliverable expectation after ARB

1. ARB publishes the new validation report (leave `32` FAIL history intact).  
2. ARB returns **PASS** or **FAIL** for **4.1** and **4.8** (this pack §5).  
3. Orchestrator updates checklist / board / scoreboard **only** from that evidence.  
4. If FAIL: list CRITICAL residuals; remediation agents may fix **without** claiming CLOSE until next ARB pass.

---

*End of pack. Post-ARB: **4.1 PASS · 4.8 PASS** (CRITICAL **0**) recorded via DEC-153 + `.engineering/34_EOS_REAUDIT_2026-08-02.md`. Phase 0 remains **51/54 NO-GO**.*
