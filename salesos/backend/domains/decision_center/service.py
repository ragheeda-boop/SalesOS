"""Decision Center service — aggregation, audit, feedback, templates, ensemble."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable, Optional

from .models import (
    Decision,
    DecisionAudit,
    DecisionDomain,
    DecisionFeedback,
    DecisionStatus,
    DecisionTemplate,
    DecisionType,
    EnsembleVote,
    FeedbackAggregate,
    FeedbackRating,
)
from .repository import DecisionCenterRepository


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_id() -> str:
    return str(uuid.uuid4())


class DecisionCenterService:
    """Unified Decision Center: aggregates, audits, collects feedback, manages templates, ensembles."""

    def __init__(self, repository: DecisionCenterRepository) -> None:
        self._repo = repository

    # ── B-1: Decision Center Aggregation ──────────────────────────────

    async def create_decision(
        self,
        domain: str,
        decision_type: str,
        entity_id: str,
        entity_type: str,
        decision: str,
        confidence: float,
        reasoning: str,
        provider: str,
        tenant_id: str,
        alternatives: Optional[list[dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
        ensemble_votes: Optional[list[EnsembleVote]] = None,
    ) -> Decision:
        dec = Decision(
            id=_generate_id(),
            domain=DecisionDomain(domain),
            type=DecisionType(decision_type),
            entity_id=entity_id,
            entity_type=entity_type,
            decision=decision,
            confidence=max(0.0, min(1.0, confidence)),
            reasoning=reasoning,
            provider=provider,
            alternatives=alternatives or [],
            timestamp=_now(),
            status=DecisionStatus.ACTIVE,
            metadata={**(metadata or {}), "tenant_id": tenant_id},
            ensemble_votes=ensemble_votes,
            is_ensemble=ensemble_votes is not None and len(ensemble_votes) >= 2,
        )
        await self._repo.save_decision(dec)
        return dec

    async def list_decisions(
        self,
        tenant_id: str,
        domain: Optional[str] = None,
        decision_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        confidence_min: Optional[float] = None,
        confidence_max: Optional[float] = None,
        entity_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Decision], int]:
        return await self._repo.list_decisions(
            tenant_id,
            domain=domain,
            decision_type=decision_type,
            date_from=date_from,
            date_to=date_to,
            confidence_min=confidence_min,
            confidence_max=confidence_max,
            entity_id=entity_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def get_decision(self, decision_id: str, tenant_id: str) -> Optional[Decision]:
        return await self._repo.get_decision(decision_id, tenant_id)

    # ── B-2: Audit Trail ──────────────────────────────────────────────

    async def create_audit(
        self,
        decision_id: str,
        input_context: dict[str, Any],
        reasoning_steps: list[dict[str, Any]],
        confidence_breakdown: dict[str, Any],
        provider_used: str,
        alternatives_considered: list[dict[str, Any]],
        tenant_id: str,
    ) -> Optional[DecisionAudit]:
        decision = await self._repo.get_decision(decision_id, tenant_id)
        if not decision:
            return None
        audit = DecisionAudit(
            decision_id=decision_id,
            input_context=input_context,
            reasoning_steps=reasoning_steps,
            confidence_breakdown=confidence_breakdown,
            provider_used=provider_used,
            alternatives_considered=alternatives_considered,
            timestamp=_now(),
            ensemble_metadata={
                "isEnsemble": decision.is_ensemble,
                "voteCount": len(decision.ensemble_votes) if decision.ensemble_votes else 0,
            }
            if decision.is_ensemble
            else None,
        )
        await self._repo.save_audit(audit)
        return audit

    async def get_audit(self, decision_id: str, tenant_id: str) -> Optional[DecisionAudit]:
        return await self._repo.get_audit(decision_id, tenant_id)

    # ── B-3: Feedback ─────────────────────────────────────────────────

    async def submit_feedback(
        self,
        decision_id: str,
        rating: str,
        tenant_id: str,
        comment: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> Optional[DecisionFeedback]:
        decision = await self._repo.get_decision(decision_id, tenant_id)
        if not decision:
            return None
        fb = DecisionFeedback(
            id=_generate_id(),
            decision_id=decision_id,
            rating=FeedbackRating(rating),
            comment=comment,
            actor_id=actor_id,
            created_at=_now(),
        )
        await self._repo.save_feedback(fb)
        return fb

    async def get_feedback_for_decision(
        self, decision_id: str, tenant_id: str
    ) -> list[DecisionFeedback]:
        return await self._repo.get_feedback_for_decision(decision_id, tenant_id)

    async def get_feedback_aggregates(self, tenant_id: str) -> list[FeedbackAggregate]:
        return await self._repo.get_feedback_by_type(tenant_id)

    # ── B-4: Decision Templates ───────────────────────────────────────

    async def create_template(
        self,
        name: str,
        template_type: str,
        config: dict[str, Any],
        tenant_id: str,
    ) -> DecisionTemplate:
        template = DecisionTemplate(
            id=_generate_id(),
            name=name,
            type=DecisionType(template_type),
            config=config,
            tenant_id=tenant_id,
            created_at=_now(),
        )
        await self._repo.save_template(template)
        return template

    async def get_template(self, template_id: str, tenant_id: str) -> Optional[DecisionTemplate]:
        return await self._repo.get_template(template_id, tenant_id)

    async def list_templates(self, template_type: Optional[str] = None, tenant_id: str = "") -> list[DecisionTemplate]:
        return await self._repo.list_templates(template_type, tenant_id)

    async def update_template(
        self, template_id: str, name: Optional[str] = None, config: Optional[dict] = None, tenant_id: str = ""
    ) -> Optional[DecisionTemplate]:
        updates = {}
        if name is not None:
            updates["name"] = name
        if config is not None:
            updates["config"] = config
        return await self._repo.update_template(template_id, updates, tenant_id)

    async def delete_template(self, template_id: str, tenant_id: str) -> bool:
        return await self._repo.delete_template(template_id, tenant_id)

    async def seed_default_templates(self, tenant_id: str) -> list[DecisionTemplate]:
        defaults = [
            {
                "name": "Lead Qualification",
                "type": "lead_qualification",
                "config": {
                    "factors": [
                        {"key": "intent_score", "weight": 0.3, "threshold": 0.5},
                        {"key": "engagement_score", "weight": 0.25, "threshold": 0.4},
                        {"key": "firmographic_fit", "weight": 0.25, "threshold": 0.6},
                        {"key": "data_completeness", "weight": 0.2, "threshold": 0.7},
                    ],
                    "auto_qualify_threshold": 0.75,
                    "manual_review_range": [0.4, 0.75],
                    "auto_disqualify_below": 0.25,
                },
            },
            {
                "name": "Deal Progression",
                "type": "deal_progression",
                "config": {
                    "factors": [
                        {"key": "stage_duration_days", "weight": 0.2, "threshold": 30},
                        {"key": "stakeholder_engagement", "weight": 0.25, "threshold": 0.6},
                        {"key": "competitive_pressure", "weight": 0.2, "threshold": 0.5},
                        {"key": "budget_confirmation", "weight": 0.35, "threshold": 0.8},
                    ],
                    "stage_criteria": {
                        "discovery": ["initial_meeting", "pain_identified"],
                        "evaluation": ["demo_completed", "requirements_mapped"],
                        "proposal": ["budget_confirmed", "decision_maker_engaged"],
                        "negotiation": ["terms_discussed", "legal_review"],
                        "closed_won": ["contract_signed"],
                    },
                    "next_action_threshold": 0.6,
                },
            },
            {
                "name": "Renewal Risk",
                "type": "renewal_risk",
                "config": {
                    "factors": [
                        {"key": "usage_decline_pct", "weight": 0.3, "threshold": 0.2},
                        {"key": "support_ticket_trend", "weight": 0.2, "threshold": 3},
                        {"key": "nps_score", "weight": 0.25, "threshold": 7},
                        {"key": "competitor_mentions", "weight": 0.25, "threshold": 2},
                    ],
                    "risk_score_ranges": {
                        "low": [0.0, 0.3],
                        "medium": [0.3, 0.6],
                        "high": [0.6, 0.8],
                        "critical": [0.8, 1.0],
                    },
                    "interventions": {
                        "low": "standard_outreach",
                        "medium": "executive_check_in",
                        "high": "success_plan_created",
                        "critical": "rescue_campaign",
                    },
                },
            },
            {
                "name": "Pricing Optimization",
                "type": "pricing",
                "config": {
                    "discount_rules": [
                        {"max_discount": 0.1, "auto_approve": True},
                        {"max_discount": 0.2, "auto_approve": False, "approver_role": "sales_manager"},
                        {"max_discount": 0.3, "auto_approve": False, "approver_role": "vp_sales"},
                        {"max_discount": 1.0, "auto_approve": False, "approver_role": "cfo"},
                    ],
                    "optimization_factors": [
                        {"key": "deal_size", "weight": 0.3},
                        {"key": "competitive_situation", "weight": 0.25},
                        {"key": "strategic_value", "weight": 0.25},
                        {"key": "volume_commitment", "weight": 0.2},
                    ],
                    "approval_thresholds": {
                        "auto": 0.1,
                        "manager": 0.2,
                        "vp": 0.3,
                        "cfo": 0.5,
                    },
                },
            },
        ]
        templates = []
        for d in defaults:
            t = await self.create_template(d["name"], d["type"], d["config"], tenant_id)
            templates.append(t)
        return templates

    # ── B-5: Multi-Provider Ensemble ──────────────────────────────────

    async def ensemble_decide(
        self,
        domain: str,
        decision_type: str,
        entity_id: str,
        entity_type: str,
        tenant_id: str,
        providers: list[Callable[[dict], Awaitable[dict]]],
        context: dict[str, Any],
        deal_value: Optional[float] = None,
    ) -> Decision:
        if len(providers) < 2:
            raise ValueError("Ensemble requires at least 2 providers")

        votes: list[EnsembleVote] = []
        for provider_fn in providers:
            try:
                result = await provider_fn(context)
                votes.append(
                    EnsembleVote(
                        provider=result.get("provider", "unknown"),
                        decision=result.get("decision", "abstain"),
                        confidence=result.get("confidence", 0.0),
                        reasoning=result.get("reasoning", ""),
                        raw_response=result,
                        latency_ms=result.get("latency_ms"),
                    )
                )
            except Exception as exc:
                votes.append(
                    EnsembleVote(
                        provider=getattr(provider_fn, "__name__", "unknown"),
                        decision="error",
                        confidence=0.0,
                        reasoning=f"Provider error: {exc}",
                    )
                )

        decision_text, winning_confidence = self._tally_votes(votes)
        reasoning = self._build_ensemble_reasoning(votes, decision_text)

        return await self.create_decision(
            domain=domain,
            decision_type=decision_type,
            entity_id=entity_id,
            entity_type=entity_type,
            decision=decision_text,
            confidence=winning_confidence,
            reasoning=reasoning,
            provider="ensemble",
            tenant_id=tenant_id,
            metadata={"deal_value": deal_value, "provider_count": len(providers)},
            ensemble_votes=votes,
        )

    def _tally_votes(self, votes: list[EnsembleVote]) -> tuple[str, float]:
        from collections import Counter

        valid_votes = [v for v in votes if v.decision not in ("error", "abstain")]
        if not valid_votes:
            return "insufficient_data", 0.0

        counts = Counter(v.decision for v in valid_votes)
        winner, count = counts.most_common(1)[0]
        winner_votes = [v for v in valid_votes if v.decision == winner]
        avg_confidence = sum(v.confidence for v in winner_votes) / len(winner_votes)

        return winner, round(avg_confidence, 4)

    def _build_ensemble_reasoning(self, votes: list[EnsembleVote], winner: str) -> str:
        parts = [f"Ensemble decision: {winner}"]
        for v in votes:
            parts.append(
                f"- {v.provider}: {v.decision} (confidence={v.confidence:.2f}) — {v.reasoning}"
            )
        return ". ".join(parts)
