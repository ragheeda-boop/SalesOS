# SalesOS Completion Program — Living Charter

**Started:** 2026-08-08  
**Director:** Program Director (agent)  
**Product:** SalesOS   
**Order:** User «ابدء الان هذا امر» — execute without waiting for «التالي» between waves  

**Principle:** AI assists. Humans decide. Evidence governs.

---

## 1. Mission

Drive agent-executable residuals to honest dispositions (Fixed / Partial / Deferred / Human-Gate) while publishing exact Human Gate cards for everything that requires ink, secrets, cloud staging, soak windows, or production migrate.


| Classification                   | Status (2026-08-08)                                                         | Meaning                                                               |
| -------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **human-declared GO**            | **YES** — [SIGN_HERE.md](./SIGN_HERE.md) CTO+TL (رغيد المدني; dual-role P1) | Human ink Decision=GO                                                 |
| **evidence-based Production GO** | **NOT claimed**                                                             | Engineering residuals remain; do not invent soak/offsite/prod migrate |


Companion honesty: [reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md](./reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md).  
Session wrap: [completion/SESSION-CLOSEOUT-2026-08-08.md](./completion/SESSION-CLOSEOUT-2026-08-08.md) (PR **~83**, testing **~104** cited; operator leftovers = Human Gates).

---



## 2. Authority chain (when docs conflict)

1. **Executable evidence** (JSON / command output under `evidence/` or EAB evidence trees)
2. **EAB-2026-08-06-003** SCORECARD / CEO-SUMMARY / RUN-REPORT / FINDINGS-RECHECK
3. **Reconciliation pack** — [AUTHORITATIVE-DOCUMENT-MAP.md](./reconciliation-2026-08-07/AUTHORITATIVE-DOCUMENT-MAP.md), [DOCUMENT-CONTRADICTIONS.md](./reconciliation-2026-08-07/DOCUMENT-CONTRADICTIONS.md), [BOARD-CONSENSUS.md](./reconciliation-2026-08-07/BOARD-CONSENSUS.md)
4. **This Completion Program** + [completion/PROGRAM-BOARD.md](./completion/PROGRAM-BOARD.md)
5. Historical baselines / STAR / Principal — **labeled era**, never shopped as current SoT without fence

Canonical links:


| Topic                    | Path                                                                                                                                                                                                                                                  |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Release/ops backlog      | [RELEASE-BACKLOG-2026-08-06.md](./RELEASE-BACKLOG-2026-08-06.md)                                                                                                                                                                                      |
| OPS-01 pack              | [enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-ADVANCEMENT.md](./enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-ADVANCEMENT.md) · [OPS-01-CHECKLIST.md](./enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md) |
| EAB status               | [enterprise-audit-board/history/EAB-2026-08-06-003/RUN-REPORT.md](./enterprise-audit-board/history/EAB-2026-08-06-003/RUN-REPORT.md)                                                                                                                  |
| Human GO declaration     | [reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md](./reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md)                                                                                                                        |
| Prod migration risk      | [PROD-MIGRATION-RISK.md](./PROD-MIGRATION-RISK.md)                                                                                                                                                                                                    |
| Reconciliation pack      | [reconciliation-2026-08-07/](./reconciliation-2026-08-07/)                                                                                                                                                                                            |
| Cutover gate (CLOSED?)   | [../../ops/DR-GA-GAPS-CHECKLIST.md](../../ops/DR-GA-GAPS-CHECKLIST.md) — gate ≠ drill facts                                                                                                                                                           |
| Human gate card (living) | [completion/HUMAN-GATE-CARD.md](./completion/HUMAN-GATE-CARD.md)                                                                                                                                                                                      |


---



## 3. Streams (A–F)


| Stream | Name               | Mission                                                                                              | Primary DoD                                                     |
| ------ | ------------------ | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **A**  | OPS Launch         | Max in-repo OPS-01 progress; publish exact human actions                                             | HUMAN-GATE-CARD complete; soak/offsite not faked                |
| **B**  | Platform Integrity | Push DUP-01 / AIGOV / DRIFT / DUP-02 / FIT toward Fixed where code-possible                          | Disposition + residual honesty on PROGRAM-BOARD                 |
| **C**  | Quality Gates      | Boot/import green for targeted unit; FE lint meaningful reduction + CI honesty                       | Boot Fixed (code); FE lint/build **Fixed (cited)** per [completion/SESSION-HARVEST-VERIFY-2026-08-08.md](./completion/SESSION-HARVEST-VERIFY-2026-08-08.md) — hold Stream C unless regression; npm not re-run in W2/W3 |
| **D**  | Security Prove     | Staging pentest checklist ready; local SSRF/KG regression; rotation instructions (no secrets in git) | Checklist + rotation runbook; no forged PASS                    |
| **E**  | Migration Dress    | Non-prod dress-rehearsal runbook only                                                                | Runbook + wall if no Docker; **NEVER** prod upgrade             |
| **F**  | Governance Sync    | Align CRITICAL contradiction labels to evidence without inventing CLOSE                              | RC-P0-01..03 labels evidence-aligned; AUTHORITATIVE map honored |


---



## 4. Ownership / file locks

Agents **must not** edit outside their lock without Director reassignment. Parallel safe = disjoint trees.


| Stream       | Owns (write)                                                                                                                           | Read-only / avoid write                                      |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| **A**        | `completion/HUMAN-GATE-CARD.md`, `runbooks/ops01-`*, OPS-01 advancement notes under `completion/`                                      | Do not forge SIGN_HERE; do not flip `soak_complete_claim`    |
| **B**        | `salesos/backend/app/modules/decision`*, decision SoT docs, MetaData freeze notes, fitness CI subset docs/workflows under agreed paths | Avoid TenantList / security P0 middleware unless assigned    |
| **C**        | `salesos/backend/app/main.py` (boot), targeted unit fixes, FE lint batches under `salesos/frontend/` (batched files only)              | No full `npm run build` without approval                     |
| **D**        | `runbooks/staging-ssrf-pentest.md`, `completion/*-SECURITY`*, local SSRF/KG tests                                                      | No secrets; no weaken auth/CSRF/RBAC                         |
| **E**        | `completion/*MIGRATION`*, non-prod runbooks                                                                                            | **Forbidden:** prod Alembic upgrade / Railway prod migrate   |
| **F**        | `docs/ops/DR-GA-GAPS-CHECKLIST.md` (honesty banners only), reconciliation addenda under `completion/`, AUTHORITATIVE map addendum      | Do not rewrite SIGN_HERE ink; do not claim evidence-based GO |
| **Director** | `COMPLETION-PROGRAM.md`, `completion/PROGRAM-BOARD.md`, `completion/M*-STATUS.md`, `completion/WAVE-*.md`                              | Coordinates locks                                            |


**Conflict rule:** If two streams need the same file → Director serializes; prefer Stream C for `main.py`, Stream F for gate checklists, Stream A for human cards.

---



## 5. Loop protocol

```text
Mn stabilize/document → parallel stream work under locks → WAVE-YYYYMMDD-n.md
  → update PROGRAM-BOARD.md → spawn next parallel batch → do not ask «التالي»
  → pause ONLY on true Human Gates (publish card, keep other streams moving)
```


| Artifact         | Path                                                               |
| ---------------- | ------------------------------------------------------------------ |
| Milestone status | `completion/M0-STATUS.md`, `M1-STATUS.md`, …                       |
| Wave report      | `completion/WAVE-YYYYMMDD-n.md` (same spirit as REMEDIATION-WAVEn) |
| Living matrix    | `completion/PROGRAM-BOARD.md`                                      |
| Human actions    | `completion/HUMAN-GATE-CARD.md`                                    |


**Status vocabulary:** `Open` · `Fixed` · `Partial` · `Deferred` · `Human-Gate` · `Blocked-Wall` · `HUMAN-GO-INK` (signatures only)

---



## 6. Human gates (never agent-closed)

1. Staging cloud GH Environments / secrets / real deploy+rollback
2. Staging soak ≥48–72h + TL evidence review (`soak_complete_claim`)
3. Offsite/WAL schedule automation + native PITR UI (Railway Not Authorized class)
4. Human CLOSE ink on DR cutover gate rows (distinct from drill JSON DONE*)
5. Credential rotation (field)
6. RPO/RTO signed acceptance (SIGN_HERE item)
7. Production migrate / cutover execution
8. Independent second-role signature (dual-role P1 residual)

---



## 7. Stop / pause criteria


| Condition                                                   | Action                                          |
| ----------------------------------------------------------- | ----------------------------------------------- |
| Agent-executable rows dispositioned + human cards published | Pause program loop; await human                 |
| Hard wall (no Docker, no secrets, no staging host)          | Document `Blocked-Wall`; continue other streams |
| Security weaken requested                                   | Refuse                                          |
| Ask to claim evidence-based Production GO without evidence  | Refuse; keep human-declared GO distinct         |
| User orders stop / commit / push                            | Obey explicit instruction                       |


---



## 8. Validation honesty

Use AGENTS.md labels only: **not validated** · **light validated** · **build validated** · **pilot-ready with conditions** · **production no-go** (engineering).

Do **not** equate human-declared GO with evidence-based GA.

Low-load default: targeted verify OK; full suites only when a stream finishes a batch **and** user/protocol allows.

---



## 9. Immediate milestone plan


| Milestone | Focus                                                | Streams                      |
| --------- | ---------------------------------------------------- | ---------------------------- |
| **M0**    | Stabilize boot + governance labels + ownership locks | C, F, Director               |
| **M1**    | First full parallel wave                             | A, B, C, D, E (+ F residual) |
| **M2**    | Prove prep (soak harness + evidence + dress probe)   | A, E, Director — [completion/M2-STATUS.md](./completion/M2-STATUS.md) · WAVE-2/3 |


### Current pointer (2026-08-08)

| Artifact | Path |
|----------|------|
| Latest wave | [completion/WAVE-20260808-5.md](./completion/WAVE-20260808-5.md) |
| Prior waves | [WAVE-20260808-4.md](./completion/WAVE-20260808-4.md) · [WAVE-20260808-3.md](./completion/WAVE-20260808-3.md) · [WAVE-20260808-2.md](./completion/WAVE-20260808-2.md) |
| Board | [completion/PROGRAM-BOARD.md](./completion/PROGRAM-BOARD.md) |
| Human card | [completion/HUMAN-GATE-CARD.md](./completion/HUMAN-GATE-CARD.md) |
| Soak mid-window | [completion/SOAK-PROGRESS-SNAPSHOT-2026-08-08.md](./completion/SOAK-PROGRESS-SNAPSHOT-2026-08-08.md) — **~20.3h / 72h**; claim **false** |
| Harvest verify | [completion/SESSION-HARVEST-VERIFY-2026-08-08.md](./completion/SESSION-HARVEST-VERIFY-2026-08-08.md) — PR **~83**; gaps **8** |

**Next agent-executable focus (suggested):** Stream **B** honesty only if obvious · Stream **E** non-prod upgrade only after restore-to-baseline + operator intent · Stream **F** score SoT fence — while soak continues Human-Gate (~20.3h elapsed). Packages lint Errors closed (W5). Do not stop loop solely for soak wall-clock. Do not start a second soak writer.

---

*Completion Program living charter — 2026-08-08 — human-declared GO ≠ evidence-based Production GO — no commit unless user asks*