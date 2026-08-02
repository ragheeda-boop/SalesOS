# STORY-10-08 — Notification Rules Studio (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Compiles to existing `rules_engine` `send_notification` (no second interpreter).

## Landed

| Piece | Detail |
|-------|--------|
| Models | `NotificationRule` (event / channels / recipients / conditions) |
| Engine | `compile_notification_rule` + `route_notification_event` |
| Store | `MemNotificationRulesStore` tenant-scoped |
| HTTP | `GET/POST /api/v1/studio/notification-rules` + `…/route` + `…/compile` |
| Tests | Match/miss routing, compile actions, inactive skip, tenant isolation |

## Acceptance

Tenant-defined notification routing live — covered by route suite.

## Non-goals

- FE `/studio/notifications` page
- SMTP/webhook delivery (routing plan only; EmailService unchanged)
- Postgres persistence / new RLS
- Territories BE (STORY-10-05) — not invented
- Production GO
