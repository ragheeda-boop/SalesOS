# 02 — Methodology | المنهجية

**Pack:** Enterprise Audit Board v2.1  
**Role:** Full audit axis catalog  
**Axis count:** **43** (axes 01–39 from v2 charter; axes **40–43** = **v2.1 additions**)  
**Execution state:** All axes `not executed` until an approved run

For every axis: **Purpose** → **Evidence questions** → **Expected artifact**.

---

## How to use

When a board runs, each axis gets: score (0–100 or N/A), validation label ([04-EVIDENCE-STANDARD.md](./04-EVIDENCE-STANDARD.md)), finding IDs ([06-FINDINGS-SCHEMA.md](./06-FINDINGS-SCHEMA.md)), evidence pointers.

Mandatory in every run: Security (30), Testing honesty (32), Release governance (29), AI honesty (12–14 + **43**), Decision Traceability (**40**), Drift (**41**), Engineering Economics (**42**).

---

## Axes 01–39 (v2 baseline)

### Axis 01 — Architecture Governance

- **Purpose:** Verify architectural authority, boundaries, and change control are explicit and followed.
- **Evidence questions:**
  1. Where is the authoritative architecture SoT (bible, ADRs, capability map)?
  2. Are conflicting sources of truth documented (dual compose, multi-engine decision)?
  3. Who owns architecture exceptions, and are they ticketed?
  4. Do parallel agents have non-overlapping ownership ([AGENTS.md](../../../../AGENTS.md))?
  5. Are quarantine / superseded docs clearly marked?
- **Expected artifact:** `AXIS-01` governance matrix + `AG-*`

### Axis 02 — Business Architecture

- **Purpose:** Map business capabilities and value streams to SalesOS modules.
- **Evidence questions:**
  1. What capabilities does SalesOS claim vs implement?
  2. Which value streams have end-to-end code paths?
  3. Where do capability boundaries leak across modules?
  4. Are platform vs product capabilities separated honestly?
- **Expected artifact:** Capability ↔ module map (`BA-*`)

### Axis 03 — Information Architecture

- **Purpose:** Assess IA for entities, navigation, and information scent (FE + API).
- **Evidence questions:**
  1. Coherent object taxonomy (company, contact, deal, evidence, decision)?
  2. Do routes and nav match capability names?
  3. Orphan pages / dead routes inventoried?
  4. Does API naming match domain language?
- **Expected artifact:** IA inventory + orphans (`IA-*`)

### Axis 04 — Capability Architecture

- **Purpose:** Treat capabilities as first-class units with owners, ADRs, and APIs.
- **Evidence questions:**
  1. Capability SoT present (DEC series / register)?
  2. Every shipped capability has owner and entrypoint?
  3. Stub / deferred capabilities labeled (AI, Decision)?
  4. Enable/disable without cross-tenant leakage?
- **Expected artifact:** Capability register (`CAP-*`)

### Axis 05 — Service Architecture

- **Purpose:** Inventory runtime services, boundaries, and coupling.
- **Evidence questions:**
  1. What processes/containers constitute runtime?
  2. Dual-defined services (root vs `salesos/` compose)?
  3. Sync vs async boundaries intentional?
  4. Shared DB sessions / MetaData incorrectly?
- **Expected artifact:** Service topology + dual-stack findings (`SVC-*`)

### Axis 06 — Domain Model

- **Purpose:** Validate canonical domain model against code and schema.
- **Evidence questions:**
  1. Aggregate roots and invariants?
  2. SQLAlchemy / Alembic match intended domain?
  3. Orphan `MetaData()` islands?
  4. Dead / contradictory fields?
- **Expected artifact:** Domain catalog + drift list (`DM-*`)

### Axis 07 — DDD Boundaries

- **Purpose:** Check bounded contexts, ACLs, and forbidden imports.
- **Evidence questions:**
  1. Packages aligned to bounded contexts?
  2. Upward or cross-context imports?
  3. Shared kernels minimal?
  4. Shared tables without ACL?
- **Expected artifact:** Context map + violations (`DDD-*`)

### Axis 08 — ADR Compliance

- **Purpose:** Measure ADR existence, implementation fidelity, conflict, and expiry.
- **Evidence questions:**
  1. Accepted vs Proposed vs Superseded under `docs/adr/`?
  2. Per Accepted ADR: implemented / partial / conflicting / unimplemented?
  3. Phantom or misnamed ADRs / DEC series?
  4. Expired decisions still driving code?
- **Expected artifact:** ADR status matrix (`ADR-*`)

### Axis 09 — SES Compliance

- **Purpose:** Align System / Engineering Spec baseline and changelog with reality.
- **Evidence questions:**
  1. SES baseline and changelog location?
  2. SES claims vs measured architecture?
  3. Required SES updates after major refactors recorded?
  4. Notion↔SES handoff defined or tribal?
- **Expected artifact:** SES drift register (`SES-*`)

### Axis 10 — Product Bible Compliance

- **Purpose:** Cross-check Product Bible maturity claims against audit evidence.
- **Evidence questions:**
  1. Bible maturity higher than ga-engineering-audit?
  2. Platform vs SalesOS-only boundaries consistent?
  3. Roadmap items without code or ADRs?
  4. Audit-wins-on-GO rule respected in comms?
- **Expected artifact:** Bible claim verification (`PB-*`)

### Axis 11 — Runtime Audit

- **Purpose:** Full async/ops path: queues, workers, jobs, cron, cache, retry, idempotency, DLQ, backpressure, recovery.
- **Evidence questions:**
  1. Job/queue systems and consumers?
  2. Retries idempotent? DLQ / poison handling?
  3. Cache invalidation and failure modes?
  4. Cron owners, overlap, failure alerts?
  5. Recovery playbooks?
- **Expected artifact:** Runtime component matrix (`RT-*`)

### Axis 12 — AI Agent Audit

- **Purpose:** Inventory agents, registries, tools, contracts vs honesty rules.
- **Evidence questions:**
  1. Agent runtimes / registries (`.ai/`, in-app)?
  2. Tools/capabilities with clear contracts?
  3. Memory / knowledge flow governed or ad hoc?
  4. Marketed beyond [AI_HONESTY.md](../AI_HONESTY.md)?
  5. `feature_ai_copilot` default False?
- **Expected artifact:** Agent/tool inventory (`AIA-*`)

### Axis 13 — Prompt Audit

- **Purpose:** Govern prompts as production artifacts (versioning, PII, injection, ownership).
- **Evidence questions:**
  1. Where do prompts live?
  2. Versioning and change control?
  3. Tenant/PII leakage in context packing?
  4. Injection / tool-exfiltration mitigations?
- **Expected artifact:** Prompt register (`PRM-*`)

### Axis 14 — Knowledge Audit

- **Purpose:** Assess knowledge stores, RAG/index paths, evidence governance.
- **Evidence questions:**
  1. Knowledge corpora (KG, search, Notion imports)?
  2. Freshness and provenance?
  3. Knowledge influence decisions without human gate?
  4. Quarantine for poisoned knowledge?
- **Expected artifact:** Knowledge flow + findings (`KN-*`)

### Axis 15 — Event Audit

- **Purpose:** Catalog published events, schemas, consumers, orphan publishers.
- **Evidence questions:**
  1. Domain / integration events published?
  2. Every event has ≥1 consumer or quarantine note?
  3. Schema evolution?
  4. Delivery assumptions documented?
- **Expected artifact:** Event catalog (`EVT-*`)

### Axis 16 — Graph Audit

- **Purpose:** Validate graph/KG construction, tenancy, query safety.
- **Evidence questions:**
  1. Graph built from canonical entities how?
  2. Tenant isolation on reads/writes?
  3. SSRF / traversal abuse controls?
  4. Orphan/stale nodes after delete?
- **Expected artifact:** Graph pipeline notes (`GR-*`)

### Axis 17 — Search Audit

- **Purpose:** Index pipeline, ranking honesty, multi-index ADR compliance.
- **Evidence questions:**
  1. Search backends/indices?
  2. Indexing lag and rebuild?
  3. Cross-tenant leak risk?
  4. ADR multi-index reflected in code?
- **Expected artifact:** Search index matrix (`SRCH-*`)

### Axis 18 — Data Lineage Audit

- **Purpose:** Trace Notion → Import → Normalization → Canonical → Entity Resolution → Graph → Search → API → Frontend.
- **Evidence questions:**
  1. Sample entity lineage end-to-end?
  2. Where transforms lose provenance?
  3. `data/` in or out of SalesOS GA path?
  4. Failure / reprocessing strategy?
  5. Entity resolution rules documented/tested?
- **Expected artifact:** Lineage map (`LIN-*`)

### Axis 19 — Canonical Object Audit

- **Purpose:** Define and verify canonical objects vs import/raw mirrors.
- **Evidence questions:**
  1. Canonical schema for core objects?
  2. Raw import tables clearly non-canonical?
  3. Conflict resolution across sources?
  4. Soft-delete / tombstone policy?
- **Expected artifact:** Canonical object dictionary (`CAN-*`)

### Axis 20 — Customer Journey Audit

- **Purpose:** Persona journeys, use cases, flows, feature gaps, edge cases.
- **Evidence questions:**
  1. Primary personas?
  2. Critical happy paths code-backed?
  3. Edge cases / failure UX?
  4. Capability coverage gaps?
  5. Operational workflows?
- **Expected artifact:** Journey × capability matrix (`CJ-*`)

### Axis 21 — Business Rule Audit

- **Purpose:** Extract and verify business rules, decision logic, state machines.
- **Evidence questions:**
  1. Where do rules live?
  2. Entitlement / quota / suspension enforced?
  3. State machines explicit or implicit?
  4. Conflicting decision engines?
  5. Human-in-the-loop for consequential decisions?
- **Expected artifact:** Rule inventory (`BR-*`)

### Axis 22 — Operational Readiness Audit

- **Purpose:** Ops maturity for run, observe, recover, change.
- **Evidence questions:**
  1. Runbooks present and evidence-synced?
  2. On-call, alerts, SLOs?
  3. Staging parity and soak?
  4. Go-live signatures signed or UNSIGNED?
- **Expected artifact:** Ops readiness scorecard (`OPS-*`)

### Axis 23 — Platform Extensibility Audit

- **Purpose:** Extension points, plugins, scalability, future/refactor/upgrade cost (feeds Axis 42).
- **Evidence questions:**
  1. Intentional extension points?
  2. Cost signals for new capability / market / connector?
  3. Plugin/module loading safe for multi-tenant?
  4. Dual compose / orphan MetaData upgrade tax?
- **Expected artifact:** Extensibility heatmap (`EXT-*`)

### Axis 24 — Technical Debt Evolution

- **Purpose:** Debt trajectory: why created, still justified, payoff order.
- **Evidence questions:**
  1. DEBT/DEC tickets for debt items?
  2. Debt accumulating faster than remediation?
  3. Structural roots vs surface fixes?
  4. Payoff cost bands (S/M/L)?
- **Expected artifact:** Debt evolution timeline (`TD-*`)

### Axis 25 — Legacy Detection

- **Purpose:** Find layers that no longer serve the goal; deletable or quarantine-only.
- **Evidence questions:**
  1. Root scrapers / `sales-os/` / duplicate trees referenced?
  2. Dead flags and unused packages?
  3. Historical “why built” vs current intent?
  4. Safe deletion candidates + blast radius?
- **Expected artifact:** Legacy candidate register (`LEG-*`)

### Axis 26 — Duplicate Capability Detection

- **Purpose:** Find two+ implementations of the same capability.
- **Evidence questions:**
  1. Multiple decision / forecast / sync paths?
  2. Duplicate FE packages vs BE APIs?
  3. Dual compose same service differently?
  4. Consolidation recommendation?
- **Expected artifact:** Duplicate matrix (`DUP-*`)

### Axis 27 — Dead Capability Detection

- **Purpose:** Shipped surfaces with no users, tests, owners, or routes.
- **Evidence questions:**
  1. Routes with no nav and no tests?
  2. Services never started in compose?
  3. API modules without callers?
  4. Quarantine vs delete?
- **Expected artifact:** Dead capability list (`DEAD-*`)

### Axis 28 — Architecture Fitness Tests

- **Purpose:** Propose and (when approved) run checkable fitness functions ([05-FITNESS-CATALOG.md](./05-FITNESS-CATALOG.md)).
- **Evidence questions:**
  1. Fitness rules already in CI?
  2. Known waived violations?
  3. Rules runnable without full npm/pytest?
  4. Owner per failing rule?
- **Expected artifact:** Fitness results (`FIT-*`) — **not validated** until run

### Axis 29 — Release Governance

- **Purpose:** Gates, evidence, signatures, forbid-GO-without-evidence.
- **Evidence questions:**
  1. Pre-deploy gates last evidence?
  2. Who can declare GO (CTO/TL)?
  3. Superseded GO docs quarantined?
  4. Wave DoD vs actual evidence labels?
- **Expected artifact:** Release gate checklist (`REL-*`)

### Axis 30 — Security (Auth / CSRF / RBAC / RLS)

- **Purpose:** Deepen security axis — never weaken for demos. **Distinct from Axis 43 AI Governance.**
- **Evidence questions:**
  1. Auth shell: session factory so middleware cannot no-op?
  2. CSRF coverage and known bypasses?
  3. RBAC matrix vs routes?
  4. Tenant GUC; BYPASSRLS owner fallback forbidden when app password empty?
  5. IDOR / SSRF residuals closed with evidence?
- **Expected artifact:** Security control matrix (`SEC-*`)

### Axis 31 — DevOps / DR

- **Purpose:** Compose authority, deploy, backup, WAL/PITR, staging, rollback.
- **Evidence questions:**
  1. Single authoritative compose?
  2. Offsite backup + restore drill evidence?
  3. WAL/PITR for GA?
  4. Staging soak 48–72h?
  5. Rollback tabletop vs production cutover?
- **Expected artifact:** DR/ops evidence pack (`DR-*`)

### Axis 32 — Testing Honesty

- **Purpose:** Separate “suite exists” from “suite green under this board.”
- **Evidence questions:**
  1. What was actually run?
  2. FE build-verify gaps?
  3. Contract tests for public APIs?
  4. Labels applied correctly?
- **Expected artifact:** Test evidence appendix (`TST-*`)

### Axis 33 — Backend Scorecard

- **Purpose:** Scored BE health (enforcement, sessions, domains, migrations).
- **Evidence questions:**
  1. Alembic head vs orphan MetaData count?
  2. Middleware fail-open paths?
  3. Domain module health?
  4. Score delta vs prior boards **with evidence only**?
- **Expected artifact:** BE scorecard (`BE-*`)

### Axis 34 — Frontend Scorecard

- **Purpose:** Scored FE health (SSR, tokens, verify path, stubs).
- **Evidence questions:**
  1. Build verify vs succeed-only?
  2. Blank SSR / provider timing?
  3. Undefined design tokens?
  4. Decision package stub honesty in UI?
- **Expected artifact:** FE scorecard (`FE-*`)

### Axis 35 — CTO Readiness

- **Purpose:** Package evidence for CTO decision quality (not marketing).
- **Evidence questions:**
  1. P0s closed with executable evidence?
  2. Residual risks with owners?
  3. Unsigned go-live blocks clear?
  4. One-page “why NO-GO / what changes mind”?
- **Expected artifact:** CTO readiness brief (`CTO-*`)

### Axis 36 — CEO Executive Summary

- **Purpose:** Non-technical executive brief: risk, timeline, ask.
- **Evidence questions:**
  1. One-sentence product truth?
  2. Business risk of shipping now?
  3. Investment ask for 30/60/90?
  4. Explicit: no Production GO without evidence?
- **Expected artifact:** 1-page CEO summary (`CEO-*`)

### Axis 37 — 30 / 60 / 90 Day Recovery Plan

- **Purpose:** Time-boxed remediation from findings (not wishful GA).
- **Evidence questions:**
  1. 30-day unblock for internal pilot conditions?
  2. 60-day structural debt?
  3. 90-day staging/DR/evidence bar?
  4. Dependencies and freeze rules?
- **Expected artifact:** 30/60/90 plan (`RCV-*`)

### Axis 38 — 12-Month Architecture Roadmap

- **Purpose:** Longer arc: fitness CI, capability SoT, lineage, AI honesty path.
- **Evidence questions:**
  1. Quarters for fitness CI, single compose, canonical lineage?
  2. When (if ever) AI copilot may default True — evidence bar?
  3. Multi-product Core — defer or plan?
  4. Evidence-based success metrics per quarter?
- **Expected artifact:** 12-month roadmap (`RM12-*`)

### Axis 39 — Production Readiness / GO-NO-GO Synthesis

- **Purpose:** Weighted synthesis across **all** axes (including 40–43) into honest classification.
- **Evidence questions:**
  1. Any P0 GA axes still `not validated`?
  2. Evidence supports only **production no-go**, **pilot-ready with conditions**, or (rare) GO?
  3. Comparison to prior boards with deltas?
  4. Explicit forbid: GO without executable evidence?
- **Expected artifact:** Final verdict table (`GO-*`) — **do not pre-fill in framework docs**

---

## Axes 40–43 — v2.1 additions | إضافات v2.1

> **Mandatory.** Introduced to close governance gaps: decision lineage, measured drift, CTO cost of change, and AI governance as a dimension separate from Security.

### Axis 40 — Decision Traceability Matrix **(v2.1)**

- **Purpose:** Ensure every material decision is traceable end-to-end:  
  **Vision → Product Bible → Capability → ADR → Implementation → API → UI → Tests → Runtime → Monitoring**
- **Evidence questions:**
  1. For a sample of Accepted ADRs / DECs: can each hop in the chain be named with an artifact path?
  2. Where does the chain break (orphan ADR, capability without ADR, API without UI, UI without tests, runtime without monitors)?
  3. Are “code became truth” changes lacking ADR/bible updates flagged?
  4. Can auditors answer: *can every decision be traced to execution?* with a filled matrix (not narrative only)?
  5. Are stub / deferred decisions (AI, Decision STUB) explicitly marked at Capability and UI hops?
- **Expected artifact:** Decision Traceability Matrix table (`DTM-*`) — template in [08-REPORTING-STANDARD.md](./08-REPORTING-STANDARD.md)

### Axis 41 — Architectural Drift Detection **(v2.1)**

- **Purpose:** **Measure** gradual drift (ADR vs code over time; “code becomes truth”) — discovery alone is insufficient.
- **Evidence questions:**
  1. What is the ADR–implementation mismatch count (Accepted ADR ≠ code behavior)?
  2. Orphan ADRs (no impl) and orphan capabilities (no ADR/DEC)?
  3. Dual engines / dual compose / dual MetaData trends vs prior board?
  4. Is there a repeatable metric or fitness function ([05-FITNESS-CATALOG.md](./05-FITNESS-CATALOG.md)) that can be re-run next board?
  5. Drift score computed per [07-SCORING-MODEL.md](./07-SCORING-MODEL.md) (even if N/A this run — state why)?
- **Expected artifact:** Drift metrics dashboard + trend notes (`DRIFT-*`)

### Axis 42 — Engineering Economics **(v2.1)**

- **Purpose:** Make CTO **cost of change** explicit using qualitative + ordinal bands (Low / Med / High / Extreme) — not fake precision currency.
- **Evidence questions:** Cost band + evidence for each:
  1. Cost to add a **Capability**
  2. Cost to add a new **country/locale (دولة)**
  3. Cost to add a **Tenant**
  4. Cost of a **framework upgrade**
  5. Cost of a **DB change** (Alembic migration + rollout)
  6. Cost of **deleting a Module**
  7. What structural factors drive High/Extreme (dual compose, orphan MetaData, missing extension points)?
- **Expected artifact:** Economics cost-band table (`ECON-*`)

### Axis 43 — AI Governance Score **(v2.1)**

- **Purpose:** Score **AI governance as its own dimension**, separate from Security (Axis 30). Align with [AI_HONESTY.md](../AI_HONESTY.md), `feature_ai_copilot=False`, and FE Decision **STUB** rules.
- **Evidence questions** (sub-scores 0–100 or N/A each, then roll up):
  1. **AI Safety** — harm, injection, tool exfiltration controls?
  2. **Explainability** — can outputs be explained to a human decision-maker?
  3. **Auditability** — prompts/tools/decisions logged with tenant context?
  4. **Prompt Governance** — versioning, ownership (ties Axis 13)?
  5. **Tool Governance** — registered contracts, least privilege?
  6. **Memory Governance** — what is stored, retained, isolated?
  7. **Human Override** — humans can block/override consequential AI paths?
  8. **Decision Transparency** — stub vs live Decision paths honest in UI/API?
  9. **Model Independence** — swap/provider abstraction vs hard-wire?
  10. **Vendor Lock-in** — exit cost / single-vendor dependency?
  11. Defaults: copilot flag False; no marketing of stubs as GA AI?
- **Expected artifact:** AI Governance scorecard (`AIGOV-*`) — dimension rollup rules in [07-SCORING-MODEL.md](./07-SCORING-MODEL.md)

---

## Axis index (quick)

| # | Axis | Prefix | v2.1? |
|---|------|--------|-------|
| 01 | Architecture Governance | AG | |
| 02 | Business Architecture | BA | |
| 03 | Information Architecture | IA | |
| 04 | Capability Architecture | CAP | |
| 05 | Service Architecture | SVC | |
| 06 | Domain Model | DM | |
| 07 | DDD Boundaries | DDD | |
| 08 | ADR Compliance | ADR | |
| 09 | SES Compliance | SES | |
| 10 | Product Bible Compliance | PB | |
| 11 | Runtime Audit | RT | |
| 12 | AI Agent Audit | AIA | |
| 13 | Prompt Audit | PRM | |
| 14 | Knowledge Audit | KN | |
| 15 | Event Audit | EVT | |
| 16 | Graph Audit | GR | |
| 17 | Search Audit | SRCH | |
| 18 | Data Lineage Audit | LIN | |
| 19 | Canonical Object Audit | CAN | |
| 20 | Customer Journey Audit | CJ | |
| 21 | Business Rule Audit | BR | |
| 22 | Operational Readiness | OPS | |
| 23 | Platform Extensibility | EXT | |
| 24 | Technical Debt Evolution | TD | |
| 25 | Legacy Detection | LEG | |
| 26 | Duplicate Capability | DUP | |
| 27 | Dead Capability | DEAD | |
| 28 | Architecture Fitness Tests | FIT | |
| 29 | Release Governance | REL | |
| 30 | Security | SEC | |
| 31 | DevOps / DR | DR | |
| 32 | Testing Honesty | TST | |
| 33 | Backend Scorecard | BE | |
| 34 | Frontend Scorecard | FE | |
| 35 | CTO Readiness | CTO | |
| 36 | CEO Executive Summary | CEO | |
| 37 | 30/60/90 Recovery | RCV | |
| 38 | 12-Month Roadmap | RM12 | |
| 39 | Production Readiness Synthesis | GO | |
| **40** | **Decision Traceability Matrix** | **DTM** | **Yes** |
| **41** | **Architectural Drift Detection** | **DRIFT** | **Yes** |
| **42** | **Engineering Economics** | **ECON** | **Yes** |
| **43** | **AI Governance Score** | **AIGOV** | **Yes** |

Future boards may add axes but must not drop Security, Testing honesty, Release governance, AI honesty/governance, Decision Traceability, Drift, or Engineering Economics.

---

*Methodology — Enterprise Audit Board v2.1 — 43 axes — not executed*
