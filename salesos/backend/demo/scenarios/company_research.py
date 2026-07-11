"""Company Research Scenario — Search → RAG → Meeting → Email.

Demonstrates the company intelligence and research capabilities.
"""

from typing import Any


def get_scenario_metadata() -> dict:
    return {
        "id": "company_research",
        "title": "Company Research Scenario",
        "description": "Search company → RAG query → Meeting brief → Email analysis",
        "steps": 4,
    }


def step_search_company(demo_service: Any) -> dict:
    """Step 1: Search for a company."""
    companies = demo_service.get_companies()
    if not companies:
        return {"step": 1, "action": "search_company", "label": "Search Company", "data": {"error": "No companies"}}

    company = companies[0]
    return {
        "step": 1,
        "action": "search_company",
        "label": "Search Company",
        "data": {
            "query": company["name_en"],
            "result": company,
            "narrative": f"Found {company['name_en']} ({company['name_ar']}). "
                         f"{company['industry'].title()} company with {company['employees']} employees.",
        },
    }


def step_rag_query(demo_service: Any) -> dict:
    """Step 2: Query RAG documents."""
    docs = demo_service.get_rag_documents()
    company_docs = [d for d in docs if d["type"] == "company_profile"]
    if not company_docs:
        return {"step": 2, "action": "rag_query", "label": "RAG Document Query", "data": {"error": "No RAG documents"}}

    doc = company_docs[0]
    return {
        "step": 2,
        "action": "rag_query",
        "label": "RAG Document Query",
        "data": {
            "query": f"Tell me about {doc['title']}",
            "document": doc,
            "narrative": f"Retrieved company profile: {doc['title']}. "
                         f"Content provides key intelligence about the company's background and operations.",
        },
    }


def step_view_meeting(demo_service: Any) -> dict:
    """Step 3: View meeting brief."""
    meetings = demo_service.get_meetings()
    if not meetings:
        return {"step": 3, "action": "view_meeting", "label": "View Meeting Brief", "data": {"error": "No meetings"}}

    meeting = meetings[0]
    return {
        "step": 3,
        "action": "view_meeting",
        "label": "View Meeting Brief",
        "data": {
            "meeting": {
                "title": meeting["title"],
                "type": meeting["type"],
                "date": meeting["date"],
                "duration": meeting["duration_minutes"],
                "notes": meeting["notes"],
                "outcome": meeting["outcome"],
            },
            "narrative": f"Meeting brief: '{meeting['title']}' ({meeting['type']}). "
                         f"Duration: {meeting['duration_minutes']} min. Outcome: {meeting['outcome']}.",
        },
    }


def step_email_analysis(demo_service: Any) -> dict:
    """Step 4: Analyze email threads."""
    emails = demo_service.get_emails()
    if not emails:
        return {"step": 4, "action": "email_analysis", "label": "Email Thread Analysis", "data": {"error": "No emails"}}

    email = emails[0]
    subject = email["subject"]
    direction = email["direction"]
    preview = email["preview"]
    sent_at = email["sent_at"]
    return {
        "step": 4,
        "action": "email_analysis",
        "label": "Email Thread Analysis",
        "data": {
            "email": {
                "subject": subject,
                "preview": preview,
                "direction": direction,
                "sent_at": sent_at,
            },
            "narrative": f"Email analysis: '{subject}' ({direction}). "
                         f"Preview: {preview[:100]}...",
        },
    }


def execute(demo_service: Any) -> list[dict]:
    """Execute the company research scenario."""
    return [
        step_search_company(demo_service),
        step_rag_query(demo_service),
        step_view_meeting(demo_service),
        step_email_analysis(demo_service),
    ]
