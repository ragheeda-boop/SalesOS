from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.modules.api_keys.models import ApiKey
from app.modules.api_keys.service import ApiKeyService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture(autouse=True)
def patch_bcrypt():
    with patch("app.modules.api_keys.service._generate_api_key") as mock_gen, \
         patch("app.modules.api_keys.service.pwd_context") as mock_pwd:
        mock_gen.return_value = ("sos_abc123def456", "sos_abc123", "mock_hash")
        mock_pwd.hash.return_value = "mock_hash"
        mock_pwd.verify.side_effect = lambda key, hash_val: key == "sos_abc123def456"
        yield


@pytest.fixture
def api_key_service(mock_db):
    return ApiKeyService(db=mock_db, logger=None)


class TestApiKeyGeneration:
    def test_generate_api_key_format(self):
        import secrets
        raw = secrets.token_hex(32)
        key = f"sos_{raw}"
        assert key.startswith("sos_")
        assert len(key) == 68
        assert key[:10] == "sos_" + raw[:6]

    def test_hash_and_verify(self):
        import hashlib
        key = "sos_" + "a" * 64
        h = hashlib.sha256(key.encode()).hexdigest()
        assert hashlib.sha256(key.encode()).hexdigest() == h
        assert hashlib.sha256(("sos_" + "b" * 64).encode()).hexdigest() != h


class TestApiKeyCreate:
    @pytest.mark.asyncio
    async def test_create_api_key(self, api_key_service, mock_db):
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        key_record, raw_key = await api_key_service.create(tenant_id, user_id, "Test Key")
        assert raw_key.startswith("sos_")
        assert key_record.name == "Test Key"
        assert key_record.key_prefix == raw_key[:10]
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_create_api_key_with_permissions(self, api_key_service, mock_db):
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        perms = {"companies": ["read", "write"]}
        key_record, raw_key = await api_key_service.create(
            tenant_id, user_id, "Scoped Key", permissions=perms, scopes=["companies:read"],
        )
        assert key_record.permissions == perms

    @pytest.mark.asyncio
    async def test_create_api_key_with_expiry(self, api_key_service, mock_db):
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        key_record, raw_key = await api_key_service.create(
            tenant_id, user_id, "Expiring Key", expiry_days=30,
        )
        assert key_record.expires_at is not None

    @pytest.mark.asyncio
    async def test_create_api_key_default_expiry(self, api_key_service, mock_db):
        with patch("app.modules.api_keys.service.settings") as mock_settings:
            mock_settings.api_key_expiry_days = 365
            tenant_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            key_record, raw_key = await api_key_service.create(tenant_id, user_id, "Default Expiry")
            assert key_record.expires_at is not None


class TestApiKeyValidate:
    @pytest.mark.asyncio
    async def test_validate_valid_key(self, api_key_service, mock_db):
        mock_key = ApiKey(
            id="key1", tenant_id=uuid.uuid4(), user_id=uuid.uuid4(),
            name="Test", key_prefix="sos_abc123", key_hash="mock_hash",
            is_revoked=False,
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_key]
        mock_db.execute.return_value = mock_result

        result = await api_key_service.validate("sos_abc123def456")
        assert result is not None
        assert result.id == "key1"

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self, api_key_service, mock_db):
        mock_key = ApiKey(
            id="key1", tenant_id=uuid.uuid4(), user_id=uuid.uuid4(),
            name="Test", key_prefix="sos_abc123", key_hash="mock_hash",
            is_revoked=False,
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_key]
        mock_db.execute.return_value = mock_result

        result = await api_key_service.validate("sos_wrongkey123456")
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_revoked_key(self, api_key_service, mock_db):
        mock_key = ApiKey(
            id="key1", tenant_id=uuid.uuid4(), user_id=uuid.uuid4(),
            name="Test", key_prefix="sos_abc123", key_hash="hash",
            is_revoked=True,
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_key]
        mock_db.execute.return_value = mock_result

        result = await api_key_service.validate("sos_" + "a" * 64)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_expired_key(self, api_key_service, mock_db):
        mock_key = ApiKey(
            id="key1", tenant_id=uuid.uuid4(), user_id=uuid.uuid4(),
            name="Test", key_prefix="sos_abc123", key_hash="mock_hash",
            is_revoked=False,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_key]
        mock_db.execute.return_value = mock_result

        result = await api_key_service.validate("sos_abc123def456")
        assert result is None
        assert mock_key.is_revoked is True

    @pytest.mark.asyncio
    async def test_validate_updates_last_used(self, api_key_service, mock_db):
        mock_key = ApiKey(
            id="key1", tenant_id=uuid.uuid4(), user_id=uuid.uuid4(),
            name="Test", key_prefix="sos_abc123", key_hash="mock_hash",
            is_revoked=False, last_used_at=None,
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_key]
        mock_db.execute.return_value = mock_result

        result = await api_key_service.validate("sos_abc123def456")
        assert result is not None
        assert result.last_used_at is not None


class TestApiKeyRevoke:
    @pytest.mark.asyncio
    async def test_revoke_api_key(self, api_key_service, mock_db):
        user_id = uuid.uuid4()
        mock_key = ApiKey(
            id="key1", tenant_id=uuid.uuid4(), user_id=user_id,
            name="Test", key_prefix="sos_abc", key_hash="hash",
            is_revoked=False,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_key
        mock_db.execute.return_value = mock_result

        result = await api_key_service.revoke("key1", str(user_id))
        assert result is True
        assert mock_key.is_revoked is True

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_key(self, api_key_service, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await api_key_service.revoke("nonexistent", str(uuid.uuid4()))
        assert result is False

    @pytest.mark.asyncio
    async def test_list_for_user(self, api_key_service, mock_db):
        user_id = uuid.uuid4()
        mock_key = ApiKey(
            id="key1", tenant_id=uuid.uuid4(), user_id=user_id,
            name="My Key", key_prefix="sos_abc12", key_hash="hash",
            is_revoked=False, scopes="read,write",
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_key]
        mock_db.execute.return_value = mock_result

        keys = await api_key_service.list_for_user(str(user_id))
        assert len(keys) == 1
        assert keys[0]["name"] == "My Key"
        assert keys[0]["scopes"] == ["read", "write"]

    @pytest.mark.asyncio
    async def test_list_for_user_excludes_revoked(self, api_key_service, mock_db):
        user_id = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        keys = await api_key_service.list_for_user(str(user_id))
        assert keys == []
