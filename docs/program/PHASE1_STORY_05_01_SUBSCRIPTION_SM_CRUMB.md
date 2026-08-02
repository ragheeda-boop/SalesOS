# Phase 1 — STORY-05-01 Subscription state machine (Stream A)

> **Honesty:** Not Production GO. No Stripe (STORY-05-02). DEC-085 untouched. BE-only.  
> **CPO review:** transition matrix below is the review artifact for Sprint-05 AC.

## Object

| Item | Detail |
|------|--------|
| OBJ-321 | `subscriptions` table — Owner-only, **no RLS** |
| Alembic | `c3a9f12d4e80` (revises `f6b2e84c1a90`) — see [`PHASE1_A_STORY_05_01_MIGRATE_NOTES.md`](PHASE1_A_STORY_05_01_MIGRATE_NOTES.md) |
| Pure SM | `app/modules/billing/state_machine.py` |
| Service | `app/modules/billing/service.py` — ensure on provision + apply_event |
| Owner API | `GET/POST /api/v1/admin/billing/subscriptions/{tenant_id}[/transition]` |
| Tests | `tests/unit/test_subscription_state_machine.py` |

## Happy path (TEST_STRATEGY)

```text
trial → activate → active → mark_past_due → past_due → suspend → suspended → reactivate → active → churn → churned
```

## Full event matrix

| From \ Event | activate | mark_past_due | suspend | reactivate | churn | resubscribe_trial | resubscribe_active |
|---|---|---|---|---|---|---|---|
| trial | active | — | suspended | — | churned | — | — |
| active | — | past_due | suspended | — | churned | — | — |
| past_due | active | — | suspended | — | churned | — | — |
| suspended | — | — | — | active | churned | — | — |
| churned | — | — | — | — | — | trial | active |

## Provision wiring

`TenantProvisioningService.provision_workflow` calls `SubscriptionService.ensure_for_tenant`:

- `trial_ends_at` set → status `trial`
- else → status `active` (sales-assisted)

Idempotent: one row per `tenant_id` (`uq_subscriptions_tenant_id`).

## Non-goals

- Stripe checkout / webhooks (STORY-05-02)
- UsageMeter (STORY-05-03)
- Dunning auto-suspend job (STORY-05-04)
- Coupling `Subscription.status` ↔ `Tenant.provisioning_status` (follow-on)
- Production GO / GA GO
