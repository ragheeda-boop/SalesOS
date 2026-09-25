"""Human-in-the-Loop domain logic.

FeedbackService: accept/reject/modify NBA recommendations
OutcomeService: log call/email/meeting outcomes
FollowupService: deterministic follow-up generation from outcomes
WorkQueueService: My Day read model (actions + follow-ups + scores)
"""
import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.signal_actions.hitl_models import (
    ActionOutcome,
    FeedbackDecision,
    NbaFeedback,
    SalesFollowup,
)

logger = logging.getLogger(__name__)


async def _pin(session: AsyncSession, tenant_id: str) -> None:
    await session.execute(
        text("SELECT set_config('app.tenant_id', :t, true)"),
        {"t": str(tenant_id)},
    )


class FeedbackService:
    """Accept / Reject / Modify NBA recommendations."""

    def __init__(self, session_factory):
        self._factory = session_factory

    async def record(
        self,
        tenant_id: str,
        action_id: str,
        recommendation_id: str,
        company_name: str,
        seller_id: str,
        decision: str,
        original_action_type: str,
        reason_code: str = "",
        notes: str = "",
        modified_action_type: str = "",
        modified_target_contact_id: str = "",
    ) -> NbaFeedback:
        fb = NbaFeedback(
            id=str(uuid4()),
            tenant_id=tenant_id,
            company_name=company_name,
            action_id=action_id,
            recommendation_id=recommendation_id,
            seller_id=seller_id,
            decision=decision,
            reason_code=reason_code,
            notes=notes,
            original_action_type=original_action_type,
            modified_action_type=modified_action_type,
            modified_target_contact_id=modified_target_contact_id,
        )

        async with self._factory() as session:
            await _pin(session, tenant_id)
            await session.execute(
                text("""
                    INSERT INTO nba_feedback
                        (id, tenant_id, company_name, action_id, recommendation_id,
                         seller_id, decision, reason_code, notes,
                         original_action_type, modified_action_type,
                         modified_target_contact_id, metadata, created_at)
                    VALUES
                        (:id, :tenant_id, :company_name, :action_id, :recommendation_id,
                         :seller_id, :decision, :reason_code, :notes,
                         :original_action_type, :modified_action_type,
                         :modified_target_contact_id, :metadata, :created_at)
                """),
                {
                    "id": fb.id,
                    "tenant_id": tenant_id,
                    "company_name": company_name,
                    "action_id": action_id,
                    "recommendation_id": recommendation_id,
                    "seller_id": seller_id,
                    "decision": decision,
                    "reason_code": reason_code,
                    "notes": notes,
                    "original_action_type": original_action_type,
                    "modified_action_type": modified_action_type or None,
                    "modified_target_contact_id": modified_target_contact_id or None,
                    "metadata": "{}",
                    "created_at": fb.created_at,
                },
            )
            if decision == FeedbackDecision.REJECTED.value:
                await session.execute(
                    text("""
                        UPDATE agent_sales_actions
                        SET status = 'skipped',
                            outcome = 'rejected',
                            completed_at = now()
                        WHERE id::text = :action_id
                          AND tenant_id = :tenant_id
                          AND status = 'pending'
                    """),
                    {"action_id": action_id, "tenant_id": tenant_id},
                )
                await session.execute(
                    text("""
                        DELETE FROM tasks
                        WHERE id::text = (
                            SELECT metadata->>'crm_task_id'
                            FROM agent_sales_actions
                            WHERE id::text = :action_id AND tenant_id = :tenant_id
                              AND status = 'skipped'
                        )
                          AND tenant_id::text = :tenant_id
                          AND source = 'nba'
                          AND completed = false
                    """),
                    {"action_id": action_id, "tenant_id": tenant_id},
                )
            await session.commit()

        logger.info("nba_feedback recorded: %s -> %s for %s", action_id, decision, company_name)
        return fb

    async def get_by_company(self, tenant_id: str, company_name: str) -> list[NbaFeedback]:
        async with self._factory() as session:
            await _pin(session, tenant_id)
            rows = await session.execute(
                text("SELECT * FROM nba_feedback WHERE company_name = :c ORDER BY created_at DESC"),
                {"c": company_name},
            )
            return [self._map(r) for r in rows.fetchall()]

    async def get_by_seller(self, tenant_id: str, seller_id: str, limit: int = 50) -> list[NbaFeedback]:
        async with self._factory() as session:
            await _pin(session, tenant_id)
            rows = await session.execute(
                text("SELECT * FROM nba_feedback WHERE seller_id = :s ORDER BY created_at DESC LIMIT :l"),
                {"s": seller_id, "l": limit},
            )
            return [self._map(r) for r in rows.fetchall()]

    def _map(self, row) -> NbaFeedback:
        return NbaFeedback(
            id=str(row.id),
            tenant_id=row.tenant_id,
            company_name=row.company_name,
            action_id=str(row.action_id),
            recommendation_id=str(row.recommendation_id),
            seller_id=row.seller_id,
            decision=row.decision,
            reason_code=row.reason_code or "",
            notes=row.notes or "",
            original_action_type=row.original_action_type,
            modified_action_type=row.modified_action_type or "",
            modified_target_contact_id=row.modified_target_contact_id or "",
            metadata=row.metadata or {},
            created_at=row.created_at,
        )


class OutcomeService:
    """Log call/email/meeting outcomes."""

    def __init__(self, session_factory):
        self._factory = session_factory

    async def record(
        self,
        tenant_id: str,
        action_id: str,
        company_name: str,
        seller_id: str,
        outcome_type: str,
        opportunity_id: str | None = None,
        idempotency_key: str | None = None,
        notes: str = "",
        contact_reached: str = "",
        duration_seconds: int | None = None,
        followup_required: bool = False,
        occurred_at: datetime | None = None,
    ) -> ActionOutcome:
        outcome = ActionOutcome(
            id=str(uuid4()),
            tenant_id=tenant_id,
            action_id=action_id,
            company_name=company_name,
            opportunity_id=opportunity_id,
            seller_id=seller_id,
            outcome_type=outcome_type,
            notes=notes,
            contact_reached=contact_reached,
            duration_seconds=duration_seconds,
            followup_required=followup_required,
            occurred_at=occurred_at or datetime.now(UTC),
        )

        async with self._factory() as session:
            await _pin(session, tenant_id)
            if opportunity_id:
                opportunity = await session.execute(
                    text(
                        "SELECT id FROM commercial_opportunities "
                        "WHERE id = :opportunity_id AND tenant_id = :tenant_id"
                    ),
                    {"opportunity_id": opportunity_id, "tenant_id": tenant_id},
                )
                if opportunity.scalar_one_or_none() is None:
                    raise OutcomeOpportunityNotFound(opportunity_id)

            inserted = await session.execute(
                text("""
                    INSERT INTO action_outcomes
                        (id, tenant_id, action_id, company_name, seller_id,
                         opportunity_id, idempotency_key, outcome_type, notes,
                         contact_reached, duration_seconds, followup_required,
                         occurred_at, metadata, created_at)
                    VALUES
                        (:id, :tenant_id, :action_id, :company_name, :seller_id,
                         :opportunity_id, :idempotency_key, :outcome_type, :notes,
                         :contact_reached, :duration_seconds, :followup_required,
                         :occurred_at, :metadata, :created_at)
                    ON CONFLICT (tenant_id, action_id, idempotency_key) DO NOTHING
                    RETURNING id
                """),
                {
                    "id": outcome.id,
                    "tenant_id": tenant_id,
                    "action_id": action_id,
                    "company_name": company_name,
                    "seller_id": seller_id,
                    "opportunity_id": opportunity_id,
                    "idempotency_key": idempotency_key,
                    "outcome_type": outcome_type,
                    "notes": notes,
                    "contact_reached": contact_reached,
                    "duration_seconds": duration_seconds,
                    "followup_required": followup_required,
                    "occurred_at": outcome.occurred_at,
                    "metadata": "{}",
                    "created_at": outcome.created_at,
                },
            )
            if inserted.scalar_one_or_none() is None:
                existing = await session.execute(
                    text(
                        "SELECT * FROM action_outcomes "
                        "WHERE tenant_id = :tenant_id AND action_id = :action_id "
                        "AND idempotency_key = :idempotency_key"
                    ),
                    {
                        "tenant_id": tenant_id,
                        "action_id": action_id,
                        "idempotency_key": idempotency_key,
                    },
                )
                row = existing.fetchone()
                if row is not None:
                    replay = self._map(row)
                    replay.is_replay = True
                    return replay
            await session.commit()

        logger.info("action_outcome recorded: %s -> %s for %s", action_id, outcome_type, company_name)
        return outcome

    async def get_by_company(self, tenant_id: str, company_name: str) -> list[ActionOutcome]:
        async with self._factory() as session:
            await _pin(session, tenant_id)
            rows = await session.execute(
                text("SELECT * FROM action_outcomes WHERE company_name = :c ORDER BY occurred_at DESC"),
                {"c": company_name},
            )
            return [self._map(r) for r in rows.fetchall()]

    async def get_by_action(self, tenant_id: str, action_id: str) -> ActionOutcome | None:
        async with self._factory() as session:
            await _pin(session, tenant_id)
            rows = await session.execute(
                text("SELECT * FROM action_outcomes WHERE action_id = :a LIMIT 1"),
                {"a": action_id},
            )
            row = rows.fetchone()
            return self._map(row) if row else None

    def _map(self, row) -> ActionOutcome:
        return ActionOutcome(
            id=str(row.id),
            tenant_id=row.tenant_id,
            action_id=str(row.action_id),
            company_name=row.company_name,
            opportunity_id=row.opportunity_id,
            seller_id=row.seller_id,
            outcome_type=row.outcome_type,
            notes=row.notes or "",
            contact_reached=row.contact_reached or "",
            duration_seconds=row.duration_seconds,
            followup_required=row.followup_required,
            occurred_at=row.occurred_at,
            metadata=row.metadata or {},
            created_at=row.created_at,
        )


class OutcomeOpportunityNotFound(ValueError):
    """The optional outcome-to-opportunity link is absent or cross-tenant."""


class FollowupService:
    """Deterministic follow-up generation from outcomes.

    Rules:
    - meeting_set -> prepare brief (tomorrow)
    - connected + positive -> send proposal (this week)
    - connected + neutral -> follow up email (2 days)
    - no_answer -> retry call (3 days)
    - left_voicemail -> retry call (2 days)
    - email_sent -> wait 3 days then follow up
    - negative -> skip (no follow-up)
    - connected + negative -> skip
    """

    FOLLOWUP_RULES: dict[str, dict] = {
        "meeting_set": {
            "action_type": "meeting",
            "title_template": "Prepare brief for {company}",
            "desc_template": "Meeting scheduled. Prepare context, agenda, and proposal materials.",
            "delay_days": 1,
        },
        "connected+positive": {
            "action_type": "proposal",
            "title_template": "Send proposal to {company}",
            "desc_template": "Positive conversation. Send tailored proposal with pricing.",
            "delay_days": 5,
        },
        "connected+neutral": {
            "action_type": "email",
            "title_template": "Follow up with {company}",
            "desc_template": "Conversation was neutral. Send follow-up email with additional context.",
            "delay_days": 2,
        },
        "connected+negative": {
            "action_type": "no_action",
            "title_template": "Close {company}",
            "desc_template": "Negative response. No further action recommended.",
            "delay_days": 0,
        },
        "no_answer": {
            "action_type": "call",
            "title_template": "Retry call to {company}",
            "desc_template": "No answer. Try again in a few days.",
            "delay_days": 3,
        },
        "left_voicemail": {
            "action_type": "call",
            "title_template": "Retry call to {company}",
            "desc_template": "Left voicemail. Follow up with another call.",
            "delay_days": 2,
        },
        "email_sent": {
            "action_type": "follow_up",
            "title_template": "Check email response from {company}",
            "desc_template": "Email sent. Check for response and follow up if needed.",
            "delay_days": 3,
        },
        "negative": {
            "action_type": "no_action",
            "title_template": "Close {company}",
            "desc_template": "Negative outcome. No further action recommended.",
            "delay_days": 0,
        },
    }

    def __init__(self, session_factory):
        self._factory = session_factory

    def _resolve_rule(self, outcome_type: str, notes: str = "") -> dict:
        """Resolve follow-up rule from outcome type + context."""
        # Check compound rules first (connected+sentiment)
        if outcome_type == "connected":
            notes_lower = notes.lower()
            if any(w in notes_lower for w in ["positive", "interested", "great", "good"]):
                return self.FOLLOWUP_RULES["connected+positive"]
            elif any(w in notes_lower for w in ["negative", "not interested", "no budget", "pass"]):
                return self.FOLLOWUP_RULES["connected+negative"]
            return self.FOLLOWUP_RULES["connected+neutral"]

        return self.FOLLOWUP_RULES.get(outcome_type, {
            "action_type": "follow_up",
            "title_template": "Follow up with {company}",
            "desc_template": "Outcome recorded. Follow up as needed.",
            "delay_days": 2,
        })

    async def generate(
        self,
        tenant_id: str,
        outcome: ActionOutcome,
    ) -> SalesFollowup | None:
        """Generate a follow-up from an outcome. Returns None if no follow-up needed."""
        rule = self._resolve_rule(outcome.outcome_type, outcome.notes)

        # No follow-up for negative outcomes
        if rule["action_type"] == "no_action":
            return None

        due_at = outcome.occurred_at + timedelta(days=rule["delay_days"])
        title = rule["title_template"].format(company=outcome.company_name)
        description = rule["desc_template"]
        rationale = f"Auto-generated from outcome: {outcome.outcome_type}"

        followup = SalesFollowup(
            id=str(uuid4()),
            tenant_id=tenant_id,
            parent_action_id=outcome.action_id,
            parent_outcome_id=outcome.id,
            company_name=outcome.company_name,
            seller_id=outcome.seller_id,
            generated_action_type=rule["action_type"],
            title=title,
            description=description,
            due_at=due_at,
            rationale=rationale,
        )

        async with self._factory() as session:
            await _pin(session, tenant_id)
            await session.execute(
                text("""
                    INSERT INTO sales_followups
                        (id, tenant_id, parent_action_id, parent_outcome_id,
                         company_name, seller_id, generated_action_type,
                         title, description, due_at, rationale,
                         status, metadata, created_at)
                    VALUES
                        (:id, :tenant_id, :parent_action_id, :parent_outcome_id,
                         :company_name, :seller_id, :generated_action_type,
                         :title, :description, :due_at, :rationale,
                         :status, :metadata, :created_at)
                """),
                {
                    "id": followup.id,
                    "tenant_id": tenant_id,
                    "parent_action_id": followup.parent_action_id,
                    "parent_outcome_id": followup.parent_outcome_id,
                    "company_name": followup.company_name,
                    "seller_id": followup.seller_id,
                    "generated_action_type": followup.generated_action_type,
                    "title": followup.title,
                    "description": followup.description,
                    "due_at": followup.due_at,
                    "rationale": followup.rationale,
                    "status": followup.status,
                    "metadata": "{}",
                    "created_at": followup.created_at,
                },
            )
            await session.commit()

        logger.info("sales_followup generated: %s for %s (due %s)", title, outcome.company_name, due_at)
        return followup

    async def get_pending(self, tenant_id: str, seller_id: str | None = None) -> list[SalesFollowup]:
        async with self._factory() as session:
            await _pin(session, tenant_id)
            if seller_id:
                rows = await session.execute(
                    text("SELECT * FROM sales_followups WHERE status = 'pending' AND seller_id = :s AND due_at <= now() ORDER BY due_at"),
                    {"s": seller_id},
                )
            else:
                rows = await session.execute(
                    text("SELECT * FROM sales_followups WHERE status = 'pending' AND due_at <= now() ORDER BY due_at"),
                )
            return [self._map(r) for r in rows.fetchall()]

    async def complete(self, tenant_id: str, followup_id: str, outcome: str = "completed") -> bool:
        async with self._factory() as session:
            await _pin(session, tenant_id)
            result = await session.execute(
                text("UPDATE sales_followups SET status = :o WHERE id = :id AND tenant_id = :t"),
                {"o": outcome, "id": followup_id, "t": tenant_id},
            )
            await session.commit()
            return (result.rowcount or 0) > 0

    def _map(self, row) -> SalesFollowup:
        return SalesFollowup(
            id=str(row.id),
            tenant_id=row.tenant_id,
            parent_action_id=str(row.parent_action_id),
            parent_outcome_id=str(row.parent_outcome_id) if row.parent_outcome_id else "",
            company_name=row.company_name,
            seller_id=row.seller_id,
            generated_action_type=row.generated_action_type,
            title=row.title,
            description=row.description or "",
            due_at=row.due_at,
            rationale=row.rationale,
            status=row.status,
            metadata=row.metadata or {},
            created_at=row.created_at,
        )


class WorkQueueService:
    """My Day read model: actions + follow-ups + scores, mine-only."""

    def __init__(self, session_factory):
        self._factory = session_factory

    async def get_my_day(self, tenant_id: str, seller_id: str) -> dict:
        """Build the seller's daily work queue."""
        async with self._factory() as session:
            await _pin(session, tenant_id)

            # Pending sales actions — user_id is the seller-owner column on
            # this table (see actions.py's INSERT); without this filter
            # "My Day" showed every seller's pending actions in the tenant,
            # not just the caller's own, unlike the followups/outcomes
            # queries below which already filter correctly.
            actions_rows = await session.execute(
                text("""
                    SELECT * FROM agent_sales_actions
                    WHERE tenant_id = :t AND status = 'pending' AND user_id = :s
                    ORDER BY created_at DESC
                """),
                {"t": tenant_id, "s": seller_id},
            )
            actions = []
            for r in actions_rows.fetchall():
                actions.append({
                    "id": str(r.id),
                    "company_name": r.company_name,
                    "action_type": r.action_type,
                    "status": r.status,
                    "notes": r.notes or "",
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                })

            # Pending follow-ups (due today or overdue)
            followups_rows = await session.execute(
                text("""
                    SELECT * FROM sales_followups
                    WHERE tenant_id = :t AND status = 'pending' AND seller_id = :s
                    ORDER BY due_at ASC
                """),
                {"t": tenant_id, "s": seller_id},
            )
            followups = []
            for r in followups_rows.fetchall():
                followups.append({
                    "id": str(r.id),
                    "company_name": r.company_name,
                    "generated_action_type": r.generated_action_type,
                    "title": r.title,
                    "description": r.description or "",
                    "due_at": r.due_at.isoformat() if r.due_at else None,
                    "rationale": r.rationale,
                    "status": r.status,
                })

            # Recent outcomes (last 7 days)
            outcomes_rows = await session.execute(
                text("""
                    SELECT * FROM action_outcomes
                    WHERE tenant_id = :t AND seller_id = :s
                      AND occurred_at >= now() - interval '7 days'
                    ORDER BY occurred_at DESC
                """),
                {"t": tenant_id, "s": seller_id},
            )
            recent_outcomes = []
            for r in outcomes_rows.fetchall():
                recent_outcomes.append({
                    "id": str(r.id),
                    "company_name": r.company_name,
                    "outcome_type": r.outcome_type,
                    "notes": r.notes or "",
                    "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
                })

            # Summary metrics
            pending_count = len(actions)
            followup_count = len(followups)
            outcome_count = len(recent_outcomes)
            connected = sum(1 for o in recent_outcomes if o["outcome_type"] in ("connected", "positive", "meeting_set"))

            return {
                "pending_actions": actions,
                "pending_followups": followups,
                "recent_outcomes": recent_outcomes,
                "summary": {
                    "pending_actions": pending_count,
                    "pending_followups": followup_count,
                    "outcomes_7d": outcome_count,
                    "connected_7d": connected,
                },
            }


class FeedbackAnalyticsService:
    """Feedback loop metrics: acceptance rate, outcome conversion, time-to-action, seller productivity."""

    def __init__(self, session_factory):
        self._factory = session_factory

    async def get_dashboard(
        self, tenant_id: str, seller_id: str | None = None, *, leaderboard: bool = True,
    ) -> dict:
        """Return full feedback analytics dashboard.

        leaderboard=False limits seller productivity to ``seller_id``'s own row
        (PO decision B6, report 99).
        """
        if not leaderboard and not seller_id:
            raise ValueError("seller_id is required when the leaderboard is hidden")
        async with self._factory() as session:
            await _pin(session, tenant_id)

            # 1. Acceptance rate
            fb_where = "WHERE tenant_id = :t"
            params: dict = {"t": tenant_id}
            if seller_id:
                fb_where += " AND seller_id = :s"
                params["s"] = seller_id

            rows = await session.execute(text(
                f"SELECT decision, COUNT(*) FROM nba_feedback {fb_where} GROUP BY decision"
            ), params)
            fb_counts = {r[0]: r[1] for r in rows.fetchall()}
            total_fb = sum(fb_counts.values())
            accepted = fb_counts.get("accepted", 0)
            rejected = fb_counts.get("rejected", 0)
            modified = fb_counts.get("modified", 0)
            acceptance_rate = accepted / total_fb if total_fb > 0 else 0.0
            modification_rate = modified / total_fb if total_fb > 0 else 0.0

            # 2. Outcome conversion (connected / meeting_set / positive as "converted")
            out_where = "WHERE tenant_id = :t"
            params2: dict = {"t": tenant_id}
            if seller_id:
                out_where += " AND seller_id = :s"
                params2["s"] = seller_id

            rows = await session.execute(text(
                f"SELECT outcome_type, COUNT(*) FROM action_outcomes {out_where} GROUP BY outcome_type"
            ), params2)
            out_counts = {r[0]: r[1] for r in rows.fetchall()}
            total_out = sum(out_counts.values())
            converted = sum(out_counts.get(k, 0) for k in ("connected", "meeting_set", "positive", "proposal_sent"))
            conversion_rate = converted / total_out if total_out > 0 else 0.0

            # 3. Time-to-action (feedback created_at lag vs action created_at, where available)
            rows = await session.execute(text(f"""
                SELECT
                    AVG(EXTRACT(EPOCH FROM (f.created_at - a.created_at))/3600) as avg_hours,
                    COUNT(f.id) as sample_size
                FROM nba_feedback f
                LEFT JOIN agent_sales_actions a ON f.action_id = a.id AND a.tenant_id = f.tenant_id
                WHERE f.tenant_id = :t
                {"AND f.seller_id = :s" if seller_id else ""}
            """), params)
            tta = rows.fetchone()
            avg_hours_to_action = float(tta[0]) if tta[0] else 0.0
            tta_sample = int(tta[1]) if tta[1] else 0

            # 4. Seller productivity (top sellers by outcome count)
            own_only = "" if leaderboard else "AND seller_id = :s"
            rows = await session.execute(text(f"""
                SELECT seller_id, COUNT(*) as cnt,
                       SUM(CASE WHEN outcome_type IN ('connected','meeting_set','positive') THEN 1 ELSE 0 END) as converted
                FROM action_outcomes
                WHERE tenant_id = :t
                  AND occurred_at >= now() - interval '30 days'
                  {own_only}
                GROUP BY seller_id
                ORDER BY converted DESC
                LIMIT 10
            """), {"t": tenant_id} if leaderboard else {"t": tenant_id, "s": seller_id})
            sellers = [
                {"seller_id": r[0], "total_outcomes": r[1], "converted": r[2],
                 "conversion_rate": round(r[2] / r[1], 3) if r[1] > 0 else 0.0}
                for r in rows.fetchall()
            ]

            # 5. Decision breakdown (for chart)
            rows = await session.execute(text(
                f"SELECT decision, COUNT(*) FROM nba_feedback {fb_where} GROUP BY decision"
            ), params)
            breakdown = [{"decision": r[0], "count": r[1]} for r in rows.fetchall()]

            return {
                "acceptance_rate": round(acceptance_rate, 3),
                "modification_rate": round(modification_rate, 3),
                "rejection_rate": round(rejected / total_fb if total_fb > 0 else 0.0, 3),
                "total_feedback": total_fb,
                "total_outcomes": total_out,
                "conversion_rate": round(conversion_rate, 3),
                "avg_hours_to_action": round(avg_hours_to_action, 2),
                "tta_sample_size": tta_sample,
                "seller_productivity": sellers,
                "decision_breakdown": breakdown,
            }
