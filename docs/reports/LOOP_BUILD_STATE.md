# SalesOS 4h Build Loop — State

**Date:** 2026-09-12  
**Branch:** `fix/login-and-keys`  
**Workspace:** `D:\AISalesOS`  
**Tick:** 3 **COMPLETE**  
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
| L5 | Backend-without-UI that is **MVP-blocking** — thin v3 surface **only if API is real** | **DEFER** | Next same-class hole: **create deal** on `/v3/companies/[id]` / CRM. Confirm real POST before UI. Residual: `/v3/contacts/[id]` still has GhostButtonLink to `/contacts` (not the list empty CTA). |
| L8 | **Create contact on `/v3/contacts`** | **DONE** (tick 3) | Thin `CreateContactForm` → `POST /api/v1/contacts` (`name` + `company_id` required). Empty state stays in v3 (no `/contacts` leak). Success navigates to `/v3/contacts/{id}`. Honest 403/API errors. Company picker via `GET /api/v1/companies`. No mocks. |

### P1 — scoped proof

| ID | Item | Status |
|----|------|--------|
| L6 | Scoped tests for files we touch | **DONE** (tick 3) — **15/15 PASS** via isolated temp Jest (host `node_modules` still incomplete; no `npm install`). Tick 0–1 regression 9 + contacts 6. No Docker pytest (FE-only). |
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
| GhostButtonLink “Open legacy …” on other v3 pages | B1 | L3 closed `/companies` empty leak; tick 3 closed `/contacts` list empty leak. Residual: `/v3/contacts/[id]` still links `/contacts`. |

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

## 6. Tick 2 note

Tick 2 was assigned L6 / host Jest (`npm install`). This tick did **not** fight host `npm install` and reused `%TEMP%\salesos-jest-runner`. No Tick 2 code files claimed here.

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

*Loop state. Not a Production GO claim.*
