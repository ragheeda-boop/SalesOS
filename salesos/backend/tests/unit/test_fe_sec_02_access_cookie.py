"""FE-SEC-02 — optional httpOnly access cookie helpers (flag default OFF)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.modules.identity.router import (
    ACCESS_COOKIE,
    _clear_access_cookie,
    _set_access_cookie,
)


def test_set_access_cookie_noop_when_flag_off() -> None:
    response = MagicMock()
    with patch("app.modules.identity.router.settings") as mock_settings:
        mock_settings.feature_httponly_access_cookie = False
        mock_settings.jwt_access_token_expire_minutes = 30
        _set_access_cookie(response, "jwt-access")
    response.set_cookie.assert_not_called()


def test_set_access_cookie_when_flag_on() -> None:
    response = MagicMock()
    with patch("app.modules.identity.router.settings") as mock_settings:
        mock_settings.feature_httponly_access_cookie = True
        mock_settings.jwt_access_token_expire_minutes = 30
        _set_access_cookie(response, "jwt-access")
    response.set_cookie.assert_called_once()
    kwargs = response.set_cookie.call_args.kwargs
    assert kwargs["key"] == ACCESS_COOKIE
    assert kwargs["value"] == "jwt-access"
    assert kwargs["httponly"] is True
    assert kwargs["samesite"] == "strict"
    assert kwargs["secure"] is True
    assert kwargs["path"] == "/"
    assert kwargs["max_age"] == 1800


def test_clear_access_cookie_always() -> None:
    response = MagicMock()
    _clear_access_cookie(response)
    response.delete_cookie.assert_called_once()
    kwargs = response.delete_cookie.call_args.kwargs
    assert kwargs["key"] == ACCESS_COOKIE
    assert kwargs["path"] == "/"
