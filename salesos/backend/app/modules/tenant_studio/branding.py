"""STORY-10-07 — CAP-092 Branding & Languages Studio models.

Logo / color / display name / locales per tenant. Not Production GO.
DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

VALID_LOCALES: frozenset[str] = frozenset({"ar", "en"})
_HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_LOGO_URL = re.compile(r"^(https://|/)[^\s]{0,500}$")


class BrandingError(ValueError):
    """Invalid branding configuration."""


@dataclass
class BrandingConfig:
    tenant_id: str
    display_name: str = ""
    logo_url: str = ""
    primary_color: str = "#0F172A"
    secondary_color: str = "#334155"
    default_locale: str = "ar"
    supported_locales: list[str] = field(default_factory=lambda: ["ar", "en"])
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "display_name": self.display_name,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "default_locale": self.default_locale,
            "supported_locales": list(self.supported_locales),
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _validate_color(name: str, value: str) -> str:
    color = (value or "").strip()
    if not color:
        raise BrandingError(f"{name} required")
    if not _HEX_COLOR.match(color):
        raise BrandingError(f"{name} must be hex #RGB or #RRGGBB")
    return "#" + color[1:].upper()


def _validate_logo_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    # Allow https://… or site-relative /… — reject javascript: and data: schemes.
    lower = raw.lower()
    if lower.startswith(("javascript:", "data:", "vbscript:")):
        raise BrandingError("logo_url scheme not allowed")
    if not (_LOGO_URL.match(raw) or raw.startswith("https://")):
        raise BrandingError("logo_url must be https:// or /path")
    if len(raw) > 512:
        raise BrandingError("logo_url too long")
    return raw


def _validate_locales(
    default_locale: str, supported_locales: list[str] | None
) -> tuple[str, list[str]]:
    loc = (default_locale or "").strip().lower()
    if loc not in VALID_LOCALES:
        raise BrandingError(f"default_locale must be one of {sorted(VALID_LOCALES)}")
    supported = []
    for item in supported_locales or [loc]:
        code = str(item).strip().lower()
        if code not in VALID_LOCALES:
            raise BrandingError(f"unsupported locale: {code}")
        if code not in supported:
            supported.append(code)
    if loc not in supported:
        supported.insert(0, loc)
    return loc, supported


def build_branding_config(
    *,
    tenant_id: str,
    display_name: str = "",
    logo_url: str = "",
    primary_color: str = "#0F172A",
    secondary_color: str = "#334155",
    default_locale: str = "ar",
    supported_locales: list[str] | None = None,
    schema_version: int = 1,
) -> BrandingConfig:
    tid = (tenant_id or "").strip()
    if not tid:
        raise BrandingError("tenant_id required")
    name = (display_name or "").strip()
    if len(name) > 200:
        raise BrandingError("display_name too long")
    loc, supported = _validate_locales(default_locale, supported_locales)
    return BrandingConfig(
        tenant_id=tid,
        display_name=name,
        logo_url=_validate_logo_url(logo_url),
        primary_color=_validate_color("primary_color", primary_color),
        secondary_color=_validate_color("secondary_color", secondary_color),
        default_locale=loc,
        supported_locales=supported,
        schema_version=max(int(schema_version), 1),
    )
