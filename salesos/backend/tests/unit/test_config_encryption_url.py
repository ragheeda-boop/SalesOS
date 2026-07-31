"""Config + encryption key regression tests (DATABASE_URL, Fernet key rotation)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from cryptography.fernet import InvalidToken


def test_resolved_database_url_postgres_schemes():
    from app.config import Settings

    with patch.dict(
        os.environ,
        {
            "SECRET_KEY": "x" * 32,
            "JWT_SECRET_KEY": "y" * 32,
            "DATABASE_URL": "postgres://u:p@h:5432/db",
        },
        clear=False,
    ):
        s = Settings(
            _env_file=None,
            secret_key="x" * 32,
            jwt_secret_key="y" * 32,
            database_url="postgres://u:p@h:5432/db",
        )
        assert s.resolved_database_url.startswith("postgresql+asyncpg://")
        assert s.resolved_database_url.count("+asyncpg") == 1

    s2 = Settings(
        _env_file=None,
        secret_key="x" * 32,
        jwt_secret_key="y" * 32,
        database_url="postgresql://u:p@h:5432/db",
    )
    assert s2.resolved_database_url == "postgresql+asyncpg://u:p@h:5432/db"

    s3 = Settings(
        _env_file=None,
        secret_key="x" * 32,
        jwt_secret_key="y" * 32,
        database_url="postgresql+asyncpg://u:p@h:5432/db",
    )
    assert s3.resolved_database_url == "postgresql+asyncpg://u:p@h:5432/db"
    assert "asyncpg+asyncpg" not in s3.resolved_database_url


def test_fernet_cache_supports_multiple_secrets():
    from sdk.security import _fernet_cache, decrypt_token, encrypt_token

    _fernet_cache.clear()
    key_a = "encryption-key-a-" + ("a" * 16)
    key_b = "encryption-key-b-" + ("b" * 16)
    ct_a = encrypt_token("token-a", key_a)
    ct_b = encrypt_token("token-b", key_b)
    assert decrypt_token(ct_a, key_a) == "token-a"
    assert decrypt_token(ct_b, key_b) == "token-b"
    with pytest.raises(InvalidToken):
        decrypt_token(ct_a, key_b)


def test_google_oauth_decrypt_falls_back_to_previous_key(monkeypatch):
    from app.modules.communication_hub import service as svc
    from sdk.security import encrypt_token

    old_key = "old-google-key-" + ("o" * 16)
    new_key = "new-google-key-" + ("n" * 16)
    ciphertext = encrypt_token("refresh-secret", old_key)

    class _S:
        google_encryption_key = new_key
        google_encryption_key_previous = old_key
        env = "development"

    monkeypatch.setattr(svc, "settings", _S())
    # Construct minimal service without DB for decrypt path.
    oauth = object.__new__(svc.GoogleOAuthService)
    assert oauth._decrypt(ciphertext) == "refresh-secret"
