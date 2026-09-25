"""Business Effectiveness: observation, cohort analysis, lift, monotonicity, calibration readiness.

Lifecycle: OBSERVE → MEASURE → VALIDATE → CALIBRATE
No automatic weight modification. No self-learning. Champion scoring frozen.
"""
import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import text

from app.database import async_session

logger = logging.getLogger(__name__)

INTENT_MODEL_VERSION = "v1"

COHORT_THRESHOLDS = [
    (80, "critical"),
    (60, "high"),
    (40, "medium"),
    (0, "low"),
]


def assign_cohort(score: float) -> str:
    for threshold, label in COHORT_THRESHOLDS:
        if score >= threshold:
            return label
    return "low"


def _safe_lift(numerator: float, denominator: float) -> dict:
    """Calculate lift safely. Returns value + reason when baseline is zero."""
    if denominator <= 0:
        return {"value": None, "reason": "baseline_rate_zero", "display": "N/A"}
    lift = round(numerator / denominator, 4)
    return {"value": lift, "reason": None, "display": f"{lift}x"}


def _safe_rate(count: float, total: float) -> float:
    """Calculate rate as percentage safely."""
    if total <= 0:
        return 0.0
    return round(count / total * 100, 1)


async def _pin(session, tenant_id: str) -> None:
    await session.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id})


class EffectivenessService:
    """Observation + effectiveness measurement for calibration readiness."""

    def __init__(self, factory):
        self._factory = factory

    # ─── Account Upsert ───────────────────────────────────────────

    async def upsert_account(
        self, tenant_id: str, company_name: str, seller_id: str,
        intent_score: float, intent_level: str = "",
        sector: str = "", company_size: str = "",
        signal_types: list[str] | None = None,
        signal_count: int = 0, critical_signal_count: int = 0,
        source_diversity: int = 0,
        nba_type: str = "", nba_urgency: str = "",
        original_nba_type: str = "", seller_selected_action: str = "",
    ) -> dict:
        cohort = assign_cohort(intent_score)
        now = datetime.now(UTC)

        async with self._factory() as session:
            await _pin(session, tenant_id)
            existing = await session.execute(text(
                "SELECT id FROM account_funnel WHERE tenant_id = :t AND company_name = :c"
            ), {"t": tenant_id, "c": company_name})
            row = existing.fetchone()

            if row:
                await session.execute(text("""
                    UPDATE account_funnel
                    SET intent_score = :score, intent_level = :level, cohort = :cohort,
                        sector = :sector, company_size = :size, signal_types = :signals,
                        signal_count = :sig_count, critical_signal_count = :crit_count,
                        source_diversity = :src_div,
                        intent_model_version = :model_ver, score_observed_at = :obs_at,
                        nba_type = :nba_type, nba_urgency = :nba_urgency,
                        original_nba_type = :orig_nba, seller_selected_action = :sel_action,
                        updated_at = now()
                    WHERE tenant_id = :t AND company_name = :c
                """), {
                    "t": tenant_id, "c": company_name,
                    "score": intent_score, "level": intent_level, "cohort": cohort,
                    "sector": sector, "size": company_size,
                    "signals": json.dumps(signal_types or []),
                    "sig_count": signal_count, "crit_count": critical_signal_count,
                    "src_div": source_diversity,
                    "model_ver": INTENT_MODEL_VERSION, "obs_at": now,
                    "nba_type": nba_type, "nba_urgency": nba_urgency,
                    "orig_nba": original_nba_type, "sel_action": seller_selected_action,
                })
                account_id = row[0]
            else:
                account_id = str(uuid4())
                await session.execute(text("""
                    INSERT INTO account_funnel
                        (id, tenant_id, company_name, seller_id,
                         intent_score, intent_level, cohort,
                         sector, company_size, signal_types,
                         signal_count, critical_signal_count, source_diversity,
                         intent_model_version, score_observed_at,
                         nba_type, nba_urgency, original_nba_type, seller_selected_action,
                         nba_accepted, nba_rejected, nba_modified,
                         total_actions, total_outcomes, connected_outcomes, meeting_outcomes)
                    VALUES
                        (:id, :tenant, :company, :seller,
                         :score, :level, :cohort,
                         :sector, :size, :signals,
                         :sig_count, :crit_count, :src_div,
                         :model_ver, :obs_at,
                         :nba_type, :nba_urgency, :orig_nba, :sel_action,
                         0, 0, 0, 0, 0, 0, 0)
                """), {
                    "id": account_id, "tenant": tenant_id,
                    "company": company_name, "seller": seller_id,
                    "score": intent_score, "level": intent_level, "cohort": cohort,
                    "sector": sector or "", "size": company_size or "",
                    "signals": json.dumps(signal_types or []),
                    "sig_count": signal_count, "crit_count": critical_signal_count,
                    "src_div": source_diversity,
                    "model_ver": INTENT_MODEL_VERSION, "obs_at": now,
                    "nba_type": nba_type, "nba_urgency": nba_urgency,
                    "orig_nba": original_nba_type, "sel_action": seller_selected_action,
                })

            # Append-only observation record
            await session.execute(text("""
                INSERT INTO score_observations
                    (id, tenant_id, company_name, seller_id,
                     intent_score, intent_level, cohort, intent_model_version,
                     signal_count, critical_signal_count, signal_types, source_diversity,
                     sector, company_size,
                     nba_type, nba_urgency, nba_confidence,
                     first_action_at, first_action_type, connection_at, meeting_at,
                     opportunity_at, proposal_at, won_at, lost_at, revenue,
                     observed_at)
                SELECT
                    :obs_id, tenant_id, company_name, seller_id,
                    intent_score, intent_level, cohort, intent_model_version,
                    signal_count, critical_signal_count, signal_types, source_diversity,
                    sector, company_size,
                    nba_type, nba_urgency, NULL,
                    first_action_at, first_action_type, connection_at, meeting_at,
                    opportunity_at, proposal_at, won_at, lost_at, revenue,
                    :observed_at
                FROM account_funnel
                WHERE tenant_id = :t AND company_name = :c
            """), {
                "obs_id": str(uuid4()), "t": tenant_id,
                "c": company_name, "observed_at": now,
            })

            await session.commit()
        return {"id": account_id, "cohort": cohort}

    # ─── Funnel Events ────────────────────────────────────────────

    async def record_event(
        self, tenant_id: str, company_name: str, event_type: str,
        event_at: datetime | None = None, action_id: str = "",
        action_type: str = "", deal_value: float | None = None,
        revenue: float | None = None,
    ) -> bool:
        ts = event_at or datetime.now(UTC)
        col_map = {
            "first_action": ("first_action_at", "first_action_type", "first_action_id"),
            "connection": ("connection_at", None, None),
            "meeting": ("meeting_at", None, None),
            "opportunity": ("opportunity_at", None, None),
            "proposal": ("proposal_at", None, None),
            "won": ("won_at", None, None),
            "lost": ("lost_at", None, None),
        }
        if event_type not in col_map:
            return False

        main_col, type_col, id_col = col_map[event_type]
        async with self._factory() as session:
            await _pin(session, tenant_id)
            sets = [f"{main_col} = COALESCE({main_col}, :ts)"]
            params: dict = {"t": tenant_id, "c": company_name, "ts": ts}

            if type_col and action_type:
                sets.append(f"{type_col} = COALESCE({type_col}, :at)")
                params["at"] = action_type
            if id_col and action_id:
                sets.append(f"{id_col} = COALESCE({id_col}, :aid)")
                params["aid"] = action_id

            if event_type == "first_action":
                sets.append("time_to_first_action_hours = COALESCE(time_to_first_action_hours, EXTRACT(EPOCH FROM (:ts - created_at)) / 3600.0)")

            if deal_value is not None:
                sets.append("deal_value = COALESCE(deal_value, :dv)")
                params["dv"] = deal_value
            if revenue is not None:
                sets.append("revenue = COALESCE(revenue, :rev)")
                params["rev"] = revenue

            sets.append("updated_at = now()")
            await session.execute(text(
                f"UPDATE account_funnel SET {', '.join(sets)} WHERE tenant_id = :t AND company_name = :c"
            ), params)

            # Update outcome counters
            if event_type == "connection":
                await session.execute(text("""
                    UPDATE account_funnel
                    SET connected_outcomes = connected_outcomes + 1
                    WHERE tenant_id = :t AND company_name = :c
                """), {"t": tenant_id, "c": company_name})
            elif event_type == "meeting":
                await session.execute(text("""
                    UPDATE account_funnel
                    SET meeting_outcomes = meeting_outcomes + 1
                    WHERE tenant_id = :t AND company_name = :c
                """), {"t": tenant_id, "c": company_name})

            await session.commit()
        return True

    async def record_feedback_event(self, tenant_id: str, company_name: str, decision: str) -> bool:
        col = {"accepted": "nba_accepted", "rejected": "nba_rejected", "modified": "nba_modified"}.get(decision)
        if not col:
            return False
        async with self._factory() as session:
            await _pin(session, tenant_id)
            await session.execute(text(
                f"UPDATE account_funnel SET {col} = {col} + 1, updated_at = now() WHERE tenant_id = :t AND company_name = :c"
            ), {"t": tenant_id, "c": company_name})
            await session.commit()
        return True

    async def record_action_event(self, tenant_id: str, company_name: str) -> bool:
        async with self._factory() as session:
            await _pin(session, tenant_id)
            await session.execute(text("""
                UPDATE account_funnel SET total_actions = total_actions + 1, updated_at = now()
                WHERE tenant_id = :t AND company_name = :c
            """), {"t": tenant_id, "c": company_name})
            await session.commit()
        return True

    async def record_outcome_event(self, tenant_id: str, company_name: str, outcome_type: str) -> bool:
        async with self._factory() as session:
            await _pin(session, tenant_id)
            await session.execute(text("""
                UPDATE account_funnel
                SET total_outcomes = total_outcomes + 1, updated_at = now()
                WHERE tenant_id = :t AND company_name = :c
            """), {"t": tenant_id, "c": company_name})
            await session.commit()
        return True

    # ─── Dashboard ────────────────────────────────────────────────

    async def get_dashboard(self, tenant_id: str, seller_id: str | None = None) -> dict:
        where = "WHERE af.tenant_id = :t"
        params: dict = {"t": tenant_id}
        if seller_id:
            where += " AND af.seller_id = :s"
            params["s"] = seller_id

        async with self._factory() as session:
            await _pin(session, tenant_id)

            # Summary
            r = await session.execute(text(f"""
                SELECT COUNT(*) as total,
                    COUNT(*) FILTER (WHERE af.first_action_at IS NOT NULL) as with_action,
                    COUNT(*) FILTER (WHERE af.connection_at IS NOT NULL) as connections,
                    COUNT(*) FILTER (WHERE af.meeting_at IS NOT NULL) as meetings,
                    COUNT(*) FILTER (WHERE af.opportunity_at IS NOT NULL) as opportunities,
                    COUNT(*) FILTER (WHERE af.proposal_at IS NOT NULL) as proposals,
                    COUNT(*) FILTER (WHERE af.won_at IS NOT NULL) as won,
                    COUNT(*) FILTER (WHERE af.lost_at IS NOT NULL) as lost,
                    COALESCE(SUM(af.revenue), 0) as revenue,
                    COALESCE(SUM(af.deal_value), 0) as deal_value,
                    COUNT(*) FILTER (WHERE af.first_action_at IS NOT NULL) as accounts_with_action,
                    COALESCE(AVG(af.time_to_first_action_hours) FILTER (WHERE af.time_to_first_action_hours > 0), 0) as avg_tta
                FROM account_funnel af {where}
            """), params)
            s = r.fetchone()
            summary = {
                "total_accounts": s[0], "accounts_with_action": s[1],
                "connections": s[2], "meetings": s[3], "opportunities": s[4],
                "proposals": s[5], "won": s[6], "lost": s[7],
                "revenue": float(s[8]), "deal_value": float(s[9]),
                "avg_time_to_action_hours": round(float(s[11]), 1),
            }

            # Rates
            total = max(summary["total_accounts"], 1)
            rates = {
                "action_rate": _safe_rate(summary["accounts_with_action"], total),
                "connection_rate": _safe_rate(summary["connections"], total),
                "meeting_rate": _safe_rate(summary["meetings"], total),
                "opportunity_rate": _safe_rate(summary["opportunities"], total),
                "proposal_rate": _safe_rate(summary["proposals"], total),
                "win_rate": _safe_rate(summary["won"], total),
                "revenue_per_won": round(float(summary["revenue"]) / max(summary["won"], 1), 2),
            }

            # NBA stats from nba_feedback
            r2 = await session.execute(text("""
                SELECT COUNT(*),
                    COUNT(*) FILTER (WHERE decision = 'accepted'),
                    COUNT(*) FILTER (WHERE decision = 'modified'),
                    COUNT(*) FILTER (WHERE decision = 'rejected')
                FROM nba_feedback WHERE tenant_id = :t
            """), {"t": tenant_id})
            nb = r2.fetchone()
            nba_total = nb[0]
            nba = {
                "total_actions": nba_total,
                "accepted": nb[1], "modified": nb[2], "rejected": nb[3],
                "acceptance_rate": _safe_rate(nb[1], nba_total),
                "modification_rate": _safe_rate(nb[2], nba_total),
                "rejection_rate": _safe_rate(nb[3], nba_total),
            }

            # Per-cohort
            r3 = await session.execute(text(f"""
                SELECT af.cohort, COUNT(*) as total,
                    COUNT(*) FILTER (WHERE af.connection_at IS NOT NULL) as connections,
                    COUNT(*) FILTER (WHERE af.meeting_at IS NOT NULL) as meetings,
                    COUNT(*) FILTER (WHERE af.opportunity_at IS NOT NULL) as opps,
                    COUNT(*) FILTER (WHERE af.proposal_at IS NOT NULL) as proposals,
                    COUNT(*) FILTER (WHERE af.won_at IS NOT NULL) as won,
                    COALESCE(SUM(af.revenue), 0) as revenue,
                    COALESCE(AVG(af.intent_score), 0) as avg_score,
                    SUM(af.nba_accepted) as nba_acc,
                    SUM(af.nba_rejected) + SUM(af.nba_modified) as nba_over,
                    COALESCE(AVG(af.time_to_first_action_hours) FILTER (WHERE af.time_to_first_action_hours > 0), 0) as avg_tta
                FROM account_funnel af {where}
                GROUP BY af.cohort
            """), params)
            cohorts = {}
            for row in r3.fetchall():
                c, tot = row[0], row[1]
                cohorts[c] = {
                    "total": tot, "connections": row[2], "meetings": row[3],
                    "opportunities": row[4], "proposals": row[5], "won": row[6],
                    "revenue": float(row[7]), "avg_score": round(float(row[8]), 1),
                    "nba_accepted": row[9], "nba_overridden": row[10],
                    "connection_rate": _safe_rate(row[2], tot),
                    "meeting_rate": _safe_rate(row[3], tot),
                    "opportunity_rate": _safe_rate(row[4], tot),
                    "proposal_rate": _safe_rate(row[5], tot),
                    "win_rate": _safe_rate(row[6], tot),
                    # row[10] is nba_over (nba_rejected+nba_modified count);
                    # avg_tta is row[11] — was silently reporting the
                    # override count as an "hours" figure.
                    "avg_time_to_action_hours": round(float(row[11]), 1),
                }

            # Lift: elevated (critical+high) vs baseline (low+medium)
            ec = sum(cohorts.get(c, {}).get("total", 0) for c in ["critical", "high"])
            bc = sum(cohorts.get(c, {}).get("total", 0) for c in ["low", "medium"])
            e_conn = sum(cohorts.get(c, {}).get("connections", 0) for c in ["critical", "high"])
            b_conn = sum(cohorts.get(c, {}).get("connections", 0) for c in ["low", "medium"])
            e_meet = sum(cohorts.get(c, {}).get("meetings", 0) for c in ["critical", "high"])
            b_meet = sum(cohorts.get(c, {}).get("meetings", 0) for c in ["low", "medium"])
            e_opp = sum(cohorts.get(c, {}).get("opportunities", 0) for c in ["critical", "high"])
            b_opp = sum(cohorts.get(c, {}).get("opportunities", 0) for c in ["low", "medium"])
            e_won = sum(cohorts.get(c, {}).get("won", 0) for c in ["critical", "high"])
            b_won = sum(cohorts.get(c, {}).get("won", 0) for c in ["low", "medium"])

            e_conn_rate = _safe_rate(e_conn, ec) / 100
            b_conn_rate = _safe_rate(b_conn, bc) / 100
            e_meet_rate = _safe_rate(e_meet, ec) / 100
            b_meet_rate = _safe_rate(b_meet, bc) / 100
            e_opp_rate = _safe_rate(e_opp, ec) / 100
            b_opp_rate = _safe_rate(b_opp, bc) / 100
            e_won_rate = _safe_rate(e_won, ec) / 100
            b_won_rate = _safe_rate(b_won, bc) / 100

            lift = {
                "elevated_total": ec, "baseline_total": bc,
                "elevated_connections": e_conn, "baseline_connections": b_conn,
                "elevated_meetings": e_meet, "baseline_meetings": b_meet,
                "elevated_opportunities": e_opp, "baseline_opportunities": b_opp,
                "elevated_won": e_won, "baseline_won": b_won,
                "connection_lift": _safe_lift(e_conn_rate, b_conn_rate),
                "meeting_lift": _safe_lift(e_meet_rate, b_meet_rate),
                "opportunity_lift": _safe_lift(e_opp_rate, b_opp_rate),
                "win_lift": _safe_lift(e_won_rate, b_won_rate),
            }

            # By level
            r4 = await session.execute(text(f"""
                SELECT af.intent_level, COUNT(*) as total,
                    COUNT(*) FILTER (WHERE af.meeting_at IS NOT NULL) as meetings,
                    COUNT(*) FILTER (WHERE af.won_at IS NOT NULL) as won,
                    COALESCE(AVG(af.time_to_first_action_hours) FILTER (WHERE af.time_to_first_action_hours > 0), 0) as avg_tta
                FROM account_funnel af {where}
                GROUP BY af.intent_level
            """), params)
            by_level = {}
            for row in r4.fetchall():
                lv = row[0]
                by_level[lv] = {
                    "total": row[1], "meetings": row[2], "won": row[3],
                    "meeting_rate": _safe_rate(row[2], row[1]),
                    "win_rate": _safe_rate(row[3], row[1]),
                    "avg_time_to_action_hours": round(float(row[4]), 1),
                }

            # By seller
            r5 = await session.execute(text(f"""
                SELECT af.seller_id, COUNT(*) as total,
                    COUNT(*) FILTER (WHERE af.meeting_at IS NOT NULL) as meetings,
                    COUNT(*) FILTER (WHERE af.won_at IS NOT NULL) as won,
                    COALESCE(SUM(af.revenue), 0) as revenue,
                    COALESCE(AVG(af.time_to_first_action_hours) FILTER (WHERE af.time_to_first_action_hours > 0), 0) as avg_tta
                FROM account_funnel af {where}
                GROUP BY af.seller_id
            """), params)
            by_seller = {}
            for row in r5.fetchall():
                sid = row[0]
                by_seller[sid] = {
                    "total": row[1], "meetings": row[2], "won": row[3],
                    "revenue": float(row[4]),
                    "meeting_rate": _safe_rate(row[2], row[1]),
                    "win_rate": _safe_rate(row[3], row[1]),
                    "avg_time_to_action_hours": round(float(row[5]), 1),
                }

            # Monotonicity check
            monotonicity = self._check_monotonicity(cohorts)

            # NBA effectiveness (accepted vs modified vs rejected)
            nba_eff = await self._nba_effectiveness(session, tenant_id)

            # Calibration readiness
            readiness = self._calibration_readiness(summary, cohorts, nba)

            # Segmentation
            segmentation = await self._segmentation(session, tenant_id)

            return {
                "summary": summary,
                "rates": rates,
                "nba": nba,
                "cohorts": cohorts,
                "lift": lift,
                "by_level": by_level,
                "by_seller": by_seller,
                "monotonicity": monotonicity,
                "nba_effectiveness": nba_eff,
                "calibration_readiness": readiness,
                "segmentation": segmentation,
                "model_version": INTENT_MODEL_VERSION,
            }

    def _check_monotonicity(self, cohorts: dict) -> dict:
        """Test whether conversion improves as intent score increases."""
        order = ["critical", "high", "medium", "low"]
        metrics = {}

        for metric_key in ["connection_rate", "meeting_rate", "opportunity_rate", "win_rate"]:
            values = []
            for c in order:
                v = cohorts.get(c, {}).get(metric_key, 0)
                values.append(v)

            # Check if strictly non-decreasing (allowing ties)
            monotonic = all(values[i] >= values[i + 1] for i in range(len(values) - 1))
            has_data = any(v > 0 for v in values)
            all_same = len(set(values)) <= 1

            if not has_data:
                status = "INSUFFICIENT_DATA"
            elif all_same:
                status = "INSUFFICIENT_DATA"
            elif monotonic:
                status = "PASS"
            else:
                status = "FAIL"

            metrics[metric_key] = {
                "critical": values[0], "high": values[1],
                "medium": values[2], "low": values[3],
                "status": status,
            }

        # Overall monotonicity
        statuses = [m["status"] for m in metrics.values()]
        if all(s == "INSUFFICIENT_DATA" for s in statuses):
            overall = "INSUFFICIENT_DATA"
        elif all(s == "PASS" for s in statuses if s != "INSUFFICIENT_DATA"):
            overall = "PASS"
        else:
            overall = "FAIL"

        return {"by_metric": metrics, "overall": overall}

    async def _nba_effectiveness(self, session, tenant_id: str) -> dict:
        """Measure whether SalesOS recommendations outperform seller overrides."""
        # Join nba_feedback with action outcomes
        r = await session.execute(text("""
            SELECT
                nf.decision,
                COUNT(DISTINCT nf.id) as feedback_count,
                COUNT(DISTINCT ao.id) FILTER (WHERE ao.outcome_type = 'connected') as connected,
                COUNT(DISTINCT ao.id) FILTER (WHERE ao.outcome_type = 'meeting_set') as meeting_set,
                COUNT(DISTINCT ao.id) FILTER (WHERE ao.outcome_type IN ('positive', 'proposal_sent')) as positive
            FROM nba_feedback nf
            LEFT JOIN action_outcomes ao ON ao.action_id = nf.action_id AND ao.tenant_id = nf.tenant_id
            WHERE nf.tenant_id = :t
            GROUP BY nf.decision
        """), {"t": tenant_id})

        decisions = {}
        for row in r.fetchall():
            dec = row[0]
            fb_count = row[1]
            decisions[dec] = {
                "feedback_count": fb_count,
                "connected": row[2],
                "meeting_set": row[3],
                "positive": row[4],
                "connection_rate": _safe_rate(row[2], fb_count),
                "meeting_rate": _safe_rate(row[3], fb_count),
                "positive_rate": _safe_rate(row[4], fb_count),
            }

        # Determine winner with confidence qualifier
        accepted = decisions.get("accepted", {}).get("meeting_rate", 0)
        modified = decisions.get("modified", {}).get("meeting_rate", 0)
        rejected = decisions.get("rejected", {}).get("meeting_rate", 0)
        total_fb = sum(d.get("feedback_count", 0) for d in decisions.values())

        # Minimum sample for directional signal
        min_sample_per_group = 5
        has_enough = all(
            decisions.get(g, {}).get("feedback_count", 0) >= min_sample_per_group
            for g in ["accepted", "modified", "rejected"]
            if decisions.get(g, {}).get("feedback_count", 0) > 0
        )

        if total_fb == 0:
            winner = "insufficient_data"
            confidence = "no_data"
        elif not has_enough:
            # Directional only — not enough sample
            if accepted > modified and accepted > rejected:
                winner = "accepted_directional"
            elif modified > accepted and modified > rejected:
                winner = "override_directional"
            else:
                winner = "no_clear_direction"
            confidence = "directional_only"
        else:
            if accepted > modified and accepted > rejected:
                winner = "accepted_outperforms"
            elif modified > accepted and modified > rejected:
                winner = "seller_override_outperforms"
            else:
                winner = "depends_on_context"
            confidence = "sufficient_sample"

        return {
            "decisions": decisions,
            "winner": winner,
            "confidence": confidence,
            "min_sample_per_group": min_sample_per_group,
            "total_feedback": total_fb,
            "accepted_meeting_rate": accepted,
            "modified_meeting_rate": modified,
            "rejected_meeting_rate": rejected,
        }

    def _calibration_readiness(self, summary: dict, cohorts: dict, nba: dict) -> dict:
        """Assess whether sufficient data exists for calibration.

        Two-tier assessment:
        1. Operational readiness — minimum data volume for observation
        2. Statistical confidence — sufficient sample for meaningful comparison
        """
        total = summary["total_accounts"]
        meetings = summary["meetings"]
        won = summary["won"]
        actions = summary["accounts_with_action"]

        # ── Operational Readiness (minimum floor) ──
        op_checks = {
            "total_accounts": {"value": total, "required": 50, "pass": total >= 50},
            "accounts_with_action": {"value": actions, "required": 20, "pass": actions >= 20},
            "meetings": {"value": meetings, "required": 10, "pass": meetings >= 10},
            "wins": {"value": won, "required": 5, "pass": won >= 5},
        }
        op_passed = sum(1 for c in op_checks.values() if c["pass"])
        op_total = len(op_checks)

        if op_passed == op_total:
            op_status = "READY"
        elif op_passed >= op_total * 0.5:
            op_status = "PARTIAL"
        else:
            op_status = "NOT_READY"

        # ── Statistical Confidence ──
        # Check per-cohort minimum + balance + observation duration
        cohort_counts = {c: cohorts.get(c, {}).get("total", 0) for c in ["critical", "high", "medium", "low"]}
        min_cohort = min(cohort_counts.values()) if cohort_counts else 0
        max_cohort = max(cohort_counts.values()) if cohort_counts else 0
        imbalance_ratio = max_cohort / max(min_cohort, 1)

        # Per-cohort minimum for meaningful rate comparison
        min_per_cohort = 10
        cohorts_with_enough = sum(1 for v in cohort_counts.values() if v >= min_per_cohort)

        stat_checks = {
            "cohort_balance": {"value": round(imbalance_ratio, 1), "max_allowed": 5.0, "pass": imbalance_ratio <= 5.0},
            "cohorts_with_enough_data": {"value": cohorts_with_enough, "required": 4, "pass": cohorts_with_enough >= 4},
            "min_per_cohort": {"value": min_cohort, "required": min_per_cohort, "pass": min_cohort >= min_per_cohort},
            "has_nba_feedback": {"value": nba["total_actions"], "required": 30, "pass": nba["total_actions"] >= 30},
            "total_meetings_for_rates": {"value": meetings, "required": 20, "pass": meetings >= 20},
        }
        stat_passed = sum(1 for c in stat_checks.values() if c["pass"])
        stat_total = len(stat_checks)

        if stat_passed == stat_total:
            stat_status = "READY"
        elif stat_passed >= stat_total * 0.6:
            stat_status = "APPROACHING"
        else:
            stat_status = "INSUFFICIENT"

        # ── Overall ──
        if op_status == "READY" and stat_status == "READY":
            overall = "READY_FOR_CALIBRATION"
        elif op_status == "NOT_READY":
            overall = "NOT_READY"
        else:
            overall = "OBSERVING"

        failed_op = [k for k, v in op_checks.items() if not v["pass"]]
        failed_stat = [k for k, v in stat_checks.items() if not v["pass"]]

        return {
            "status": overall,
            "operational": {"status": op_status, "checks": op_checks, "passed": op_passed, "total": op_total, "failed": failed_op},
            "statistical": {"status": stat_status, "checks": stat_checks, "passed": stat_passed, "total": stat_total, "failed": failed_stat},
            "checks": {**op_checks, **stat_checks},  # backward compat
            "passed": op_passed + stat_passed,
            "total": op_total + stat_total,
            "failed_checks": failed_op + failed_stat,
        }

    async def _segmentation(self, session, tenant_id: str) -> dict:
        """Segmentation by NBA decision, signal type, sector, company size."""
        # By NBA decision
        r = await session.execute(text("""
            SELECT nf.decision, COUNT(DISTINCT af.company_name) as accounts,
                COUNT(*) FILTER (WHERE af.meeting_at IS NOT NULL) as meetings
            FROM nba_feedback nf
            JOIN account_funnel af ON af.company_name = nf.company_name AND af.tenant_id = nf.tenant_id
            WHERE nf.tenant_id = :t
            GROUP BY nf.decision
        """), {"t": tenant_id})
        by_nba_decision = {}
        for row in r.fetchall():
            by_nba_decision[row[0]] = {"accounts": row[1], "meetings": row[2]}

        # By sector
        r2 = await session.execute(text("""
            SELECT COALESCE(NULLIF(sector, ''), 'unknown') as sector,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE meeting_at IS NOT NULL) as meetings,
                COUNT(*) FILTER (WHERE won_at IS NOT NULL) as won
            FROM account_funnel WHERE tenant_id = :t
            GROUP BY sector ORDER BY total DESC LIMIT 20
        """), {"t": tenant_id})
        by_sector = {}
        for row in r2.fetchall():
            by_sector[row[0]] = {
                "total": row[1], "meetings": row[2], "won": row[3],
                "meeting_rate": _safe_rate(row[2], row[1]),
                "win_rate": _safe_rate(row[3], row[1]),
            }

        # By company size
        r3 = await session.execute(text("""
            SELECT COALESCE(NULLIF(company_size, ''), 'unknown') as size,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE meeting_at IS NOT NULL) as meetings,
                COUNT(*) FILTER (WHERE won_at IS NOT NULL) as won
            FROM account_funnel WHERE tenant_id = :t
            GROUP BY size ORDER BY total DESC
        """), {"t": tenant_id})
        by_company_size = {}
        for row in r3.fetchall():
            by_company_size[row[0]] = {
                "total": row[1], "meetings": row[2], "won": row[3],
                "meeting_rate": _safe_rate(row[2], row[1]),
                "win_rate": _safe_rate(row[3], row[1]),
            }

        # By model version
        r4 = await session.execute(text("""
            SELECT intent_model_version, COUNT(*) as total,
                COUNT(*) FILTER (WHERE meeting_at IS NOT NULL) as meetings
            FROM account_funnel WHERE tenant_id = :t
            GROUP BY intent_model_version
        """), {"t": tenant_id})
        by_model_version = {}
        for row in r4.fetchall():
            by_model_version[row[0]] = {"total": row[1], "meetings": row[2]}

        # By signal type (from JSON signal_types)
        # This requires unnesting JSON arrays — use a simpler approach
        r5 = await session.execute(text("""
            SELECT intent_level, intent_model_version,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE meeting_at IS NOT NULL) as meetings,
                COUNT(*) FILTER (WHERE won_at IS NOT NULL) as won
            FROM account_funnel WHERE tenant_id = :t
            GROUP BY intent_level, intent_model_version
        """), {"t": tenant_id})
        by_level_version = {}
        for row in r5.fetchall():
            key = f"{row[0]}_{row[1]}"
            by_level_version[key] = {"total": row[2], "meetings": row[3], "won": row[4]}

        return {
            "by_nba_decision": by_nba_decision,
            "by_sector": by_sector,
            "by_company_size": by_company_size,
            "by_model_version": by_model_version,
            "by_level_version": by_level_version,
        }
