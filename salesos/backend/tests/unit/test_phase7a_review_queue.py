"""Unit tests for Phase 7-A review-queue tooling (pure logic + record-only rules)."""

from http import HTTPStatus

import pytest
from pydantic import ValidationError

from app.modules.master_data.phase7.review_queue import (
    _DISPOSITIONS,
    QUEUE_P1,
    QUEUE_P2_SAMPLE,
    QUEUE_MA_UNRESOLVED,
    QUEUE_P3,
    QUEUE_SHORT_CR,
    QUEUE_TRIAGE,
    ReviewQueueService,
)
from app.modules.master_data.phase7.schemas import (
    MAUnresolvedDisposition,
    P1CandidateDisposition,
    P2SampleDisposition,
    P3PairDisposition,
    ShortCRDisposition,
    TriageDisposition,
)
from sdk.permissions import Permission, PermissionAction, PermissionRegistry


class TestDispositionEnums:
    """Each queue type has exactly its allowed dispositions (capture-only)."""

    def test_p3_pair_enums(self):
        assert {d.value for d in P3PairDisposition} == {"MATCH", "SEPARATE", "UNSURE", "ESCALATE"}
        assert _DISPOSITIONS[QUEUE_P3] == {"MATCH", "SEPARATE", "UNSURE", "ESCALATE"}

    def test_short_cr_enums(self):
        assert {d.value for d in ShortCRDisposition} == {
            "CONFIRMED_VALID_SHORT_CR", "CONFIRMED_ARTIFACT", "UNRESOLVED_ESCALATE",
        }
        assert _DISPOSITIONS[QUEUE_SHORT_CR] == {
            "CONFIRMED_VALID_SHORT_CR", "CONFIRMED_ARTIFACT", "UNRESOLVED_ESCALATE",
        }

    def test_triage_enums(self):
        assert {d.value for d in TriageDisposition} == {"CONFIRM", "REVIEW", "ESCALATE"}
        assert _DISPOSITIONS[QUEUE_TRIAGE] == {"CONFIRM", "REVIEW", "ESCALATE"}

    def test_p1_and_p2_enums(self):
        assert {d.value for d in P1CandidateDisposition} == {"CONFIRM", "REVIEW", "ESCALATE"}
        assert _DISPOSITIONS[QUEUE_P1] == {"CONFIRM", "REVIEW", "ESCALATE"}
        assert {d.value for d in P2SampleDisposition} == {
            "ACCEPT_SAMPLE", "REJECT_SAMPLE", "EXPAND_SAMPLE"
        }
        assert _DISPOSITIONS[QUEUE_P2_SAMPLE] == {
            "ACCEPT_SAMPLE", "REJECT_SAMPLE", "EXPAND_SAMPLE"
        }
        assert {d.value for d in MAUnresolvedDisposition} == {
            "CONFIRM_EXACT", "REVIEW", "ESCALATE"
        }
        assert _DISPOSITIONS[QUEUE_MA_UNRESOLVED] == {
            "CONFIRM_EXACT", "REVIEW", "ESCALATE"
        }


class TestNoSideEffectByDesign:
    """The disposition-capture models/API expose NO field capable of a
    side effect (merge, CR promotion, classification change)."""

    def test_disposition_payload_has_no_side_effect_field(self):
        from app.modules.master_data.phase7.schemas import ReviewQueueDisposition
        fields = set(ReviewQueueDisposition.model_fields.keys())
        # `evidence` is structured review provenance merged into evidence_ref; it
        # is not an action field, and PII is rejected by the schema validator.
        assert fields == {"disposition", "reviewer", "notes", "evidence"}
        # Explicitly assert no merge/CR/classification field is present.
        assert not ({"merge", "promote_cr", "reclassify", "new_classification"} & fields)

    def test_evidence_is_pii_free_enforced(self):
        from app.modules.master_data.phase7.schemas import ReviewQueueDisposition
        for bad in ({"email": "x@y.z"}, {"contact": {"phone": "+20"}},
                    {"reason": "ok", "rows": [{"full_name": "Jane"}]}):
            with pytest.raises(ValidationError, match="PII"):
                ReviewQueueDisposition(
                    disposition="CONFIRM", reviewer="t", evidence=bad
                )
        # Company-level facts are accepted.
        ok = ReviewQueueDisposition(
            disposition="CONFIRM", reviewer="t",
            evidence={"reason": "corroboration", "domain_relation": "shared"},
        )
        assert ok.evidence == {"reason": "corroboration", "domain_relation": "shared"}

    def test_disposition_route_contract(self):
        """Router registers record-only endpoints; verify the service signature
        carries only record-only kwargs.

        `evidence` is additive provenance (merged into evidence_ref). No kwarg
        can express a merge, CR promotion, or classification change.
        """
        import inspect
        sig = inspect.signature(ReviewQueueService.record_disposition)
        params = set(sig.parameters.keys())
        # Must include queue_type/subject_key/disposition/reviewer/notes, plus
        # the additive evidence bag.
        assert {"self", "queue_type", "subject_key", "disposition", "reviewer",
                "notes", "evidence"} == params
        # Nothing that could act on master data.
        assert not ({"merge", "promote_cr", "reclassify", "new_classification"} & params)
        # Backwards compatible: every new param is optional.
        assert sig.parameters["evidence"].default is None


class TestCRPartitionLogic:
    """The short-CR partition mirrors Phase 5/6 normalize_cr: >=8 digits valid."""

    @pytest.fixture
    def svc(self):
        return ReviewQueueService(session=None)  # pure helper, no DB needed

    def test_valid_token_accepted(self, svc):
        valid, rejected = svc._partition_cr_tokens(["1100530300", "7137"])
        assert valid == ["1100530300"]
        assert rejected == ["7137"]

    def test_short_token_rejected(self, svc):
        valid, rejected = svc._partition_cr_tokens(["1005", "7066"])
        assert valid == []
        assert rejected == ["1005", "7066"]

    def test_exact_8_digit_valid(self, svc):
        valid, rejected = svc._partition_cr_tokens(["12345678"])
        assert valid == ["12345678"]
        assert rejected == []

    def test_7_digit_rejected(self, svc):
        valid, rejected = svc._partition_cr_tokens(["1234567"])
        assert valid == []
        assert rejected == ["1234567"]

    def test_non_numeric_rejected(self, svc):
        valid, rejected = svc._partition_cr_tokens(["abc"])
        assert valid == []
        assert rejected == ["abc"]


class TestDatabaseScope:
    @pytest.mark.asyncio
    async def test_reads_refuse_non_test_database(self):
        class Result:
            @staticmethod
            def scalar():
                return "salesos"

        class Session:
            @staticmethod
            async def execute(_query):
                return Result()

        svc = ReviewQueueService(session=Session())
        with pytest.raises(RuntimeError, match="restricted to salesos_test"):
            await svc._current_db()


class TestEnvironmentGate:
    def test_service_refuses_production_environment(self, monkeypatch):
        from fastapi import HTTPException

        from app.modules.master_data.phase7 import review_router

        monkeypatch.setattr(review_router.settings, "env", "production")
        with pytest.raises(HTTPException) as exc:
            review_router.get_service()
        assert exc.value.status_code == HTTPStatus.SERVICE_UNAVAILABLE


class TestReviewPermission:
    def test_review_endpoints_are_not_granted_to_regular_tenant_roles(self):
        roles = PermissionRegistry.default_roles()
        admin = set(roles["admin"])
        assert Permission("master-data-review", PermissionAction.READ) in admin
        assert Permission("master-data-review", PermissionAction.UPDATE) in admin
        for role in ("manager", "user", "api", "auditor"):
            granted = set(roles[role])
            assert Permission("master-data-review", PermissionAction.READ) not in granted
            assert Permission("master-data-review", PermissionAction.UPDATE) not in granted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
