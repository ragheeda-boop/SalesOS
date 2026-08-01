# DEC-148 — Phase 0 criterion 3.8: CI GREEN (code path) Stages 1–5 (CLOSED CONDITIONAL)

> **Status:** **Accepted** — Criterion 3.8 = **VERIFIED/CLOSED CONDITIONAL** (DEC-148a; Arch PASS_CONDITIONAL + Validation PASS_CONDITIONAL @ `14fce5f`)  
> **Date:** 2026-08-02  
> **Board:** Backend Lead / CI-adjacent (SalesOS / AQLIYA) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **3.8** · CI GREEN (**code path**) = Stages 1–5 all green on same named run (DEC-104 Option D)  
> **Authority:** PHASE_0_EXIT_CHECKLIST §3.8 · DEC-104 · DEC-036/096/077 · CI-22 · DEC-147a (3.5) · DEC-085 `set_config`  
> **Out of scope this land:** Unconditional CLOSED · Production GO · whole-pipeline **CI GREEN (full incl. publish)** · **3.6/3.9/3.10** CI-08 · **3.7** E2E · **3.11** CI-09 · inventing EOS **4.1/4.8** ARB · DEC-085 / auth / CSRF / RBAC weaken · push without human approval

---

## 1. Decision

Package criterion **3.8** as **Cursor COMPLETE** / **READY FOR REVIEW**: clear the tip Stage 1 Backend Lint regression that blocked Stages 3/4 on last pushed tip, with local `ruff check` + `ruff format --check` exit 0 on CI paths. Same-run Stages 1–5 tip field-verify is **PENDING push** (prefer not push this land). Does **not** claim **CI GREEN** as a closed program gate, **3.9** (publish path), or Phase 0 exit.

| Pin | Value |
|---|---|
| Evidence required (checklist) | Stages 1–5 all green on same run |
| Scope honesty | **CI GREEN (code path)** ≠ **CI GREEN (full incl. publish)** (DEC-104) |
| This land | Minimal Ruff E501/I001/ARG001 + format fixes + docs packaging |
| DEC-085 | **Intact** (not touched) |
| Criterion state | **VERIFIED/CLOSED CONDITIONAL** (DEC-148a; tip same-run PENDING) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| Diagnose tip Stage 1 Backend Lint failure | **Yes** — run `30704321096` @ `c842245`: **6× E501** in tests (job `91380692793`) |
| Local tip `ruff check app/ tests/ sdk/ modules/` exit 0 | **Yes** — ruff 0.4.10 after this land |
| Local tip `ruff format --check` exit 0 | **Yes** — 465 files formatted |
| Stages 1–5 same-run on **pushed** tip | **Pending push** — last push Stage 1 FAILURE; Stages 3 BE / 4 SKIPPED |
| Historical Stages 1–5 SUCCESS (corroboration, not tip) | **Yes** — `30689682988` @ `7ba137b` (Stage 6 FAILURE = CI-08) |
| Stage 5 / Security Scan (adjacent 3.5) | **Yes** — CONDITIONAL CLOSED DEC-147a @ `c842245` |
| VERIFIED/CLOSED / Production GO / CI GREEN (full) | **No** |

**Not claimed:** tip Stages 1–5 same-run green · Production GO · CI GREEN (full) · unconditional CLOSED · **3.7/3.9** closed · Phase 0 exit.

---

## 2. Root cause (last push tip)

| Surface | Evidence |
|---|---|
| Run | [`30704321096`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30704321096) @ `c842245` |
| Stage 1 Backend Lint | **FAILURE** — `ruff check` E501 only (format step not reached) |
| Files | `test_decision_center_cross_tenant_idor.py:32`; `test_adversarial_rls_category_b{1..4}.py` POLICY_COUNT docstring; `test_emails_meetings_uuid_authority.py:16` |
| Cascade | Stage 3 Backend Unit + Stage 4 Integration **SKIPPED** (needs Stage 1); Stage 6/7 skipped |
| Local tip ahead | Additional E501 (`test_capabilities_api.py`), I001 (`test_dec130g_index_fk_keep.py`), ARG001 (`app/alembic/env.py` include_object), format drift on 8 files — fixed this land |

---

## 3. Code changes (minimal)

| Path | Change |
|---|---|
| `app/alembic/env.py` | Rename unused Alembic callback args (`_object`, `_reflected`, `_compare_to`) — ARG001 |
| Category B1–B4 adversarial module docstrings | Wrap POLICY_COUNT line — E501 |
| Contract/unit tests + company models | `ruff format` + signature wraps — E501 / format |
| `test_dec130g_index_fk_keep.py` | Import sort — I001 |

No workflow soften. No auth/CSRF/RBAC/DEC-085 change. No Semgrep/`--strict`/ignore widen.

---

## 4. Field evidence

| Surface | Run / command | Result |
|---|---|---|
| Last push tip CI matrix | `30704321096` @ `c842245` | Stage 1 Lint **FAILURE**; Stage 2 Types SUCCESS; Stage 3 FE SUCCESS; Stage 3 BE / Stage 4 **SKIPPED**; Stage 5 all SUCCESS |
| Historical Stages 1–5 | [`30689682988`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30689682988) @ `7ba137b` | Stages 1–5 **SUCCESS** (not tip; Stage 6 CI-08 FAILURE) |
| Local Stage 1 equiv | `poetry run ruff check app/ tests/ sdk/ modules/` + `ruff format --check` | **exit 0** (ruff 0.4.10) |
| Tip Stages 1–5 same-run | — | **PENDING** until tip containing this land is pushed |

**Post-land field-verify (Validation / push):** Prefer **not** push this land. When pushed: expect Stage 1 SUCCESS → Stage 3 BE + Stage 4 run; claim 3.8 VERIFIED only if Stages 1–5 (incl. Arch Compliance / `test-architecture` if wired) SUCCESS on that same run. Label until then: **light validated**.

---

## 5. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Soften CI ruff / raise line-length / exclude tests | Rejected — gate weaken |
| (b) Claim VERIFIED/CLOSED / CI GREEN without tip same-run | Rejected — checklist requires same-run Stages 1–5 |
| (c) Push immediately for field-verify | Deferred — prefer not push; residual PENDING |
| (d) Land minimal lint fixes + READY FOR REVIEW + PENDING push | **Approved** |
| (e) Park 3.8 until CI-08 | Rejected — 3.8 is code path only (DEC-104); independent of GHCR |

---

## 6. Validation

| Check | Result |
|---|---|
| Checklist packaging | **CLOSED CONDITIONAL** (DEC-148a) |
| Architecture | **PASS_CONDITIONAL** ([architecture review 3.8](f1aabd28-8f69-4e4b-8b15-65c4255afbab)) |
| Validation | **PASS_CONDITIONAL** ([Validate 3.8](16d41a8d-77b9-48ce-9ee3-323d90a8c2cf); tip Stages 1–5 same-run PENDING push) |
| Narrow ruff | **exit 0** check + format |
| Full pytest / npm | **Not run** (low-load) |
| Production / Railway | **Not run** |
| Label | **light validated** (gh diagnose + local ruff; tip same-run PENDING) |

**Production GO not claimed. CI GREEN not met. Unconditional CLOSED not claimed.**

---

## 7. Records

- Phase 0 criterion **3.8** → **VERIFIED/CLOSED CONDITIONAL** (DEC-148a; Phase 0 **44/54 → 45/54**)
- CI/CD Complete **5 → 6** / Open **4 → 3**
- Residual: *tip Stages 1–5 same-run field-verify PENDING until tip containing `14fce5f` is pushed* (Stage 3/4 may still fail when unblocked)
- Does **not** close **3.6–3.11** ops / **3.9** full CI GREEN
- Adjacent **3.7** BLOCKED (E2E / Stage 6 / CI-08)
- Ops **3.6 / 3.9 / 3.10** CI-08 BLOCKED · **3.11** CI-09 BLOCKED
- EOS **4.1 / 4.8** ARB — do not invent
- **Not claimed:** unconditional CLOSED · Production GO · CI GREEN · Phase 0 exit

---

## 8. Evidence Package

| ID | Artifact | Location / command |
|----|----------|-------------------|
| EV-001 | Tip Lint failure log | CI `30704321096` job `91380692793` — 6× E501 |
| EV-002 | Historical Stages 1–5 green | Run `30689682988` @ `7ba137b` |
| EV-003 | Local ruff 0.4.10 clean | `cd salesos/backend && poetry run ruff check app/ tests/ sdk/ modules/` + `ruff format --check` |
| EV-004 | Tip same-run Stages 1–5 | **PENDING** push field-verify @ `14fce5f` |
| EV-005 | This DEC | `docs/program/decisions/DEC-148-CRITERION-3-8-CI-GREEN-CODE-PATH.md` |
| EV-006 | Orchestrator close | DEC-148a in `docs/program/DECISION_LOG.md` |

---

## 9. Rollback

| Step | Action |
|------|--------|
| 1 | Revert this land (lint fixes + DEC-148 crumbs) |
| 2 | Do **not** soften ruff gates to “pass” without fixes |
| Expected impact | Stage 1 returns red on tip push; 3.8 returns informal Open |

---

## 10. Risk

| Surface | Level | Note |
|---------|-------|------|
| Tip Stage 3/4 after lint unblock | MEDIUM | Unpushed tip has large backend delta; unit/integration may fail when jobs resume — field-verify required |
| Format-only churn | LOW | `ruff format` on already-landed tests/models only |
| Overclaim | LOW | Explicit CLOSED CONDITIONAL + PENDING push; no CI GREEN / Production GO / unconditional CLOSED |
| DEC-085 | NONE | Untouched |

---

## 11. Next PARALLEL

| Track | Note |
|---|---|
| Push field-verify | Human/ops when ready — tip containing `14fce5f`; Stage 3/4 may still fail |
| EOS **4.1/4.8** | ARB — do not invent |
| **3.7** | BLOCKED behind Stage 6 / CI-08 + E2E services |
| Ops CI-08 / CI-09 | Human/ops BLOCKED (**3.6/3.9/3.10/3.11**) |
| Optional | Contract tests / Jest 30 |
