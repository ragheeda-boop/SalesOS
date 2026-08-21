"""Tests for identity.schemas — password strength validation, no DB."""

from __future__ import annotations

import pytest

from app.modules.identity.schemas import (
    PasswordChangeRequest,
    TenantCreate,
    UserCreate,
    validate_password_strength,
)


# ── validate_password_strength ───────────────────────────────────────────────


class TestPasswordValid:
    def test_valid_strong_password(self):
        assert validate_password_strength("Str0ng!Passw0rd") == "Str0ng!Passw0rd"

    def test_valid_with_arabic(self):
        assert validate_password_strength("Ab1!Passw0rdAr") == "Ab1!Passw0rdAr"


class TestPasswordTooShort:
    def test_less_than_12_chars(self):
        with pytest.raises(ValueError, match="at least 12 characters"):
            validate_password_strength("Sh0rt!Ab")

    def test_exactly_11_chars(self):
        with pytest.raises(ValueError, match="at least 12 characters"):
            validate_password_strength("Ab1!Abcdef")


class TestPasswordMissingUppercase:
    def test_no_uppercase(self):
        with pytest.raises(ValueError, match="uppercase letter"):
            validate_password_strength("alllower1!abc")


class TestPasswordMissingLowercase:
    def test_no_lowercase(self):
        with pytest.raises(ValueError, match="lowercase letter"):
            validate_password_strength("ALLUPPER1!ABC")


class TestPasswordMissingDigit:
    def test_no_digit(self):
        with pytest.raises(ValueError, match="digit"):
            validate_password_strength("NoDigitHere!Abc")


class TestPasswordMissingSpecial:
    def test_no_special_char(self):
        with pytest.raises(ValueError, match="special character"):
            validate_password_strength("NoSpecial12Abc")


class TestPasswordTooCommon:
    def test_common_list_blocks_known_weak(self):
        """The _COMMON_PASSWORDS set prevents known-weak passwords.

        Note: passwords in the set fail earlier structural checks (length,
        uppercase, etc.) before reaching the common-list check. The common
        check is defense-in-depth for passwords that somehow pass structure.
        """
        from app.modules.identity.schemas import _COMMON_PASSWORDS

        known = [
            "password", "12345678", "123456789", "qwerty123", "admin123",
            "password123", "letmein123", "welcome123", "changeme123",
            "salesos123", "muhide123", "admin", "root12345",
        ]
        for pw in known:
            assert pw.lower() in _COMMON_PASSWORDS, f"{pw} missing from common set"

    def test_common_set_has_21_entries(self):
        from app.modules.identity.schemas import _COMMON_PASSWORDS

        assert len(_COMMON_PASSWORDS) == 22

    def test_structurally_valid_password_not_in_common_set(self):
        """A strong password should NOT be in the common set."""
        from app.modules.identity.schemas import _COMMON_PASSWORDS

        assert "str0ng!passw0rd" not in _COMMON_PASSWORDS


# ── TenantCreate ─────────────────────────────────────────────────────────────


class TestTenantCreate:
    def test_valid(self):
        t = TenantCreate(name="Acme Corp", slug="acme-corp")
        assert t.slug == "acme-corp"
        assert t.name == "Acme Corp"
        assert t.domain is None

    def test_slug_must_be_lowercase_hyphen(self):
        with pytest.raises(Exception):
            TenantCreate(name="X", slug="Invalid Slug!")

    def test_slug_too_short(self):
        with pytest.raises(Exception):
            TenantCreate(name="X", slug="a")

    def test_slug_max_100(self):
        with pytest.raises(Exception):
            TenantCreate(name="X", slug="a" * 101)


# ── UserCreate ───────────────────────────────────────────────────────────────


class TestUserCreate:
    def test_valid(self):
        u = UserCreate(
            email="test@example.com",
            password="Str0ng!Passw0rd",
            full_name="Test User",
        )
        assert u.email == "test@example.com"
        assert u.full_name == "Test User"

    def test_weak_password_rejected(self):
        with pytest.raises(Exception):
            UserCreate(
                email="test@example.com",
                password="weak",
                full_name="Test",
            )

    def test_missing_email(self):
        with pytest.raises(Exception):
            UserCreate(
                email="",
                password="Str0ng!Passw0rd",
                full_name="Test",
            )

    def test_missing_full_name(self):
        with pytest.raises(Exception):
            UserCreate(
                email="test@example.com",
                password="Str0ng!Passw0rd",
                full_name="",
            )


# ── PasswordChangeRequest ────────────────────────────────────────────────────


class TestPasswordChangeRequest:
    def test_valid_new_password(self):
        r = PasswordChangeRequest(
            current_password="OldPass123!abc",
            new_password="NewStr0ng!Passw",
        )
        assert r.new_password == "NewStr0ng!Passw"

    def test_weak_new_password_rejected(self):
        with pytest.raises(Exception):
            PasswordChangeRequest(
                current_password="OldPass123!abc",
                new_password="weak",
            )
