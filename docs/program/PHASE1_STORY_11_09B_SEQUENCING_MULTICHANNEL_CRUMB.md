# STORY-11-09b — Sequencing LinkedIn + WhatsApp channels (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> LinkedIn via **compliant partner API shape only** — no browser/ToS-risk automation.  
> Live SMTP / LinkedIn / WhatsApp network sends — **not claimed**.

## Landed

| Piece | Detail |
|-------|--------|
| Channels | `email`, `linkedin`, `whatsapp` on `SequenceStep` |
| Senders | `MemLinkedInPartnerSender` / `MemWhatsAppPartnerSender` / email recorded |
| Guard | Forbidden modes: browser_automation, scraping, unofficial_api, … |
| HTTP | Same `/api/v1/gtm/sequences` — enroll accepts `linkedin` / `whatsapp` handles |
| Tests | Multi-channel advance, URN/E.164 required, ToS-risk mode rejected |

## Acceptance

LinkedIn via compliant partner API only — no ToS-risk automation — covered in CI.

## Non-goals

- Live partner network calls
- Browser/session-cookie LinkedIn automation
- Production GO / territories invent
