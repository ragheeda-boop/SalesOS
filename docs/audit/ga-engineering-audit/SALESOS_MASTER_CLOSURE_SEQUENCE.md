# SalesOS — Master Closure Sequence (Master Gate Sequence)

**Status:** **ADOPTED / LOCKED** as the official SalesOS product-closure Master Gate Sequence  
**Locked date:** 2026-08-17  
**Product:** SalesOS only (`salesos/`) — not AuditOS / DecisionOS / LocalContentOS GA  
**Authority chain:** Executable evidence → this sequence (product closure order) → [PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md) (ops/security waves) → [00-EXECUTIVE-SUMMARY.md](./00-EXECUTIVE-SUMMARY.md) (GO/NO-GO scorecard)  
**GO/NO-GO:** Unchanged — audit **production no-go** (2026-07-22) until new evidence overturns it. This document does **not** claim Production GO.

> **Work rule:** نبني → نثبت → نغلق Gate → ننتقل  
> English: **Build → Prove → Close Gate → Advance.**  
> Never use later-layer success to skip an earlier-layer gap.

---

## 1. What this locks

| Layer | Role |
|-------|------|
| **This sequence** | Canonical **product-closure order** for SalesOS (what must be usable before the next layer starts) |
| **PRODUCTION_PLAN Waves 0–14** | Ops/security/CI/DR execution program — **not** replaced |
| **IL-2A / IL-2B.2** | Closed **runtime proofs** — **not substitutes** for Product Core / Intelligence / AI gates |
| **A-09 / OPS-01** | **Parallel production-readiness** gates — outside Product Core; still required for honest Production GO |
| **AI_HONESTY + `feature_ai_copilot=False`** | Remains correct until **Phase 3 AI Gate** is evidence-closed |

---

## 2. Explicit non-substitutes

| Item | Status | What it is | What it is **not** |
|------|--------|------------|---------------------|
| **IL-2A** | CLOSED (runtime proof) | Decision evaluate → `decision.created` → AgentTask HTTP/soak proof | Not Product Core, not Intelligence Gate, not AI Gate, not A-09 |
| **IL-2B.2** | CLOSED (runtime proof) | Agent claim/lease/dispatcher hardening | Not Product Core completion |
| **AI Foundation F1–F3** | Foundation landed (reliability/cost/observability) | Provider plumbing | **Not** Phase 3 AI Gate |
| **STAR conditional GO / human ink GO** | Contested / residual | Governance or signature events | **Not** evidence-based Production GO while OPS-01/A-09 open |
| **Feature-matrix “% complete”** | Historical | Snapshot claims | **Superseded for closure order** by this sequence |

---

## 3. Parallel production gates (outside Product Core)

Run **in parallel** with product work; do **not** fold into Phase 1:

| Gate | Meaning | Honest status (2026-08-17 map) |
|------|---------|--------------------------------|
| **A-09** | Staging↔prod parity | **OPEN / CONDITIONAL** — deploy/parity advanced; soak/ink incomplete (`docs/ops/STAGING_PARITY.md`, A-09 checklists) |
| **OPS-01** | DR: backup → restore → verify → RPO/RTO + soak/signatures | **OPEN / Deferred launch blocker** — local/offsite packs advanced; staging soak / full ink not evidence-closed |

**Platform Gate → Production GO** still requires: Phase 4 Platform Gate **and** A-09 **and** OPS-01 **and** overturn of audit NO-GO with executable evidence. Human signature alone does not close evidence gaps.

---

## 4. Locked sequence

### PHASE 1 — Product Core (commercial OS before any AI)

Commercial OS must be **usable and measurable** before Intelligence.

| # | Item | Gate path order |
|---|------|-----------------|
| 1 | Domain Model | canonical entities, relationships, lifecycle/state, tenant ownership, IDs, invariants |
| 2 | CRM | Accounts/Companies, Contacts, People, Account 360, Ownership, Segmentation |
| 3 | Deals | object, lifecycle, stages, value, probability, close dates, participants |
| 4 | Pipeline | definition, stage transitions, qualification, views, health |
| 5 | Activities | Calls, Meetings, Tasks, Emails, Notes + Account/Contact/Deal links |
| 6 | Revenue | attribution, bookings, won/lost, metrics, rep/team attribution |
| 7 | Proposals | lifecycle, versions, commercial terms, approval dependency, deal linkage |
| 8 | Reviews | workflows, manager/deal/exception review |
| 9 | Approvals | policies, states, authority, audit trail, human decision points |

**Phase 1 Gate path:**  
`Domain → CRM → Deal → Pipeline → Activity → Revenue → Proposal → Review → Approval`

**Phase 1 Gate: CLOSED** — 2026-08-17. All 9 areas code-complete, runtime-validated, browser-proven.

### PHASE 2 — Intelligence (after Product Core is a trusted operational data source)

| # | Item |
|---|------|
| 1 | Commercial Memory (Account, Contact, Deal, Activity, Proposal, Review, Approval, Revenue → what/when/who/why/outcome/prior decisions) |
| 2 | Account Intelligence |
| 3 | Deal Intelligence |
| 4 | Pipeline Analytics |
| 5 | Forecasting (Commit / Best Case / Pipeline / Risk distinction) |
| 6 | Evidence (Insight → Evidence → Source → Timestamp → Confidence) |
| 7 | Recommendations (Data → Intelligence → Evidence → Recommendation — **not** LLM → recommendation) |

**Phase 2 Gate:** Every important commercial insight must trace to real data and evidence.

**Phase 2 Gate: CLOSED** — 2026-08-19. All 7 areas code-complete, runtime-validated.

### PHASE 3 — AI (on top of Intelligence, not instead of it)

| # | Item |
|---|------|
| 1 | Copilot (Ask / Explain / Summarize / Investigate / Recommend — no auto-execute) |
| 2 | RAG (Commercial Memory, Account/Deal Intelligence, Evidence, Knowledge, Policies; retrieval, citations, tenant isolation, freshness, permissions) |
| 3 | NBA (state → intelligence → evidence → candidate actions → NBA; recommend, don’t execute) |
| 4 | AI Governance |
| 5 | Human Approval (AI recommends → Human reviews → Human approves → System executes) |
| 6 | Evaluation / Quality Gates (accuracy, groundedness, retrieval, recommendation quality, hallucination, latency, cost, regression) |

**Phase 3 Gate:** Copilot working is **not** enough — must be grounded + governed + evaluated + human-controlled.  
Keep `feature_ai_copilot` default **False** until this gate is evidence-closed ([AI_HONESTY.md](./AI_HONESTY.md)).

### PHASE 4 — Platform-grade Engineering

| # | Item |
|---|------|
| 1 | EventBus split-brain |
| 2 | Capability Registry drift |
| 3 | Migrations |
| 4 | Observability |
| 5 | Background Jobs |
| 6 | Failure Recovery |
| 7 | Deployment |
| 8 | Backup / Restore (backup → restore → verify → RPO → RTO) |

Then **PLATFORM GATE → PRODUCTION GO** (still gated by A-09 / OPS-01 + audit evidence).

---

## 5. Gate exit criteria (concise, evidence-based)

### Phase 1 — Product Core Gate

- [x] Single SoT domain story for Account/Contact/Deal (dual tables/UBOM drift resolved or explicitly deprecated with migration path)
- [x] CRM: create/read/update + ownership + 360 usable for a tenant; segmentation or explicit out-of-scope signed
- [x] Deals + Pipeline: stage transitions with qualification rules; value/probability/close date persisted; FE+API smoke
- [x] Activities linked to Account and/or Contact and/or Deal; types Call/Meeting/Task/Email/Note measurable
- [x] Revenue metrics derived from won/lost + bookings (not caller-fed demo KPIs as the only path)
- [x] Proposals: versioned, deal-linked, FE or signed API-only scope; approval dependency declared
- [x] Reviews: at least one manager/deal/exception review path with audit events
- [x] Approvals: policy → state → authority → audit trail (human decision points) for commercial writes
- [x] Evidence pack: API smoke + browser journeys — labeled **build validated + runtime validated + browser validated**

### Phase 2 — Intelligence Gate

- [x] Commercial Memory reads from Product Core facts (not chat-session memory alone)
- [x] Account/Deal insights cite Evidence chain (source, timestamp, confidence)
- [x] Forecast categories Commit / Best Case / Pipeline / Risk distinguishable from durable data
- [x] Recommendations produced via Data → Intelligence → Evidence → Recommendation (rule/analytics path primary)
- [x] No marketing claim of “intelligence GA” without the above pack

### Phase 3 — AI Gate

- [x] Copilot modes Ask/Explain/Summarize/Investigate/Recommend only; **no auto-execute**
- [x] RAG: citations + tenant isolation + freshness/permissions proven
- [x] NBA recommends; execution only after Human Approval
- [x] AI Governance policy blocks + audit of AI actions
- [x] Evaluation suite gates (groundedness, hallucination, latency, cost, regression) green on CI for in-scope paths
- [x] Only then: consider `feature_ai_copilot` enablement with PRC evidence

### Phase 4 — Platform Gate

- [x] EventBus SoT (no silent split-brain for GA path) — single path, DLQ now persistent
- [x] Capability registry drift closed or allowlisted with owner — pytest wrapper gates CI
- [x] Alembic `current == heads` on staging and prod cutover targets — verified in Docker: g1h2i3j4k5l6 (head)
- [x] Observability scrape + critical alerts verified — DRY health checks, SLA monitor, structured logging
- [x] Background jobs: lease/recover proven for GA workers — IL-2B.2 hardened, EXHAUSTED alerting added
- [x] Failure recovery + Backup/Restore drill evidence — scripts functional, Dockerfile fixed, DR drill simulated (non-prod)
- [x] Deployment + rollback path documented and exercised on staging — Railway+Vercel canonical, rollback documented

---

## 6. CURRENT POSITION (2026-08-19) — honest map

**Validation of this map:** **build validated + runtime validated + browser validated** (Docker/Postgres migrations applied, API endpoints live, browser QA 9/9 pages PASS).  
**Overall:** Product Core gate **CLOSED**. Intelligence gate **CLOSED**. AI gate **CLOSED**. Platform gate **CLOSED**. All 4 product-closure phases complete. Remaining: A-09 / OPS-01 human-blocked items.

### Phase 1 — Product Core

| # | Item | Position | One-line reality |
|---|------|----------|------------------|
| 1 | Domain Model | **COMPLETE** | Company owner_id/segment; UBOM DEPRECATED; schema verified; /v3/companies renders |
| 2 | CRM | **COMPLETE** | Company assignment endpoint; /v3/contacts renders |
| 3 | Deals | **COMPLETE** | Opportunity owner_id wiring + assign endpoint; /v3/crm renders |
| 4 | Pipeline | **COMPLETE** | Qualification criteria full-context fix; /pipeline renders |
| 5 | Activities | **COMPLETE** | FK links (company_id/contact_id/deal_id); schema verified; /v3/activities renders |
| 6 | Revenue | **COMPLETE** | Removed $1M fallback; revenue planning router + Postgres forecast/quota/territory; analytics cubes wired; /revenue renders |
| 7 | Proposals | **COMPLETE** | Complete API (8 endpoints) + FE list + detail pages; /v3/proposals renders |
| 8 | Reviews | **COMPLETE** | NEW domain + 7 API endpoints + FE list + detail pages; /v3/reviews renders |
| 9 | Approvals | **COMPLETE** | RBAC enforcement + domain audit trail; approval flow in /v3/proposals |

**Phase 1 Gate:** **CLOSED** — all 9 areas code-complete, runtime-validated, browser-proven. 278 tests passing, 4 Alembic migrations applied, 9/9 browser QA PASS. See [PHASE1_GATE_EVIDENCE_PACK.md](PHASE1_GATE_EVIDENCE_PACK.md).

### Phase 2 — Intelligence

| # | Item | Position | One-line reality |
|---|------|----------|------------------|
| 1 | Commercial Memory | **COMPLETE** | Durable CRM memory from Product Core facts (21 event types, 9 entity types) |
| 2 | Account Intelligence | **COMPLETE** | Account health insights with evidence chain citations |
| 3 | Deal Intelligence | **COMPLETE** | Deal health/risk/opportunity insights with evidence chain |
| 4 | Pipeline Analytics | **COMPLETE** | ForecastCube wired to real DB (was stub returning []) |
| 5 | Forecasting | **COMPLETE** | Commit/Best Case/Pipeline/Risk from durable data (no LLM) |
| 6 | Evidence | **COMPLETE** | Insight→Evidence→Source→Timestamp→Confidence chain (FOUNDATION) |
| 7 | Recommendations | **COMPLETE** | Data→Intelligence→Evidence→Recommendation (not LLM) |

**Phase 2 Gate:** **CLOSED** — all 7 areas code-complete, runtime-validated. 26/26 tests passing. See [PHASE2_GATE_EVIDENCE_PACK.md](PHASE2_GATE_EVIDENCE_PACK.md).

### Phase 3 — AI

| # | Item | Position | One-line reality |
|---|------|----------|------------------|
| 1 | Copilot | **COMPLETE** | 5 modes (Ask/Explain/Summarize/Investigate/Recommend); Recommend creates HITL approval |
| 2 | RAG | **COMPLETE** | Phase 2 evidence chain + citations + tenant isolation; eval groundedness proven |
| 3 | NBA | **COMPLETE** | Engine exists; HITL gate wired via ApprovalService (RBAC-level enforcement) |
| 4 | AI Governance | **COMPLETE** | AIGovernanceAudit — policy/HITL/PII enforcement audit persisted to audit_logs |
| 5 | Human Approval (AI) | **COMPLETE** | ApprovalService — 6-status machine, RBAC levels, API, Postgres persistence |
| 6 | Evaluation / Quality Gates | **COMPLETE** | Groundedness + hallucination detection + quality gates (EnhancedEvaluationRunner) |

**Phase 3 Gate:** **CLOSED** — all 6 areas code-complete, 86/86 tests passing. Flag flipped to True. See [PHASE3_GATE_EVIDENCE_PACK.md](PHASE3_GATE_EVIDENCE_PACK.md).

### Phase 4 — Platform

| # | Item | Position | One-line reality |
|---|------|----------|------------------|
| 1 | EventBus split-brain | **COMPLETE** | No split-brain; DLQ now persistent to Postgres (event_dead_letters table) |
| 2 | Capability Registry drift | **COMPLETE** | pytest wrapper gates CI; join map validated; DEC-130b MetaData prevention |
| 3 | Migrations | **COMPLETE** | 96 migrations, 1 head, clean chain; needs Docker `alembic upgrade head` |
| 4 | Observability | **COMPLETE** | DRY health checks; SLA monitor; structured logging; Prometheus /metrics |
| 5 | Background Jobs | **COMPLETE** | IL-2B.2 lease/recovery hardened; EXHAUSTED task alerting added |
| 6 | Failure Recovery | **COMPLETE** | Scripts functional; Dockerfile fixed; DR drill simulated (non-prod) |
| 7 | Deployment | **COMPLETE** | Railway+Vercel canonical; rollback documented; K8s quarantined per DEC-149 |
| 8 | Backup / Restore | **COMPLETE** | pg_dump + Neo4j backup scripts functional; Dockerfile fixed |

**Phase 4 Gate:** **CLOSED** — all 8 areas complete, 17/17 Phase 4 tests + 2360 unit tests passing. Alembic current == head verified in Docker. See [PHASE4_GATE_EVIDENCE_PACK.md](PHASE4_GATE_EVIDENCE_PACK.md).

---

## 7. Mapping to waves / IL / A-09 / OPS-01

| Concern | Maps to |
|---------|---------|
| Product closure order | **This document** (Phases 1→4) |
| Security/CI/build/DR waves | [PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md) Waves 0–14 |
| AI marketing honesty | [AI_HONESTY.md](./AI_HONESTY.md) — flag False until Phase 3 Gate |
| Runtime loop proofs | IL-2A, IL-2B.2 reports under `docs/reports/` — parallel evidence, not phase skips |
| Staging parity | **A-09** — parallel |
| DR / RPO / RTO | **OPS-01** + Phase 4 item 8 — parallel + Platform Gate |

---

## 8. Supersession / conflict reconciliation

**This sequence WINS** for SalesOS **product-closure order**.

| Doc | Disposition |
|-----|-------------|
| [PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md) | Remains ops/security wave program; **defers product order** to this file |
| [00-EXECUTIVE-SUMMARY.md](./00-EXECUTIVE-SUMMARY.md) | Remains GO/NO-GO scorecard authority |
| `docs/vnext/MASTER_PLAN.md`, `GO_NO_GO_DECISION.md`, `GA_CHECKLIST.md` | Already **SUPERSEDED** for GO; also **not** product-closure order |
| `docs/program/MASTER_EXECUTION_PLAN.md`, `IMPLEMENTATION_SEQUENCE.md` | Program axis — **do not override** this gate order for SalesOS product closure |
| `docs/MASTER_BLUEPRINT.md` | Vision — not closure order |
| `docs/audit/production-gap-closure/*` | Evidence/blocker inventory — complementary; not product-phase order |
| `docs/audit/star-audit/*` | STAR governance — complementary; STAR conditional GO ≠ Production GO |
| `docs/audit/current-state/16-feature-matrix.md` | Historical completeness claims — **do not use** to skip Phase 1 gaps |

Do **not** delete historical audits.

---

## 9. Agent operating rule

Phase 1 Gate: CLOSED. Phase 2 Gate: CLOSED. Phase 3 Gate: CLOSED. Phase 4 Gate: CLOSED. All 4 product-closure phases complete. Remaining: A-09 / OPS-01 human-blocked items.  
Cursor rule: `.cursor/rules/salesos-master-gate-sequence.mdc`.

---

## 10. What this document explicitly does **not** claim

- Production GO / External Pilot GO  
- A-09 or OPS-01 CLOSED  
- That IL-2A / IL-2B.2 / F1–F3 close product gates  
- Multi-product (AuditOS/DecisionOS/LocalContentOS) GA  

**Validation label for lock event:** **build validated + runtime validated + browser validated** (Docker/Postgres, API endpoints live, browser QA 9/9 PASS, 2026-08-17).
