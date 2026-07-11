"""Enterprise Deal Scenario — Walk through NBA → Task → Email → Close.

Shows the complete deal lifecycle from NBA recommendation to closing won.
"""

from typing import Any


def get_scenario_metadata() -> dict:
    return {
        "id": "enterprise_deal",
        "title": "Enterprise Deal Scenario",
        "description": "Show NBA recommendation → Create task → Send email → Close deal",
        "steps": 4,
    }


def step_view_nba(demo_service: Any) -> dict:
    """Step 1: View NBA recommendations for a high-value opportunity."""
    recs = demo_service.get_nba_recommendations()
    active = [r for r in recs if r.get("status") == "active"]
    return {
        "step": 1,
        "action": "view_nba",
        "label": "View NBA Recommendation",
        "data": {
            "recommendations": active[:5],
            "total_active": len(active),
            "narrative": f"Found {len(active)} active NBA recommendations. "
                         f"Top priority: {active[0]['title'] if active else 'None'}",
        },
    }


def step_create_task(demo_service: Any) -> dict:
    """Step 2: Create a task from an NBA recommendation."""
    recs = demo_service.get_nba_recommendations()
    active = [r for r in recs if r.get("status") == "active"]
    if not active:
        return {"step": 2, "action": "create_task", "label": "Create Task from Recommendation", "data": {"error": "No active recommendations"}}
    rec = active[0]
    task = {
        "title": f"[NBA] {rec['title']}",
        "description": rec["description"],
        "priority": rec["priority"],
        "opportunity_id": rec["opportunity_id"],
        "source": "nba_demo",
    }
    return {
        "step": 2,
        "action": "create_task",
        "label": "Create Task from Recommendation",
        "data": {"task": task, "narrative": f"Created task '{task['title']}' with {task['priority']} priority."},
    }


def step_send_email(demo_service: Any) -> dict:
    """Step 3: Send a follow-up email."""
    opps = demo_service.get_opportunities()
    if not opps:
        return {"step": 3, "action": "send_email", "label": "Send Follow-up Email", "data": {"error": "No opportunities"}}
    opp = next((o for o in opps if o["stage"] in ("proposal", "negotiation")), opps[0])
    return {
        "step": 3,
        "action": "send_email",
        "label": "Send Follow-up Email",
        "data": {
            "to": f"contact@{opp['company_name'].lower().replace(' ', '')}.sa",
            "subject": f"Follow-up: {opp['title']}",
            "body": f"Dear team,\n\nFollowing up on our discussion regarding {opp['title']}. "
                    f"Please find attached the revised proposal as discussed.\n\nBest regards,\nSalesOS Demo",
            "narrative": f"Sent follow-up email regarding '{opp['title']}' to {opp['company_name']}.",
        },
    }


def step_close_deal(demo_service: Any) -> dict:
    """Step 4: Close a deal as won."""
    opps = demo_service.get_opportunities()
    negotiation = [o for o in opps if o["stage"] == "negotiation"]
    if not negotiation:
        return {
            "step": 4,
            "action": "close_deal",
            "label": "Close Won Deal",
            "data": {"narrative": "No deals in negotiation stage to close. Demo completed successfully."},
        }
    opp = negotiation[0]
    return {
        "step": 4,
        "action": "close_deal",
        "label": "Close Won Deal",
        "data": {
            "opportunity": opp,
            "won_amount": opp["estimated_value"],
            "narrative": f"Closed deal '{opp['title']}' with {opp['company_name']} at SAR {opp['estimated_value']:,}. "
                         f"Total pipeline value updated.",
        },
    }


def execute(demo_service: Any) -> list[dict]:
    """Execute the full enterprise deal scenario."""
    results = []
    results.append(step_view_nba(demo_service))
    results.append(step_create_task(demo_service))
    results.append(step_send_email(demo_service))
    results.append(step_close_deal(demo_service))
    return results
