"""Unit tests for the ANTI-ICP-only Agent Reach loop helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = BACKEND_ROOT / "scripts"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_reach_anti_icp_loop import (  # noqa: E402
    DEFAULT_CYCLE_OVERHEAD_SECONDS,
    assert_anti_icp_only,
    estimate_cycle_seconds,
    inspect_ready_rows,
    inspect_ready_value,
)

from app.modules.agent_reach.contact_enrichment import (  # noqa: E402
    EnrichmentCandidate,
    EnrichmentRow,
)


def _row(account_id: str, field: str, value: str, tier: str = "ANTI-ICP") -> EnrichmentRow:
    return EnrichmentRow(account_id, "Co", "co.com", tier, field, value)


def test_assert_anti_icp_only_accepts_exclusive_queue():
    pending = [
        EnrichmentCandidate("A1", "A", "a.com", "ANTI-ICP"),
        EnrichmentCandidate("A2", "B", "b.com", "ANTI-ICP"),
    ]
    assert_anti_icp_only(pending)


def test_assert_anti_icp_only_stops_on_mixed_tier():
    pending = [
        EnrichmentCandidate("A1", "A", "a.com", "ANTI-ICP"),
        EnrichmentCandidate("A2", "B", "b.com", "TIER C"),
    ]
    with pytest.raises(RuntimeError, match="non-ANTI-ICP"):
        assert_anti_icp_only(pending)


def test_inspect_flags_whatsapp_text_and_platform_linkedin():
    rows = [
        _row("A1", "واتساب", "https://wa.me/966501234567?text=hello"),
        _row("A2", "لينكدإن", "https://www.linkedin.com/company/grails-com"),
        _row("A3", "جوال", "+966501234567"),
    ]
    report = inspect_ready_rows(rows)
    expected_inspected = 3
    assert report["ready_rows_inspected"] == expected_inspected
    reasons = {item["id"]: item["reasons"] for item in report["flagged"]}
    assert "whatsapp_text_param" in reasons["A1"]
    assert any(reason.startswith("platform_linkedin_") for reason in reasons["A2"])
    assert "A3" not in reasons


def test_inspect_flags_twitter_intent_and_instagram_reserved():
    assert "twitter_intent_or_share" in inspect_ready_value(
        "تويتر/X",
        "https://x.com/intent/tweet?url=https://example.com",
    )
    assert "instagram_reserved" in inspect_ready_value(
        "انستقرام",
        "https://www.instagram.com/p/abc123/",
    )
    assert "social_homepage" in inspect_ready_value(
        "فيسبوك",
        "https://www.facebook.com/",
    )
    assert "tracking_subdomain" in inspect_ready_value(
        "فيسبوك",
        "https://static.facebook.com/brand",
    )


def test_inspect_repeated_fp_stops_for_tighten():
    rows = [
        _row("A1", "لينكدإن", "https://www.linkedin.com/company/odoo"),
        _row("A2", "لينكدإن", "https://www.linkedin.com/company/shopify"),
    ]
    report = inspect_ready_rows(rows)
    assert report["stop_for_tighten"] is True
    assert report["repeated_platform_footer_fp"] is True


def test_estimate_cycle_scales_with_assigned_accounts():
    full = estimate_cycle_seconds(
        200,
        workers=8,
        shard_size=25,
        sleep_seconds=1.0,
        stagger_seconds=10.0,
    )
    remainder = estimate_cycle_seconds(
        10,
        workers=8,
        shard_size=25,
        sleep_seconds=1.0,
        stagger_seconds=10.0,
    )
    assert full > remainder
    assert remainder > DEFAULT_CYCLE_OVERHEAD_SECONDS
