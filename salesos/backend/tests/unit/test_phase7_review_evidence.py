"""Report 116 W1 — typed review evidence model.

Locks in the guarantees the typed `ReviewEvidence` model is supposed to give
over the old free-form `evidence: dict[str, Any]` bag:
  1. `reason` is required (closes the "591/643 rows have no error_type" gap).
  2. Unknown keys are rejected outright (`extra="forbid"`), not silently
     dropped or silently stored — a differently-named key can no longer
     smuggle a value past a key-only blocklist.
  3. PII is impossible by construction for the typed, non-free-text fields,
     and the two free-text fields (`reason`, `detail`) are scanned for
     email/phone-shaped values, not just forbidden key names.
  4. `record_disposition` enforces this the same way whether the caller sends
     a `ReviewEvidence` instance or an equivalent plain dict (script/test
     callers), so neither path can bypass the guarantee.
  5. The `test:` subject-key bypass in `_resolve_company_link` only fires
     when a service is explicitly constructed with
     `unsafe_allow_test_subjects=True` — never for a normally-constructed
     service, regardless of what subject_key a caller sends.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.master_data.phase7.review_queue import ReviewQueueService
from app.modules.master_data.phase7.schemas import ReviewEvidence, ReviewQueueDisposition


def test_reason_is_required() -> None:
    with pytest.raises(ValidationError, match="reason"):
        ReviewEvidence()  # type: ignore[call-arg]


def test_reason_rejects_empty_string() -> None:
    with pytest.raises(ValidationError):
        ReviewEvidence(reason="")


def test_unknown_key_is_rejected_not_silently_dropped() -> None:
    with pytest.raises(ValidationError, match="reviewed_via"):
        ReviewEvidence(reason="ok", reviewed_via="workbook")  # type: ignore[call-arg]


def test_unknown_key_rejected_even_when_it_looks_like_a_pii_field_name() -> None:
    """A key not on the whitelist is refused outright, regardless of what it
    is called — this is the fix for the old blocklist's blind spot (a value
    could hide under an unlisted, innocuous-looking key)."""
    with pytest.raises(ValidationError):
        ReviewEvidence(reason="ok", contact_phone="0555555555")  # type: ignore[call-arg]


@pytest.mark.parametrize("field", ["reason", "detail"])
def test_email_in_free_text_field_is_rejected(field: str) -> None:
    kwargs = {"reason": "ok", "detail": "ok"}
    kwargs[field] = "please contact ali@example.com about this"
    with pytest.raises(ValidationError, match="email"):
        ReviewEvidence(**kwargs)


@pytest.mark.parametrize("field", ["reason", "detail"])
def test_phone_number_in_free_text_field_is_rejected(field: str) -> None:
    kwargs = {"reason": "ok", "detail": "ok"}
    kwargs[field] = "call +966 55 123 4567 to confirm"
    with pytest.raises(ValidationError, match="phone"):
        ReviewEvidence(**kwargs)


def test_identifier_fields_are_not_phone_scanned() -> None:
    """Typed, constrained identifier fields (pair_id, cr_class, ...)
    legitimately contain long digit runs (e.g. real P3 pair ids look like
    "FZ-00001-315216-318033") and must not be flagged as phone numbers — their
    PII-safety comes from being a fixed-purpose field, not from a value scan."""
    ReviewEvidence(reason="ok", pair_id="FZ-00001-315216-318033",
                   candidate_domain="example.com", cr_class="SUSPICIOUS_MULTI")


def test_typed_fields_have_no_slot_for_natural_person_pii() -> None:
    """There is no field named name/email/phone/address at all — confirms the
    "impossible by construction" claim structurally, not just behaviorally."""
    forbidden = {"name", "full_name", "email", "phone", "address", "contact_name"}
    assert forbidden.isdisjoint(ReviewEvidence.model_fields.keys())


def test_error_type_is_constrained_to_the_established_vocabulary() -> None:
    with pytest.raises(ValidationError):
        ReviewEvidence(reason="ok", error_type="SOMETHING_ELSE")  # type: ignore[arg-type]
    ReviewEvidence(reason="ok", error_type="WRONG_DOMAIN")


def test_disposition_model_requires_evidence() -> None:
    with pytest.raises(ValidationError, match="evidence"):
        ReviewQueueDisposition(disposition="CONFIRM", reviewer="tester")  # type: ignore[call-arg]


def test_disposition_model_rejects_pii_in_notes() -> None:
    with pytest.raises(ValidationError, match="email"):
        ReviewQueueDisposition(
            disposition="CONFIRM", reviewer="tester",
            notes="reach out to ali@example.com",
            evidence=ReviewEvidence(reason="ok"),
        )


def test_record_disposition_accepts_plain_dict_and_validates_it(monkeypatch) -> None:
    """Direct script/test callers pass a plain dict, not a ReviewEvidence
    instance — the service must validate it exactly the same way the HTTP
    layer would, so a script cannot bypass the required-reason guarantee."""
    svc = ReviewQueueService.__new__(ReviewQueueService)  # bypass __init__, no DB needed
    svc._unsafe_allow_test_subjects = False

    async def _noop_write_db(self):
        return None

    monkeypatch.setattr(ReviewQueueService, "_assert_write_db", _noop_write_db)
    import asyncio

    with pytest.raises(ValidationError, match="reason"):
        asyncio.run(svc.record_disposition(
            queue_type="TRIAGE", subject_key="x", disposition="CONFIRM",
            reviewer="tester", evidence={},
        ))


def test_service_defaults_to_disallowing_test_subject_bypass() -> None:
    """A normally-constructed service can never activate the `test:`
    subject-key bypass — the flag defaults False and must be opted into
    explicitly (report 116 W1 #3: no backdoor reachable from production code
    regardless of what subject_key a caller sends)."""
    assert ReviewQueueService.__init__.__kwdefaults__["unsafe_allow_test_subjects"] is False
