# 182 — G8 workstream opened (2026-09-30)

**Decided by:** Ragheed (PO), in chat: «G8 يلا افتحها ونشوف المهام عشان ننفذها».
**Effect:** The production-readiness **work list** is open. Tasks below may be executed.
**Not the effect:** Production is **NOT APPROVED**. No production database write, no catalog ingest into `salesos`, no Railway deploy, no `feature_ai_copilot` flip, no auto-merge of G2/G4.

Report 91 §6 said G8 was not asked. This record is the ask. It does not close G2, G3, G4, G5, G9–G16, and it does not promote register rows 40, 46, 52, 53, 59, 60, 131, 132.

## What “open” means

G8 was never a single switch. It is the list of evidence that must exist before a later production decision. Opening it authorizes that list. Checking a box still needs its own proof.

## Task board

### A. Engineering, this checkout, no production write

| # | Task | State on 2026-09-30 |
|---|---|---|
| A1 | Owner refresh re-checks `is_platform_owner` before rotating | Coded on D:; unit test 3/3; pilot API on port 8001 restarted. Uncommitted. |
| A2 | Organization-registration owner approval | Coded, live on the pilot database only. Uncommitted. |
| A3 | Approvals UI sends `decided_by: "current-user"` | Server `decide_approval` uses the JWT `user_id` and ignores that field. Safe to delete from the client. Not done. |
| A4 | Contracts UI sends `signed_by: "current-user"` | Not assessed against the sign route. Inspect before editing. |
| A5 | Phase 7 reviewer identity and ER `tenant_id` from the client | Inspect only. No auto-merge, no auto-adjudication. |
| A6 | Seller journey in the browser: register, invite, owner-login denied for a tenant admin | Partially exercised on the local pilot. Full invite path not run. |

### B. Operator (Ragheed or Railway), not a code patch

| # | Task | Blocker |
|---|---|---|
| B1 | After a future migration of the **target** environment, set `is_platform_owner` on the named owner | Do not write production `salesos` until that migration is an explicit step. Local pilot already has ragheed marked. |
| B2 | Build the Railway image from `df41b2df` (JWKS dir `/data/jwks`) and mount a writable volume there | Image was never built. |
| B3 | Confirm the live Railway `preDeployCommand` is `alembic upgrade head` (root `railway.json` already says that) | Live dashboard was not opened this session. |
| B4 | Enable the Railway managed backup schedule | Railway owner access. |
| B5 | Sultan invites `feras@muhide.com`, `shahir@muhide.com`, `maria@muhide.com`, `nojood@muhide.com` as `user` | Sultan’s session. ibrahem still has no email. |

### C. External or a product decision — coding does not close these

| # | Gate | What is left |
|---|---|---|
| C1 | G2 / G4 / G5 / short-CR | Human data review. Catalog of 296,746 companies stays in `salesos_test`. |
| C2 | Catalog visibility | `md_global_companies` has no tenant RLS. Any role with `master-data:READ` sees the whole list once it is loaded. Decide shared-catalog vs per-tenant before any ingest. |
| C3 | G13 PDPL | Hosting is outside KSA. Needs a legal statement. |
| C4 | G14 SOC2 | External auditor. |
| C5 | G9 / G12 | Google, Microsoft, and GitHub apps and credentials. |
| C6 | G15 / G16 | Customer Success lifecycle and adaptive ICP need real usage data and a product rule. |
| C7 | AI | `feature_ai_copilot` stays false until a production provider contract exists. |
| C8 | Stripe, Maps | Stripe stays fail-closed. Google Maps stays excluded as a lead source. |
| C9 | Git history | HS256 token in `3de118a5` is on the remote. Rotation or history purge is a separate owner decision. |

## Next execution

A3 is the first code change that is already specified and does not touch a database. A4 and A5 are inspect-first. B and C are not started by this record.

## Sign-off

| Field | Value |
|---|---|
| Decided at | 2026-09-30 |
| Production | NOT APPROVED |
| Reconfirmed | 2026-09-30, PO: «حدث الإنتاج: غير معتمد» |
| Database writes | None for this record |
