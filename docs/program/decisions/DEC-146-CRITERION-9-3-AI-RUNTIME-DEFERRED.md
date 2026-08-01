# DEC-146 — `.ai/` Agent OS runtime explicitly deferred (Phase 0 criterion 9.3)

> **Status:** **Accepted** — Criterion 9.3 = **VERIFIED/CLOSED** via DEC-146a (Arch PASS + Validation PASS light · Orchestrator 2026-08-01) · ADR-036 Applied **COMPLETE 4/4**  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / ADR-036 Applied (SalesOS / AQLIYA) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **9.3** · `.ai/` explicitly deferred with trigger condition  
> **Authority:** PHASE_0_EXIT_CHECKLIST §9.3 · ADR-036 · ARB-2026-08-01-003 · DEC-145 (org baseline ≠ full runtime) · DEC-141 bridges  
> **Out of scope this land:** inventing Agent OS scheduler/queue · EOS **4.1/4.8** ARB · CI-08/CI-09 ops · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN · Phase 0 exit

---

## 1. Decision

Resolve criterion **9.3** by packaging an **honest deferral evidence set**: distinguish committed **AI Organization baseline** (roles/bindings/runtime SPEC) from **deferred full Agent OS runtime**, and pin **explicit trigger conditions** before Phase 3 construction may begin.

| Pin | Value |
|---|---|
| Evidence required | Documented with trigger condition |
| Observation | ADR-036 deferred `.ai/` runtime; DEC-145 committed org baseline + `runtime-spec.yaml` `status: SPECIFICATION`; bridges already say “full Agent OS runtime DEFERRED (9.3)”; checklist 9.3 lacked formal VERIFIED packaging |
| Disposition | Pin triggers in ADR-036 + `.ai/README`; wire DEC-146; CLOSED via DEC-146a |
| Criterion state | **VERIFIED/CLOSED** (DEC-146a) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| Org baseline ≠ running Agent OS documented | **Yes** — ADR-036 deferral section + `.ai/README` + `runtime-spec.yaml` status SPECIFICATION |
| Explicit trigger conditions listed | **Yes** — ADR-036 §`.ai/` Runtime deferral (criterion 9.3) |
| Bridges / DEC-145 retain deferred runtime | **Yes** — no scheduler invented |
| DEC-085 / auth untouched | **Yes** |
| VERIFIED/CLOSED (criterion 9.3) | **Yes** — DEC-146a after Arch PASS + Val PASS (light) |
| Production GO / CI GREEN | **No** |

**Not claimed:** Production GO · CI GREEN · Phase 0 exit · closing 4.1 / 4.8 · inventing ARB PASS · claiming Agent OS runtime live.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Treat checklist bare ✅ as CLOSED without trigger package | Rejected — Open 1 residual after DEC-141a; evidence required |
| (b) Claim VERIFIED/CLOSED in this land | Rejected — Arch+Val + Orchestrator gate |
| (c) Build / invent running scheduler to “satisfy” 9.3 | Rejected — contradicts ADR-036 / Architecture FROZEN |
| (d) Remove `.ai/` org baseline to make deferral “pure” | Rejected — breaks 8.2 / ARB-003; org ≠ runtime |
| (e) Explicit deferral + triggers + READY FOR REVIEW | **Approved** |

---

## 3. Validation

| Check | Result |
|---|---|
| ADR-036 deferral + triggers present | **Yes** (this land) |
| `.ai/README` deferral pointer | **Yes** (this land) |
| `runtime-spec.yaml` status | `SPECIFICATION` (unchanged semantics) |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (filesystem + doc presence; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met.**

---

## 4. Records

- Phase 0 criterion **9.3** → **VERIFIED/CLOSED** (DEC-146a; Phase 0 **42/54 → 43/54**)
- ADR-036 Applied: Complete **4** / Open **0** (cluster **COMPLETE 4/4**)
- Residuals (non-blocking for 9.3): EOS **4.1/4.8** ARB · CI-08/CI-09 ops · CI **3.5/3.7/3.8** · 2.3 multi-tenant residual
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | ADR-036 deferral + triggers | `docs/adr/0036-engineering-organization-layer-separation.md` |
| EV-002 | `.ai/` honesty + deferral | `.ai/README.md` |
| EV-003 | Runtime SPEC (not engine) | `.ai/runtime/runtime-spec.yaml` (`status: SPECIFICATION`) |
| EV-004 | Layer bridges (org vs runtime) | `docs/program/ENGINEERING_LAYER_BRIDGE.md` · `.engineering/33_PROGRAM_LAYER_BRIDGE.md` |
| EV-005 | Org baseline land (runtime still deferred) | `docs/program/decisions/DEC-145-CRITERION-8-2-AGENT-COORDINATION.md` |
| EV-006 | This DEC | `docs/program/decisions/DEC-146-CRITERION-9-3-AI-RUNTIME-DEFERRED.md` |
| EV-007 | Checklist / board / DAG crumbs | `PHASE_0_EXIT_CHECKLIST.md` · `SPRINT_05_DELIVERY_BOARD.md` · `EXECUTION_DAG.md` · `DECISION_LOG.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (ADR-036 deferral section + `.ai/README` + DEC-146 crumbs) |
| 2 | No auth/DB/runtime behavior to undo |
| Expected impact | 9.3 returns informal/Open without packaged triggers |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Confusing org baseline with runtime live | LOW | Explicit split in ADR + README + bridges |
| Premature Phase 3 construction | LOW | Triggers require Phase 0 54/54 + CI GREEN + ARB 4.1/4.8 + formal ARB |
| Overclaim Production GO / CI GREEN / Phase 0 exit | LOW | 9.3 CLOSED only; residuals remain |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 9.3? | **Done** — DEC-146a VERIFIED/CLOSED; ADR-036 Applied **COMPLETE 4/4** |
| Next PARALLEL | EOS **4.1/4.8** ARB (do not invent) · CI **3.5/3.7/3.8** (non-GHCR) · optional contract tests / Jest 30 · ops CI-08/09 BLOCKED |
| Do not | Invent Agent OS runtime · claim Production GO / CI GREEN · claim Phase 0 exit · weaken auth / DEC-085 |
