"""STORY-09-03 — InteractionNote sync + AI-GR-001 PII scrub before RAG."""

from __future__ import annotations

import pytest

from app.modules.integration_hub.note_sync import sync_interaction_notes
from app.modules.integration_hub.odoo_adapter import InMemoryOdooRpc, OdooAdapter
from app.modules.integration_hub.types import WriteBackRequest
from intelligence.guardrails import detect_pii_leakage, scrub_pii_for_rag


def test_ai_gr_001_scrubs_phone_email_id_iban() -> None:
    raw = (
        "Called Name: Sara Al-Harbi at +966 50 123 4567 "
        "(email sara.harbi@example.com). Iqama 2123456789. "
        "IBAN SA0380000000608010167519."
    )
    scrubbed = scrub_pii_for_rag(raw)
    assert scrubbed.redaction_count >= 4
    assert detect_pii_leakage(scrubbed.text) == []
    assert "[PHONE]" in scrubbed.text
    assert "[EMAIL]" in scrubbed.text
    assert "[NATIONAL_ID]" in scrubbed.text
    assert "[IBAN]" in scrubbed.text
    assert "[NAME]" in scrubbed.text
    assert "501234567" not in scrubbed.text.replace(" ", "")
    assert "sara.harbi@example.com" not in scrubbed.text


def test_production_shaped_fixture_corpus_zero_pii_leakage() -> None:
    """AC: scrub verified on ≥100 production-shaped note samples (fixture corpus).

    Honesty: synthetic fixtures mirroring production note shapes (phones,
    emails, Iqama, IBAN) — not a live production dump. Live ≥100 ops audit
    remains residual before RAG Production GO.
    """
    corpus: list[str] = []
    for i in range(100):
        phone = f"+9665{i % 10}{i:07d}"[:13]
        # Keep national ids as 1/2 + 9 digits.
        nid = f"{1 + (i % 2)}{i:09d}"[:10]
        corpus.append(
            f"<p>Follow-up #{i}: Name: Contact {i} "
            f"phone {phone} email user{i}@muhide-sample.test "
            f"id {nid} IBAN SA03{i:020d}</p>"
        )
    assert len(corpus) == 100
    leaks = 0
    for note in corpus:
        out = scrub_pii_for_rag(note)
        found = detect_pii_leakage(out.text)
        if found:
            leaks += 1
    assert leaks == 0


@pytest.mark.asyncio
async def test_mail_message_sync_scrubs_before_rag() -> None:
    rpc = InMemoryOdooRpc()
    adapter = OdooAdapter(rpc=rpc)
    await adapter.write_back(
        credential_ref="vault://t/odoo",
        config={},
        request=WriteBackRequest(
            model="mail.message",
            external_id="9001",
            payload={
                "subject": "Call note",
                "body": (
                    "<p>Spoke with Name: Ahmed about renewal. "
                    "Reach him on 0501234567 or ahmed@client.example.</p>"
                ),
                "message_type": "comment",
                "model": "res.partner",
                "res_id": 42,
                "author_id": [7, "Rep"],
            },
        ),
    )
    pulled = await adapter.pull_incremental(
        credential_ref="vault://t/odoo",
        config={},
        model="mail.message",
        cursor=None,
        limit=20,
    )
    assert len(pulled.records) == 1
    batch = await sync_interaction_notes(pulled.records, sync_run_id="sr-note-1")
    assert len(batch.synced) == 1
    item = batch.synced[0]
    assert item.timeline_event_type == "interaction_note"
    assert detect_pii_leakage(item.rag_text) == []
    assert "0501234567" not in item.rag_text
    assert "ahmed@client.example" not in item.rag_text
    assert item.record.payload["rag_text"] == item.rag_text
    # RAG field must not equal raw unscrubbed HTML body.
    assert "0501234567" in item.record.payload["body_raw"]
    assert item.rag_text != item.record.payload["body_raw"]
