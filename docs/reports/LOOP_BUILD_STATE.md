# SalesOS 4h Build Loop — State

**Date:** 2026-09-12  
**Branch:** `fix/login-and-keys`  
**Workspace:** `D:\AISalesOS`  
**Tick:** 8 **COMPLETE**  
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
| L5 | Backend-without-UI that is **MVP-blocking** — thin v3 surface **only if API is real** | **DEFER** | Create company / contact / deal / task closed (L3/L8/L9/L11). Contact 360 `/contacts` leak closed (tick 5). Company 360 `/companies/{id}` leak closed (tick 7). `/v3/activities` `/activities` leak closed (tick 7). Residual Legacy company on `/v3/contacts/[id]` and `/v3/tasks/[id]` closed (tick 8). Pipeline create: POST `/api/v1/pipelines` is real but body-less (default sales pipeline only); FE has GET `listPipelines` only — no `createPipeline` client. Do not invent name/stages UI. |
| L8 | **Create contact on `/v3/contacts`** | **DONE** (tick 3) | Thin `CreateContactForm` → `POST /api/v1/contacts` (`name` + `company_id` required). Empty state stays in v3 (no `/contacts` leak). Success navigates to `/v3/contacts/{id}`. Honest 403/API errors. Company picker via `GET /api/v1/companies`. No mocks. |
| L9 | **Create deal on `/v3/companies/[id]` + `/v3/crm`** | **DONE** (tick 4) | Thin `CreateDealForm` → existing `createOpportunity` (`POST /api/v1/opportunities` query: `company_id`, `name`, optional `value` default 0). Company tab locks `company_id`. CRM empty CTA no longer bounces to companies / “legacy pipeline”. Success → `/v3/crm/{id}`. Honest 403/API errors. No mocks. Did not invent `owner_id` UI (FE client does not send it). |
| L10 | Residual GhostButtonLink `/contacts` on `/v3/contacts/[id]` | **DONE** (tick 5) | Header “Legacy contacts” removed (exits shell; “Back to list” already `/v3/contacts`). Company-tab empty CTA retargeted `/contacts` → `/v3/companies` (“Browse companies”). Honest no-`company_id` copy. Did not invent link-company. Left company-tab “Legacy company” (`/companies/{id}`) — not this hole. |
| L11 | **Create task on `/v3/tasks`** | **DONE** (tick 6) | Thin `CreateTaskForm` → existing `createTask` (`POST /api/v1/tasks`: required `title`; optional `priority` default `medium`, `source` default `manual`, `company_id`, `opportunity_id`, `due_date`). Empty CTA no longer bounces to companies. Success → `/v3/tasks/{id}` (real detail route). Honest 403/API errors. No mocks. Extended FE client with last-arg `dueDate` so the real field is not dropped. |

### P1 — scoped proof

| ID | Item | Status |
|----|------|--------|
| L6 | Scoped tests for files we touch | **DONE** — Tick 8 isolated runner **39/39 PASS** (ticks 0–8). Tick 2 host Jest **4/4 PASS** on the two Tick 0 files only (`commands` + `employee`). Host `npm install` still **not clean**; `jest.frontend.cjs` prefers `%TEMP%\salesos-jest-runner`. No Docker pytest (FE-only). |
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
| Nav prune to ~12 MVP items | B1 §8 | After golden-path create |
| `/v3/shell` remove from CmdK | B1 P1 | Later |
| GhostButtonLink “Open legacy …” on other v3 pages | B1 | L3 closed `/companies` empty leak; tick 3 closed `/contacts` list empty leak; tick 4 closed CRM/company-deal empty CTAs; tick 5 closed `/v3/contacts/[id]` `/contacts` leak; tick 6 closed `/v3/tasks` empty bounce; tick 7 closed company 360 `/companies/{id}` + `/v3/activities` `/activities`; tick 8 closed Legacy company on `/v3/contacts/[id]` and `/v3/tasks/[id]`. Admin/settings/analytics/people (`/employees`) legacy hubs still frozen. |

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
| Commit | *(pending named-path commit this tick)* |
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

*Loop state. Not a Production GO claim.*
