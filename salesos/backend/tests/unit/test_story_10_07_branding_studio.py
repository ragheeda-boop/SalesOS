"""STORY-10-07 — Branding & Languages Studio."""

from __future__ import annotations

import pytest

from app.modules.tenant_studio.branding import BrandingError, build_branding_config
from app.modules.tenant_studio.branding_store import MemBrandingStore


def test_upsert_and_get_live_per_tenant() -> None:
    store = MemBrandingStore()
    row = store.upsert(
        tenant_id="t1",
        display_name="Acme KSA",
        logo_url="https://cdn.example.com/logo.svg",
        primary_color="#1D4ED8",
        secondary_color="#93C5FD",
        default_locale="ar",
        supported_locales=["ar", "en"],
    )
    assert row.display_name == "Acme KSA"
    assert row.primary_color == "#1D4ED8"
    got = store.get(tenant_id="t1")
    assert got.display_name == "Acme KSA"
    assert got.schema_version == 1


def test_tenant_isolation() -> None:
    store = MemBrandingStore()
    store.upsert(tenant_id="t1", display_name="One", primary_color="#111111")
    other = store.get(tenant_id="t2")
    assert other.display_name == ""
    assert other.tenant_id == "t2"


def test_reject_bad_color_and_locale() -> None:
    with pytest.raises(BrandingError, match="hex"):
        build_branding_config(tenant_id="t1", primary_color="blue")
    with pytest.raises(BrandingError, match="locale"):
        build_branding_config(tenant_id="t1", default_locale="fr")


def test_reject_dangerous_logo_scheme() -> None:
    with pytest.raises(BrandingError, match="scheme|logo_url"):
        build_branding_config(tenant_id="t1", logo_url="javascript:alert(1)")


def test_schema_version_bumps_on_update() -> None:
    store = MemBrandingStore()
    store.upsert(tenant_id="t1", display_name="A", primary_color="#000000")
    v2 = store.upsert(tenant_id="t1", display_name="B", primary_color="#FFFFFF")
    assert v2.schema_version == 2
    assert v2.display_name == "B"


def test_default_locale_included_in_supported() -> None:
    cfg = build_branding_config(
        tenant_id="t1",
        default_locale="en",
        supported_locales=["ar"],
    )
    assert cfg.default_locale == "en"
    assert "en" in cfg.supported_locales
