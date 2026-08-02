# STORY-09-03 — InteractionNote / TimelineEvent + PII scrub (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented Odoo secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Unlinked badge list API remains 09-01 residual (not scoped here).

## Landed

| Piece | Detail |
|-------|--------|
| Pull | `OdooAdapter.pull_incremental(model="mail.message")` + message fields |
| Sync | `sync_interaction_notes` → InteractionNote / TimelineEvent projection |
| PII | AI-GR-001 `scrub_pii_for_rag` (phone, email, national ID, IBAN, card, labeled name) |
| RAG gate | `rag_text` is scrubbed only; raw body kept as `body_raw` for sync audit, never as RAG input |
| Tests | Unit scrub + ≥100 production-shaped fixture corpus (zero leakage) |

## Acceptance

PII scrubbing verified against production-shaped note samples before RAG —
covered by `test_production_shaped_fixture_corpus_zero_pii_leakage` + mail.message sync test.

**Residual:** Live ≥100 real production note ops audit before RAG Production GO
(TEST_STRATEGY / PRODUCTION_READINESS). Fixture corpus ≠ live dump.

## Non-goals

- Partitioned `interaction_notes` ORM + FORCE RLS (follow-on; POLICY_COUNT discipline)
- Unlinked cr_number badge list API
- Live Odoo password / vault material in repo
- RAG Production GO / AI Coach live feed claim
