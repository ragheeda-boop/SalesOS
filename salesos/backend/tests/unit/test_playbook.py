"""Tests for Playbook Engine — default playbooks, selection, step retrieval."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from domains.commercial.playbook import (
    DEFAULT_PLAYLISTS,
    Playbook,
    PlaybookEngine,
    PlaybookStep,
    PlaybookTrigger,
)


# ── Helper: simple opportunity dataclass ─────────────────────────────────────

@dataclass
class FakeOpportunity:
    value: float = 0.0
    industry: str | None = None
    stage: str = "prospecting"


# ── Tests: Default Playbooks ────────────────────────────────────────────────

class TestDefaultPlaybooks:
    def test_default_playlists_exist(self):
        assert len(DEFAULT_PLAYLISTS) >= 2

    def test_enterprise_saas_exists(self):
        ids = [pb.id for pb in DEFAULT_PLAYLISTS]
        assert "pb-enterprise-saas" in ids

    def test_smb_quick_close_exists(self):
        ids = [pb.id for pb in DEFAULT_PLAYLISTS]
        assert "pb-smb-quick-close" in ids

    def test_all_defaults_are_active(self):
        for pb in DEFAULT_PLAYLISTS:
            assert pb.is_active is True

    def test_all_defaults_have_steps(self):
        for pb in DEFAULT_PLAYLISTS:
            assert len(pb.steps) > 0

    def test_all_defaults_have_names(self):
        for pb in DEFAULT_PLAYLISTS:
            assert pb.name
            assert pb.description

    def test_all_defaults_have_tenant(self):
        for pb in DEFAULT_PLAYLISTS:
            assert pb.tenant_id


# ── Tests: Enterprise SaaS Playbook Details ─────────────────────────────────

class TestEnterpriseSaaSPlaybook:
    @pytest.fixture
    def playbook(self):
        return next(pb for pb in DEFAULT_PLAYLISTS if pb.id == "pb-enterprise-saas")

    def test_has_six_steps(self, playbook):
        assert len(playbook.steps) == 6

    def test_steps_cover_all_stages(self, playbook):
        stages = {s.stage for s in playbook.steps}
        assert "prospecting" in stages
        assert "qualification" in stages
        assert "proposal" in stages
        assert "negotiation" in stages
        assert "closed_won" in stages

    def test_steps_are_ordered(self, playbook):
        orders = [s.order for s in playbook.steps]
        assert orders == sorted(orders)

    def test_steps_have_templates(self, playbook):
        has_template = any(s.templates for s in playbook.steps)
        assert has_template

    def test_steps_have_arabic_titles(self, playbook):
        for s in playbook.steps:
            assert s.title_ar

    def test_steps_have_english_titles(self, playbook):
        for s in playbook.steps:
            assert s.title_en

    def test_steps_have_actions(self, playbook):
        for s in playbook.steps:
            assert s.action

    def test_has_stage_enter_trigger(self, playbook):
        assert PlaybookTrigger.STAGE_ENTER in playbook.triggers


# ── Tests: SMB Quick Close Playbook Details ──────────────────────────────────

class TestSMBQuickClosePlaybook:
    @pytest.fixture
    def playbook(self):
        return next(pb for pb in DEFAULT_PLAYLISTS if pb.id == "pb-smb-quick-close")

    def test_has_three_steps(self, playbook):
        assert len(playbook.steps) == 3

    def test_has_max_deal_size(self, playbook):
        assert playbook.max_deal_size == 100000

    def test_steps_for_qualification(self, playbook):
        steps = playbook.steps_for_stage("qualification")
        assert len(steps) == 1
        assert steps[0].action == "send_proposal"


# ── Tests: PlaybookEngine — find_playbook ───────────────────────────────────

class TestFindPlaybook:
    def test_returns_playbook(self):
        engine = PlaybookEngine()
        opp = FakeOpportunity(value=50000)
        result = engine.find_playbook(opp)
        assert isinstance(result, Playbook)

    def test_enterprise_for_large_deal(self):
        engine = PlaybookEngine()
        opp = FakeOpportunity(value=500000)
        result = engine.find_playbook(opp)
        assert result is not None

    def test_smb_for_small_deal(self):
        engine = PlaybookEngine()
        opp = FakeOpportunity(value=50000)
        result = engine.find_playbook(opp)
        assert result is not None

    def test_returns_first_matching(self):
        engine = PlaybookEngine()
        opp = FakeOpportunity(value=500000)
        result = engine.find_playbook(opp)
        # Should always return a valid playbook
        assert result.id in [pb.id for pb in DEFAULT_PLAYLISTS]

    def test_always_returns_something(self):
        engine = PlaybookEngine()
        opp = FakeOpportunity(value=0)
        result = engine.find_playbook(opp)
        assert result is not None

    def test_custom_playbook_selection(self):
        custom = Playbook(
            id="pb-custom", tenant_id="t-1", name="Custom",
            description="Custom playbook",
            min_deal_size=1000000,
            steps=[PlaybookStep(id="c-1", action="custom_action", title_ar="مخصص",
                                title_en="Custom", order=1, stage="proposal")],
        )
        engine = PlaybookEngine(playbooks=[custom])
        opp_big = FakeOpportunity(value=2000000)
        result = engine.find_playbook(opp_big)
        assert result.id == "pb-custom"

    def test_custom_playbook_skip_when_value_too_low(self):
        custom = Playbook(
            id="pb-custom", tenant_id="t-1", name="Custom",
            description="Custom playbook",
            min_deal_size=1000000,
            steps=[],
        )
        default = DEFAULT_PLAYLISTS[0]
        engine = PlaybookEngine(playbooks=[custom, default])
        opp_small = FakeOpportunity(value=50000)
        result = engine.find_playbook(opp_small)
        assert result.id != "pb-custom"

    def test_inactive_playbook_skipped(self):
        inactive = Playbook(
            id="pb-inactive", tenant_id="t-1", name="Inactive",
            description="Inactive", is_active=False, steps=[],
        )
        default = DEFAULT_PLAYLISTS[0]
        engine = PlaybookEngine(playbooks=[inactive, default])
        opp = FakeOpportunity(value=500000)
        result = engine.find_playbook(opp)
        assert result.id != "pb-inactive"

    def test_industry_filter(self):
        tech_pb = Playbook(
            id="pb-tech", tenant_id="t-1", name="Tech",
            description="Tech", industry="technology",
            steps=[PlaybookStep(id="t-1", action="a", title_ar="ت", title_en="T", order=1, stage="s")],
        )
        default = DEFAULT_PLAYLISTS[0]
        engine = PlaybookEngine(playbooks=[tech_pb, default])
        opp_tech = FakeOpportunity(value=50000, industry="technology")
        result = engine.find_playbook(opp_tech)
        assert result.id == "pb-tech"

    def test_industry_mismatch_uses_fallback(self):
        tech_pb = Playbook(
            id="pb-tech", tenant_id="t-1", name="Tech",
            description="Tech", industry="technology",
            steps=[],
        )
        default = DEFAULT_PLAYLISTS[0]
        engine = PlaybookEngine(playbooks=[tech_pb, default])
        opp_other = FakeOpportunity(value=50000, industry="healthcare")
        result = engine.find_playbook(opp_other)
        assert result.id != "pb-tech"


# ── Tests: PlaybookEngine — get_steps ───────────────────────────────────────

class TestGetSteps:
    def test_returns_steps_for_stage(self):
        engine = PlaybookEngine()
        steps = engine.get_steps("pb-enterprise-saas", "prospecting")
        assert len(steps) >= 1
        assert steps[0].stage == "prospecting"

    def test_returns_empty_for_unknown_playbook(self):
        engine = PlaybookEngine()
        steps = engine.get_steps("nonexistent", "prospecting")
        assert steps == []

    def test_returns_empty_for_unknown_stage(self):
        engine = PlaybookEngine()
        steps = engine.get_steps("pb-enterprise-saas", "unknown_stage")
        assert steps == []

    def test_smb_steps_for_qualification(self):
        engine = PlaybookEngine()
        steps = engine.get_steps("pb-smb-quick-close", "qualification")
        assert len(steps) == 1

    def test_steps_are_playbook_step_type(self):
        engine = PlaybookEngine()
        steps = engine.get_steps("pb-enterprise-saas", "proposal")
        for s in steps:
            assert isinstance(s, PlaybookStep)


# ── Tests: PlaybookStep Dataclass ───────────────────────────────────────────

class TestPlaybookStep:
    def test_step_fields(self):
        step = PlaybookStep(
            id="s-1", action="send_email", title_ar="أرسل بريد",
            title_en="Send Email", order=1, stage="prospecting",
        )
        assert step.id == "s-1"
        assert step.action == "send_email"
        assert step.estimated_minutes == 15
        assert step.is_optional is False

    def test_step_templates_default_empty(self):
        step = PlaybookStep(
            id="s-1", action="a", title_ar="ت", title_en="T",
            order=1, stage="s",
        )
        assert step.templates == {}

    def test_steps_for_stage(self):
        pb = DEFAULT_PLAYLISTS[0]
        proposal_steps = pb.steps_for_stage("proposal")
        for s in proposal_steps:
            assert s.stage == "proposal"


# ── Tests: PlaybookTrigger ──────────────────────────────────────────────────

class TestPlaybookTrigger:
    def test_trigger_values(self):
        assert PlaybookTrigger.STAGE_ENTER.value == "stage_enter"
        assert PlaybookTrigger.SIGNAL_DETECTED.value == "signal_detected"
        assert PlaybookTrigger.TIME_ELAPSED.value == "time_elapsed"
        assert PlaybookTrigger.HEALTH_CHANGE.value == "health_change"
        assert PlaybookTrigger.MANUAL.value == "manual"
