# SalesOS 4h Build Loop — State

**Date:** 2026-09-12  
**Branch:** `fix/login-and-keys`  
**Workspace:** `D:\AISalesOS`  
**Tick:** 20 **COMPLETE**  
**Production GA:** **NOT APPROVED** / **production no-go**  
**Phase 7:** **BLOCKED** (54,185 ER candidates + 36 short-CR + DI P1/P2 + PO sign-off)  
**AI flag:** `feature_ai_copilot` default **False** (do not flip)

Sources: `PHASE3_MERGE-2026-09-12.md`, `UI_SHELL_STRATEGY-2026-09-12.md`, `CAPABILITY_MATRIX_VERIFIED-2026-09-12.md`, `B3_VERIFY_COMMIT-2026-09-12.md`, `project-audit/17_NEXT_ACTIONS.md`, `project-audit/06_MVP_SCOPE.md`.

---

## 0. Already DONE (do not redo)

| Item | Evidence | Label |
|------|----------|-------|
| Option B — `feature_ai_copilot` default False + 12 unit files | commit `162ef993`; B3 Option B **101/101** Docker pytest | **build validated** |
| Register success → `/v3` | `register/page.tsx` in `162ef993` | **light validated** (static; browser **not validated**) |
| `/v3/icp` in `V3_DOMAIN_NAV` + v3 CmdK | `nav.ts` in `162ef993` | **light validated** (static) |
| Root `railway.json` `preDeployCommand: alembic upgrade head` | `162ef993` | **light validated** (file). Live dashboard **not validated** |
| Audit pack `project-audit/` + Wave 0–2 reports committed | `162ef993` (54 files) | **committed** — **not pushed** |
| B3 verify memo | `85fec4b7` | **committed** — **not pushed** |
| Login fallback already `/v3` | B1 + PHASE3_MERGE | **FACT** before this loop |
| `getDemoData` removed from graph/knowledge | AGENTS §39; B1 §7.3 | **FACT** |

---

## 1. This 4h loop — IN SCOPE (code)

### P0 — keep users in v3 (slice 1)

| ID | Item | Status | Notes |
|----|------|--------|-------|
| L1 | `/v3/employee` exits v3 → `/employees/me` | **DONE** (tick 0) | Now `redirect("/v3/people")`. Emp360 product still parked (MVP out). |
| L2 | Legacy CmdK `go.dashboard` / `go.companies` | **DONE** (tick 0) | Handlers → `/v3` and `/v3/companies`. Palette still mounted only on legacy layout. |

### P1 — golden-path UI holes (slice 2+)

| ID | Item | Status | Why next |
|----|------|--------|----------|
| L3 | **Create company on `/v3/companies`** | **DONE** (tick 1) | Thin `CreateCompanyForm` → `POST /api/v1/companies`. Empty state stays in v3 (no `/companies` leak). Success navigates to `/v3/companies/{id}`. Honest 403/API errors. No mocks. |
| L4 | Honest empty states only (no mock/demo) on any page we touch | **STANDING RULE** | B1: zero `getDemoData` in `src/` — followed on companies + contacts empty/create. |
| L5 | Backend-without-UI that is **MVP-blocking** — thin v3 surface **only if API is real** | **DEFER** | Create company / contact / deal / task / default pipeline / quote / proposal / review / contract closed (L3/L8/L9/L11/L12/L13/L14/L15/L16). Contact 360 `/contacts` leak closed (tick 5). Company 360 `/companies/{id}` leak closed (tick 7). `/v3/activities` `/activities` leak closed (tick 7). Residual Legacy company on `/v3/contacts/[id]` and `/v3/tasks/[id]` closed (tick 8). Residual **Legacy opportunities** on `/v3/crm/[id]` (`/opportunities`) closed (tick 10). Tick 11 scan: **zero** golden-path GhostButtonLink/href to `/companies`, `/contacts`, `/opportunities`, `/activities`, `/tasks`, `/dashboard`. Commercial create cluster closed. `/v3/approvals` remains HITL — leave. |
| L8 | **Create contact on `/v3/contacts`** | **DONE** (tick 3) | Thin `CreateContactForm` → `POST /api/v1/contacts` (`name` + `company_id` required). Empty state stays in v3 (no `/contacts` leak). Success navigates to `/v3/contacts/{id}`. Honest 403/API errors. Company picker via `GET /api/v1/companies`. No mocks. |
| L9 | **Create deal on `/v3/companies/[id]` + `/v3/crm`** | **DONE** (tick 4) | Thin `CreateDealForm` → existing `createOpportunity` (`POST /api/v1/opportunities` query: `company_id`, `name`, optional `value` default 0). Company tab locks `company_id`. CRM empty CTA no longer bounces to companies / “legacy pipeline”. Success → `/v3/crm/{id}`. Honest 403/API errors. No mocks. Did not invent `owner_id` UI (FE client does not send it). |
| L10 | Residual GhostButtonLink `/contacts` on `/v3/contacts/[id]` | **DONE** (tick 5) | Header “Legacy contacts” removed (exits shell; “Back to list” already `/v3/contacts`). Company-tab empty CTA retargeted `/contacts` → `/v3/companies` (“Browse companies”). Honest no-`company_id` copy. Did not invent link-company. Left company-tab “Legacy company” (`/companies/{id}`) — not this hole. |
| L11 | **Create task on `/v3/tasks`** | **DONE** (tick 6) | Thin `CreateTaskForm` → existing `createTask` (`POST /api/v1/tasks`: required `title`; optional `priority` default `medium`, `source` default `manual`, `company_id`, `opportunity_id`, `due_date`). Empty CTA no longer bounces to companies. Success → `/v3/tasks/{id}` (real detail route). Honest 403/API errors. No mocks. Extended FE client with last-arg `dueDate` so the real field is not dropped. |
| L12 | **Create default pipeline on `/v3/crm`** | **DONE** (tick 9) | Confirmed `POST /api/v1/pipelines` is real and **body-less** (`create_pipeline` builds `default_sales_pipeline`). Added FE `createPipeline` (null body, tenant header only — no invented name/stages). Thin toggle + button on existing v3 CRM pipeline page. Success stays on `/v3/crm` (no designer, no invented detail route). Honest 403/API errors. No mocks. |
| L13 | **Create quote on `/v3/quotes` + `/v3/crm/[id]`** | **DONE** (tick 11) | Tick 11 scan found **zero** golden-path leaks to `/companies` `/contacts` `/opportunities` `/activities` `/tasks` `/dashboard`. Next real-API hole: empty `/v3/quotes` said “create from an opportunity” with no form. Confirmed `POST /api/v1/quotes` is real (`opportunity_id` Query required, `title` default `Quote`, **null body**). Fixed FE `createQuote` (was sending JSON body). Thin form + deal-360 lock. Success → `/v3/quotes/{id}`. No deals → `/v3/crm`. Honest 403. No line-item UI. |
| L14 | **Create proposal on `/v3/proposals`** | **DONE** (tick 12) | Confirmed `POST /api/v1/proposals` is real (`opportunity_id` + `quote_id` Query required, **null body**, 201 `{id,status,sections}`). Needs a quote first (L13). GET `/quotes` and GET `/proposals` without `opportunity_id` return `[]` — form picks deal then quotes for that deal. Thin form on `/v3/proposals`. Success → `/v3/proposals/{id}` (route exists). No deals → `/v3/crm`. No quotes → `/v3/quotes`. Honest 403. No sections UI. |
| L15 | **Create review on `/v3/reviews`** | **DONE** (tick 13) | Confirmed `POST /api/v1/reviews` is real (`review_type` + `target_id` + `target_type` Query required, `assigned_to` default `""`, **null body**, 201 `{id,status,review_type}`). Types on disk: `deal_review` / `manager_review` / `exception_review` / `quote_review` / `proposal_review`. Target types on disk: `opportunity` / `quote` / `proposal`. GET `/reviews` lists by tenant. Thin form on `/v3/reviews`. Success → `/v3/reviews/{id}` (route exists). No deals → `/v3/crm`. No quotes → `/v3/quotes`. No proposals → `/v3/proposals`. Honest 403. No assign/decide UI on create. |
| L16 | **Create contract on `/v3/contracts`** | **DONE** (tick 14) | Confirmed `POST /api/v1/contracts` is real (`opportunity_id` required via Query or JSON body; `quote_id` / `title` optional; 201). FE `createContract` already posted JSON body — title made optional to match API. Thin form on `/v3/contracts`. Success → `/v3/contracts/{id}` (route exists). No deals → `/v3/crm`. No quotes does **not** block (quote optional) + `/v3/quotes` link. Honest 403. No invented sign/activate on create. |
| L17 | **v3 nav prune to ~12 MVP items** | **DONE** (tick 15) | Primary `V3_DOMAIN_NAV` **26 → 12**. Kept golden path + commercial create (L3/L8–L16) + live ICP + Settings (Gmail/integrations for the Activities feed — not leak-only). Activities kept (real `getGlobalActivities` feed, not a Tasks duplicate). Dropped from primary only (pages stay): People, Approvals, Analytics, Sales Dashboard, My Day, Effectiveness, CS, Admin, Data + MD children, Review Queue. v3 CmdK now inherits nav only (**12** destinations; `/v3/shell` removed tick 16). Legacy `commands.ts` untouched. |
| L18 | **Remove `/v3/shell` from customer v3 CmdK** | **DONE** (tick 16) | Emptied `V3_CMD_EXTRA`. Page stays on disk (internal spec). Customer CmdK = 12 golden-path destinations. Did not un-prune nav. |
| L19 | **Legacy CmdK `go.settings` → `/v3/settings`** | **DONE** (tick 17) | Settings is already in the 12-item MVP nav (Gmail/integrations). Left `go.admin` on `/admin` (Admin pruned from customer chrome). Did not touch the `/v3/settings` page GhostButtonLinks. |
| L20 | **Stop advertising pruned leftover CmdK** | **DONE** (tick 18) | Removed `go.v3.approvals`, `go.v3.data*`, `go.data.*` (10 ids). Pages stay. Left `go.admin` on `/admin`. Kept `go.v3.quotes` / `go.v3.contracts`. Count **51 → 41**. |
| L21 | **Stop advertising leftover GTM tip CmdK** | **DONE** (tick 19) | Removed `go.gtm` + `go.gtm.*` (10 ids). Pages stay. Customer ICP remains `/v3/icp` in the 12-item MVP nav. Left `go.admin` on `/admin`. Count **41 → 31**. |
| L22 | **Stop advertising leftover Tenant Studio / Marketplace tip CmdK** | **DONE** (tick 20) | Removed `go.studio.*` (11 ids) + `go.marketplace.listings`. Pages stay. Left `go.admin` on `/admin`. Count **31 → 19**. |

### P1 — scoped proof

| ID | Item | Status |
|----|------|--------|
| L6 | Scoped tests for files we touch | **DONE** — Tick 20 isolated runner **94/94 PASS** (ticks 0–20, +1 CmdK studio/marketplace-ids). Tick 2 host Jest **4/4 PASS** on the two Tick 0 files only (`commands` + `employee`). Host `npm install` still **not clean**; `jest.frontend.cjs` prefers `%TEMP%\salesos-jest-runner`. No Docker pytest (FE-only). |
| L7 | Named-path git commit. Never `git add -A`. Never push. | **STANDING RULE** |

---

## 2. OUT OF SCOPE (this loop)

- Phase 7 / production DB / `salesos` production ingest
- Flip `feature_ai_copilot` True
- Secrets, Stripe keys, OAuth app creation, Railway dashboard
- Deleting 78 legacy pages wholesale
- Claiming Production GO
- Editing `project-audit/`
- Human ops: MOU, LLM contract, SSO apps, backup schedule, Stripe KYC, Sentry, status page, MSA/DPA
- Wholesale Next redirects of all legacy hubs

---

## 3. Frozen / later (not this 4h)

| Item | Source | Why frozen |
|------|--------|------------|
| Phase 7-B/C + 54,185 review | AGENTS, 17_NEXT #16–18 | Human + PO |
| Railway live `preDeployCommand` confirm | 17_NEXT #3 | Dashboard |
| Railway managed backup | 17_NEXT #4 | Platform |
| Google OAuth staging app | 17_NEXT #9 | Console |
| Stripe live keys | MVP #11 | Keys empty → 503 |
| Production LLM contract | MVP #5 | Procurement |
| GTM 8 MOCK stories | Matrix §5.10 | Out of MVP |
| KG / Neo4j | ADR-108 | Offline |
| Decision FE STUB | Matrix | Do not sell |
| Nav prune to ~12 MVP items | B1 §8 | **DONE** (tick 15). Primary `V3_DOMAIN_NAV` **26 → 12**. Pages not deleted. |
| `/v3/shell` remove from CmdK | B1 P1 | **DONE** (tick 16). `V3_CMD_EXTRA` empty. Page stays. |
| Legacy CmdK `go.settings` → `/v3/settings` | B1 P0 #4 | **DONE** (tick 17). `go.admin` left on `/admin`. Settings **page** GhostButtonLinks still frozen. |
| Legacy CmdK pruned Approvals / Data / Review Queue | Tick 18 / B1 §8 | **DONE** (tick 18). `go.v3.approvals` + `go.v3.data*` + `go.data.*` removed from leftover palette. Pages stay. |
| Legacy CmdK leftover GTM tip destinations | Tick 19 / Matrix §5.10 | **DONE** (tick 19). `go.gtm` + `go.gtm.*` removed from leftover palette. GTM pages stay. Customer ICP is `/v3/icp`. |
| Legacy CmdK leftover Tenant Studio / Marketplace tip destinations | Tick 20 / B1 §8 | **DONE** (tick 20). `go.studio.*` + `go.marketplace.listings` removed from leftover palette. Studio + listings pages stay (MVP out). |
| GhostButtonLink “Open legacy …” on other v3 pages | B1 | Golden-path leaks to `/companies`, `/contacts`, `/opportunities`, `/activities`, `/tasks`, `/dashboard` = **ZERO** (tick 11 scan). Remaining **frozen** GhostButtonLink: `/v3/people` + `/v3/people/[id]` → `/employees` (Emp360 parked); `/v3/admin` → `/admin`; `/v3/settings` → `/settings`; `/v3/analytics` → `/analytics`. |

---

## 4. Tick 0 log

| Field | Value |
|-------|-------|
| Done | Slice 1 v3 containment: `/v3/employee` stays in v3; legacy CmdK home/companies go to v3. |
| Files | `salesos/frontend/src/app/v3/employee/page.tsx`; `salesos/frontend/src/app/v3/employee/__tests__/page.test.tsx` (new); `salesos/frontend/src/lib/commands.ts`; `salesos/frontend/src/lib/__tests__/commands.test.tsx`; this file |
| Tests | Jest written. **not validated** — host `npm install` **aborted** (exit unknown, ~24 min); extract errors (`TAR_ENTRY_ERROR ENOENT`, including `ts-jest/dist`). No browser QA. No pytest (no BE). |
| Commit | **`905d3468`** (`905d3468` — `fix: keep v3 users off legacy employee and CmdK destinations`). **Not pushed.** |
| Validation | Code **light validated** (static read of handlers + redirect). Tests **not validated**. Browser **not validated**. **production no-go** unchanged. |
| Next slice (tick 1) | **L3 — create company on `/v3/companies`** — **closed this tick**. |

---

## 5. Tick 1 log

| Field | Value |
|-------|-------|
| Done | L1/L2 confirmed already in `905d3468`. Slice 2 **L3**: in-v3 create company + honest empty (no legacy `/companies` CTA). CmdK count assertion 39→51 (matches 51 `registerCommand`). |
| Files | `salesos/frontend/src/app/v3/companies/page.tsx`; `salesos/frontend/src/app/v3/companies/create-company-form.tsx` (new); `salesos/frontend/src/app/v3/companies/__tests__/page.test.tsx` (new); `salesos/frontend/src/app/v3/companies/__tests__/create-company-form.test.tsx` (new); `salesos/frontend/src/lib/__tests__/commands.test.tsx`; this file |
| Tests | **9/9 PASS**: employee redirect (1) + CmdK (3) + companies empty/create (5). Isolated runner `%TEMP%\salesos-jest-runner` because host `node_modules` is incomplete (`npm install` ENOTEMPTY). Browser **not validated**. No pytest (no BE). |
| Commit | **`61c78b96`** (`fix: add in-v3 company create so empty tenants stay off legacy /companies`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. Host `npm test` **not validated** (broken `node_modules/.bin`). **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Next slice (tick 2) | **Create contact on `/v3/contacts`** (same class of hole: empty CTA → `/contacts`; `POST /api/v1/contacts` is real). Or create deal on `/v3/companies/[id]` if contacts is already patched. Stay in v3. No mocks. |

### Tick 1 commands

```text
npm install                         # salesos/frontend — ENOTEMPTY (jsx-ast-utils / graphql / next)
npm install ts-jest@29.2.6          # same ENOTEMPTY
# Isolated runner (not committed):
npm install jest ts-jest typescript jest-environment-jsdom   # %TEMP%\salesos-jest-runner
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # 9/9 PASS (employee + commands + companies __tests__)
```

No `git add -A`. No push.

---

## 6. Tick 2 log

| Field | Value |
|-------|-------|
| Done | L6 host Jest for Tick 0 files only. **L3 was still OPEN** at tick start → did **not** start create-contact (Tick 3 closed L8 later). |
| Files | This file only (plus uncommitted host `node_modules` repairs — **not** committed). Did not touch `v3/companies` or Tick 1 L3 files. |
| Tests | Host Jest **4/4 PASS**: `src/lib/__tests__/commands.test.tsx` (3) + `src/app/v3/employee/__tests__/page.test.tsx` (1). Full `npm test` / `npm run build` **not run**. Browser **not validated**. No pytest (no BE). |
| Commit | **`86b1867e`** (`docs: record tick 2 host Jest 4/4 for Tick 0 files`). **Not pushed.** `node_modules` **not** committed. |
| Validation | Those two files **build validated** on host Jest after surgical repair. Host toolchain **not** a clean `npm install`. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Next slice | **Create deal** on `/v3/companies/[id]` / CRM if opportunity POST is real (L3 + L8 already closed by ticks 1 and 3). Stay in v3. No mocks. |

### Tick 2 commands

```text
# L3 OPEN at start → stayed on L6. Did not implement create-contact.
npm install --no-audit --no-fund   # salesos/frontend — hung (~10 min, no children/network); killed
# Prior leftover npm pid 15464 also hung; killed so extracts could proceed.
# Surgical npm pack + tar extract (not committed): resolve, ejs, @babel/types,
# @babel/traverse, @babel/core, typescript@5.7.3, cssstyle, jsdom@20.0.3,
# pure-rand, aria-query, @babel/runtime. Host next had no package.json.
# Uncommitted Jest-only stub: node_modules/next/{package.json,navigation.js}
node node_modules/jest/bin/jest.js --config jest.config.js --no-coverage --forceExit \
  --testPathPattern="src/lib/__tests__/commands.test.tsx|src/app/v3/employee/__tests__/page.test.tsx"
  # 2 suites / 4 tests PASS
```

No `git add -A`. No push. No Phase 7. Flag unchanged.

---

## 7. Tick 3 log

| Field | Value |
|-------|-------|
| Done | Slice **L8**: in-v3 create contact + honest empty (no legacy `/contacts` CTA). Form posts `createContact` (`name`, `company_id`, optional email/phone/position). No company → stay in v3 (`/v3/companies`). Success → `/v3/contacts/{id}` if id exists. |
| Files | `salesos/frontend/src/app/v3/contacts/page.tsx`; `salesos/frontend/src/app/v3/contacts/create-contact-form.tsx` (new); `salesos/frontend/src/app/v3/contacts/__tests__/page.test.tsx` (new); `salesos/frontend/src/app/v3/contacts/__tests__/create-contact-form.test.tsx` (new); this file |
| Tests | **6/6** contacts + **15/15** tick 0–3 scoped **PASS** (`%TEMP%\salesos-jest-runner`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`57d45779`** (`fix: add in-v3 contact create so empty tenants stay off legacy /contacts`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Next slice (tick 4) | **Create deal** on `/v3/companies/[id]` (or CRM) if `POST` opportunity API is real. Confirm contract first. Stay in v3. No mocks. Residual optional: remove `/contacts` GhostButtonLink on `/v3/contacts/[id]`. |

### Tick 3 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # contacts __tests__: 6/6 PASS
  # employee + commands + companies + contacts: 15/15 PASS
```

No `git add -A`. No push.

---

## 8. Tick 4 log

| Field | Value |
|-------|-------|
| Done | Slice **L9**: confirmed real `POST /api/v1/opportunities` (`company_id` + `name` required, `value` default 0) and existing FE `createOpportunity`. In-v3 create deal on `/v3/companies/[id]` (locked company_id) and `/v3/crm` (company picker). Empty CTAs no longer bounce CRM↔company or mention legacy pipeline. Success → `/v3/crm/{id}`. |
| Files | `salesos/frontend/src/app/v3/crm/create-deal-form.tsx` (new); `salesos/frontend/src/app/v3/crm/page.tsx`; `salesos/frontend/src/app/v3/crm/__tests__/create-deal-form.test.tsx` (new); `salesos/frontend/src/app/v3/crm/__tests__/page.test.tsx` (new); `salesos/frontend/src/app/v3/companies/[id]/page.tsx`; `salesos/frontend/src/app/v3/companies/[id]/__tests__/page.test.tsx` (new); `salesos/frontend/jest.frontend.cjs` (new; isolated runner); `salesos/frontend/jest.frontend.setup.cjs` (new); `salesos/frontend/jest.frontend.next-link.cjs` (new); this file |
| Tests | **9/9** deal/company-detail + **24/24** ticks 0–4 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`6ab5ca15`** (`fix: add in-v3 deal create so empty CRM stays off legacy pipeline`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Next slice (tick 5) | Residual **GhostButtonLink `/contacts` on `/v3/contacts/[id]`**, or thin **create task** if `POST /api/v1/tasks` is real — confirm contract first. Stay in v3. No mocks. Do not redo L3/L8/L9. |

### Tick 4 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # crm + company [id] __tests__: 9/9 PASS
  # employee + commands + companies + contacts + crm + company [id]: 24/24 PASS
```

No `git add -A`. No push.

---

## 9. Tick 5 log

| Field | Value |
|-------|-------|
| Done | Slice **L10**: residual GhostButtonLink `/contacts` on `/v3/contacts/[id]`. Header “Legacy contacts” removed (exits shell; list already `/v3/contacts`). No-company tab CTA retargeted to `/v3/companies`. Did **not** start create task (preference 1 was still open). Did **not** redo L3/L8/L9. |
| Files | `salesos/frontend/src/app/v3/contacts/[id]/page.tsx`; `salesos/frontend/src/app/v3/contacts/[id]/__tests__/page.test.tsx` (new); this file |
| Tests | **2/2** contact detail + **26/26** ticks 0–5 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`d3b9fdad`** (`fix: keep v3 contact 360 off legacy /contacts`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Next slice (tick 6) | Thin **create task** on `/v3/tasks` (not activities feed). `POST /api/v1/tasks` is real; FE `createTask` exists. Contract: required `title`; optional `priority` (default `medium`, pattern critical\|high\|medium\|low), `source` (default `manual`), `company_id`, `opportunity_id`, `due_date`. No invented fields. Stay in v3. Honest errors. No mocks. Do not redo L3/L8/L9/L10. |

### Tick 5 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # contacts/[id] __tests__: 2/2 PASS
  # employee + commands + companies + contacts + crm + company [id] + contact [id]: 26/26 PASS
```

No `git add -A`. No push.

---

## 10. Tick 6 log

| Field | Value |
|-------|-------|
| Done | Slice **L11**: in-v3 create task on `/v3/tasks`. Confirmed real `POST /api/v1/tasks` + FE `createTask`. Empty CTA no longer bounces to companies. Success → `/v3/tasks/{id}`. Extended `createTask` last-arg `dueDate` so optional `due_date` is sent. Did **not** redo L3/L8/L9/L10. |
| Files | `salesos/frontend/src/app/v3/tasks/page.tsx`; `salesos/frontend/src/app/v3/tasks/create-task-form.tsx` (new); `salesos/frontend/src/app/v3/tasks/__tests__/page.test.tsx` (new); `salesos/frontend/src/app/v3/tasks/__tests__/create-task-form.test.tsx` (new); `salesos/frontend/src/lib/api/admin.ts` (`dueDate` last arg); this file |
| Tests | **6/6** tasks + **32/32** ticks 0–6 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`b53731fb`** (`b53731fb` — `fix: add in-v3 task create so empty tenants stay on /v3/tasks`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Next slice (tick 7) | Residual **GhostButtonLink Legacy company** on `/v3/companies/[id]` (`/companies/{id}`) and/or **Legacy activities** on `/v3/activities`. Pipeline create: FE has GET `listPipelines` only — confirm POST before starting. Stay in v3. No mocks. Do not redo L3/L8/L9/L10/L11. |

### Tick 6 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # tasks __tests__: 6/6 PASS
  # employee + commands + companies + contacts + crm + company [id] + contact [id] + tasks: 32/32 PASS
```

No `git add -A`. No push.

---

## 11. Tick 7 log

| Field | Value |
|-------|-------|
| Done | Residual v3→legacy leaks: removed GhostButtonLink **Legacy company** on `/v3/companies/[id]` (header + opportunities/tasks footers → `/companies/{id}`). Removed **Legacy activities** on `/v3/activities` (`/activities`). Already on v3 company 360 / v3 activities — no retarget needed. Did **not** start pipeline create. Did **not** redo L3/L8/L9/L10/L11. Confirmed POST `/api/v1/pipelines` exists (`create_pipeline`, 201) but accepts **no body** (default sales pipeline); FE still GET `listPipelines` only. |
| Files | `salesos/frontend/src/app/v3/companies/[id]/page.tsx`; `salesos/frontend/src/app/v3/companies/[id]/__tests__/page.test.tsx`; `salesos/frontend/src/app/v3/activities/page.tsx`; `salesos/frontend/src/app/v3/activities/__tests__/page.test.tsx` (new); this file |
| Tests | **6/6** company-detail+activities + **36/36** ticks 0–7 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`979af7c0`** (`979af7c0` — `fix: keep v3 company 360 and activities off legacy hubs`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Next slice (tick 8) | Residual **Legacy company** on `/v3/contacts/[id]` and `/v3/tasks/[id]` (`/companies/{id}`). Pipeline create only after those are gone: POST is real but body-less default pipeline — thin button only, no invented name/stages, needs FE `createPipeline`. Stay in v3. No mocks. Do not redo L3/L8/L9/L10/L11. |

### Tick 7 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # company [id] + activities __tests__: 6/6 PASS
  # employee + commands + companies + contacts + crm + company [id] + contact [id] + tasks + activities: 36/36 PASS
```

No `git add -A`. No push.

---

## 12. Tick 8 log

| Field | Value |
|-------|-------|
| Done | Residual v3→legacy leaks: removed GhostButtonLink **Legacy company** on `/v3/contacts/[id]` company tab (`/companies/{id}`) and `/v3/tasks/[id]` related-company footer (`/companies/{id}`). Already have v3 Company 360 CTAs — no retarget needed. Did **not** start pipeline create (residuals were still open at tick start). Did **not** redo L3/L8/L9/L10/L11. |
| Files | `salesos/frontend/src/app/v3/contacts/[id]/page.tsx`; `salesos/frontend/src/app/v3/contacts/[id]/__tests__/page.test.tsx`; `salesos/frontend/src/app/v3/tasks/[id]/page.tsx`; `salesos/frontend/src/app/v3/tasks/[id]/__tests__/page.test.tsx` (new); this file |
| Tests | **5/5** contact-detail+task-detail + **39/39** ticks 0–8 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`e1147dee`** (`e1147dee` — `fix: keep v3 contact 360 and task detail off legacy /companies`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Next slice (tick 9) | Thin **pipeline create** only: POST `/api/v1/pipelines` is real but **body-less** (default sales pipeline); FE still GET `listPipelines` only — add `createPipeline` client, no invented name/stages UI. Stay in v3. No mocks. Do not redo L3/L8/L9/L10/L11. People `/employees` GhostButtonLink remains frozen (Emp360 parked). |

### Tick 8 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # contacts/[id] + tasks/[id] __tests__: 5/5 PASS
  # employee + commands + companies + contacts + crm + company [id] + contact [id] + tasks + task [id] + activities: 39/39 PASS
```

No `git add -A`. No push.

---

## 13. Tick 9 log

| Field | Value |
|-------|-------|
| Done | Slice **L12**: confirmed `POST /api/v1/pipelines` is real and body-less (`default_sales_pipeline`, 201, `{id,name,stages[]}`). Added FE `createPipeline` (null body, no invented name/stages). Thin toggle + button on existing `/v3/crm` pipeline page. Success stays on CRM — no designer, no invented `/v3/pipelines/{id}`. Honest 403. Did **not** redo L3/L8/L9/L10/L11. Did **not** touch Emp360 / `/employees`. |
| Files | `salesos/frontend/src/lib/api/pipeline.ts`; `salesos/frontend/src/lib/api/types/pipeline.ts`; `salesos/frontend/src/lib/api/__tests__/pipeline.test.ts` (new); `salesos/frontend/src/app/v3/crm/create-pipeline-button.tsx` (new); `salesos/frontend/src/app/v3/crm/page.tsx`; `salesos/frontend/src/app/v3/crm/__tests__/create-pipeline-button.test.tsx` (new); `salesos/frontend/src/app/v3/crm/__tests__/page.test.tsx`; this file |
| Tests | **4/4** pipeline-create + **43/43** ticks 0–9 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`adba2369`** (`adba2369` — `fix: add in-v3 default pipeline create on CRM without a designer`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Next slice (tick 10) | Residual **GhostButtonLink Legacy opportunities** on `/v3/crm/[id]` (`/opportunities`). Remaining GhostButtonLink legacy hubs: admin `/admin`, settings `/settings`, analytics `/analytics`, people `/employees` — **frozen** (Emp360 parked). Stay in v3. No mocks. Do not redo L3/L8/L9/L10/L11/L12. |

### Tick 9 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # crm pipeline + createPipeline client: 4/4 PASS (plus existing crm deal tests → 11/11 on crm+client)
  # employee + commands + companies + contacts + contact [id] + crm + company [id] + tasks + task [id] + activities + pipeline client: 43/43 PASS
```

No `git add -A`. No push.

---

## 14. Tick 10 log

| Field | Value |
|-------|-------|
| Done | Residual v3→legacy leak: removed GhostButtonLink **Legacy opportunities** on `/v3/crm/[id]` (`/opportunities`). Already on v3 deal 360 with **Back to CRM** → `/v3/crm` — no retarget needed. Did **not** redo L3/L8/L9/L10/L11/L12. Did **not** touch frozen admin `/admin`, settings `/settings`, analytics `/analytics`, people `/employees`. |
| Files | `salesos/frontend/src/app/v3/crm/[id]/page.tsx`; `salesos/frontend/src/app/v3/crm/[id]/__tests__/page.test.tsx` (new); this file |
| Tests | **2/2** deal 360 + **45/45** ticks 0–10 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`40966155`** (`40966155` — `fix: keep v3 deal 360 off legacy /opportunities`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Next slice (tick 11) | Scan remaining v3 GhostButtonLink to `/companies`, `/contacts`, `/opportunities`, `/activities`, `/tasks`, `/dashboard` on **golden-path pages only**. Leave frozen: admin `/admin`, settings `/settings`, analytics `/analytics`, people `/employees`. Stay in v3. No mocks. Do not redo L3/L8/L9/L10/L11/L12. |

### Tick 10 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # crm/[id] __tests__: 2/2 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client: 45/45 PASS
```

No `git add -A`. No push.

---

## 15. Tick 11 log

| Field | Value |
|-------|-------|
| Done | **Scan:** golden-path v3 pages (companies, contacts, crm, activities, tasks, people list, v3 home) have **zero** GhostButtonLink/href to `/companies`, `/contacts`, `/opportunities`, `/activities`, `/tasks`, `/dashboard`. Frozen leftovers left untouched: people `/employees`, admin `/admin`, settings `/settings`, analytics `/analytics`. **Closed cluster L13:** in-v3 create quote. Confirmed `POST /api/v1/quotes` (`opportunity_id` query required, `title` default Quote, null body). Fixed FE `createQuote` (was JSON body — would 422). Thin form on `/v3/quotes` (deal picker) and `/v3/crm/[id]` (locked opportunity_id). Empty quotes CTA no longer dead. Success → `/v3/quotes/{id}`. No deals → `/v3/crm`. No line-item designer. Did **not** redo L3/L8/L9/L10/L11/L12. Did **not** touch Emp360. |
| Files | `salesos/frontend/src/lib/api/quotes.ts`; `salesos/frontend/src/lib/api/__tests__/quotes-create.test.ts` (new); `salesos/frontend/src/app/v3/quotes/create-quote-form.tsx` (new); `salesos/frontend/src/app/v3/quotes/page.tsx`; `salesos/frontend/src/app/v3/quotes/__tests__/page.test.tsx` (new); `salesos/frontend/src/app/v3/quotes/__tests__/create-quote-form.test.tsx` (new); `salesos/frontend/src/app/v3/crm/[id]/page.tsx`; `salesos/frontend/src/app/v3/crm/[id]/__tests__/page.test.tsx`; this file |
| Tests | **8/8** quote-create + **53/53** ticks 0–11 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`da6bb178`** (`da6bb178` — `fix: add in-v3 quote create so empty quotes stay on /v3/quotes`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Remaining leaks (frozen) | `/v3/people` header + empty → `/employees`; `/v3/people/[id]` → `/employees/{id}` (Emp360). `/v3/admin` → `/admin`. `/v3/settings` → `/settings`. `/v3/analytics` → `/analytics`. |
| Next slice (tick 12) | Thin **create proposal** on `/v3/proposals` if FE client is aligned: `POST /api/v1/proposals` is real (`opportunity_id` + `quote_id` Query required, null body, 201 `{id,status,sections}`). Needs a quote first (L13). No invented sections UI. Stay in v3. No mocks. Leave Emp360 / admin / settings / analytics frozen. Do not redo L3/L8/L9/L10/L11/L12/L13. |

### Tick 11 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # quotes + createQuote client + deal 360: 10/10 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client + quotes: 53/53 PASS
```

No `git add -A`. No push.

---

## 16. Tick 12 log

| Field | Value |
|-------|-------|
| Done | Slice **L14**: in-v3 create proposal on `/v3/proposals`. Confirmed `POST /api/v1/proposals` (`opportunity_id` + `quote_id` query required, **null body**, 201 `{id,status,sections}`). Added FE `createProposal` (null body). Thin form: deal picker then quote picker (`GET /quotes` without `opportunity_id` returns `[]`). Empty proposals CTA no longer dead. Success → `/v3/proposals/{id}`. No deals → `/v3/crm`. No quotes → `/v3/quotes`. Honest 403. No sections editor. Did **not** redo L3/L8/L9/L10/L11/L12/L13. Did **not** touch Emp360 / admin / settings / analytics. |
| Files | `salesos/frontend/src/lib/api/proposals.ts` (new); `salesos/frontend/src/lib/api/__tests__/proposals-create.test.ts` (new); `salesos/frontend/src/app/v3/proposals/create-proposal-form.tsx` (new); `salesos/frontend/src/app/v3/proposals/page.tsx`; `salesos/frontend/src/app/v3/proposals/__tests__/page.test.tsx` (new); `salesos/frontend/src/app/v3/proposals/__tests__/create-proposal-form.test.tsx` (new); this file |
| Tests | **9/9** proposal-create + **62/62** ticks 0–12 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`14937885`** (`14937885` — `fix: add in-v3 proposal create so empty proposals stay on /v3/proposals`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Remaining leaks (frozen) | `/v3/people` header + empty → `/employees`; `/v3/people/[id]` → `/employees/{id}` (Emp360). `/v3/admin` → `/admin`. `/v3/settings` → `/settings`. `/v3/analytics` → `/analytics`. |
| Next slice (tick 13) | Thin **create review** on `/v3/reviews` if FE client is aligned: `POST /api/v1/reviews` is real (`review_type` + `target_id` + `target_type` Query required, `assigned_to` default `""`, 201 `{id,status,review_type}`). Types on disk: `deal_review` / `manager_review` / `exception_review` / `quote_review` / `proposal_review`. Empty `/v3/reviews` says create with no form. Success → `/v3/reviews/{id}` (route exists). GET `/reviews` lists by tenant (unlike quotes/proposals). Stay in v3. No mocks. Leave Emp360 / admin / settings / analytics frozen. Do not redo L3/L8/L9/L10/L11/L12/L13/L14. |

### Tick 12 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # proposals + createProposal client: 9/9 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client + quotes + proposals: 62/62 PASS
```

No `git add -A`. No push.

---

## 17. Tick 13 log

| Field | Value |
|-------|-------|
| Done | Slice **L15**: in-v3 create review on `/v3/reviews`. Confirmed `POST /api/v1/reviews` (`review_type` + `target_id` + `target_type` query required, `assigned_to` default `""`, **null body**, 201 `{id,status,review_type}`). Added FE `createReview` (null body). Thin form: type picker (5 on-disk types) + target_type (`opportunity`/`quote`/`proposal`) + deal/quote/proposal pickers. Empty reviews CTA no longer dead. Success → `/v3/reviews/{id}`. No deals → `/v3/crm`. No quotes → `/v3/quotes`. No proposals → `/v3/proposals`. Honest 403. No assign/decide workflow on create. Did **not** redo L3/L8–L14. Did **not** touch Emp360 / admin / settings / analytics. |
| Files | `salesos/frontend/src/lib/api/reviews.ts` (new); `salesos/frontend/src/lib/api/__tests__/reviews-create.test.ts` (new); `salesos/frontend/src/lib/api/proposals.ts` (`listProposals` for proposal_review picker); `salesos/frontend/src/app/v3/reviews/create-review-form.tsx` (new); `salesos/frontend/src/app/v3/reviews/page.tsx`; `salesos/frontend/src/app/v3/reviews/__tests__/page.test.tsx` (new); `salesos/frontend/src/app/v3/reviews/__tests__/create-review-form.test.tsx` (new); this file |
| Tests | **10/10** review-create + **72/72** ticks 0–13 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`36eebb65`** (`36eebb65` — `fix: add in-v3 review create so empty reviews stay on /v3/reviews`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Remaining leaks (frozen) | `/v3/people` header + empty → `/employees`; `/v3/people/[id]` → `/employees/{id}` (Emp360). `/v3/admin` → `/admin`. `/v3/settings` → `/settings`. `/v3/analytics` → `/analytics`. |
| Next slice (tick 14) | Thin **create contract** on `/v3/contracts` if FE client is aligned: `POST /api/v1/contracts` is real (`opportunity_id` required via Query or body; `quote_id` optional; `title` optional; 201). Empty `/v3/contracts` says create from an approved quote with no form. Detail route `/v3/contracts/{id}` exists. Stay in v3. No mocks. Leave Emp360 / admin / settings / analytics frozen. Do not invent sign/activate workflow on create. Do not redo L3/L8–L15. `/v3/approvals` empty is HITL (`POST /approvals` JSON body for AI recommendations) — leave until AI flag is evidence-validated. |

### Tick 13 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # reviews + createReview client: 10/10 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client + quotes + proposals + reviews: 72/72 PASS
```

No `git add -A`. No push.

---

## 18. Tick 14 log

| Field | Value |
|-------|-------|
| Done | Slice **L16**: in-v3 create contract on `/v3/contracts`. Confirmed `POST /api/v1/contracts` (`opportunity_id` required via Query or JSON `ContractCreateBody`; `quote_id` / `title` optional; 201). FE `createContract` already sent JSON body — `title` made optional to match API. Thin form: deal picker (required) + optional title + optional quote picker. Empty contracts CTA no longer dead. Success → `/v3/contracts/{id}`. No deals → `/v3/crm`. No quotes does not block (quote optional) + `/v3/quotes`. Honest 403. No sign/activate on create (detail route already has those). Did **not** redo L3/L8–L15. Did **not** touch `/v3/approvals`, Emp360, admin, settings, analytics. |
| Files | `salesos/frontend/src/lib/api/contracts.ts` (`title` optional); `salesos/frontend/src/lib/api/__tests__/contracts-create.test.ts` (new); `salesos/frontend/src/app/v3/contracts/create-contract-form.tsx` (new); `salesos/frontend/src/app/v3/contracts/page.tsx`; `salesos/frontend/src/app/v3/contracts/__tests__/page.test.tsx` (new); `salesos/frontend/src/app/v3/contracts/__tests__/create-contract-form.test.tsx` (new); this file |
| Tests | **10/10** contract-create + **82/82** ticks 0–14 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`663aa7c0`** (`663aa7c0` — `fix: add in-v3 contract create so empty contracts stay on /v3/contracts`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Remaining leaks (frozen) | `/v3/people` header + empty → `/employees`; `/v3/people/[id]` → `/employees/{id}` (Emp360). `/v3/admin` → `/admin`. `/v3/settings` → `/settings`. `/v3/analytics` → `/analytics`. |
| Next slice (tick 15) | Commercial create cluster (L3/L8–L16) is **closed**. Do **not** start `/v3/approvals` (HITL / `POST /approvals` JSON for AI recommendations). Leave Emp360 / admin / settings / analytics frozen. `POST /api/v1/activity-sessions` is real (`target_id` required, `title` default Session) but `/v3/activities` empty CTA is the Gmail/Calendar **feed** (Settings → Integrations) — do not invent a session form that pretends to be that feed. Eligible later: **nav prune** to ~12 MVP items (B1 §8, previously frozen until golden-path create closed). |

### Tick 14 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # contracts + createContract client: 10/10 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client + quotes + proposals + reviews + contracts: 82/82 PASS
```

No `git add -A`. No push.

---

## 19. Tick 15 log

| Field | Value |
|-------|-------|
| Done | Slice **L17**: conservative v3 nav prune (B1 §8). Primary `V3_DOMAIN_NAV` **26 → 12**. Kept: Home, Companies, Contacts, CRM, Activities (real feed), Tasks, Quotes, Proposals, Reviews, Contracts, ICP (live `GET/POST /api/v1/icp/profiles`), Settings (Gmail/integrations — not leak-only). Dropped from primary only (pages stay): People (Emp360 parked), Approvals (HITL — not started), Analytics, Sales Dashboard, My Day, Effectiveness, CS, Admin, Data + MD children, Review Queue. v3 CmdK inherits nav → **27 → 13** destinations (`12` + `/v3/shell` still in `V3_CMD_EXTRA`). Did **not** rewrite legacy `commands.ts`. Did **not** start `/v3/approvals` HITL. Did **not** invent activity-session form. Did **not** touch Emp360 / admin / settings / analytics **pages**. |
| Files | `salesos/frontend/src/components/v3/nav.ts`; `salesos/frontend/src/components/v3/__tests__/nav.test.ts` (new); `salesos/frontend/jest.frontend.cjs` (lucide stub map for isolated runner); `salesos/frontend/jest.frontend.lucide.cjs` (new); this file |
| Tests | **7/7** nav + **89/89** ticks 0–15 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`4f2954e0`** (`4f2954e0` — `fix: prune v3 primary nav to the 12-item MVP golden path`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Remaining leaks (frozen) | `/v3/people` header + empty → `/employees`; `/v3/people/[id]` → `/employees/{id}` (Emp360). `/v3/admin` → `/admin`. `/v3/settings` → `/settings`. `/v3/analytics` → `/analytics`. |
| Next slice (tick 16) | Remove **`/v3/shell` from customer CmdK** (B1 P1; still in `V3_CMD_EXTRA`). Page stays. Do **not** start `/v3/approvals` HITL. Do **not** invent activity-session form. Leave Emp360 / admin / settings / analytics pages frozen. Do not redo L3/L8–L17. |

### Tick 15 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # nav __tests__: 7/7 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client + quotes + proposals + reviews + contracts + nav: 89/89 PASS
```

No `git add -A`. No push.

---

## 20. Tick 16 log

| Field | Value |
|-------|-------|
| Done | Slice **L18**: removed `/v3/shell` from customer v3 CmdK. Emptied `V3_CMD_EXTRA` (was the only extra). Page stays on disk — not advertised. Customer CmdK destinations **13 → 12** (primary nav only). Did **not** un-prune nav. Did **not** start `/v3/approvals` HITL. Did **not** invent activity-session form. Did **not** touch Emp360 / admin / settings / analytics pages. Did **not** rewrite legacy `commands.ts`. |
| Files | `salesos/frontend/src/components/v3/nav.ts`; `salesos/frontend/src/components/v3/__tests__/nav.test.ts`; this file |
| Tests | **8/8** nav + **90/90** ticks 0–16 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`b869aa85`** (`b869aa85` — `fix: stop advertising /v3/shell in the customer v3 command palette`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Remaining leaks (frozen) | `/v3/people` header + empty → `/employees`; `/v3/people/[id]` → `/employees/{id}` (Emp360). `/v3/admin` → `/admin`. `/v3/settings` → `/settings`. `/v3/analytics` → `/analytics`. |
| Next slice (tick 17) | Retarget leftover **legacy CmdK** `go.settings` → `/v3/settings` (B1 P0 #4; Settings is already in the 12-item MVP nav for Gmail/integrations). Do **not** retarget `go.admin` (Admin was pruned from customer chrome). Do **not** start `/v3/approvals` HITL. Do **not** invent activity-session form. Do **not** un-prune nav. Leave Emp360 / admin / settings / analytics **pages** frozen. Wholesale Next redirects of legacy hubs stay out of this loop. Do not redo L3/L8–L18. |

### Tick 16 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs
  # nav __tests__: 8/8 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client + quotes + proposals + reviews + contracts + nav: 90/90 PASS
```

No `git add -A`. No push.

---

## 21. Tick 17 log

| Field | Value |
|-------|-------|
| Done | Slice **L19**: leftover legacy CmdK `go.settings` retargeted `/settings` → `/v3/settings` (B1 P0 #4; Settings already in the 12-item MVP nav). Left `go.admin` on `/admin`. Did **not** start `/v3/approvals` HITL. Did **not** invent activity-session form. Did **not** un-prune nav. Did **not** touch Emp360 / admin / settings / analytics **pages**. |
| Files | `salesos/frontend/src/lib/commands.ts`; `salesos/frontend/src/lib/__tests__/commands.test.tsx`; this file |
| Tests | **4/4** commands (+1 settings/admin) + **91/91** ticks 0–17 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`a4b23298`** (`a4b23298` — `fix: retarget leftover CmdK go.settings to /v3/settings`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Remaining leaks (frozen) | `/v3/people` header + empty → `/employees`; `/v3/people/[id]` → `/employees/{id}` (Emp360). `/v3/admin` → `/admin`. `/v3/settings` → `/settings` (page GhostButtonLinks only; CmdK now `/v3/settings`). `/v3/analytics` → `/analytics`. Legacy CmdK `go.admin` still `/admin`. |
| Next slice (tick 18) | Stop advertising **pruned** destinations in leftover legacy CmdK (`go.v3.approvals`, `go.v3.data*`, `go.data.*`) — pages stay; do **not** start HITL. Do **not** retarget `go.admin`. Do **not** invent activity-session form. Do **not** un-prune nav. Leave Emp360 / admin / settings / analytics **pages** frozen. Wholesale Next redirects of legacy hubs stay out of this loop. Do not redo L3/L8–L19. |

### Tick 17 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs --testPathPattern="<ticks 0-17 scoped>"
  # commands __tests__: 4/4 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client + quotes + proposals + reviews + contracts + nav: 91/91 PASS
```

No `git add -A`. No push.

---

## 22. Tick 18 log

| Field | Value |
|-------|-------|
| Done | Slice **L20**: leftover legacy CmdK no longer advertises pruned Approvals / Data / Review Queue. Removed `go.v3.approvals`, `go.v3.data`, `go.v3.data.companies`, `go.v3.data.people`, `go.v3.data.er`, `go.v3.data.review-queue`, `go.data.companies`, `go.data.people`, `go.data.imports`, `go.data.er` (10 ids). Pages stay on disk. Count **51 → 41**. Kept `go.v3.quotes` / `go.v3.contracts` (in the 12-item MVP nav). Left `go.admin` on `/admin`. Did **not** start `/v3/approvals` HITL. Did **not** invent activity-session form. Did **not** un-prune nav. Did **not** touch Emp360 / admin / settings / analytics **pages**. |
| Files | `salesos/frontend/src/lib/commands.ts`; `salesos/frontend/src/lib/__tests__/commands.test.tsx`; this file |
| Tests | **5/5** commands (+1 pruned-ids) + **92/92** ticks 0–18 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`86a4c176`** (`86a4c176` — `fix: stop advertising pruned approvals and data in leftover CmdK`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Remaining leaks (frozen) | `/v3/people` header + empty → `/employees`; `/v3/people/[id]` → `/employees/{id}` (Emp360). `/v3/admin` → `/admin`. `/v3/settings` → `/settings` (page GhostButtonLinks only; CmdK now `/v3/settings`). `/v3/analytics` → `/analytics`. Legacy CmdK `go.admin` still `/admin`. |
| Next slice (tick 19) | Stop advertising leftover **GTM tip** destinations in leftover CmdK (`go.gtm.*`) — **closed this tick**. |

### Tick 18 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs --testPathPattern="<ticks 0-18 scoped>"
  # commands __tests__: 5/5 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client + quotes + proposals + reviews + contracts + nav: 92/92 PASS
```

No `git add -A`. No push.

---

## 23. Tick 19 log

| Field | Value |
|-------|-------|
| Done | Slice **L21**: leftover legacy CmdK no longer advertises GTM tip destinations. Removed `go.gtm`, `go.gtm.icp`, `go.gtm.market-sizing`, `go.gtm.lead-discovery`, `go.gtm.enrichment`, `go.gtm.website-intelligence`, `go.gtm.outreach`, `go.gtm.verification`, `go.gtm.lookalikes`, `go.gtm.sequences` (10 ids). Pages stay on disk. Customer ICP remains `/v3/icp` in the 12-item MVP nav. Count **41 → 31**. Left `go.admin` on `/admin`. Did **not** start `/v3/approvals` HITL. Did **not** invent activity-session form. Did **not** un-prune nav. Did **not** touch Emp360 / admin / settings / analytics **pages**. |
| Files | `salesos/frontend/src/lib/commands.ts`; `salesos/frontend/src/lib/__tests__/commands.test.tsx`; this file |
| Tests | **6/6** commands (+1 gtm-ids) + **93/93** ticks 0–19 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | **`93fc2899`** (`93fc2899` — `fix: stop advertising leftover GTM tip destinations in leftover CmdK`). **Not pushed.** |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Remaining leaks (frozen) | `/v3/people` header + empty → `/employees`; `/v3/people/[id]` → `/employees/{id}` (Emp360). `/v3/admin` → `/admin`. `/v3/settings` → `/settings` (page GhostButtonLinks only; CmdK now `/v3/settings`). `/v3/analytics` → `/analytics`. Legacy CmdK `go.admin` still `/admin`. |
| Next slice (tick 20) | Stop advertising leftover **Tenant Studio / Marketplace tip** destinations in leftover CmdK (`go.studio.*`, `go.marketplace.listings`) — **closed this tick**. |

### Tick 19 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs --testPathPattern="<ticks 0-19 scoped>"
  # commands __tests__: 6/6 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client + quotes + proposals + reviews + contracts + nav: 93/93 PASS
```

No `git add -A`. No push.

---

## 24. Tick 20 log

| Field | Value |
|-------|-------|
| Done | Slice **L22**: leftover legacy CmdK no longer advertises Tenant Studio / Marketplace tip destinations. Removed `go.studio.custom-fields`, `go.studio.scoring`, `go.studio.permissions`, `go.studio.workflows`, `go.studio.notifications`, `go.studio.branding`, `go.studio.territories`, `go.studio.ai-model-tiers`, `go.studio.prompt-library`, `go.studio.ai-policies`, `go.studio.ai-memory`, `go.marketplace.listings` (12 ids). Pages stay on disk. Count **31 → 19**. Left `go.admin` on `/admin`. Did **not** start `/v3/approvals` HITL. Did **not** invent activity-session form. Did **not** un-prune nav. Did **not** touch Emp360 / admin / settings / analytics **pages**. |
| Files | `salesos/frontend/src/lib/commands.ts`; `salesos/frontend/src/lib/__tests__/commands.test.tsx`; this file |
| Tests | **7/7** commands (+1 studio/marketplace-ids) + **94/94** ticks 0–20 scoped **PASS** (`%TEMP%\salesos-jest-runner` + `jest.frontend.cjs`). Browser **not validated**. Host `npm test` **not validated**. No pytest (no BE). |
| Commit | *(pending this tick)* |
| Validation | Scoped Jest **build validated** (isolated runner). Browser **not validated**. **production no-go** unchanged. Phase 7 still **BLOCKED**. `feature_ai_copilot` untouched. |
| Remaining leaks (frozen) | `/v3/people` header + empty → `/employees`; `/v3/people/[id]` → `/employees/{id}` (Emp360). `/v3/admin` → `/admin`. `/v3/settings` → `/settings` (page GhostButtonLinks only; CmdK now `/v3/settings`). `/v3/analytics` → `/analytics`. Legacy CmdK `go.admin` still `/admin`. |
| Next slice (tick 21) | Stop advertising leftover **Integrations Studio tip** destinations in leftover CmdK (`go.integrations` + `go.integrations.*` step tips) — pages stay; Gmail OAuth is MVP via `/v3/settings`, not this studio. Do **not** retarget `go.admin`. Do **not** start `/v3/approvals` HITL. Do **not** invent activity-session form. Do **not** un-prune nav. Leave Emp360 / admin / settings / analytics **pages** frozen. Wholesale Next redirects of legacy hubs stay out of this loop. Do not redo L3/L8–L22. |

### Tick 20 commands

```text
# Isolated runner (not committed; reused from tick 1 — no host npm install):
node %TEMP%\salesos-jest-runner\node_modules\jest\bin\jest.js --config jest.frontend.cjs --testPathPattern="<ticks 0-20 scoped>"
  # commands __tests__: 7/7 PASS
  # employee + commands + companies + contacts + contact [id] + crm + crm [id] + company [id] + tasks + task [id] + activities + pipeline client + quotes + proposals + reviews + contracts + nav: 94/94 PASS
```

No `git add -A`. No push.

---

*Loop state. Not a Production GO claim.*
