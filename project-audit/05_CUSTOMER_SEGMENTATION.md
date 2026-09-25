# 05 — Customer Segmentation — تقسيم العملاء
> **أحدث متابعة 2026-09-20:** الصفحات المصادق عليها لبيانات SalesOS اختُبرت على `salesos_test` عند migration head `q9r0s1t2u3v4`؛ أُصلحت pagination في P3 وP1/P2. راجع التقرير [22](22_AUTHENTICATED_DATA_AND_BROWSER_VERIFICATION_2026-09-20.md) للأعداد والحدود الحالية.
> يحتفظ هذا المستند بتحليله المؤرخ. نتائج browser QA لا تفتح Phase 7 ولا تغيّر قرار الإنتاج؛ Phase 7 ما زالت BLOCKED والإنتاج NOT APPROVED.

**Basis:** `PRODUCT_BIBLE.md` §Personas + Saudi B2B market observation + code capabilities (`app/modules/gtm/`, `master_data/`, `signal_marketplace/`, knowledge packs).

**Status:** ICP profiles NOT signed yet (`icp_profiles` DB is empty by default; only `pif-icp-demo` seeded). This document proposes ICPs to be signed by product owner.

---

## 1. الشرائح المستهدفة / Target segments (priority order)

### ICP-1: **Design Partner** (زبون الاختبار الحقيقي)
- **Segment size:** 1–3 companies (this is intentionally small)
- **Firmographics:** KSA-based, 10–200 employees, B2B focus, active BD / sales function
- **Persona:** Founder / Head of BD / Head of Sales
- **Pain:** hours/day lost researching Saudi companies; no bilingual AI-safe tool exists
- **Willingness to pay:** SAR 0 (barter for feedback + case-study rights)
- **Timeframe:** 90 days
- **Success = ** at least one HITL-approved AI recommendation → booked activity → captured as case study

### ICP-2: **Saudi B2B SMB Sales Team** (الشريحة الأولى المدفوعة)
- **Segment size:** ~100–500 tenants addressable in KSA
- **Firmographics:** KSA-registered, 20–200 employees, B2B sales function of 5–15 seats, revenue SAR 20M–200M
- **Verticals:** Construction supply, healthcare services, financial services (matches shipped signal packs)
- **Persona:** Head of Sales / Sales Manager / Sales Ops
- **Pain:** Excel-based pipeline, no Arabic-first CRM, no confidence in generic AI
- **Willingness to pay:** SAR 50k–80k / year (Team tier)
- **Buying criteria:** Arabic-first UX, real Saudi company data, evidence-cited AI (not chatbot), integration with Gmail / Outlook / Calendar
- **Buying trigger:** losing deals to competitors with better intelligence, or being asked by executives to move off Excel
- **Decision maker:** Head of Sales; economic buyer: GM/CEO for SME
- **Sales cycle:** 6–12 weeks
- **Contract:** annual, per-team

### ICP-3: **KSA Investment / VC Analyst Team** (شريحة مختصة عالية القيمة)
- **Segment size:** ~30–60 addressable orgs (VC funds, PIF sub-portfolios, family offices, investment banks)
- **Firmographics:** KSA/Gulf-based, small team (3–15 analysts), tech-forward
- **Persona:** Head of Deal Flow / Head of Research
- **Pain:** relationship-graph blindness, deal-flow inefficiency, no bilingual context on target companies
- **Willingness to pay:** SAR 180k–350k / year (Business or Enterprise tier)
- **Buying criteria:** relationships / knowledge-graph (currently OFFLINE per ADR-108 → **this ICP is blocked until Neo4j / KG activated in v2.0**)
- **Sales cycle:** 3–6 months
- **Contract:** annual + custom data ingestion add-ons

### ICP-4: **Enterprise Sales at KSA Enterprise / Government-Adjacent** (الشريحة المؤسسية)
- **Segment size:** ~50 addressable (Aramco vendors, Saudi Telecom vendors, PIF partners, Vision-2030 program suppliers)
- **Firmographics:** 500+ employees, 50+ sales seats, need multi-tenant / SSO
- **Persona:** VP Sales / Chief Commercial Officer
- **Pain:** compliance-safe AI (PDPL, audit trail); tenant isolation; on-prem preference
- **Willingness to pay:** SAR 500k+ / year (Enterprise tier)
- **Buying criteria:** SOC2 / ISO27001 / PDPL alignment; single-tenant deployment option (VPC); SSO; audit exports
- **Sales cycle:** 6–12 months
- **Contract:** annual + implementation fee + optional VPC hosting

### ICP-5 (parked): **International / non-Saudi Middle East**
- Deprioritized until KSA is proven. Do NOT sell here in 2026-2027.

---

## 2. ICP scoring criteria (fits into ICP Engine — `app/modules/gtm/icp_router.py`)

Suggested weights for `ICPProfile` v1 to seed into `icp_profiles` table:

| Signal | Weight | Score-if-present | Notes |
|--------|--------|------------------|-------|
| KSA-registered legal entity (has CR) | 20 | 20 | HARD filter, not soft — non-Saudi = out |
| Employee band 20–500 | 15 | 15 | Match SMB Team ICP |
| Has active B2B sales function (roles in `Contact` include "sales" / "BD") | 15 | 15 | Detected via Comm Hub / Employee 360 |
| Vertical in {construction, healthcare, financial-services} | 10 | 10 | Matches shipped signal packs |
| Uses Gmail / Workspace | 10 | 10 | Enables Comm Hub integration |
| Existing CRM (HubSpot / Salesforce / Zoho) — replaceable | 10 | 10 | Migration story exists |
| Revenue SAR 20M–200M | 10 | 10 | Fits Team tier price |
| Named champion / warm intro | 10 | 10 | Sales-cycle acceleration |
| **Total** | **100** | | Threshold: HIGH ≥ 70, MEDIUM 50–69, LOW < 50 |

**Recommendation:** persist this as the first tenant's `icp_profiles` row via `/api/v1/icp/profiles` (Phase 4C `icp_admin_router` is live per AGENTS.md §25).

---

## 3. Personas × Product surface mapping (evidence-based)

| Persona | Primary v3 surfaces (from `nav.ts`) | Key backend endpoints | Success moment |
|---------|--------------------------------------|------------------------|----------------|
| BD Director | `/v3/companies`, `/v3/data/companies`, `/v3/data/er`, Copilot | `company_router`, `master_data_router`, `entity_resolution_router`, `copilot_router` | Opens a company profile → sees AI summary with sources → creates opportunity |
| Sales Manager | `/v3/crm`, `/v3/sales-dashboard`, `/v3/my-day`, `/v3/approvals`, `/v3/effectiveness` | `commercial_router`, `nba_router`, `approval_router`, `effectiveness_router` | Reviews AI-recommended next actions in `/v3/my-day`, approves via `/v3/approvals` |
| Investment Analyst | `/v3/companies/[id]/360`, Signal Marketplace, Relationships (KG-parked) | `master_data_router`, `signal_marketplace_router`, `graph_router` (offline) | Reviews 360 view + signals; **KG offline = weaker offering for this ICP today** |
| Executive | `/v3/analytics`, `/v3/effectiveness`, `/v3/sales-dashboard`, `/v3/reviews` | `analytics_router`, `effectiveness_router`, `revenue_router` | Reads deterministic forecast (Commit/Best Case/Pipeline/Risk); no LLM in forecast per Phase 2 |
| Data Steward | `/v3/data/*` (5 sub-pages: companies, people, imports, er, review-queue) | `master_data_router`, `review_queue_router` (Phase 7) | Works through Review Queue; PO decisions per PHASE7A_PO_DECISION |
| Admin | `/v3/admin`, `/v3/settings` | `admin_router`, `settings_router`, `sso_router` | Manages users, roles, integrations, feature flags |
| Studio Author (custom rules / prompts) | `/v3/settings` (Studio surfaces at legacy `/studio/*`) | `tenant_studio_router` + 9 sub-routers | Authors ICP, scoring rules, prompt library — advanced tenant |

---

## 4. Anti-personas (do NOT sell to today)

| Anti-persona | Why not |
|--------------|---------|
| Solo consultant / freelancer | Product is team-tier; onboarding overhead too high |
| Marketing team (not sales) | Not the intended workflow; no marketing automation |
| E-commerce merchant | No commerce logic; misaligned |
| Non-Arabic-speaking global team | Losing our real edge |
| Company under 10 employees | Below team-tier fit; can't sustain SAR 60k ACV |
| Regulated bank without a formal AI-usage policy | AI Copilot compliance risk; wait for SAMA guidance clarity |

---

## 5. Segmentation × contract signals to detect ICP fit at demo

Suggested Copilot investigation checklist for a first-meeting brief:
- Does the target have `CR` on record? (validate via `md_global_companies`)
- Employee count band? (`Employee 360` or LinkedIn / gov data)
- Existing CRM? (Comm Hub Gmail/Calendar signal for CRM notifications)
- Vertical? (Match to shipped signal packs)
- Has Arabic-heavy communication? (fits UX moat)
- Champion identified? (`Contact` role field)

Output = ICP fit HIGH/MEDIUM/LOW + evidence-cited reasoning, presentable directly in demo.

---

## 6. Sales-tier progression

```
Design Partner (0 SAR, feedback+case) 
   ↓  after 3 months + case study written
Team (SAR 60k)
   ↓  after 12 months + 2 successful renewals + expansion signals
Business (SAR 180k)
   ↓  after governance/compliance readiness
Enterprise (SAR 500k+)
```

Do not skip levels. Do not offer Enterprise before Team+Business proven.

---

*Segmentation — evidence and market-observation based. See `07_GTM_STRATEGY.md` for how to reach each and `08_SALES_PLAYBOOK.md` for how to close.*
**File-specific update:** Segments and ICP remain product scope; provider and master-data gates still control usable lead data.


---

## Current audit addendum — 2026-09-22 / Audit Refresh 49

**Status authority:** This addendum supersedes stale progress percentages and current-state claims in this file while preserving the historical narrative above. The complete current snapshot is [Audit Refresh 49](49_AUDIT_REFRESH_2026-09-22.md), with execution evidence in [Production Readiness Loop 45](48_PRODUCTION_READINESS_LOOP_2026-09-22.md).

- Current code-scope roadmap: **85/113 = 75.2% (75%)**.
- Backend health: /health HTTP 200; database, cache, graph and Redis connected.
- Scoped evidence: focused product **69/69**, Phase 5 CR **7/7**, ER pipeline **10/10**, compileall and diff checks PASS.
- Phase 7 remains controlled and non-canonical: P2 sample 1,213 at 0.00% internal material error; P1 6,904 captured; Fuzzy 2,661 captured without merge; Short-CR 11 unresolved escalation; MA staging 1,114 rows on salesos_test only (792 PROPOSED / 322 ESCALATED).
- Production database remained read-only: 107 policies total, 106 tenant-isolation named; commercial contracts have RLS and FORCE RLS; no Phase 7 proposal table or write in salesos.
- Frontend source inventory is 49 V3 pages and 78 legacy pages. Local dependency repair failed with EISDIR/EPERM; TypeScript, Next build and authenticated browser are **not release evidence** in this checkout.
- No provider call, CRM apply, production migration, deployment, commit or push occurred.
- Production approval remains **NOT APPROVED** pending frontend toolchain, Phase 7 owner closure, staging connector E2E, backup/restore, monitoring/DR, SSO, Stripe, PDPL and final PO/Data/DevOps sign-off.

Current detailed evidence: report 49 and report 48.
