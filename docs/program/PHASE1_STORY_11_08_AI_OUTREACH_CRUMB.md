# STORY-11-08 — AI Outreach (AI-Lead / CAP-103)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> CI uses `FixtureOutreachGenerator` + governed prompt-registry key `gtm.ai_outreach.v1`.  
> Live LLM / SMTP / LinkedIn / WhatsApp / RAG GO — **not claimed**.  
> `feature_ai_copilot` default remains **False**. FE Decision package remains **STUB**.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `OutreachDraft` / `OutreachRequest` (draft_only delivery) |
| Prompt path | Governed CAP-023-shaped key `gtm.ai_outreach.v1` (platform LLM spend path) |
| Generator | `FixtureOutreachGenerator` deterministic subject/body |
| HTTP | `POST/GET /api/v1/gtm/outreach` + `/meta` + `/{id}` |
| Channel | Email drafts only — LI/WA deferred |
| Tests | Governed prompt guard, channel/intent guards, tenant isolation, flag False |

## Acceptance

Routed through existing governed Prompt Registry — not a disconnected copy tool — covered in CI via fixture.

## Unblocks

- **FE-S11-08** AI Outreach UI under `/gtm/outreach`

## Non-goals

- Live SMTP / mailbox delivery
- LinkedIn / WhatsApp channels
- Live OpenAI/Claude inference or enabling `feature_ai_copilot`
- RAG GO / Production GO
