# Phase 1 Launch — STORY-04-01 Pre-task Package (A1)

> **Status:** A1 ACCEPTED · A2 DRAFT LANDED (6b2e84c1a90) — Docker upgrade proof pending  
> **Triggered by:** TRIGGER_POST_PHASE0_PLAN 2026-08-02 — Phase 0 checklist **54/54** (DEC-155)  
> **Story:** STORY-04-01 Tenant extension — docs/program/SPRINT_PLAN/Sprint-04.md  
> **Honesty:** Schema/API wired; non-prod migrate proof not yet run. **No Production GO.**

---

## 1. Goal

Extend Tenant with Owner Platform fields required for calendar Sprint 04:

| Field | Proposed type | Notes |
|-------|---------------|-------|
| plan_id | String(64) nullable → required after backfill | Links to plan tier / catalog |
| 
egion | String(32) nullable | e.g. me-central-1 |
| data_residency | String(32) nullable | Policy tag; not invent GA residency engine |
| provisioning_status | String(32) default pending | Enum-like: pending / ctive / suspended / ailed |
| 	rial_ends_at | DateTime(timezone=True) nullable | Optional trial window |

## 2. Constraints (non-negotiable)

1. **DEC-085** set_config / RLS patterns untouched.  
2. New columns on 	enants inherit existing Category-A tenant RLS — no BYPASSRLS.  
3. Alembic only (no Prisma). Migration must be upgrade/downgrade safe.  
4. eature_ai_copilot remains default **False**.  
5. Do not claim Production GO / GA GO.

## 3. Delivery sequence

| Step | Owner | Output |
|------|-------|--------|
| A1 (this) | Backend | Field contract + constraints — **DONE** |
| A2 | Backend | Alembic 6b2e84c1a90 + ORM/API — **LANDED** (Docker proof pending) |
| A3 | Backend | STORY-04-02 provisioning skeleton — **LANDED** with A2 |
| B1/B2 | Frontend | Inventory + read-path — **LANDED** (8fd06e) |
| D3 | Validation | Adversarial RLS still PASS after A2 migrate |

## 4. Explicit non-claims

- No production Alembic upgrade in this package.  
- No Stripe / billing.  
- Production GA remains **NO-GO** per ga-engineering-audit.
