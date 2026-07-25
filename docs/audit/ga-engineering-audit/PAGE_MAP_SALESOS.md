# SalesOS — Full Site Page Map

> **Date:** 2026-07-22  
> **Product:** SalesOS (AQLIYA first operational product)  
> **Code root:** `salesos/frontend` (Next.js App Router)  
> **Validation:** **light validated** (static route/nav/doc cross-check + Wave 13 crawl cross-ref)  
> **Production GO:** **NO** — not claimed  
> **Design artifact claim:** **NOT all pages designed** — no per-page Figma inventory found

---

## Executive summary / الملخص التنفيذي

### English

SalesOS ships **54 App Router `page.tsx` routes** (auth + marketing + dashboard; dynamic `[id]` as patterns). Primary sidebar exposes **25 unique destinations** (26 `NAV_KEYS` entries with duplicate `/contacts`). Wave 13 full UI crawl opened **49/49** catalogued shells (entity `[id]` deep links skipped).

**Are ALL pages designed?** **No.** Evidence of design is:

| Evidence | Status |
|----------|--------|
| `@salesos/design-language` + `@salesos/ui` token/component system | Exists (code) |
| `docs/vnext/DESIGN_STRATEGY.md` | Draft strategy + backlog; **not** a per-page Figma pass |
| `docs/audit/current-state/10-design-audit.md` | System-level audit (2026-07-15); sample pages only |
| Per-page Figma / screen design inventory | **Not found** in repo (zip `MUHIDE Design System.zip` is an archive, not a page matrix) |
| `09-screen-inventory.md` | **Outdated** (30 screens vs 54 routes today) |

Using honest labels below: most routes are **implemented with design-system usage** (`designed+implemented`), a few are **stubs/demo/honesty-gated**, several roadmap UIs are **planned-missing**, and a small set is **nav-orphaned** (real code, weak/no sidebar entry). **Do not equate “route exists + uses `@salesos/ui`” with “designer-approved Figma complete.”**

### العربية

واجهة SalesOS تحتوي على **54 مساراً** في App Router، والقائمة الجانبية تعرض **25 وجهة فريدة**. زحف Wave 13 فتح **49/49** صفحة من الكتالوج (بدون روابط الكيانات الديناميكية `[id]`).

**هل كل الصفحات مصمّمة؟** **لا.** يوجد نظام تصميم في الكود واستراتيجية تصميم مسودة، لكن **لا توجد خريطة Figma/اعتماد تصميم لكل صفحة**. معظم الصفحات **منفَّذة بمكونات نظام التصميم**، وبعضها **stub/تجريبي**، وبعض شاشات الخطة **مفقودة في الكود**، وبعض المسارات **خارج الـ nav**.

### Status counts (this map)

| Design status | Count | Meaning in this doc |
|---------------|------:|---------------------|
| `designed+implemented` | **46** | Route exists; real UI / workspace; uses DS or feature workspace (not empty stub). **Figma pass: unknown.** |
| `implemented-stub` | **4** | Thin / demo / honesty-disabled / minimal shell |
| `planned-missing` | **7** | In FEATURE_ROADMAP / IA / i18n intent; no dedicated route |
| `orphaned-code` | **4** | Route exists; not in primary nav and barely discoverable |
| `design-unknown` | **0** *(as primary row label)* | Reserved; Figma-unknown is noted globally for **all** rows |

**Wave 13 crawl delta:** 49 opened vs 54 code routes → **5** uncrawled = entity/plugin dynamics: `/companies/[id]`, `/companies/[id]/360`, `/employees/[id]`, `/opportunities/[id]`, `/marketplace/[pluginId]/config`.

---

## Product boundaries

| Product | In this FE? | Notes |
|---------|-------------|-------|
| **SalesOS** | Yes — sole shipped UI under `salesos/frontend` | Primary scope of this map |
| **AuditOS** | No separate app | Vision only in AQLIYA platform docs |
| **DecisionOS** | No separate app | SalesOS has `/decisions*` (Decision Center HTTP APIs). FE `@salesos` decision **package is STUB** — not the page |
| **LocalContentOS** | No separate app | Not present as routes |

---

## Sources

| Source | Role |
|--------|------|
| `salesos/frontend/src/app/**/page.tsx` | Code inventory (authoritative for routes) |
| `salesos/frontend/src/app/(dashboard)/layout.tsx` → `NAV_KEYS` | Primary nav |
| `docs/audit/current-state/09-screen-inventory.md` | Plan/inventory (2026-07-15, **30** screens — stale) |
| `docs/vnext/FEATURE_ROADMAP.md` | Planned feature UIs |
| `docs/vnext/DESIGN_STRATEGY.md` | Design system V2 + IA templates (no page matrix) |
| `docs/audit/ga-engineering-audit/PROGRESS-WAVE13-FULL-UI-CRAWL.md` | 49-page crawl evidence |
| `docs/audit/ga-engineering-audit/AI_HONESTY.md` | Copilot / AI honesty |

---

## Nav (primary sidebar)

From `NAV_KEYS` in `(dashboard)/layout.tsx` (order preserved). Labels from `en.json` keys.

| # | Path | i18n | In Wave13? |
|--:|------|------|------------|
| 1 | `/dashboard` | nav.dashboard | Yes |
| 2 | `/companies` | nav.companies | Yes |
| 3 | `/employees` | nav.employees | Yes |
| 4 | `/employees/me` | nav.profile | Yes |
| 5–6 | `/contacts` | nav.contacts | Yes (**duplicate nav entry**) |
| 7 | `/opportunities` | nav.opportunities | Yes |
| 8 | `/activities` | nav.activities | Yes |
| 9 | `/revenue` | nav.revenue | Yes |
| 10 | `/pipeline` | nav.pipeline | Yes |
| 11 | `/forecast` | nav.forecast | Yes |
| 12 | `/search` | nav.search | Yes |
| 13 | `/decisions` | nav.decisions | Yes |
| 14 | `/meetings` | nav.meetings | Yes |
| 15 | `/rag` | nav.rag | Yes |
| 16 | `/ai` | nav.ai | Yes |
| 17 | `/graph` | nav.graph | Yes |
| 18 | `/copilot` | nav.copilot | Yes (gated by `feature_ai_copilot`) |
| 19 | `/automation` | nav.workflows | Yes |
| 20 | `/analytics` | nav.analytics | Yes |
| 21 | `/signals` | nav.signals | Yes |
| 22 | `/rules` | nav.rules | Yes |
| 23 | `/monitoring` | nav.monitoring | Yes |
| 24 | `/customer-success` | nav.customer_success | Yes |
| 25 | `/settings` | nav.settings | Yes |
| 26 | `/admin` | nav.admin | Yes |

**i18n without route:** `nav.nba` exists; **no** `/nba` page → `planned-missing`.

**Not in sidebar:** `/knowledge*`, `/marketplace*`, all analytics/admin/revenue deep routes, entity `[id]` pages.

---

## Master matrix

Legend — **Design status** (honest labels only):

- `designed+implemented` — page exists, real UI / workspace, DS or feature shell; **not** a Figma certification
- `implemented-stub` — empty / minimal / demo-fallback-primary / honesty-disabled shell
- `planned-missing` — in plan/inventory/i18n; no route
- `orphaned-code` — route exists; not in plan+nav discoverability (weak IA)
- `design-unknown` — no design artifact (used globally in summary; not duplicated per row)

**Code:** `Y` = `page.tsx` present · **Plan:** `09` = in 09-screen-inventory · `FR` = FEATURE_ROADMAP surface · `W13` = Wave 13 crawl PASS

| Product surface | Page path | Nav? | Code | Plan ref | Design status | Notes |
|-----------------|-----------|------|------|----------|---------------|-------|
| Marketing | `/` | No | Y | 09 | `implemented-stub` | Mini landing (~30 lines); CTAs only; not full marketing design |
| Auth | `/login` | No | Y | 09 | `designed+implemented` | W13 PASS; DESIGN_STRATEGY still flags shadcn token mismatch on login |
| Auth | `/register` | No | Y | 09 | `designed+implemented` | W13 PASS |
| SalesOS core | `/dashboard` | Yes | Y | 09 (as `/(dashboard)/`) | `designed+implemented` | W13 PASS; `DashboardPage` workspace. Ghost index of `(dashboard)/page.tsx` may exist in search — treat `/dashboard` as canonical |
| Company 360 | `/companies` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS |
| Company 360 | `/companies/[id]` | Deep | Y | 09, FR | `designed+implemented` | **Not in W13** (no seeded id) |
| Company 360 | `/companies/[id]/360` | Deep | Y | FR (Company 360) | `designed+implemented` | **Not in W13**; dedicated 360 route beyond detail |
| Employee 360 | `/employees` | Yes | Y | FR | `designed+implemented` | W13 PASS; **missing from 09 inventory** |
| Employee 360 | `/employees/me` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS |
| Employee 360 | `/employees/[id]` | Deep | Y | 09, FR | `designed+implemented` | **Not in W13** |
| SalesOS core | `/contacts` | Yes | Y | 09 | `designed+implemented` | W13 PASS; duplicate sidebar entry |
| SalesOS core | `/opportunities` | Yes | Y | 09 | `designed+implemented` | W13 PASS; kanban |
| SalesOS core | `/opportunities/[id]` | Deep | Y | 09 | `designed+implemented` | **Not in W13**; DecisionProvider + NBA widgets |
| SalesOS core | `/activities` | Yes | Y | 09 | `designed+implemented` | W13 PASS |
| Revenue | `/revenue` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS; API 422 residuals in crawl |
| Revenue | `/revenue/territories` | Deep | Y | FR (Revenue) | `designed+implemented` | W13 PASS; **demoTerritories fallback** on API fail — honesty risk |
| Revenue | `/revenue/quotas` | Deep | Y | FR (Revenue) | `designed+implemented` | W13 PASS; **demoQuotas fallback** on API fail |
| Revenue | `/pipeline` | Yes | Y | 09 | `designed+implemented` | W13 PASS |
| Analytics | `/pipeline/analytics` | Deep | Y | FR (Analytics) | `designed+implemented` | W13 PASS; API 422 |
| Revenue | `/forecast` | Yes | Y | 09 | `designed+implemented` | W13 PASS |
| Search | `/search` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS |
| Search | `/search/analytics` | Deep | Y | FR (Search) | `designed+implemented` | W13 PASS; **API 404** |
| Decision Center | `/decisions` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS; uses HTTP APIs not stub package |
| Decision Center | `/decisions/templates` | Deep | Y | FR | `designed+implemented` | W13 PASS |
| SalesOS core | `/meetings` | Yes | Y | 09 | `designed+implemented` | W13 PASS |
| Knowledge / RAG | `/rag` | Yes | Y | 09 | `designed+implemented` | W13 PASS |
| AI / Copilot | `/ai` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS; ExperimentalAiBadge + honesty hint |
| Knowledge | `/graph` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS; FR still wants path-analysis UX |
| AI / Copilot | `/copilot` | Yes* | Y | 09, AI_HONESTY | `implemented-stub` | W13 shell PASS; **default flag off**; sample history; not GA AI |
| AI / Copilot | `/copilot/telemetry` | Deep | Y | — | `designed+implemented` | W13 PASS; **API 404** |
| Automation | `/automation` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS; **workflows API 500** |
| Automation | `/automation/workflows/new` | Deep | Y | FR | `designed+implemented` | W13 PASS |
| Automation | `/automation/analytics` | Deep | Y | FR | `designed+implemented` | W13 PASS; API 500 |
| Analytics | `/analytics` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS; API 422s |
| Analytics | `/analytics/sales` | Deep | Y | FR | `designed+implemented` | W13 PASS; API 422 |
| Analytics | `/analytics/revenue` | Deep | Y | FR | `designed+implemented` | W13 PASS; API 422 |
| Analytics | `/analytics/pipeline` | Deep | Y | FR | `designed+implemented` | W13 PASS; API 422 |
| Analytics | `/analytics/employees` | Deep | Y | FR | `designed+implemented` | W13 PASS; API 422 |
| Analytics | `/analytics/automation` | Deep | Y | FR | `designed+implemented` | W13 PASS; API 500 |
| Analytics | `/analytics/reports/builder` | Deep | Y | FR | `designed+implemented` | W13 PASS |
| Signals | `/signals` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS; empty-state common |
| Automation / Rules | `/rules` | Yes | Y | 09 | `designed+implemented` | W13 PASS |
| Admin / Ops | `/monitoring` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS |
| Customer Success | `/customer-success` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS |
| Admin | `/settings` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS; FR still calls Settings incomplete |
| Admin | `/admin` | Yes | Y | 09, FR | `designed+implemented` | W13 PASS; tabbed workspace |
| Admin | `/admin/flags` | Deep | Y | FR | `designed+implemented` | W13 PASS |
| Admin | `/admin/config` | Deep | Y | FR | `designed+implemented` | W13 PASS |
| Admin | `/admin/audit` | Deep | Y | FR | `designed+implemented` | W13 PASS |
| Admin | `/admin/tenants` | Deep | Y | FR | `designed+implemented` | W13 PASS |
| Knowledge | `/knowledge` | No | Y | FR (KG) | `orphaned-code` | W13 PASS; **not in sidebar**; overlaps `/graph` conceptually |
| Knowledge / Data Fabric | `/knowledge/connectors` | No | Y | FR (Data Fabric) | `orphaned-code` | W13 PASS; not in sidebar |
| Marketplace | `/marketplace` | No | Y | FR (Marketplace) | `orphaned-code` | W13 PASS; plugin gallery + BUILTIN_PLUGINS; not in sidebar |
| Marketplace | `/marketplace/[pluginId]/config` | No | Y | FR | `orphaned-code` | **Not in W13** |

\*Copilot nav item hidden unless `feature_ai_copilot` enabled.

---

## Planned-missing (no dedicated route)

| Product surface | Intended UI (plan) | Plan ref | Design status | Notes |
|-----------------|-------------------|----------|---------------|-------|
| AI / NBA | Dedicated Next Best Action screen | i18n `nav.nba`; Opportunity widgets only | `planned-missing` | No `/nba` route |
| Knowledge | Graph **path analysis** view | FEATURE_ROADMAP Knowledge Graph | `planned-missing` | `/graph` exists; path analysis called out as missing |
| Knowledge | Feature **registry** + **drift** dashboard | FEATURE_ROADMAP Feature Store | `planned-missing` | No FE route found |
| Data Fabric | Ingestion pipeline config + data quality dashboard | FEATURE_ROADMAP Data Fabric | `planned-missing` | Partial: `/knowledge/connectors` only |
| Marketplace | **Widget** marketplace (dashboard widgets) | FEATURE_ROADMAP Widget Marketplace | `planned-missing` | `/marketplace` is **plugins**, not widget gallery DoD |
| Signals | Signal **rule configuration** UI | FEATURE_ROADMAP Signals | `planned-missing` | Feed page exists; rule-config UX called missing |
| Admin | Full **RBAC permission matrix** editor | FEATURE_ROADMAP Admin | `planned-missing` | Admin partial; dedicated matrix editor not evidenced as route |

---

## Inventory drift (09-screen-inventory → today)

`09-screen-inventory.md` (2026-07-15) listed **30** screens. Code now has **~54** routes. Notable additions since inventory:

- `/dashboard` (canonical home; inventory described `/(dashboard)/`)
- `/employees` list
- `/companies/[id]/360`
- `/revenue/territories`, `/revenue/quotas`
- `/pipeline/analytics`
- `/search/analytics`
- `/decisions/templates`
- `/copilot/telemetry`
- `/automation/workflows/new`, `/automation/analytics`
- `/analytics/{sales,revenue,pipeline,employees,automation}`, `/analytics/reports/builder`
- `/admin/{flags,config,audit,tenants}`
- `/knowledge`, `/knowledge/connectors`
- `/marketplace`, `/marketplace/[pluginId]/config`

---

## Wave 13 crawl cross-check

| Metric | Value |
|--------|------:|
| Catalogued shells opened | 49/49 PASS |
| Code routes (this map) | 54 |
| Uncrawled (dynamic) | 5 |
| Clicks | 136 (128 OK / 8 soft fail) |
| Production GO | **NO** |

Notable crawl residuals (shell OK, data not): workflows **500**, search/copilot telemetry **404**, analytics **422**, CORS host mix.

---

## Design evidence honesty

1. **No per-page Figma matrix** was found under `docs/` or as an extractable page list from `MUHIDE Design System.zip` in this pass.  
2. `DESIGN_STRATEGY.md` defines **templates** (List/Detail/Dashboard/Form) and a **component backlog** — not screen sign-off.  
3. `10-design-audit.md` audited tokens/`@salesos/ui`/sample pages — **not** 54-page visual QA.  
4. Therefore: **cannot claim “all pages have been designed.”** Closest true statement: *most SalesOS routes are implemented against the in-repo design system; design-system V2 and per-page design approval remain open.*

---

## Top gaps (actionable)

1. **Figma / design sign-off gap** — invent inventory or extract from Design System zip before claiming “all designed.”  
2. **Nav IA** — `/knowledge`, `/marketplace` (and deep admin/analytics) are hard to discover; duplicate `/contacts`.  
3. **Stale docs** — refresh `09-screen-inventory.md` to 54 routes.  
4. **Roadmap missing UIs** — widget marketplace DoD, feature drift UI, path analysis, signal rules, NBA page, RBAC matrix.  
5. **Honesty stubs** — `/` mini-landing; `/copilot` flag-off; demo quotas/territories.  
6. **Crawl gap** — seed IDs and crawl 5 dynamic routes.  
7. **API residuals** — do not confuse W13 shell PASS with working product surfaces.

---

## Validation

| Item | Status |
|------|--------|
| Route enumeration | **light validated** (Glob + layout read) |
| Nav extraction | **light validated** |
| Wave 13 cross-check | **light validated** (doc evidence) |
| Figma per-page design | **not validated** / **absent** |
| Browser re-crawl this pass | **not run** |
| Production GO | **NO** |

---

*Evidence governs. AI assists. Humans decide.*
