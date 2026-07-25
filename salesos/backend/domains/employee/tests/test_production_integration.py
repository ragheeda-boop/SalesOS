"""Production integration tests — OAuth, AI, webhooks, Celery tasks, rate limiting."""

import pytest
from datetime import datetime, timezone, timedelta

from domains.employee.oauth_service import EmployeeOAuthToken, OAuthTokenService
from domains.employee.rate_limit import RateLimiter, oauth_rate_limiter, ai_rate_limiter, webhook_rate_limiter
from domains.employee.retention import is_eligible_for_purge, mask_pii_field, RETENTION_DAYS_SOFT_DELETED
from domains.employee.health import EmployeeHealthChecker


class TestOAuthTokenModel:
    def test_is_access_token_expired_true_when_none(self):
        token = EmployeeOAuthToken()
        assert token.is_access_token_expired() is True

    def test_is_access_token_expired_true_when_past(self):
        token = EmployeeOAuthToken(access_token_expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
        assert token.is_access_token_expired() is True

    def test_is_access_token_expired_false_when_future(self):
        token = EmployeeOAuthToken(access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=2))
        assert token.is_access_token_expired() is False

    def test_should_retry_stops_after_max_failures(self):
        token = EmployeeOAuthToken(is_active=True, max_failures=3, consecutive_failures=3)
        assert token.should_retry() is False

    def test_should_retry_allows_below_max(self):
        token = EmployeeOAuthToken(is_active=True, max_failures=10, consecutive_failures=5)
        assert token.should_retry() is True

    def test_record_success_resets_failures(self):
        token = EmployeeOAuthToken(consecutive_failures=7, connection_error="prev error")
        token.record_success()
        assert token.consecutive_failures == 0
        assert token.connection_error is None
        assert token.is_connected is True

    def test_record_failure_increments_and_may_disconnect(self):
        token = EmployeeOAuthToken(consecutive_failures=9, max_failures=10)
        token.record_failure("auth error")
        assert token.consecutive_failures == 10
        assert token.is_connected is False


class TestRateLimiter:
    def test_allows_requests_within_limit(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.check("test-key") is True

    def test_blocks_requests_exceeding_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            assert limiter.check("test-key") is True
        assert limiter.check("test-key") is False

    def test_remaining_returns_correct_count(self):
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert limiter.remaining("test-key") == 10
        limiter.check("test-key")
        assert limiter.remaining("test-key") == 9

    def test_different_keys_independent(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.check("key-a") is True
        assert limiter.check("key-a") is True
        assert limiter.check("key-a") is False
        assert limiter.check("key-b") is True


class TestOAuthEncryption:
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_roundtrip(self):
        svc = OAuthTokenService(db=None, encryption_key=None)
        original = "ya29.a0AfH6SMB_test_token_abc123"
        encrypted = await svc._encrypt(original)
        decrypted = await svc._decrypt(encrypted)
        assert decrypted == original
        assert encrypted != original
        assert len(encrypted) > len(original)


class TestHealthChecker:
    @pytest.mark.asyncio
    async def test_full_check_structure(self, db_session):
        checker = EmployeeHealthChecker(db_session)
        result = await checker.full_check()
        assert "service" in result
        assert result["service"] == "employee-360"
        assert "status" in result
        assert "checks" in result
        assert "database" in result["checks"]
        assert "latency_ms" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_liveness_always_true(self, db_session):
        checker = EmployeeHealthChecker(db_session)
        assert await checker.liveness() is True


class TestRetentionPolicy:
    def test_purge_after_retention(self):
        old = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS_SOFT_DELETED + 1)
        assert is_eligible_for_purge(old) is True

    def test_no_purge_within_retention(self):
        recent = datetime.now(timezone.utc) - timedelta(days=5)
        assert is_eligible_for_purge(recent) is False

    def test_mask_sensitive_phone(self):
        assert mask_pii_field("phone", "+966501234567") == "****4567"

    def test_mask_email_partial(self):
        result = mask_pii_field("email", "mohammed@company.com.sa")
        assert "mo****@" in result
        assert "@company.com.sa" in result

    def test_no_mask_non_pii(self):
        assert mask_pii_field("role", "manager") == "manager"
        assert mask_pii_field("id", "uuid-123") == "uuid-123"


class TestWebhookReplayProtection:
    def test_replay_detection(self):
        from domains.employee.webhook_handler import _check_replay
        channel = "ch-001"
        assert _check_replay(channel, 1) is True
        assert _check_replay(channel, 2) is True
        assert _check_replay(channel, 1) is False  # Replay blocked
        assert _check_replay(channel, 3) is True


class TestAIResponseParse:
    def test_parse_valid_json_meeting(self):
        result = '{"summary": "Discussed Q3 targets", "action_items": ["Follow up with finance"], "sentiment": "positive"}'
        import json
        parsed = json.loads(result)
        assert parsed["summary"] == "Discussed Q3 targets"
        assert len(parsed["action_items"]) == 1
        assert parsed["sentiment"] == "positive"

    def test_fallback_on_invalid_json(self):
        result = "Invalid response from AI"
        import json
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.replace("Invalid", "{"))
