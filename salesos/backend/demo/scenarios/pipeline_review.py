"""Pipeline Review Scenario — Pipeline health → Forecast → Team performance.

Demonstrates the pipeline analytics and forecasting capabilities.
"""

from typing import Any


def get_scenario_metadata() -> dict:
    return {
        "id": "pipeline_review",
        "title": "Pipeline Review Scenario",
        "description": "Show pipeline health → Forecast → Team performance",
        "steps": 3,
    }


def step_view_pipeline(demo_service: Any) -> dict:
    """Step 1: View pipeline health."""
    opps = demo_service.get_opportunities()
    total_value = sum(o["estimated_value"] for o in opps if o["stage"] not in ("closed_won", "closed_lost"))
    won_value = sum(o.get("won_amount", 0) or 0 for o in opps if o["stage"] == "closed_won")
    by_stage = {}
    for opp in opps:
        s = opp["stage"]
        by_stage.setdefault(s, {"count": 0, "value": 0})
        by_stage[s]["count"] += 1
        by_stage[s]["value"] += opp["estimated_value"]

    return {
        "step": 1,
        "action": "view_pipeline",
        "label": "View Pipeline Health",
        "data": {
            "total_opportunities": len(opps),
            "total_pipeline_value": total_value,
            "won_value": won_value,
            "by_stage": by_stage,
            "narrative": f"Pipeline shows {len(opps)} opportunities worth SAR {total_value:,}. "
                         f"Win rate: {len([o for o in opps if o['stage'] == 'closed_won'])} won out of "
                         f"{len([o for o in opps if o['stage'] in ('closed_won', 'closed_lost')])} closed.",
        },
    }


def step_view_forecast(demo_service: Any) -> dict:
    """Step 2: Review forecast."""
    opps = demo_service.get_opportunities()
    weighted = sum(o["estimated_value"] * o["confidence"] for o in opps if o["stage"] not in ("closed_won", "closed_lost"))
    expected = sum(o["estimated_value"] for o in opps if o["stage"] in ("proposal", "negotiation"))
    best_case = sum(o["estimated_value"] for o in opps if o["stage"] not in ("closed_lost",))

    return {
        "step": 2,
        "action": "view_forecast",
        "label": "Review Forecast",
        "data": {
            "weighted_pipeline": round(weighted, 2),
            "expected_revenue": expected,
            "best_case_revenue": best_case,
            "commitment_revenue": sum(o["estimated_value"] for o in opps if o["stage"] == "negotiation"),
            "narrative": f"Weighted pipeline: SAR {weighted:,.0f}. Expected: SAR {expected:,.0f}. "
                         f"Best case: SAR {best_case:,.0f}.",
        },
    }


def step_team_performance(demo_service: Any) -> dict:
    """Step 3: Team performance analysis."""
    opps = demo_service.get_opportunities()
    users = demo_service.load_demo_data().get("users", []) if demo_service.load_demo_data() else []
    by_owner = {}
    for opp in opps:
        owner = opp.get("owner_id", "unknown")
        by_owner.setdefault(owner, {"count": 0, "value": 0, "won": 0})
        by_owner[owner]["count"] += 1
        by_owner[owner]["value"] += opp["estimated_value"]
        if opp["stage"] == "closed_won":
            by_owner[owner]["won"] += 1

    team_data = []
    for owner, stats in by_owner.items():
        user = next((u for u in users if u["id"] == owner), {"name": owner, "role": "unknown"})
        team_data.append({
            "name": user["name"],
            "role": user["role"],
            "deals": stats["count"],
            "pipeline_value": stats["value"],
            "won": stats["won"],
        })

    return {
        "step": 3,
        "action": "team_performance",
        "label": "Team Performance Analysis",
        "data": {
            "team": team_data,
            "narrative": f"Team performance across {len(team_data)} members. "
                         f"Top performer: {max(team_data, key=lambda x: x['pipeline_value'])['name'] if team_data else 'N/A'}.",
        },
    }


def execute(demo_service: Any) -> list[dict]:
    """Execute the pipeline review scenario."""
    return [
        step_view_pipeline(demo_service),
        step_view_forecast(demo_service),
        step_team_performance(demo_service),
    ]
