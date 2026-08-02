# Phase 1 Launch — STORY-04-01 Pre-task Package (A1)

> **Status:** READY FOR REVIEW (Backend stream)  
> **Triggered by:** TRIGGER_POST_PHASE0_PLAN 2026-08-02 — Phase 0 checklist **54/54** (DEC-155)  
> **Story:** STORY-04-01 Tenant extension — `docs/program/SPRINT_PLAN/Sprint-04.md`  
> **Honesty:** Pre-task only. No migration applied this land. **No Production GO.**

---

## 1. Goal

Extend `Tenant` with Owner Platform fields required for calendar Sprint 04:

| Field | Proposed type | Notes |
|-------|---------------|-------|
| `plan_id` | `String(64)` nullable → required after backfill | Links to plan tier / catalog |
| `region` | `String(32)` nullable | e.g. `me-central-1` |
| `data_residency` | `String(32)` nullable | Policy tag; not invent GA residency engine |
| `provisioning_status` | `String(32)` default `pending` | Enum-like: `pending` / `active` / `suspended` / `failed` |
| `trial_ends_at` | `DateTime(timezone=True)` nullable | Optional trial window |

## 2. Constraints (non-negotiable)

1. **DEC-085** `set_config` / RLS patterns untouched.  
2. New columns on `tenants` (or equivalent Tenant table) inherit existing Category-A tenant RLS — no BYPASSRLS.  
3. Alembic only (no Prisma). Migration must be upgrade/downgrade safe.  
4. `feature_ai_copilot` remains default **False**.  
5. Do not claim Production GO / GA GO.

## 3. Proposed delivery sequence

| Step | Owner | Output |
|------|-------|--------|
| A1 (this) | Backend | Field contract + constraints |
| A2 | Backend | Alembic revision + Docker upgrade/downgrade proof (non-prod) |
| A3 | Backend | STORY-04-02 provisioning skeleton pre-task (after A1 stable) |
| B1/B2 | Frontend | Inventory + read-path stubs after A1 contract |
| D3 | Validation | Adversarial RLS still PASS after A2 |

## 4. Open design questions (human/ARB if contested)

1. `plan_id` FK to a plans table vs opaque string — **default: opaque string** for Sprint 04 skeleton.  
2. `provisioning_status` as Postgres ENUM vs check constraint vs app-validated string — **default: string + app validation**.  
3. Backfill for existing Muhide tenant — **default: `provisioning_status='active'`, other fields null**.

## 5. Explicit non-claims

- No schema land in this file.  
- No UI.  
- No Stripe / billing.  
- Production GA remains **NO-GO** per ga-engineering-audit.
