# 12 — Gap Analysis — تحليل الفجوات

**Method:** every "promised" claim from README / PRODUCT_BIBLE / marketing-adjacent docs, cross-checked against code + tests + config + gate packs. Gaps ranked by impact.

**Labels:** FACT / INFERENCE / RECOMMENDATION / UNKNOWN.

---

## 1. Promise vs Reality — top 20 gaps

| # | Claim | Where claimed | Reality | Gap type | Severity |
|---|-------|---------------|---------|---------|----------|
| G-01 | "Production GA" ready | Historical `docs/vnext/GO_NO_GO_DECISION.md` (superseded) | `FINAL_GO_NOGO_ASSESSMENT.md` 2026-09-05 says **NOT DECLARED**; audit `00-EXECUTIVE-SUMMARY.md` **NO-GO** | Marketing overclaim, resolved | LOW (already reconciled internally) |
| G-02 | "AI-native OS" / "Copilot production-ready" | Historical language | `AI_HONESTY.md` §1: NO; `feature_ai_copilot` = True in config but mandate says False. Provider DEV-ONLY (AI Horde) | Marketing overclaim, live | **HIGH** |
| G-03 | `README.md` "Domains: AI Copilot / Decision Center / Knowledge Graph / Communication Hub 🟢 Live" | `README.md` §Domains | KG OFFLINE per ADR-108; Copilot provider DEV-ONLY; Decision Center FE package STUB; Comm Hub OAuth staging pending | Marketing overclaim | **HIGH** |
| G-04 | "MUHIDE production data live" | Session summaries reference 296,746 ingestion | Only in `salesos_test` DB. Production `salesos` has different 141,221-row population. Phase 7 BLOCKED | Data promise unrealized | **HIGH — product-critical** |
| G-05 | "Multi-product platform (AuditOS / DecisionOS / LocalContentOS)" | Vision docs | Zero code | Vision-vs-reality gap | HIGH if said in sales |
| G-06 | Alembic head clean chain | Various | 109 files on disk; docs cite 96 / 97; prod at `g1h2i3j4k5l6` (Aug 21) — 6+ heads behind repo latest `p7q8r9s0t1u2` | Drift + doc inconsistency | MEDIUM |
| G-07 | "Backup / Restore complete" (Phase 4 item 8) | `SALESOS_MASTER_CLOSURE_SEQUENCE.md` | Scripts + Dockerfile done; **Railway managed backup schedule NOT enabled** (row 3b BLOCKED-HUMAN) | Live DR gap | **HIGH** |
| G-08 | "Deployment + rollback exercised" | Phase 4 evidence | Staging deploy 2026-08-21 proven; production `preDeployCommand` drift (uses `init_db()` not `alembic upgrade head`) | Config drift | MEDIUM |
| G-09 | "SSO Google OAuth live" | README §Domains | Only prod / dev; **staging OAuth blocked pending Google Cloud Console** | Environment gap | MEDIUM |
| G-10 | "Knowledge Graph 🟢 Live" | README, feature matrices | `ADR-108`: Neo4j OFFLINE for v1.0; deployed on Railway but no production traffic (NEO4J_GOVERNANCE_GAP.md) | Governance drift | MEDIUM |
| G-11 | "Universal Search" | PRODUCT_BIBLE.md P0 | Runtime search + experimental search both live but no live evidence of user-visible universal top-bar search across v3 shell | UX promise partial | MEDIUM |
| G-12 | "AI Summary in every list" | PRODUCT_BIBLE.md Principle 1 | Not systematically shipped; Copilot is opt-in per action | UX principle vs shipped | MEDIUM |
| G-13 | "3-click max to any info" | PRODUCT_BIBLE.md Rule 2 | Not measured; 24-item nav suggests > 3 clicks for some data-steward flows | UX principle vs shipped | LOW |
| G-14 | "AR + EN bilingual first day" | PRODUCT_BIBLE.md Principle 6 | Code supports i18n (`en.json` etc); depth of AR translation of every page NOT re-verified this audit | UX partial (proven in nav labels + product bible) | LOW |
| G-15 | "Dark Mode from day 1" | PRODUCT_BIBLE.md Rule 8 | Tailwind config supports; per-page verification not done this audit | UX unknown | LOW |
| G-16 | "Autonomous Sales Agent (12-month)" | PRODUCT_BIBLE.md Horizon | Zero code; VIOLATES HITL invariant of Phase 3 | Vision claim | HIGH if said in sales |
| G-17 | "SOC2 / ISO27001 / PDPL certified" | Not claimed explicitly, but implied by "enterprise ready" language | Not certified; scaffolding exists (STORY-14-05) | Compliance gap | HIGH for Enterprise sale |
| G-18 | "SLA 99.9% uptime" | Not explicit; would be assumed by buyers | No published SLA doc | Missing | MEDIUM |
| G-19 | "Data residency in KSA" | ADR-0107 exists | Currently hosted on Railway (US) + Vercel (iad1 US). No KSA-hosted evidence | Regulatory gap for KSA Enterprise | **HIGH** |
| G-20 | "Zero mock data (as of 2026-09-05 productization gate)" | AGENTS.md §39 | `getDemoData()` cleaned in graph + knowledge; other pages **UNKNOWN this audit** — would need file-by-file scan | Cleanup partial | MEDIUM |

---

## 2. Feature-vs-README domain-table reality check

**README.md §Domains table:**

| Claim in README | Truth (evidence) |
|-----------------|------------------|
| Identity 🟢 Live | TRUE (auth RS256, JWT, RBAC, OAuth code present) |
| Company 🟢 Live | TRUE (Phase 1 CLOSED + browser QA) |
| Search 🟢 Live | PARTIAL (runtime primary; experimental duplicate; PAGE_MAP notes 404s on search analytics) |
| CRM 🟢 Live | TRUE (Phase 1 CLOSED) |
| **AI 🟢 Live** | **PARTIAL / overclaim** — code Live, provider DEV-ONLY, HONESTY mandate says False |
| Entity Resolution 🟢 Live | TRUE for logic in `salesos_test`; production ingestion blocked |
| Communication Hub 🟢 Live | PARTIAL — code Live, OAuth staging blocked |
| Activity Intelligence 🟢 Live | TRUE |
| **Knowledge Graph 🟢 Live** | **FALSE** — ADR-108 OFFLINE for v1.0 |
| Decision Center 🟢 Live | PARTIAL — HTTP API Live, FE package STUB |
| Feature Store 🟢 Live | TRUE (`runtime/feature_store`) |
| Workflow 🟢 Live | TRUE (`workflow_engine` + `automation_router`) |
| Webhooks 🟢 Live | TRUE (SSRF-hardened) |

**Action:** rewrite README §Domains to match reality. See `17_NEXT_ACTIONS.md`.

---

## 3. Gaps by category

### 3.1 Product gaps
- No live production Muhide data
- No live paying tenant
- No case study
- No public status page
- No support channel with SLA
- No published pricing
- Dual FE shell (`/v3` + `/(dashboard)`) creates IA + QA drift

### 3.2 Engineering gaps
- 4,748-file git working-tree deletion state on `fix/login-and-keys`
- Migration count reconciliation across docs (109 disk vs 96/97 docs)
- Sentry DSN empty (no live error stream)
- Neo4j deployed but offline (governance)
- Dual search routers (runtime primary + experimental)
- Legacy shell 78 pages retained
- 12 mypy_cache_* dirs + `.venv/` in repo path

### 3.3 Business gaps
- No pricing signed
- No MSA / DPA / Order Form / ToS / SLA templates
- No Stripe live keys provisioned
- No unit economics document
- No CAC / LTV baselines
- No board pack template

### 3.4 Data gaps
- 54,185 Phase 6 review candidates unaddressed
- 36 SUSPICIOUS_SHORT CRs unadjudicated
- 2,661 fuzzy pairs unresolved (never auto-merge, but never manually reviewed either)
- DI P1/P2 methodology unreconciled (18,657/17,222 best-effort vs 23,306/37,719 official)
- Muhide not ingested to production
- ICP profiles empty for real tenants
- RAG corpus 5 rows

### 3.5 Compliance gaps
- No PDPL alignment doc signed
- No SOC2 attestation
- No external pentest
- No published data-residency posture
- No DPO named
- No SAMA statement (if selling to banks)

### 3.6 Governance gaps
- AI honesty vs config flag contradiction
- README domain table vs reality
- Multiple superseded docs live (GO_NO_GO / GA_CHECKLIST) despite formal supersession
- STAR audit conditional-GO vs Executive Summary NO-GO reconciliation not fully surfaced to marketing
- Neo4j deployed vs ADR-108 offline

---

## 4. Positive gaps (surprise strengths)

- Grounded EvidencePack loader is **rare in commercial AI products** and is a differentiator
- Government-ID hard-veto merge policy is **enterprise-grade Saudi hygiene**
- Dual DB roles (owner vs `salesos_app`) with fail-closed empty-password refusal in prod is **best-practice tenant isolation**
- STORY-14-06 / STORY-14-07 chaos harnesses (fake providers, LLM regression golden fixtures) — **rare for pre-revenue startup**
- 110+ ADRs formalized — **best-in-class governance culture**
- Bilingual (AR/EN) code depth in Arabic normalization / CR safety / RTL handling — **genuine local moat**

---

## 5. What must close before "sellable-as-SaaS today"

Priority-ordered — this is the definitive gap-closure list:

1. **P0** — Reconcile `feature_ai_copilot` + `AI_HONESTY.md` + README (0.5 day)
2. **P0** — Enable Railway backup schedule (< 1 day, needs Railway Owner)
3. **P0** — Sign production LLM contract (2–4 weeks)
4. **P0** — OAuth staging + production Google Cloud Console (< 1 day, needs GCP admin)
5. **P0** — Draft + legal-review MSA + DPA + Order Form + ToS + SLA-lite (2–3 weeks with counsel)
6. **P0** — Stripe live keys + pricing page live (< 1 day after tiers signed)
7. **P0** — Public status page + support email + response SLA-lite (1 day)
8. **P0** — Repair `fix/login-and-keys` git working tree (0.5 day)
9. **P1** — Repo hygiene (nested duplicates, .venv, .mypy_cache_*) (2 days)
10. **P1** — Deprecate legacy `(dashboard)` shell visibly (1 day)
11. **P1** — Phase 7-B execution for one tenant subset + production ingestion (weeks; needs paid reviewer FTE)
12. **P1** — Fix Alembic drift on production; align `preDeployCommand` (1 day)
13. **P2** — Sentry DSN + live error stream (< 1 day)
14. **P2** — Rewrite `PAGE_MAP_SALESOS.md` for v3-first world (1 day)
15. **P2** — PDPL alignment statement + DPO named (2 weeks with legal)

**Sum:** ~4–6 weeks of focused non-code work + ~4 weeks legal + ~2–4 weeks LLM vendor RFP + Phase 7 workstream in parallel. This is the realistic timeline to "MVP sellable-as-SaaS".

---

## 6. What can NEVER close (permanent commitments)

Some claims should be permanently retired, not "closed":
- "Autonomous Sales Agent" as pre-2027 language
- "Multi-product platform" as pre-2028 marketing
- "AI-native GA" without provider + PRC evidence
- "Bloomberg Terminal for Saudi Arabia" is defensible; "Bloomberg replacement" is not (different market)

---

*Gap analysis — evidence-cited. See `17_NEXT_ACTIONS.md` for time-boxed close plans and `19_RISK_REGISTER.md` for risk classification.*
