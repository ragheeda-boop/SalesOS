from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.routers.notifications import _repo, _ws_manager, create_and_notify, broadcast_notification
from domains.notifications.models import InMemoryNotificationRepository, Notification
from intelligence.notifications.email import EmailService
from intelligence.notifications.websocket import WebSocketManager


# ── Fixtures ──

@pytest.fixture
def repo():
    return InMemoryNotificationRepository()


@pytest.fixture
def email_service():
    return EmailService()


@pytest.fixture
def ws_manager():
    return WebSocketManager()


@pytest.fixture
def sample_notification():
    return Notification(
        id="n-1",
        tenant_id="t-1",
        user_id="u-1",
        type="workflow",
        title="Workflow Executed",
        body="Workflow completed successfully",
        data={"workflow_id": "wf-1", "status": "completed"},
    )


@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


# ── Notification Model Tests ──

class TestNotificationModel:
    def test_notification_defaults(self):
        n = Notification(id="n-1", tenant_id="t-1", user_id="u-1", type="alert", title="Test", body="Body")
        assert n.read is False
        assert n.data == {}
        assert isinstance(n.created_at, datetime)

    def test_notification_with_data(self):
        n = Notification(id="n-1", tenant_id="t-1", user_id="u-1", type="nba", title="NBA", body="Body",
                         data={"action": "follow_up", "confidence": 0.85})
        assert n.data["action"] == "follow_up"
        assert n.data["confidence"] == 0.85

    def test_notification_types(self):
        for t in ("workflow", "nba", "report", "alert"):
            n = Notification(id=f"n-{t}", tenant_id="t-1", user_id="u-1", type=t, title=t, body=t)
            assert n.type == t


class TestNotificationRepository:
    @pytest.mark.asyncio
    async def test_create_notification(self, repo):
        n = Notification(id="n-1", tenant_id="t-1", user_id="u-1", type="workflow", title="Test", body="Body")
        created = await repo.create(n)
        assert created.id == "n-1"

    @pytest.mark.asyncio
    async def test_get_notification(self, repo, sample_notification):
        await repo.create(sample_notification)
        found = await repo.get("n-1", "t-1")
        assert found is not None
        assert found.title == "Workflow Executed"

    @pytest.mark.asyncio
    async def test_get_notification_tenant_isolation(self, repo, sample_notification):
        await repo.create(sample_notification)
        found = await repo.get("n-1", "other-tenant")
        assert found is None

    @pytest.mark.asyncio
    async def test_list_by_user(self, repo):
        for i in range(3):
            n = Notification(id=f"n-{i}", tenant_id="t-1", user_id="u-1", type="alert", title=f"Alert {i}", body="Body")
            await repo.create(n)
        notifs = await repo.list_by_user("t-1", "u-1")
        assert len(notifs) == 3

    @pytest.mark.asyncio
    async def test_list_by_user_tenant_isolation(self, repo):
        n1 = Notification(id="n-1", tenant_id="t-1", user_id="u-1", type="alert", title="A", body="B")
        n2 = Notification(id="n-2", tenant_id="t-2", user_id="u-1", type="alert", title="A", body="B")
        await repo.create(n1)
        await repo.create(n2)
        t1_notifs = await repo.list_by_user("t-1", "u-1")
        assert len(t1_notifs) == 1

    @pytest.mark.asyncio
    async def test_list_by_user_limit(self, repo):
        for i in range(5):
            n = Notification(id=f"n-{i}", tenant_id="t-1", user_id="u-1", type="alert", title=f"A{i}", body="B")
            await repo.create(n)
        notifs = await repo.list_by_user("t-1", "u-1", limit=2)
        assert len(notifs) == 2

    @pytest.mark.asyncio
    async def test_mark_read(self, repo, sample_notification):
        await repo.create(sample_notification)
        ok = await repo.mark_read("n-1", "t-1", "u-1")
        assert ok is True
        n = await repo.get("n-1", "t-1")
        assert n.read is True

    @pytest.mark.asyncio
    async def test_mark_read_wrong_user(self, repo, sample_notification):
        await repo.create(sample_notification)
        ok = await repo.mark_read("n-1", "t-1", "other-user")
        assert ok is False

    @pytest.mark.asyncio
    async def test_mark_read_not_found(self, repo):
        ok = await repo.mark_read("nonexistent", "t-1", "u-1")
        assert ok is False

    @pytest.mark.asyncio
    async def test_mark_all_read(self, repo):
        for i in range(3):
            n = Notification(id=f"n-{i}", tenant_id="t-1", user_id="u-1", type="alert", title=f"A{i}", body="B")
            await repo.create(n)
        count = await repo.mark_all_read("t-1", "u-1")
        assert count == 3
        assert (await repo.count_unread("t-1", "u-1")) == 0

    @pytest.mark.asyncio
    async def test_count_unread(self, repo):
        n1 = Notification(id="n-1", tenant_id="t-1", user_id="u-1", type="alert", title="A", body="B")
        n2 = Notification(id="n-2", tenant_id="t-1", user_id="u-1", type="alert", title="A", body="B")
        n2.read = True
        await repo.create(n1)
        await repo.create(n2)
        count = await repo.count_unread("t-1", "u-1")
        assert count == 1

    @pytest.mark.asyncio
    async def test_list_sorted_by_date_desc(self, repo):
        n1 = Notification(id="n-1", tenant_id="t-1", user_id="u-1", type="alert", title="A", body="B",
                          created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        n2 = Notification(id="n-2", tenant_id="t-1", user_id="u-1", type="alert", title="B", body="B",
                          created_at=datetime(2026, 6, 1, tzinfo=timezone.utc))
        await repo.create(n1)
        await repo.create(n2)
        notifs = await repo.list_by_user("t-1", "u-1")
        assert notifs[0].id == "n-2"
        assert notifs[1].id == "n-1"


# ── Email Service Tests ──

class TestEmailService:
    def test_not_configured_by_default(self, email_service):
        assert email_service.configured is False

    def test_configured_when_host_user_password_set(self):
        svc = EmailService(smtp_host="smtp.example.com", smtp_user="user", smtp_password="pass")
        assert svc.configured is True

    def test_send_fallback_when_not_configured(self, email_service):
        result = email_service.send("test@example.com", "Subject", "Body")
        assert result is False

    @patch("smtplib.SMTP_SSL")
    def test_send_smtp_success(self, mock_smtp):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        svc = EmailService(smtp_host="smtp.example.com", smtp_port=465, smtp_user="user", smtp_password="pass", smtp_from="from@example.com")
        result = svc.send("to@example.com", "Test", "Hello")
        assert result is True
        mock_smtp.assert_called_once_with("smtp.example.com", 465)

    @patch("smtplib.SMTP_SSL")
    def test_send_smtp_html_body(self, mock_smtp):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        svc = EmailService(smtp_host="smtp.example.com", smtp_port=465, smtp_user="user", smtp_password="pass", smtp_from="from@example.com")
        result = svc.send("to@example.com", "Test", "Plain", "<h1>HTML</h1>")
        assert result is True

    @patch("smtplib.SMTP_SSL")
    def test_send_smtp_failure(self, mock_smtp):
        mock_smtp.return_value.__enter__.side_effect = Exception("Connection failed")
        svc = EmailService(smtp_host="smtp.example.com", smtp_port=465, smtp_user="user", smtp_password="pass")
        result = svc.send("to@example.com", "Test", "Hello")
        assert result is False

    def test_send_template_not_configured(self, email_service):
        result = email_service.send_template("to@example.com", "workflow_triggered.html", {"workflow_name": "Test"})
        assert result is False

    def test_send_template_not_found(self, email_service):
        result = email_service.send_template("to@example.com", "nonexistent.html", {})
        assert result is False

    @patch.object(EmailService, "send", return_value=True)
    def test_send_template_delegates_to_send(self, mock_send):
        svc = EmailService()
        result = svc.send_template("to@example.com", "workflow_triggered.html", {"workflow_name": "Test WF", "status": "completed", "triggered_at": "now"})
        assert result is True
        mock_send.assert_called_once()

    def test_render_template(self, email_service):
        template = "<h1>{{ name }}</h1>"
        rendered = email_service._render_template(template, {"name": "Alice"})
        assert rendered == "<h1>Alice</h1>"

    def test_to_plain_text(self, email_service):
        html = "<h2>Title</h2><p>Body text</p>"
        plain = email_service._to_plain_text(html)
        assert "Title" in plain
        assert "Body text" in plain
        assert "<" not in plain

    def test_send_to_many(self, email_service):
        with patch.object(email_service, "send", return_value=True):
            count = email_service.send_to_many(["a@b.com", "c@d.com"], "Sub", "Body")
            assert count == 2


# ── WebSocket Manager Tests ──

class TestWebSocketManager:
    @pytest.mark.asyncio
    async def test_connect(self, ws_manager, mock_websocket):
        await ws_manager.connect(mock_websocket, "t-1", "u-1")
        assert ws_manager.active_connections == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, ws_manager, mock_websocket):
        await ws_manager.connect(mock_websocket, "t-1", "u-1")
        await ws_manager.disconnect(mock_websocket)
        assert ws_manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_disconnect_unknown(self, ws_manager):
        await ws_manager.disconnect("unknown")
        assert ws_manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_tenant(self, ws_manager):
        ws1 = AsyncMock()
        ws1.send_text = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_text = AsyncMock()
        ws_other = AsyncMock()
        ws_other.send_text = AsyncMock()

        await ws_manager.connect(ws1, "t-1", "u-1")
        await ws_manager.connect(ws2, "t-1", "u-2")
        await ws_manager.connect(ws_other, "t-2", "u-3")

        sent = await ws_manager.broadcast("t-1", "test_event", {"msg": "hello"})

        assert sent == 2
        ws1.send_text.assert_awaited_once()
        ws2.send_text.assert_awaited_once()
        ws_other.send_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_broadcast_cleans_stale(self, ws_manager):
        ws = AsyncMock()
        ws.send_text = AsyncMock(side_effect=Exception("gone"))
        await ws_manager.connect(ws, "t-1", "u-1")

        sent = await ws_manager.broadcast("t-1", "test", {})
        assert sent == 0
        assert ws_manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_send_to_user(self, ws_manager):
        ws_target = AsyncMock()
        ws_target.send_text = AsyncMock()
        ws_other = AsyncMock()
        ws_other.send_text = AsyncMock()

        await ws_manager.connect(ws_target, "t-1", "u-1")
        await ws_manager.connect(ws_other, "t-1", "u-2")

        sent = await ws_manager.send_to_user("t-1", "u-1", "private", {"msg": "secret"})

        assert sent == 1
        ws_target.send_text.assert_awaited_once()
        ws_other.send_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_to_user_tenant_isolation(self, ws_manager):
        ws = AsyncMock()
        ws.send_text = AsyncMock()
        await ws_manager.connect(ws, "t-1", "u-1")

        sent = await ws_manager.send_to_user("t-2", "u-1", "test", {})
        assert sent == 0
        ws.send_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cleanup_stale(self, ws_manager, mock_websocket):
        await ws_manager.connect(mock_websocket, "t-1", "u-1")
        import time
        for info in ws_manager._connections.values():
            info["last_active"] = time.time() - 120
        cleaned = await ws_manager.cleanup_stale()
        assert cleaned == 1
        assert ws_manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, ws_manager):
        wss = [AsyncMock() for _ in range(5)]
        for idx, ws in enumerate(wss):
            ws.send_text = AsyncMock()
            await ws_manager.connect(ws, "t-1", f"u-{idx}")
        assert ws_manager.active_connections == 5
        count = await ws_manager.get_connection_count()
        assert count == 5


# ── Integration: create_and_notify ──

class TestCreateAndNotify:
    @pytest.mark.asyncio
    async def test_create_and_notify_creates_notification(self):
        n = await create_and_notify("t-1", "u-1", "workflow", "Test", "Body", {"key": "val"})
        assert n.id is not None
        assert n.tenant_id == "t-1"
        assert n.user_id == "u-1"
        assert n.type == "workflow"

    @pytest.mark.asyncio
    async def test_create_and_notify_stores_in_repo(self):
        n = await create_and_notify("t-1", "u-1", "nba", "NBA Alert", "New rec", {})
        found = await _repo.get(n.id, "t-1")
        assert found is not None
        assert found.title == "NBA Alert"

    @pytest.mark.asyncio
    async def test_broadcast_notification(self):
        n = await broadcast_notification("t-1", "alert", "System Alert", "Something happened", {"severity": "high"})
        assert n.type == "alert"
        assert n.data["severity"] == "high"


# ── Integration: WebSocket payload format ──

class TestWebSocketPayload:
    @pytest.mark.asyncio
    async def test_broadcast_payload_format(self, ws_manager):
        ws = AsyncMock()
        ws.send_text = AsyncMock()
        await ws_manager.connect(ws, "t-1", "u-1")

        await ws_manager.broadcast("t-1", "workflow", {"id": "n-1", "title": "Test"})

        call_args = ws.send_text.await_args[0][0]
        payload = json.loads(call_args)
        assert payload["type"] == "workflow"
        assert payload["data"]["id"] == "n-1"

    @pytest.mark.asyncio
    async def test_send_to_user_payload_format(self, ws_manager):
        ws = AsyncMock()
        ws.send_text = AsyncMock()
        await ws_manager.connect(ws, "t-1", "u-1")

        await ws_manager.send_to_user("t-1", "u-1", "nba", {"action": "follow_up"})

        call_args = ws.send_text.await_args[0][0]
        payload = json.loads(call_args)
        assert payload["type"] == "nba"
        assert payload["data"]["action"] == "follow_up"
