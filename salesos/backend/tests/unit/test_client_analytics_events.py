from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.routers.analytics import ClientAnalyticsBatch, ingest_analytics_events

PAYLOAD_TOO_LARGE_STATUS = 413
TEST_CLIENT_EVENT_ID = UUID("88888888-8888-4888-8888-888888888888")


class _FakeSession:
    def __init__(self):
        self.events = []
        self.statements = []

    async def execute(self, statement, params=None):
        self.statements.append((str(statement), params or {}))

    def add(self, event):
        self.events.append(event)

    async def flush(self):
        self.events[-1].id = len(self.events)


@pytest.mark.asyncio
async def test_client_batch_persists_events_under_authenticated_identity():
    session = _FakeSession()
    body = ClientAnalyticsBatch.model_validate(
        {
            "events": [
                {
                    "type": "nba.viewed",
                    "timestamp": "2026-09-20T08:00:00Z",
                    "userId": "spoofed-user",
                    "companyId": "company-1",
                    "metadata": {"surface": "dashboard"},
                },
                {
                    "type": "search.performed",
                    "timestamp": "2026-09-20T08:01:00Z",
                    "metadata": {"query_id": "q-1"},
                },
            ]
        }
    )

    result = await ingest_analytics_events(
        body=body,
        tenant_id="tenant-authenticated",
        user_id="user-authenticated",
        db=session,
    )

    assert result == {"status": "ok", "received": 2}
    assert session.statements[0][1] == {"tenant_id": "tenant-authenticated"}
    assert [event.event_type for event in session.events] == ["nba_view", "search_query"]
    assert {event.tenant_id for event in session.events} == {"tenant-authenticated"}
    assert {event.user_id for event in session.events} == {"user-authenticated"}
    assert session.events[0].properties == {
        "surface": "dashboard",
        "client_event_type": "nba.viewed",
        "company_id": "company-1",
    }
    assert session.events[0].timestamp == datetime(2026, 9, 20, 8, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_empty_batch_is_a_no_op():
    session = _FakeSession()
    result = await ingest_analytics_events(
        body=ClientAnalyticsBatch(events=[]),
        tenant_id="tenant-1",
        user_id="user-1",
        db=session,
    )
    assert result == {"status": "ok", "received": 0}
    assert session.events == []


@pytest.mark.asyncio
async def test_nba_acceptance_and_execution_are_stored_as_distinct_events():
    session = _FakeSession()
    body = ClientAnalyticsBatch.model_validate(
        {
            "events": [
                {
                    "type": "nba.accepted",
                    "timestamp": "2026-09-20T08:00:00Z",
                    "metadata": {"actionId": "action-1"},
                },
                {
                    "type": "nba.executed",
                    "timestamp": "2026-09-20T08:01:00Z",
                    "metadata": {"actionId": "action-1"},
                },
                {
                    "type": "nba.rejected",
                    "timestamp": "2026-09-20T08:02:00Z",
                    "metadata": {"actionId": "action-2"},
                },
                {
                    "type": "nba.outcome_recorded",
                    "timestamp": "2026-09-20T08:03:00Z",
                    "metadata": {"actionId": "action-1", "outcomeType": "meeting_set"},
                },
            ]
        }
    )

    await ingest_analytics_events(
        body=body,
        tenant_id="tenant-1",
        user_id="user-1",
        db=session,
    )

    assert [event.event_type for event in session.events] == [
        "nba_accept",
        "nba_executed",
        "nba_reject",
        "nba_outcome_recorded",
    ]


def test_client_event_id_is_parsed_as_a_uuid():
    batch = ClientAnalyticsBatch.model_validate(
        {
            "events": [
                {
                    "type": "nba.viewed",
                    "timestamp": "2026-09-20T08:00:00Z",
                    "eventId": str(TEST_CLIENT_EVENT_ID),
                }
            ]
        }
    )

    assert batch.events[0].event_id == TEST_CLIENT_EVENT_ID


@pytest.mark.asyncio
async def test_oversized_metadata_is_rejected_before_any_write():
    session = _FakeSession()
    body = ClientAnalyticsBatch.model_validate(
        {
            "events": [
                {
                    "type": "widget.interacted",
                    "timestamp": "2026-09-20T08:00:00Z",
                    "metadata": {"payload": "x" * 9000},
                }
            ]
        }
    )

    with pytest.raises(HTTPException) as error:
        await ingest_analytics_events(
            body=body,
            tenant_id="tenant-1",
            user_id="user-1",
            db=session,
        )

    assert error.value.status_code == PAYLOAD_TOO_LARGE_STATUS
    assert session.statements == []
    assert session.events == []
