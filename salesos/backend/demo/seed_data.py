"""SalesOS Demo Environment — Comprehensive Seed Data Generator
Generates 5 demo SaaS companies with full pipeline, opportunities, meetings,
NBA recommendations, workflow templates, RAG documents, and dashboard analytics.

Run: python -m backend.demo.seed_data
"""

import json
import os
import random
from datetime import datetime, timedelta, timezone

DEMO_TENANT_ID = "demo_tenant"
NOW = datetime.now(timezone.utc)

PIPELINE_STAGES = [
    "qualification", "discovery", "proposal", "negotiation",
    "closed_won", "closed_lost",
]

USERS = [
    {"id": "user_admin", "name": "Ahmed Al-Sulami", "role": "admin", "email": "admin@salesos.io"},
    {"id": "user_manager", "name": "Noura Al-Qahtani", "role": "manager", "email": "manager@salesos.io"},
    {"id": "user_rep1", "name": "Fahad Al-Otaibi", "role": "rep", "email": "rep1@salesos.io"},
    {"id": "user_rep2", "name": "Sara Al-Dosari", "role": "rep", "email": "rep2@salesos.io"},
    {"id": "user_rep3", "name": "Khalid Al-Mutairi", "role": "rep", "email": "rep3@salesos.io"},
]

COMPANIES = [
    {
        "id": "comp_techco", "tenant_id": DEMO_TENANT_ID,
        "name_en": "TechCo Solutions", "name_ar": "شركة تككو للحلول التقنية",
        "cr_number": "3010000101", "city": "Riyadh", "region": "Riyadh",
        "industry": "technology", "employees": 450, "status": "active",
        "description": "Leading SaaS provider of enterprise resource planning and cloud infrastructure solutions serving 200+ clients across MENA.",
        "annual_revenue": 85_000_000, "founded_year": 2015,
    },
    {
        "id": "comp_finserve", "tenant_id": DEMO_TENANT_ID,
        "name_en": "FinServe Technologies", "name_ar": "شركة فن سيرف للتقنية المالية",
        "cr_number": "3010000102", "city": "Jeddah", "region": "Makkah",
        "industry": "fintech", "employees": 320, "status": "active",
        "description": "Digital banking and payment processing platform powering 15 financial institutions with AI-driven fraud detection and real-time settlements.",
        "annual_revenue": 120_000_000, "founded_year": 2018,
    },
    {
        "id": "comp_healthplus", "tenant_id": DEMO_TENANT_ID,
        "name_en": "HealthPlus Systems", "name_ar": "شركة هيلث بلاس للأنظمة الصحية",
        "cr_number": "3010000103", "city": "Dammam", "region": "Eastern",
        "industry": "healthcare", "employees": 280, "status": "active",
        "description": "Electronic health records and telemedicine platform used by 45 hospitals and 200+ clinics across the Gulf region.",
        "annual_revenue": 65_000_000, "founded_year": 2017,
    },
    {
        "id": "comp_retailmax", "tenant_id": DEMO_TENANT_ID,
        "name_en": "RetailMax AI", "name_ar": "شركة ريتيل ماكس للذكاء الاصطناعي",
        "cr_number": "3010000104", "city": "Khobar", "region": "Eastern",
        "industry": "retail", "employees": 180, "status": "active",
        "description": "AI-powered retail analytics and inventory optimization platform serving omnichannel retailers with demand forecasting and dynamic pricing.",
        "annual_revenue": 42_000_000, "founded_year": 2020,
    },
    {
        "id": "comp_eduglobal", "tenant_id": DEMO_TENANT_ID,
        "name_en": "EduGlobal Learning", "name_ar": "شركة إديو جلوبال للتعليم",
        "cr_number": "3010000105", "city": "Riyadh", "region": "Riyadh",
        "industry": "education", "employees": 150, "status": "active",
        "description": "Digital learning management system and virtual classroom platform serving 500+ educational institutions with AI-powered personalized learning paths.",
        "annual_revenue": 38_000_000, "founded_year": 2019,
    },
]

DECISION_MAKERS = [
    {"id": "dm_tc_1", "company_id": "comp_techco", "name": "Dr. Youssef Al-Otaibi", "role": "CEO", "influence": "high", "connected": True, "email": "y.otaibi@techco.sa"},
    {"id": "dm_tc_2", "company_id": "comp_techco", "name": "Eng. Saad Al-Ghamdi", "role": "CTO", "influence": "high", "connected": True, "email": "s.ghamdi@techco.sa"},
    {"id": "dm_tc_3", "company_id": "comp_techco", "name": "Mr. Khaled Al-Mutairi", "role": "Procurement Director", "influence": "medium", "connected": False, "email": "k.almutairi@techco.sa"},
    {"id": "dm_fs_1", "company_id": "comp_finserve", "name": "Ms. Noura Al-Zahrani", "role": "CEO", "influence": "high", "connected": True, "email": "n.zahrani@finserve.sa"},
    {"id": "dm_fs_2", "company_id": "comp_finserve", "name": "Eng. Faisal Al-Ahmadi", "role": "CTO", "influence": "high", "connected": True, "email": "f.alahmadi@finserve.sa"},
    {"id": "dm_fs_3", "company_id": "comp_finserve", "name": "Mr. Abdullah Al-Tamimi", "role": "CFO", "influence": "high", "connected": True, "email": "a.tamimi@finserve.sa"},
    {"id": "dm_hp_1", "company_id": "comp_healthplus", "name": "Dr. Hani Baharith", "role": "CEO", "influence": "high", "connected": True, "email": "h.baharith@healthplus.sa"},
    {"id": "dm_hp_2", "company_id": "comp_healthplus", "name": "Ms. Manal Al-Shammari", "role": "Procurement Director", "influence": "medium", "connected": True, "email": "m.alshammari@healthplus.sa"},
    {"id": "dm_hp_3", "company_id": "comp_healthplus", "name": "Dr. Ahmed Al-Qahtani", "role": "Medical Director", "influence": "high", "connected": False, "email": "a.alqahtani@healthplus.sa"},
    {"id": "dm_rm_1", "company_id": "comp_retailmax", "name": "Eng. Abdulaziz Al-Sohaibani", "role": "CEO", "influence": "high", "connected": True, "email": "a.alsohaibani@retailmax.sa"},
    {"id": "dm_rm_2", "company_id": "comp_retailmax", "name": "Ms. Reem Al-Harthi", "role": "CTO", "influence": "high", "connected": True, "email": "r.alharthi@retailmax.sa"},
    {"id": "dm_eg_1", "company_id": "comp_eduglobal", "name": "Dr. Sultan Al-Dosari", "role": "CEO", "influence": "high", "connected": True, "email": "s.aldosari@eduglobal.sa"},
    {"id": "dm_eg_2", "company_id": "comp_eduglobal", "name": "Ms. Lina Al-Harbi", "role": "CTO", "influence": "high", "connected": True, "email": "l.alharbi@eduglobal.sa"},
    {"id": "dm_eg_3", "company_id": "comp_eduglobal", "name": "Mr. Mohammed Al-Anzi", "role": "VP Education", "influence": "medium", "connected": True, "email": "m.alanzi@eduglobal.sa"},
]

OPPORTUNITY_TEMPLATES = [
    {"stage": "qualification", "val_range": (15000, 80000), "conf_range": (0.15, 0.35)},
    {"stage": "discovery", "val_range": (30000, 150000), "conf_range": (0.25, 0.50)},
    {"stage": "proposal", "val_range": (50000, 300000), "conf_range": (0.40, 0.65)},
    {"stage": "negotiation", "val_range": (80000, 500000), "conf_range": (0.60, 0.85)},
    {"stage": "closed_won", "val_range": (10000, 450000), "conf_range": (1.0, 1.0)},
    {"stage": "closed_lost", "val_range": (10000, 250000), "conf_range": (0.0, 0.0)},
]

OPPORTUNITY_TITLES_BY_INDUSTRY = {
    "technology": [
        "ERP Cloud Migration Project", "AI-Powered Analytics Platform",
        "DevOps Pipeline Automation Suite", "Cybersecurity Framework Implementation",
        "Enterprise Data Lake Architecture",
    ],
    "fintech": [
        "Real-Time Payment Gateway Integration", "Fraud Detection ML Engine",
        "Open Banking API Platform", "Digital Onboarding Solution",
        "RegTech Compliance Automation",
    ],
    "healthcare": [
        "EHR System Upgrade", "Telemedicine Platform Expansion",
        "AI Diagnostic Assistant", "Patient Portal Modernization",
        "Hospital Management System",
    ],
    "retail": [
        "Omnichannel Analytics Suite", "Inventory Optimization Engine",
        "Dynamic Pricing Platform", "Customer 360 Data Platform",
        "Supply Chain Visibility Solution",
    ],
    "education": [
        "LMS Platform Migration", "Virtual Classroom Enhancement",
        "AI Learning Path Engine", "Student Analytics Dashboard",
        "Assessment Automation Platform",
    ],
}

SIGNAL_TYPES = ["hiring", "expansion", "partnership", "contract", "regulation", "market", "financial", "news"]

MEETING_TYPES = ["discovery_call", "product_demo", "technical_review", "executive_briefing", "negotiation_session", "kickoff"]
MEETING_NOTES = {
    "discovery_call": "Discussed current challenges with existing solution. Customer identified key pain points in scalability and reporting. Agreed to schedule a technical deep-dive next week.",
    "product_demo": "Demonstrated core platform capabilities including real-time analytics dashboard and workflow automation. Customer team impressed with UI/UX but raised concerns about integration complexity.",
    "technical_review": "Reviewed API documentation and integration architecture. Engineering team asked detailed questions about data residency and compliance. Shared architecture diagram and SLA commitments.",
    "executive_briefing": "Presented ROI analysis and case studies from similar deployments. CEO and CTO expressed strong interest. Discussed high-level budget range and timeline expectations.",
    "negotiation_session": "Reviewed contract terms and pricing structure. Customer requested additional discount for multi-year commitment. Agreed to prepare revised proposal with volume pricing.",
    "kickoff": "Project kickoff meeting with stakeholder mapping and success criteria definition. Established bi-weekly steering committee. Agreed on 90-day implementation timeline.",
}

EMAIL_THREADS = [
    {"subject": "Follow-up on product demo", "preview": "Thank you for the comprehensive demo yesterday. Our team would like to schedule a technical review session to discuss integration requirements."},
    {"subject": "Proposal & Pricing", "preview": "Please find attached the detailed proposal and pricing breakdown. We are available to discuss terms at your earliest convenience."},
    {"subject": "Contract Review", "preview": "Our legal team has reviewed the contract. We have a few comments on the SLA and data processing terms that we'd like to address."},
    {"subject": "Meeting Recap & Next Steps", "preview": "Great meeting today. Here is a summary of the key decisions and action items we agreed upon."},
    {"subject": "ROI Analysis Request", "preview": "Could you provide a detailed ROI analysis based on the implementation scope we discussed? This will help us secure internal budget approval."},
]

NBA_RECOMMENDATIONS = [
    {"type": "send_email", "title": "Send follow-up email after demo", "description": "Customer showed strong interest during demo. Send personalized follow-up with case studies.", "priority": "high"},
    {"type": "schedule_meeting", "title": "Schedule technical deep-dive", "description": "Engineering team needs to evaluate integration complexity. Schedule technical review session.", "priority": "high"},
    {"type": "prepare_proposal", "title": "Prepare revised proposal", "description": "Customer requested updated pricing for multi-year commitment. Adjust discount structure.", "priority": "critical"},
    {"type": "share_roi", "title": "Share ROI analysis", "description": "Customer needs internal budget approval. Provide detailed ROI analysis with industry benchmarks.", "priority": "high"},
    {"type": "send_contract", "title": "Send contract for e-signature", "description": "All terms agreed verbally. Send digital contract for signing.", "priority": "critical"},
    {"type": "check_in", "title": "Check in with champion", "description": "No activity for 5 days. Reach out to internal champion to assess timeline.", "priority": "medium"},
    {"type": "share_case_study", "title": "Share relevant case study", "description": "Customer in similar industry. Share case study of successful deployment.", "priority": "medium"},
    {"type": "schedule_executive", "title": "Schedule executive briefing", "description": "C-level engagement needed to move deal forward. Arrange meeting with VP Sales.", "priority": "high"},
]

WORKFLOW_TEMPLATES = [
    {"id": "wf_deal_review", "name": "Deal Review Approval", "category": "sales", "steps": ["Submit deal for review", "Manager approves", "VP reviews if >$100K", "Deal moves to negotiation"]},
    {"id": "wf_onboarding", "name": "Customer Onboarding", "category": "operations", "steps": ["Welcome email", "Kickoff call", "Technical setup", "Training session", "Go-live"]},
    {"id": "wf_renewal", "name": "Contract Renewal", "category": "revenue", "steps": ["90-day reminder", "Usage review", "Proposal sent", "Negotiation", "Signed"]},
    {"id": "wf_lead_followup", "name": "Lead Follow-up Process", "category": "marketing", "steps": ["Initial outreach", "Follow-up call", "Demo scheduled", "Proposal sent", "Closed"]},
]


def _random_date(days_ago_min: int, days_ago_max: int) -> str:
    return (NOW - timedelta(days=random.randint(days_ago_min, days_ago_max))).isoformat()


def generate_opportunities():
    opportunities = []
    global_covered: dict[str, bool] = {s: False for s in PIPELINE_STAGES}
    for company in COMPANIES:
        industry = company["industry"]
        titles = OPPORTUNITY_TITLES_BY_INDUSTRY.get(industry, OPPORTUNITY_TITLES_BY_INDUSTRY["technology"])
        num_opps = random.randint(3, 5)
        selected_titles = random.sample(titles, min(num_opps, len(titles)))
        for i, title in enumerate(selected_titles):
            uncovered = [s for s in PIPELINE_STAGES if not global_covered[s]]
            if uncovered:
                stage = uncovered[0]
            else:
                stage = random.choice(PIPELINE_STAGES)
            global_covered[stage] = True
            tmpl = next(t for t in OPPORTUNITY_TEMPLATES if t["stage"] == stage)
            val = random.randint(tmpl["val_range"][0], tmpl["val_range"][1])
            conf = round(random.uniform(tmpl["conf_range"][0], tmpl["conf_range"][1]), 2)
            opp = {
                "id": f"opp_{company['id']}_{i}",
                "tenant_id": DEMO_TENANT_ID,
                "company_id": company["id"],
                "company_name": company["name_en"],
                "title": title,
                "stage": stage,
                "estimated_value": val,
                "confidence": conf,
                "buying_intent": round(random.uniform(0.3, 0.95), 2),
                "relationship_strength": round(random.uniform(0.3, 0.95), 2),
                "currency": "SAR",
                "owner_id": random.choice(USERS)["id"],
                "created_at": _random_date(15, 90),
                "expected_close": _random_date(1, 60) if stage != "closed_won" else None,
                "won_amount": val if stage == "closed_won" else None,
                "loss_reason": "Budget constraints" if stage == "closed_lost" else None,
            }
            opportunities.append(opp)
    return opportunities


def generate_meetings(opportunities):
    meetings = []
    for opp in opportunities:
        num_meetings = random.randint(1, 3)
        for i in range(num_meetings):
            mt = random.choice(MEETING_TYPES)
            notes = MEETING_NOTES.get(mt, "General discussion about project requirements and next steps.")
            meetings.append({
                "id": f"mtg_{opp['id']}_{i}",
                "tenant_id": DEMO_TENANT_ID,
                "opportunity_id": opp["id"],
                "company_id": opp["company_id"],
                "type": mt,
                "title": f"{mt.replace('_', ' ').title()} — {opp['company_name']}",
                "notes": notes,
                "date": _random_date(1, 45),
                "duration_minutes": random.choice([30, 45, 60, 90]),
                "owner_id": opp["owner_id"],
                "outcome": random.choice(["completed", "completed", "completed", "cancelled", "rescheduled"]),
            })
    return meetings


def generate_emails(opportunities):
    emails = []
    for opp in opportunities:
        num_emails = random.randint(1, 2)
        for i in range(num_emails):
            thread = random.choice(EMAIL_THREADS)
            emails.append({
                "id": f"email_{opp['id']}_{i}",
                "tenant_id": DEMO_TENANT_ID,
                "opportunity_id": opp["id"],
                "company_id": opp["company_id"],
                "subject": thread["subject"],
                "preview": thread["preview"],
                "from_address": opp["owner_id"] + "@salesos.io",
                "to_address": f"contact@{opp['company_id'].replace('comp_', '')}.sa",
                "sent_at": _random_date(1, 30),
                "direction": random.choice(["outbound", "inbound"]),
            })
    return emails


def generate_signals(opportunities):
    signals = []
    company_ids = list(set(o["company_id"] for o in opportunities))
    for cid in company_ids:
        company = next(c for c in COMPANIES if c["id"] == cid)
        for _ in range(random.randint(2, 4)):
            sig_type = random.choice(SIGNAL_TYPES)
            signals.append({
                "id": f"sig_{cid}_{random.randint(1000,9999)}",
                "tenant_id": DEMO_TENANT_ID,
                "company_id": cid,
                "type": sig_type,
                "title": f"{sig_type.title()} signal — {company['name_en']}",
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "ai_confidence": round(random.uniform(0.6, 0.98), 2),
                "timestamp": _random_date(1, 30),
                "details": f"Detected {sig_type} activity at {company['name_en']}. Relevant to ongoing opportunities.",
            })
    return signals


def generate_tasks(opportunities):
    tasks = []
    for opp in opportunities[:12]:
        rec = random.choice(NBA_RECOMMENDATIONS)
        tasks.append({
            "id": f"task_{opp['id']}_{random.randint(100,999)}",
            "tenant_id": DEMO_TENANT_ID,
            "opportunity_id": opp["id"],
            "company_id": opp["company_id"],
            "title": f"[{rec['type']}] {rec['title']} — {opp['company_name']}",
            "description": rec["description"],
            "priority": rec["priority"],
            "source": "nba",
            "status": random.choice(["pending", "in_progress", "completed"]),
            "assigned_to": opp["owner_id"],
            "created_at": _random_date(1, 14),
            "due_at": _random_date(0, 14) if random.random() > 0.3 else None,
        })
    return tasks


def generate_nba_recommendations(opportunities):
    recs = []
    for opp in opportunities[:15]:
        rec = random.choice(NBA_RECOMMENDATIONS)
        recs.append({
            "id": f"nba_{opp['id']}_{random.randint(100,999)}",
            "tenant_id": DEMO_TENANT_ID,
            "opportunity_id": opp["id"],
            "company_id": opp["company_id"],
            "type": rec["type"],
            "title": rec["title"],
            "description": rec["description"],
            "priority": rec["priority"],
            "confidence": round(random.uniform(0.5, 0.95), 2),
            "generated_at": _random_date(0, 7),
            "status": random.choice(["active", "completed", "dismissed"]),
        })
    return recs


def generate_workflow_templates():
    templates = []
    for wf in WORKFLOW_TEMPLATES:
        templates.append({
            "id": wf["id"],
            "tenant_id": DEMO_TENANT_ID,
            "name": wf["name"],
            "category": wf["category"],
            "steps": [{"order": i + 1, "name": s} for i, s in enumerate(wf["steps"])],
            "is_active": True,
            "created_at": _random_date(30, 90),
        })
    return templates


def generate_rag_documents():
    docs = []
    for company in COMPANIES:
        docs.append({
            "id": f"doc_profile_{company['id']}",
            "tenant_id": DEMO_TENANT_ID,
            "company_id": company["id"],
            "type": "company_profile",
            "title": f"{company['name_en']} — Company Profile",
            "content": f"{company['name_en']} ({company['name_ar']}) is a leading {company['industry']} company "
                       f"based in {company['city']}, {company['region']}. Founded in {company['founded_year']}, "
                       f"the company employs {company['employees']} people and generates {company['annual_revenue']} SAR "
                       f"in annual revenue. {company['description']}",
            "created_at": _random_date(30, 90),
        })
        docs.append({
            "id": f"doc_meeting_{company['id']}",
            "tenant_id": DEMO_TENANT_ID,
            "company_id": company["id"],
            "type": "meeting_notes",
            "title": f"{company['name_en']} — Executive Briefing Notes",
            "content": f"Executive briefing with {company['name_en']}'s leadership team. Discussed "
                       f"digital transformation initiatives and potential partnership opportunities. "
                       f"Key decision makers include the CEO and CTO who showed strong interest in our platform.",
            "created_at": _random_date(7, 30),
        })
    return docs


def generate_dashboard_analytics():
    days = 90
    analytics = []
    for company in COMPANIES:
        for day_offset in range(0, days, 7):
            dt = NOW - timedelta(days=day_offset)
            analytics.append({
                "id": f"analytics_{company['id']}_{day_offset}",
                "tenant_id": DEMO_TENANT_ID,
                "company_id": company["id"],
                "metric": "pipeline_value",
                "value": round(random.uniform(200000, 2000000), 2),
                "dimension": "total",
                "recorded_at": dt.isoformat(),
            })
            analytics.append({
                "id": f"analytics_{company['id']}_{day_offset}_opps",
                "tenant_id": DEMO_TENANT_ID,
                "company_id": company["id"],
                "metric": "opportunities_count",
                "value": random.randint(2, 8),
                "dimension": "total",
                "recorded_at": dt.isoformat(),
            })
    return analytics


def generate_timeline_events(opportunities):
    events = []
    for opp in opportunities[:15]:
        for i in range(random.randint(1, 3)):
            event_type = random.choice(["meeting", "email", "call", "demo", "note", "task"])
            events.append({
                "id": f"tl_{opp['id']}_{i}",
                "tenant_id": DEMO_TENANT_ID,
                "opportunity_id": opp["id"],
                "company_id": opp["company_id"],
                "event_type": event_type,
                "title": f"{event_type.title()} — {opp['title'][:30]}",
                "description": f"Activity logged for opportunity '{opp['title']}' with {opp['company_name']}.",
                "timestamp": _random_date(1, 30),
                "user": opp["owner_id"],
            })
    return events


def seed_data(base_dir: str | None = None):
    print("=" * 60)
    print("  SalesOS Demo Environment Seed Generator")
    print("=" * 60)
    print(f"  Tenant: {DEMO_TENANT_ID}")
    print()

    opportunities = generate_opportunities()
    meetings = generate_meetings(opportunities)
    emails = generate_emails(opportunities)
    signals = generate_signals(opportunities)
    tasks = generate_tasks(opportunities)
    nba_recs = generate_nba_recommendations(opportunities)
    workflows = generate_workflow_templates()
    rag_docs = generate_rag_documents()
    analytics = generate_dashboard_analytics()
    timeline = generate_timeline_events(opportunities)

    output = {
        "tenant_id": DEMO_TENANT_ID,
        "users": USERS,
        "companies": COMPANIES,
        "decision_makers": DECISION_MAKERS,
        "opportunities": opportunities,
        "meetings": meetings,
        "emails": emails,
        "signals": signals,
        "tasks": tasks,
        "nba_recommendations": nba_recs,
        "workflow_templates": workflows,
        "rag_documents": rag_docs,
        "dashboard_analytics": analytics,
        "timeline_events": timeline,
        "generated_at": NOW.isoformat(),
        "total": {
            "users": len(USERS),
            "companies": len(COMPANIES),
            "decision_makers": len(DECISION_MAKERS),
            "opportunities": len(opportunities),
            "meetings": len(meetings),
            "emails": len(emails),
            "signals": len(signals),
            "tasks": len(tasks),
            "nba_recommendations": len(nba_recs),
            "workflow_templates": len(workflows),
            "rag_documents": len(rag_docs),
            "dashboard_analytics": len(analytics),
            "timeline_events": len(timeline),
        },
    }

    print("  +----------------------+-------+")
    print("  | Metric               | Count |")
    print("  +----------------------+-------+")
    for key, val in output["total"].items():
        print(f"  | {key:20s} | {val:5d} |")
    print("  +----------------------+-------+")

    demo_dir = base_dir or os.path.join(os.path.dirname(__file__))
    os.makedirs(demo_dir, exist_ok=True)
    output_path = os.path.join(demo_dir, "demo_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  [FILE] Written to: {output_path}")

    return output


if __name__ == "__main__":
    data = seed_data()
    print(f"\n  [DONE] Demo environment ready with {data['total']['companies']} companies, "
          f"{data['total']['opportunities']} opportunities, {data['total']['meetings']} meetings")
