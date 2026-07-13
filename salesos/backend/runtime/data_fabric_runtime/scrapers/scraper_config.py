"""Scraper API Key Configuration — validates and manages data source credentials.

Each scraper requires an API key to access Saudi government data sources.
This module:
- Validates keys are real (not placeholders like "your-api-key-here")
- Provides a startup check that warns if keys are still placeholders
- Exposes scraper health check status
- Integrates with the settings system

Usage:
    from scraper_config import SCRAPER_KEYS, validate_scraper_keys

    if not validate_scraper_keys():
        logger.warning("Some scrapers have placeholder API keys")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


# ── Placeholder patterns to detect unconfigured keys ──────────────────────

PLACEHOLDER_PATTERNS: tuple[str, ...] = (
    "your-",
    "change-me",
    "replace-me",
    "set-me",
    "placeholder",
    "api-key-here",
    "sk-",
    "not-a-real-key",
    "test_key",
    "example_key",
    "demo_key",
)


class KeyStatus(Enum):
    VALID = "valid"
    PLACEHOLDER = "placeholder"
    MISSING = "missing"


@dataclass
class ScraperApiKey:
    """Configuration for a single scraper's API key."""

    slug: str
    env_var: str
    label_ar: str = ""
    description: str = ""
    documentation_url: str = ""
    required: bool = True

    @property
    def key(self) -> str | None:
        return os.getenv(self.env_var)

    def status(self) -> KeyStatus:
        value = self.key
        if not value:
            return KeyStatus.MISSING
        lower = value.lower()
        if any(p in lower for p in PLACEHOLDER_PATTERNS):
            return KeyStatus.PLACEHOLDER
        if len(value) < 8:
            return KeyStatus.PLACEHOLDER
        return KeyStatus.VALID

    def is_ready(self) -> bool:
        return self.status() == KeyStatus.VALID


# ── Scraper Registry ──────────────────────────────────────────────────────

SCRAPER_KEYS_REGISTRY: list[ScraperApiKey] = [
    ScraperApiKey(
        slug="balady",
        env_var="BALADY_API_KEY",
        label_ar="مفتاح بلدي API",
        description="API key for Balady (بلدى) municipal commercial license data",
        documentation_url="https://balady.gov.sa/developers",
    ),
    ScraperApiKey(
        slug="taqeem",
        env_var="TAQEEM_API_KEY",
        label_ar="مفتاح تقييم API",
        description="API key for Taqeem (تقييم) credit bureau data",
        documentation_url="https://taqeem.gov.sa/developers",
    ),
    ScraperApiKey(
        slug="rega",
        env_var="REGA_API_KEY",
        label_ar="مفتاح الهيئة العامة للعقار API",
        description="API key for REGA Real Estate General Authority data",
        documentation_url="https://rega.gov.sa/developers",
    ),
    ScraperApiKey(
        slug="najiz",
        env_var="NAJIZ_API_KEY",
        label_ar="مفتاح ناجز API",
        description="API key for Najiz (ناجز) Ministry of Justice litigation data",
        documentation_url="https://najiz.gov.sa/developers",
    ),
    ScraperApiKey(
        slug="ncnp",
        env_var="NCNP_API_KEY",
        label_ar="مفتاح الإعلانات التجارية API",
        description="API key for NCNP commercial notification platform",
        documentation_url="https://ncnp.gov.sa/developers",
    ),
]

SCRAPER_KEYS: dict[str, ScraperApiKey] = {
    k.slug: k for k in SCRAPER_KEYS_REGISTRY
}


# ── Validation Functions ──────────────────────────────────────────────────


def validate_scraper_keys() -> bool:
    """Check that all required scraper keys are configured correctly.

    Returns:
        True if all required keys are valid (not placeholders), False otherwise.

    Logs warnings for any placeholder or missing keys.
    """
    all_valid = True

    for scraper in SCRAPER_KEYS_REGISTRY:
        status = scraper.status()

        if status == KeyStatus.MISSING:
            if scraper.required:
                logger.warning(
                    "Scraper '%s' API key is MISSING. Set %s env var. "
                    "Scraper will operate in mock mode.",
                    scraper.slug, scraper.env_var,
                )
                all_valid = False
            else:
                logger.debug(
                    "Optional scraper '%s' API key not set (%s).",
                    scraper.slug, scraper.env_var,
                )
        elif status == KeyStatus.PLACEHOLDER:
            logger.warning(
                "Scraper '%s' API key appears to be a PLACEHOLDER. "
                "Check %s env var — still set to a demo/example value. "
                "%s",
                scraper.slug, scraper.env_var, scraper.description,
            )
            all_valid = False
        else:
            logger.debug("Scraper '%s' API key is valid.", scraper.slug)

    return all_valid


def get_scraper_health() -> dict[str, Any]:
    """Return health status for all configured scrapers.

    Returns:
        Dict with scraper slug → status info for health check endpoints.
    """
    result: dict[str, Any] = {
        "all_ready": True,
        "scrapers": {},
    }

    for scraper in SCRAPER_KEYS_REGISTRY:
        status = scraper.status()
        scraper_info = {
            "status": status.value,
            "env_var": scraper.env_var,
            "ready": scraper.is_ready(),
            "label_ar": scraper.label_ar,
        }

        if scraper.documentation_url:
            scraper_info["docs_url"] = scraper.documentation_url

        result["scrapers"][scraper.slug] = scraper_info

        if status != KeyStatus.VALID and scraper.required:
            result["all_ready"] = False

    return result


def get_scraper_key_for(source_slug: str) -> str | None:
    """Get the API key for a specific scraper source.

    Args:
        source_slug: Scraper identifier (balady, taqeem, etc.)

    Returns:
        API key string or None if not configured
    """
    scraper = SCRAPER_KEYS.get(source_slug)
    if scraper is None:
        return None
    return scraper.key


def validate_scraper_keys_startup() -> None:
    """Run at application startup to validate all scraper keys.

    This is called during app initialization to catch misconfigured
    scrapers before they're used in production.
    """
    all_valid = validate_scraper_keys()

    if not all_valid:
        logger.warning(
            "=" * 70 + "\n"
            "Some scraper API keys are missing or appear to be placeholders.\n"
            "Scrapers without valid keys will operate in MOCK MODE.\n"
            "Set the required environment variables for production data:\n"
            "  BALADY_API_KEY, TAQEEM_API_KEY, REGA_API_KEY, NAJIZ_API_KEY, NCNP_API_KEY\n"
            "See .env.production.template for details.\n"
            "=" * 70,
        )

    # Log summary
    valid_count = sum(1 for s in SCRAPER_KEYS_REGISTRY if s.is_ready())
    logger.info(
        "Scraper API keys: %d/%d configured",
        valid_count, len(SCRAPER_KEYS_REGISTRY),
    )
