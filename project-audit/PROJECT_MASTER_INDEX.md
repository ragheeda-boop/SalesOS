# PROJECT MASTER INDEX

**Audit date:** 2026-09-12  
**Audit type:** Read-only, evidence-first, board-ready  
**Workspace:** `D:\AISalesOS` (AQLIYA / SalesOS)  
**Branch:** `fix/login-and-keys` @ commit `3bfa6adb`  
**Honesty label:** *pilot-ready with conditions — production no-go for AI Copilot without provider*

---

## 1. How to read this audit

**Read in this order** if you have limited time:

1. [`00_EXECUTIVE_SUMMARY.md`](00_EXECUTIVE_SUMMARY.md) — **10-minute board-ready one-pager (AR + EN)**
2. [`20_FINAL_VERDICT.md`](20_FINAL_VERDICT.md) — **12-bullet final verdict, MVP/sellable/production-ready honest table**
3. [`17_NEXT_ACTIONS.md`](17_NEXT_ACTIONS.md) — **0–90 day priority actions**
4. [`19_RISK_REGISTER.md`](19_RISK_REGISTER.md) — **30-item risk log, top-5 focus**

**For deep dives:**
- Product & strategy → sections 02–10
- Engineering & architecture → sections 11–15
- Reality check & inventory → sections 16, AUDIT_INVENTORY, AUDIT_LIMITATIONS

---

## 2. Meta / audit-integrity files

| File | Purpose |
|------|---------|
| [`AUDIT_INVENTORY.md`](AUDIT_INVENTORY.md) | Everything read/inspected: workspace tree, backend routers (~85), 109 Alembic migrations, config.py evidence, frontend (40+78 pages), doc inventory, deployment evidence, git state, feature flags, tests, data intelligence |
| [`AUDIT_LIMITATIONS.md`](AUDIT_LIMITATIONS.md) | What was NOT verified: live Railway/Vercel/MCPs, live DB, code paths not fully inspected, runtime verifications not performed, external providers, historical claims accepted |
| [`PROJECT_MASTER_INDEX.md`](PROJECT_MASTER_INDEX.md) | (this file) |

---

## 3. Numbered deliverables (00 → 20)

### Executive / Product

| # | File | One-liner |
|---|------|-----------|
| 00 | [`00_EXECUTIVE_SUMMARY.md`](00_EXECUTIVE_SUMMARY.md) | Bilingual board-ready summary + 15-dim scorecard + verdict (48/100 composite) |
| 01 | [`01_CURRENT_STATE.md`](01_CURRENT_STATE.md) | Bilingual current state: Phase 1-4 + Productization + Phase 6 + Phase 7-A status; 7 contradictions to resolve |
| 02 | [`02_PRODUCT_BRIEF.md`](02_PRODUCT_BRIEF.md) | Bilingual product brief: pitch, problem, 3-lens view, moats, weakest links, positioning |
| 03 | [`03_PRODUCT_STRATEGY.md`](03_PRODUCT_STRATEGY.md) | 3-layer strategy (Consolidate/Prove/Scale) + PMF falsification + optimization priorities |
| 04 | [`04_BUSINESS_MODEL.md`](04_BUSINESS_MODEL.md) | 4-tier pricing + revenue math + cost model + unit economics + billing rails |
| 05 | [`05_CUSTOMER_SEGMENTATION.md`](05_CUSTOMER_SEGMENTATION.md) | 5 ICPs (Design Partner, SMB, VC Analyst, Enterprise, International-parked) + scoring + personas |
| 06 | [`06_MVP_SCOPE.md`](06_MVP_SCOPE.md) | MVP definition (bilingual) + 12 in-scope + 15 out-of-scope + 12-cond DoD + 2-week sprint |

### GTM / Sales

| # | File | One-liner |
|---|------|-----------|
| 07 | [`07_GTM_STRATEGY.md`](07_GTM_STRATEGY.md) | Founder-led design-partner motion + timeline phases + persona value props |
| 08 | [`08_SALES_PLAYBOOK.md`](08_SALES_PLAYBOOK.md) | Discovery Qs + 25-min demo script + 7 objection handlers + MOU + Order Form templates |
| 09 | [`09_PRODUCT_ROADMAP.md`](09_PRODUCT_ROADMAP.md) | Q4 2026 – Q4 2027 quarterly roadmap + feature backlog + release cadence + failure conditions |
| 10 | [`10_KPI_FRAMEWORK.md`](10_KPI_FRAMEWORK.md) | North Star (PWAT-HITL) + Product/Engineering/Business/Security/Data KPIs + anti-metrics + dashboards |

### Engineering / Reality

| # | File | One-liner |
|---|------|-----------|
| 11 | [`11_CAPABILITY_MATRIX.md`](11_CAPABILITY_MATRIX.md) | ~110-row Product Capability Matrix (13 columns) covering Product Core + Intelligence + AI + Master Data + Platform + Auth + Integrations + Runtime + Tenant Studio + GTM + Chaos + Frontend |
| 12 | [`12_GAP_ANALYSIS.md`](12_GAP_ANALYSIS.md) | 20 top gaps promise-vs-reality + README domain-table reality check + positive strengths + 15-item priority-ordered closure list |
| 13 | [`13_TECHNICAL_ARCHITECTURE.md`](13_TECHNICAL_ARCHITECTURE.md) | Bird's-eye + backend DDD + data model + AI architecture (grounded EvidencePack) + frontend + deployment + security + testing + ADRs + risks |
| 14 | [`14_DEPLOYMENT_HOSTING_AUDIT.md`](14_DEPLOYMENT_HOSTING_AUDIT.md) | Railway + Vercel + DB + Neo4j + CI/CD + environments + backup/DR + secrets + networking + compliance + cost model + 13 recommended actions |
| 15 | [`15_REPOSITORY_FILE_AUDIT.md`](15_REPOSITORY_FILE_AUDIT.md) | Top-level classification + salesos sub-inventory + docs inventory + duplicates + stale/diagnostic + git state (CRITICAL 4,748 deletions) + hygiene sprint |

### Verdict / Action

| # | File | One-liner |
|---|------|-----------|
| 16 | [`16_WHAT_HAS_BEEN_BUILT.md`](16_WHAT_HAS_BEEN_BUILT.md) | Honest inventory: Product Core + Intelligence + AI + Master Data/ER + Platform + Frontend + NOT-built list + what's live in prod today |
| 17 | [`17_NEXT_ACTIONS.md`](17_NEXT_ACTIONS.md) | 0-90 day priority action list: Sprint 0 (repo hygiene) → Sprint 1 (Design Partner) → Sprint 2 (Master Data) → Sprint 3 (pricing) → Sprint 4+ (growth) + non-negotiable evidence gates |
| 18 | [`18_PROJECT_STRATEGY.md`](18_PROJECT_STRATEGY.md) | How to run the project: principles, weekly cadence, decision framework, team org, financial discipline, communication, when to say NO |
| 19 | [`19_RISK_REGISTER.md`](19_RISK_REGISTER.md) | 30-item risk log with I×L scoring, top-5 focus, governance for updating |
| 20 | [`20_FINAL_VERDICT.md`](20_FINAL_VERDICT.md) | **One-line verdict + MVP/sellable/production-ready honest table + 12-bullet Board verdict + scorecard + 3 questions + stop/start/continue + final adjudication** |

---

## 4. What is LIVE / STALE / SUPERSEDED (workspace outside `project-audit/`)

### LIVE authority (workspace)

- `AGENTS.md` (root, 78 KB) — 39 session summaries + agent essentials
- `PRODUCT_BIBLE.md` (root) — product narrative
- `docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md` — GA verdict authority
- `docs/audit/ga-engineering-audit/SALESOS_MASTER_CLOSURE_SEQUENCE.md` — closure order (locked 2026-08-17)
- `docs/audit/ga-engineering-audit/AI_HONESTY.md` — AI marketing / feature-flag mandate
- `docs/audit/ga-engineering-audit/FINAL_GO_NOGO_ASSESSMENT.md` — 2026-09-05 assessment
- `docs/data/phase6/` — Phase 6 evidence
- `docs/data/phase7/` — Phase 7-A PO decision
- `docs/adr/` — 40+ ADRs including 0101, 0102, 0103-0108, 0109
- `.github/workflows/` — 9 CI workflows
- `.cursor/rules/` — active agent rules

### STALE (needs updating or STALE banner)

- `docs/audit/current-state/*` (2026-07-15) — feature counts outdated
- `docs/audit/current-state/09-screen-inventory.md` — 30 screens vs 54 today
- `docs/audit/ga-engineering-audit/PAGE_MAP_SALESOS.md` — needs v3-first refresh
- `README.md` Domains table — needs reality alignment

### SUPERSEDED (retain per policy, add banner)

- `docs/vnext/GO_NO_GO_DECISION.md`
- `docs/vnext/GA_CHECKLIST.md`
- `docs/vnext/MASTER_PLAN.md` (for closure order)

### ARCHIVED (retire visibly)

- `.engineering/` (30+ EOS/engineering catalog files)
- `docs/v2/` (v2-planning era)
- `archive/*`

---

## 5. Critical items requiring IMMEDIATE action

| # | Item | Severity | Owner | Reference |
|---|------|----------|-------|-----------|
| 1 | Repair git working tree — 4,748 deletions staged on `fix/login-and-keys` | 🔴 CRITICAL | Founder + TL | REPO_AUDIT §6 |
| 2 | Reconcile `feature_ai_copilot=True` (code) vs `False` (AI_HONESTY.md) | 🔴 CRITICAL | Founder + PO | GAP §F-04 |
| 3 | Sign production LLM provider contract (OpenAI / Azure / Anthropic) | 🔴 CRITICAL | Founder | NEXT_ACTIONS §Sprint1-P0-8 |
| 4 | Enable Railway managed backup schedule | 🔴 CRITICAL | Platform Owner | NEXT_ACTIONS §Sprint0-P0-4 |
| 5 | Set up Google OAuth staging + production apps | 🔴 CRITICAL | DevOps | NEXT_ACTIONS §Sprint1-P0-9 |
| 6 | Fix `preDeployCommand` drift between `railway.json` and live | 🟡 HIGH | DevOps | NEXT_ACTIONS §Sprint0-P0-3 |
| 7 | Rewrite `README.md` Domains table + add STALE banners | 🟡 HIGH | TL | NEXT_ACTIONS §Sprint0-P0-5 & 6 |
| 8 | Sign first Design Partner MOU | 🟡 HIGH | Founder | NEXT_ACTIONS §Sprint1-P0-7 |

---

## 6. Reading path by audience

### Board / Investor (30 minutes)

1. [`00_EXECUTIVE_SUMMARY.md`](00_EXECUTIVE_SUMMARY.md)
2. [`20_FINAL_VERDICT.md`](20_FINAL_VERDICT.md)
3. [`19_RISK_REGISTER.md`](19_RISK_REGISTER.md)
4. Ask 3 questions from §5 of `20_FINAL_VERDICT.md`

### Founder / CEO (2 hours)

1. All above +
2. [`03_PRODUCT_STRATEGY.md`](03_PRODUCT_STRATEGY.md)
3. [`04_BUSINESS_MODEL.md`](04_BUSINESS_MODEL.md)
4. [`17_NEXT_ACTIONS.md`](17_NEXT_ACTIONS.md)
5. [`18_PROJECT_STRATEGY.md`](18_PROJECT_STRATEGY.md)

### CTO / TL (3 hours)

1. All above +
2. [`13_TECHNICAL_ARCHITECTURE.md`](13_TECHNICAL_ARCHITECTURE.md)
3. [`14_DEPLOYMENT_HOSTING_AUDIT.md`](14_DEPLOYMENT_HOSTING_AUDIT.md)
4. [`15_REPOSITORY_FILE_AUDIT.md`](15_REPOSITORY_FILE_AUDIT.md)
5. [`11_CAPABILITY_MATRIX.md`](11_CAPABILITY_MATRIX.md)
6. [`12_GAP_ANALYSIS.md`](12_GAP_ANALYSIS.md)

### Product Owner / PM (2 hours)

1. Executive + Verdict +
2. [`02_PRODUCT_BRIEF.md`](02_PRODUCT_BRIEF.md)
3. [`06_MVP_SCOPE.md`](06_MVP_SCOPE.md)
4. [`09_PRODUCT_ROADMAP.md`](09_PRODUCT_ROADMAP.md)
5. [`10_KPI_FRAMEWORK.md`](10_KPI_FRAMEWORK.md)
6. [`11_CAPABILITY_MATRIX.md`](11_CAPABILITY_MATRIX.md)
7. [`16_WHAT_HAS_BEEN_BUILT.md`](16_WHAT_HAS_BEEN_BUILT.md)

### Sales Lead (2 hours)

1. Executive + Verdict +
2. [`02_PRODUCT_BRIEF.md`](02_PRODUCT_BRIEF.md)
3. [`05_CUSTOMER_SEGMENTATION.md`](05_CUSTOMER_SEGMENTATION.md)
4. [`07_GTM_STRATEGY.md`](07_GTM_STRATEGY.md)
5. [`08_SALES_PLAYBOOK.md`](08_SALES_PLAYBOOK.md)
6. [`16_WHAT_HAS_BEEN_BUILT.md`](16_WHAT_HAS_BEEN_BUILT.md) — for honest scope

### Compliance / Security auditor (1 hour)

1. [`14_DEPLOYMENT_HOSTING_AUDIT.md`](14_DEPLOYMENT_HOSTING_AUDIT.md)
2. [`19_RISK_REGISTER.md`](19_RISK_REGISTER.md)
3. [`AUDIT_LIMITATIONS.md`](AUDIT_LIMITATIONS.md)

---

## 7. Evidence + label convention (used across audit)

- **FACT** — verified from source file at commit `3bfa6adb`
- **INFERENCE** — reasoned from multiple facts, may need verification
- **RECOMMENDATION** — audit author's suggestion, not fact
- **UNKNOWN** — not verified this audit; see `AUDIT_LIMITATIONS.md`

**Honesty labels for build state:**
- `not validated`
- `light validated`
- `build validated`
- `pilot-ready with conditions`
- `production no-go`

---

## 8. Sources of truth chain (reconfirmed)

1. **Executable evidence** (test output, DB query, `/health` response)
2. **STAR audit** (`docs/audit/star-audit/`) — historical
3. **ga-engineering-audit** (`docs/audit/ga-engineering-audit/`) — LIVE authority
4. **SALESOS_MASTER_CLOSURE_SEQUENCE.md** — locked 2026-08-17
5. **AI_HONESTY.md** — feature-flag + AI marketing mandate
6. **AGENTS.md** — session ledger + agent essentials
7. **PRODUCT_BIBLE.md** — product narrative
8. **docs/PROJECT_BIBLE.md** — SalesOS engineering bible (note: dual-bible hazard EAB-001-P1-DOC-01)

**Precedence rule:** executable evidence > STAR audit > ga-engineering-audit > SALESOS_MASTER_CLOSURE_SEQUENCE > AGENTS.md > PROJECT_BIBLE.md. Where conflicts exist, this audit sides with the higher-authority source.

---

## 9. Not to be modified

Everything **outside** `project-audit/` was NOT modified by this audit. This is a read-only exercise. All actionable changes are captured in [`17_NEXT_ACTIONS.md`](17_NEXT_ACTIONS.md) for owner-driven execution.

---

*Master index — single source of truth for this audit. Distribute this file with the report bundle.*
