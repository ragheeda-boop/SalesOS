# STORY-11-09 — Sequencing Engine, email channel (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Email channel only — LinkedIn / WhatsApp deferred (Sprint-18 scope).  
> No live SMTP send claimed (`sent` = recorded state + Task/Activity bindings).  
> No territories / live ML / 141221 invent.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `SequenceDefinition` / `SequenceEnrollment` / Task+Activity bindings |
| Engine | State machine: enroll → advance → complete; pause/resume/cancel |
| Binding | Each advanced step emits `BoundTaskRef` + `BoundActivityRef` |
| HTTP | `POST/GET /api/v1/gtm/sequences` + enrollments + advance/pause/resume/cancel |
| Tests | Email-only channel guard, Task/Activity bind, tenant isolation |

## Acceptance

Bound to existing Activity/Task objects (shaped refs; no parallel CRM model) — covered in CI.

## Non-goals

- Live SMTP / mailbox delivery
- LinkedIn / WhatsApp channels
- Territories BE / live 141221
- Production GO
