# STORY-11-06 — Contact Verification (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> CI uses in-memory `MemVerificationConnector` (`fake_verify`).  
> Live NeverBounce / ZeroBounce / Twilio Lookup — **not claimed**.  
> Live **141,221** Postgres / territories — **not claimed**.

## Landed

| Piece | Detail |
|-------|--------|
| Port | `VerificationConnector` — single commodity swap-in interface |
| Engine | Email + phone channel verdicts (`valid`/`invalid`/`unknown`/`risky`) |
| Default | `fake_verify` MemVerificationConnector |
| HTTP | `POST/GET /api/v1/gtm/verification` + `/meta` |
| Tests | Valid/invalid/risky, connector swap-in, tenant isolation |

## Acceptance

Single connector interface, commodity swap-in — covered in CI.

## Non-goals

- Live vendor verification network calls
- LinkedIn channel (ToS risk — deferred)
- Territories BE (STORY-10-05)
- Production GO
