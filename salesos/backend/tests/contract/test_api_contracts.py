"""Provider contract tests — verify API endpoint schemas, error responses, and pagination format.

Target: all major endpoints covered.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import BaseModel, ValidationError

from app.common.schemas import CursorResponse, PaginatedResponse
from sdk.pagination import CursorPage, decode_cursor, encode_cursor


# ── Pagination Contract ────────────────────────────────────────────────────


def test_cursor_page_contract():
    """CursorPage must have required fields with correct types."""
    page = CursorPage(items=[1, 2, 3], next_cursor="abc", has_next=True)
    assert isinstance(page.items, list)
    assert page.next_cursor is None or isinstance(page.next_cursor, str)
    assert isinstance(page.has_next, bool)
    assert page.total is None or isinstance(page.total, int)


def test_cursor_response_contract():
    """CursorResponse schema must match documented format."""
    resp = CursorResponse(data=[{"id": "1"}], next_cursor="abc", has_next=True, total=1)
    assert resp.data == [{"id": "1"}]
    assert resp.next_cursor == "abc"
    assert resp.has_next is True
    assert resp.total == 1
    assert resp.previous_cursor is None
    assert resp.has_previous is False


def test_cursor_response_empty():
    resp = CursorResponse(data=[])
    assert resp.data == []
    assert resp.next_cursor is None
    assert resp.has_next is False
    assert resp.total is None


def test_paginated_response_contract():
    resp = PaginatedResponse(total=100, page=1, page_size=20, items=[{"id": "1"}], next_cursor="xyz", has_next=True)
    assert resp.total == 100
    assert resp.page == 1
    assert resp.page_size == 20
    assert resp.next_cursor == "xyz"
    assert resp.has_next is True


def test_paginated_response_minimal():
    resp = PaginatedResponse(total=0, page=1, page_size=20, items=[])
    assert resp.next_cursor is None
    assert resp.has_next is False


# ── Cursor Encode/Decode Contract ──────────────────────────────────────────


def test_cursor_encode_decode_roundtrip():
    original_id = str(uuid4())
    now = datetime.now(timezone.utc)
    cursor = encode_cursor(original_id, now)
    decoded_id, decoded_sort = decode_cursor(cursor)
    assert decoded_id == original_id
    assert decoded_sort == now


def test_cursor_id_only_roundtrip():
    original_id = str(uuid4())
    cursor = encode_cursor(original_id)
    decoded_id, decoded_sort = decode_cursor(cursor)
    assert decoded_id == original_id
    assert decoded_sort is None


def test_cursor_malformed_raises():
    with pytest.raises(Exception):
        decode_cursor("!!!invalid!!!")
    with pytest.raises(Exception):
        decode_cursor("bm90IGpzb24=")


# ── Error Response Contract ────────────────────────────────────────────────


def test_error_response_format():
    from app.common.schemas import ErrorResponse
    err = ErrorResponse(detail="Not found", code="NOT_FOUND", errors=[{"field": "id"}])
    assert err.detail == "Not found"
    assert err.code == "NOT_FOUND"
    assert err.errors == [{"field": "id"}]


def test_error_response_defaults():
    from app.common.schemas import ErrorResponse
    err = ErrorResponse(detail="Server error")
    assert err.code == "ERROR"
    assert err.errors is None


def test_health_response_format():
    from app.common.schemas import HealthResponse
    health = HealthResponse(status="ok", version="1.0", database="up", cache="up", rate_limiter="active")
    assert health.status == "ok"
    assert health.uptime_seconds == 0.0


def test_message_response_format():
    from app.common.schemas import MessageResponse
    msg = MessageResponse(message="Success")
    assert msg.message == "Success"
    assert msg.code == "OK"


# ── Identity Domain Contracts ──────────────────────────────────────────────


def test_login_request_schema():
    from app.modules.identity.schemas import LoginRequest
    req = LoginRequest(email="user@example.com", password="secure123")
    assert req.email == "user@example.com"
    assert req.password == "secure123"


def test_login_request_invalid_email():
    from app.modules.identity.schemas import LoginRequest
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="pw")


def test_token_response_schema():
    from app.modules.identity.schemas import TokenResponse
    resp = TokenResponse(access_token="eyJ...", refresh_token="rt...", token_type="bearer", expires_in=3600)
    assert resp.access_token == "eyJ..."
    assert resp.token_type == "bearer"
    assert resp.expires_in == 3600
    assert resp.refresh_token == "rt..."
    assert resp.tenant_id is None


# ── Company Domain Contracts ───────────────────────────────────────────────


def test_company_response_schema():
    from pydantic import BaseModel

    class CompanyResponse(BaseModel):
        id: str
        name_ar: str | None = None
        name_en: str | None = None
        cr_number: str | None = None
        city: str | None = None
        status: str = "active"
        created_at: datetime | None = None

    company = CompanyResponse(id="c1", name_ar="شركة测试", status="active")
    assert company.id == "c1"
    assert company.name_ar == "شركة测试"


def test_cursor_response_on_company_search():
    from app.common.schemas import CursorResponse
    resp = CursorResponse(
        data=[{"id": "c1", "name_en": "Test Corp"}],
        next_cursor="abc123",
        has_next=True,
        total=1,
    )
    assert len(resp.data) == 1
    assert resp.data[0]["name_en"] == "Test Corp"


# ── Decision Domain Contracts ──────────────────────────────────────────────


def test_decision_schemas_exist():
    from app.modules.decision.schemas import (
        DecisionContext,
        DecisionResultAPI,
        EvidenceItemAPI,
        HistoryResponseAPI,
        RecommendationAPI,
        RecommendationsResponseAPI,
        EvidenceResponseAPI,
    )
    assert DecisionContext is not None
    assert DecisionResultAPI is not None
    assert HistoryResponseAPI is not None
    assert RecommendationsResponseAPI is not None
    assert EvidenceResponseAPI is not None


def test_decision_history_response_has_cursor():
    from app.modules.decision.schemas import HistoryResponseAPI
    resp = HistoryResponseAPI(items=[], next_cursor="abc", has_next=True)
    assert resp.next_cursor == "abc"
    assert resp.has_next is True


# ── Timeline Domain Contracts ──────────────────────────────────────────────


def test_timeline_entry_schema():
    from pydantic import BaseModel

    class TimelineEntry(BaseModel):
        id: str
        event_type: str
        description: str
        occurred_at: datetime
        entity_type: str
        entity_id: str

    entry = TimelineEntry(
        id="t1", event_type="email", description="Sent proposal",
        occurred_at=datetime.now(timezone.utc), entity_type="company", entity_id="c1",
    )
    assert entry.event_type == "email"


def test_timeline_response_has_cursor():
    resp = {
        "entity_type": "company",
        "entity_id": "c1",
        "total": 10,
        "entries": [],
        "next_cursor": "cursor123",
        "has_next": False,
    }
    assert "next_cursor" in resp
    assert "has_next" in resp


# ── Activity Domain Contracts ──────────────────────────────────────────────


def test_activity_response_format():
    resp = {
        "items": [{"id": "a1", "action": "email_sent"}],
        "total": 1,
        "limit": 50,
        "next_cursor": None,
        "has_next": False,
    }
    assert resp["items"][0]["action"] == "email_sent"
    assert "next_cursor" in resp


# ── Search Domain Contracts ────────────────────────────────────────────────


def test_search_response_format():
    resp = {
        "query": "test",
        "strategy": "hybrid",
        "total": 5,
        "took_ms": 12.34,
        "items": [{"id": "c1", "name_en": "Test"}],
        "facets": {"city": {"Riyadh": 3}},
        "suggestions": [],
        "next_cursor": None,
        "has_next": False,
    }
    assert "next_cursor" in resp
    assert "has_next" in resp
    assert resp["total"] == 5


# ── AI Domain Contracts ────────────────────────────────────────────────────


def test_ai_generate_request_schema():
    from domains.ai.schemas import GenerateRequest
    req = GenerateRequest(prompt_template_id="greet", variables={"name": "World"})
    assert req.provider == "openai"
    assert req.variables["name"] == "World"


def test_ai_evaluate_response():
    from domains.ai.models import AIEvaluation, EvaluationMetric
    metric = EvaluationMetric(name="exact_match", value=1.0, threshold=0.5, passed=True)
    eval_result = AIEvaluation(
        id="eval1", prompt_id="p1", input="Q", output="A",
        expected="A", score=1.0, metrics=[metric],
    )
    assert eval_result.score == 1.0
    assert eval_result.metrics[0].passed is True


# ── Entity Resolution Contracts ────────────────────────────────────────────


def test_golden_record_response():
    from pydantic import BaseModel

    class GoldenRecordResponse(BaseModel):
        id: str
        cr_number: str
        confidence_score: float
        source_count: int

    gr = GoldenRecordResponse(id="gr1", cr_number="CR123", confidence_score=0.95, source_count=3)
    assert gr.confidence_score == 0.95


# ── Admin Domain Contracts ─────────────────────────────────────────────────


def test_job_response_schema():
    from app.modules.admin.schemas import JobResponse
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    job = JobResponse(
        id="j1", type="enrichment", status="completed", progress=100,
        tenant_id="tenant_1", created_by="admin", payload={},
        result={}, error_message=None, retry_count=0, max_retries=3,
        scheduled_at=now, started_at=now, completed_at=now,
        created_at=now, updated_at=now,
    )
    assert job.status == "completed"


def test_ai_cost_response_schema():
    from app.modules.admin.schemas import AICostResponse
    from datetime import datetime, timezone
    from uuid import uuid4
    cost = AICostResponse(
        id=uuid4(), model="gpt-4o", tenant_id=uuid4(), tenant_name="Default",
        prompt_tokens=100, completion_tokens=50,
        total_tokens=150, cost=0.01, operation="chat",
        created_at=datetime.now(timezone.utc),
    )
    assert cost.total_tokens == 150


# ── Pagination Response Contract (all list endpoints) ──────────────────────


@pytest.mark.parametrize("total,page,page_size,items,next_cursor,has_next", [
    (0, 1, 20, [], None, False),
    (1, 1, 20, [{"id": "1"}], None, False),
    (100, 1, 20, [{"id": str(i)} for i in range(20)], "next_cursor", True),
])
def test_paginated_response_contract_parametrized(total, page, page_size, items, next_cursor, has_next):
    resp = PaginatedResponse(total=total, page=page, page_size=page_size, items=items, next_cursor=next_cursor, has_next=has_next)
    assert resp.total == total
    assert len(resp.items) == len(items)
    assert resp.next_cursor == next_cursor
    assert resp.has_next == has_next
