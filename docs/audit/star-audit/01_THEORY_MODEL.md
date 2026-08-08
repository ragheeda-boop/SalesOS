# 01 — THEORY MODEL: What SalesOS Is Supposed to Become

> Source: Documentation-only analysis (Phase 1)
> Classification: THEORY MODEL

---

## Executive Summary

SalesOS is documented as a **Business Intelligence Operating System (BIOS)** — not a CRM — targeting the Saudi Arabian market and expanding to GCC → MENA → Global. It is the first product of the multi-product platform (alongside AuditOS, DecisionOS, LocalContentOS).

The vision is extraordinary: an AI-native intelligence platform with Digital Twins, Agent Runtimes, Knowledge Graphs, Marketplace extensibility, and a $50M ARR target by 2030.

---

## 1. Vision Statement

**From PROJECT_BIBLE.md:** "Unify fragmented business data into AI-native revenue intelligence that every team member can act on — without engineering support."

**From MASTER_BLUEPRINT.md:** "Bloomberg Terminal for Saudi companies, with AI intelligence at CRM pricing."

---

## 2. Product Identity

| Dimension | Documented Vision |
|-----------|-------------------|
| Category | Business Intelligence Operating System (not CRM) |
| Market | Saudi-first (KSA PDPL compliance), Arabic-first NLP |
| Parent Platform | multi-product |
| Target ARR | $50M+ by 2030 |
| Target Customers | 1000+ by 2030 |
| Regions | 4 (KSA → GCC → MENA → Global) |

---

## 3. Target Users (4 Personas)

| Persona | Role | Primary Pain Point |
|---------|------|-------------------|
| Sales Rep (AE) | Daily outreach, pipeline management | Doesn't know which opportunity to pursue first |
| Sales Manager | Pipeline reviews, coaching | Can't see deal health at a glance |
| Customer Success | Retention, expansion | Can't predict which customers will churn |
| VP Sales / CRO | Strategy, forecasting | Pipeline data arrives too late |

---

## 4. Platform Architecture (6 Sub-Platforms)

### 4.1 Revenue Intelligence Platform
- Pipeline kanban, deal scoring, forecasting
- Quota management, territory management
- Next Best Action (NBA) engine
- Revenue execution (contracts, proposals, quotes)
- **Documented status:** 75% (gaps: quota, territory, ML forecasting)

### 4.2 AI Platform
- Multi-agent system (Planner → Memory → Executor → Tools → Policies)
- Prompt registry (versioned, A/B testable)
- RAG pipeline, Knowledge Graph
- Arabic NLP (normalization, sentiment, extraction)
- AI Copilot (natural language → query → summarize → recommend)
- **Documented status:** 85% (but critical gaps: agent runtime placeholder, 0% AI test coverage)

### 4.3 Knowledge Platform
- Entity Resolution (golden record merging)
- Knowledge Graph (Neo4j)
- Feature Store (7 score computers)
- Data Fabric (scrapers, ETL, enrichment)
- **Documented status:** 65-85%

### 4.4 Automation Platform
- Visual workflow builder
- Rules engine
- Webhooks, scheduled jobs
- **Documented status:** 85%

### 4.5 Marketplace
- Signal marketplace
- Widget registry
- Integration marketplace
- **Documented status:** Stub only

### 4.6 Developer Platform
- Public API (REST + GraphQL)
- Plugin SDK, Widget SDK
- MCP server, Agent SDK
- **Documented status:** Widget SDK frozen v1.0; rest early-stage

---

## 5. Additional Capabilities

### Tenant Studio (No-Code Configuration)
- Custom field definitions
- Workflow canvas builder
- Scoring rules studio
- Territory rules studio
- Permissions studio
- Notification rules studio
- Branding & languages studio
- Prompt library (AI Studio)
- AI policies
- AI memory settings

### GTM Studio (Go-to-Market Intelligence)
- ICP Engine (Ideal Customer Profile)
- Market sizing (TAM/SAM/SOM)
- Lead discovery (gov-first + HubSpot fallback)
- Lookalike accounts
- Enrichment waterfall (multi-provider)
- Contact verification
- Website intelligence
- AI outreach (draft generation)
- Sequencing engine (email channel)

### Integration Hub
- Generic connector framework
- Odoo as first certified adapter
- Planned: SAP, Dynamics, HubSpot, Salesforce
- Field mapping, conflict resolution, sync scheduling

### Digital Twin Engine
- Real-time computational mirror per workspace
- State manager, predictor, risk detector
- Scenario simulator, recommendation engine
- Feedback loop

### Knowledge Packs
- Portable industry bundles
- Healthcare, Construction, Financial Services, Technology, Education, Retail

---

## 6. Security Model (Documented)

| Layer | Documented Mechanism |
|-------|---------------------|
| Row-level isolation | Postgres RLS on every tenant-scoped table |
| Auth | JWT (RS256) + OAuth 2.0 (Google) + RBAC |
| Owner/Tenant boundary | Two separate JWT issuers/audiences |
| Zero-trust | Every endpoint authenticated, every request authorized |
| Credential isolation | Fernet-encrypted, vault-referenced credentials |
| Cross-tenant regression | Mandatory merge gate on PRs touching tenant-scoped tables |
| Support impersonation | Time-boxed, tenant-consented, fully audited |
| Data residency | Tenant.region / data_residency field for PDPL |
| Secrets vault | All credentials in dedicated secrets manager |
| Webhook SSRF/CSRF | URL allowlist + CSRF protection |

---

## 7. AI Model (Documented)

| Component | Purpose |
|-----------|---------|
| Revenue Brain | Central intelligence: NBA per user per context |
| Agent Runtime | Full agent lifecycle (plan → execute → learn) |
| AI Copilot | Natural language interface |
| Scoring Engine | ICP fit, engagement, intent scores |
| Company DNA | Multi-dimensional company profile embeddings |
| AI Memory | Short-term (session), long-term (PostgreSQL), working (task) |
| Prompt Studio | Versioned prompts, A/B testable |
| AI Governance | Model costs, latency, accuracy, hallucination tracking |
| Simulation Engine | What-if scenario modeling |
| Experiment Engine | A/B tests with auto-selection |
| Digital Twin | Real-time computational mirror |

**Providers:** OpenAI GPT-4o (complex), GPT-4o-mini (simple), text-embedding-3-small/large, Anthropic Claude 3.5 (planned)

---

## 8. Multi-Tenancy Model (Documented)

**Two-plane architecture:**

```
Side A — Owner Platform (control plane)     Side B — Tenant Workspace (data plane ×N)
├── Tenants, Subscriptions, Billing         ├── Tenant's own users, CRM, ERP link
├── Marketplace, Connector Registry         ├── Tenant's own AI: prompts, scoring, memory
├── Usage Analytics, Platform Health        ├── Tenant's own Studio configuration
└── Releases, Feature Flags, AI Providers   └── Tenant's own integrations
```

**Isolation tiers:** Pooled (shared Postgres + RLS) → Siloed (dedicated schema/DB)

---

## 9. Revenue Model (Documented)

| Stream | Description |
|--------|-------------|
| SaaS Tiers | Free → Starter → Growth → Enterprise |
| Marketplace | 20% rev share on third-party listings |
| Data Enrichment | Usage-based connector syncs |
| Knowledge Packs | Industry-specific bundles |

**Hybrid monetization:** Seats + AI tokens + connector syncs + storage + marketplace installs.

**Financial targets:** Year 3 (2028) 200+ customers; Year 5 (2030) $50M+ ARR, 1000+ customers.

---

## 10. Production Readiness Claims

| Source | Claim |
|--------|-------|
| PROJECT_BIBLE.md | 7.5/10 → target ≥9.0/10 |
| MASTER_BLUEPRINT.md | 12% completion ("most honest assessment") |
| CANONICAL_ARCHITECTURE.md | B- / "Needs Improvement" |
| vNext MASTER_PLAN.md | 7.5/10, 79-85% completion |
| GA Engineering Audit (2026-07-22) | **38/100 Production Readiness, 48/100 Security — PRODUCTION NO-GO** |

---

## 11. Key Architectural Claims

| Claim | Source |
|-------|--------|
| Modular monolith with DDD | CANONICAL_ARCHITECTURE.md |
| Event-driven architecture | RUNTIME_ARCHITECTURE.md |
| Repository Pattern (InMemory → PostgreSQL) | CANONICAL_ARCHITECTURE.md |
| 4 API surfaces (REST + GraphQL + MCP + Agent SDK) | MASTER_BLUEPRINT.md |
| 14 bounded contexts (DDD) | CANONICAL_ARCHITECTURE.md |
| 300+ API endpoints | CANONICAL_ARCHITECTURE.md |
| 72+ database tables | CANONICAL_ARCHITECTURE.md |
| Arabic-first, RTL | PROJECT_BIBLE.md |
| WCAG AA accessibility | PROJECT_BIBLE.md |
| 50K+ companies scraped | DATA_CONTRACTS.md |

---

*This model represents the THEORETICAL vision as documented. Reality is captured in 02_IMPLEMENTATION_MODEL.md.*
