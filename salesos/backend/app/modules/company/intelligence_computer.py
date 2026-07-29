"""Transform Company360Response → CompanyIntelligenceDTO for frontend consumption."""
from __future__ import annotations

from datetime import datetime, timezone

from .intelligence_dto import (
    AIRecommendationDTO,
    BuyingJourneyDTO,
    CompanyDNADTO,
    CompanyFirmographicDTO,
    CompanyIntelligenceDTO,
    DecisionMakerDTO,
    DocumentItemDTO,
    GoldenRecordEntryDTO,
    GovernmentRecordDTO,
    RelationshipEdgeDTO,
    RelationshipNodeDTO,
    RelationshipsDTO,
    SignalItemDTO,
    TimelineEventDTO,
)
from .schemas import Company360Response


def build_intelligence_dto(resp: Company360Response) -> CompanyIntelligenceDTO:
    """Convert a Company360Response into the CompanyIntelligenceDTO the frontend expects."""
    company = resp.company
    overview = resp.overview
    org = resp.organization

    firmographic = CompanyFirmographicDTO(
        nameAr=company.name_ar or "",
        nameEn=company.name_en or "",
        crNumber=company.cr_number or "",
        city=company.city or "",
        region=company.region or "",
        status=company.status or "",
        industry=getattr(company, "activity_description", "") or "",
        employees=org.employees_count,
        foundedYear=_parse_year(org.incorporation_date),
        businessModel="b2b",
    )

    dna = _build_dna(resp, firmographic)
    ai_rec = _build_ai_recommendation(resp)
    decision_makers = _map_decision_makers(resp.decision_makers)
    relationships = _build_relationships(resp)
    timeline = _map_timeline(resp.timeline)
    signals = _map_signals(resp.signals.items)
    government = _map_government(resp.licenses)
    documents = _map_documents(resp.documents)
    buying_journey = _build_buying_journey(resp)
    golden_record = _map_golden_record(resp)

    return CompanyIntelligenceDTO(
        companyId=company.id,
        generatedAt=datetime.now(timezone.utc).isoformat(),
        dna=dna,
        aiRecommendation=ai_rec,
        decisionMakers=decision_makers,
        relationships=relationships,
        timeline=timeline,
        signals=signals,
        government=government,
        documents=documents,
        buyingJourney=buying_journey,
        goldenRecord=golden_record,
        firmographic=firmographic,
    )


# ── Private helpers ──────────────────────────────────────────────────────────


def _parse_year(date_str: str | None) -> int:
    if not date_str:
        return 0
    try:
        return int(date_str[:4])
    except (ValueError, IndexError):
        return 0


def _build_dna(resp: Company360Response, firmographic: CompanyFirmographicDTO) -> CompanyDNADTO:
    overview = resp.overview
    org = resp.organization
    emp = org.employees_count
    rev = overview.total_revenue

    if emp > 1000:
        size_label = "enterprise"
    elif emp > 250:
        size_label = "large"
    elif emp > 50:
        size_label = "medium"
    else:
        size_label = "small"

    return CompanyDNADTO(
        industry=firmographic.industry,
        businessModel="b2b",
        size={"employees": emp, "revenue": str(rev), "label": size_label},
        growthPattern="stable",
        buyingBehaviour={"score": 50, "intent": "medium"},
        technologyProfile={},
        financialHealth={"score": resp.health_score * 100, "revenue": rev, "growth": 0, "trend": "stable"},
        governmentExposure={"level": "low", "contracts": 0},
        expansionPotential={"score": 30, "markets": []},
        digitalPresence={"score": 20, "website": "basic", "social": "none"},
        hiringTrend={"trend": "stable", "openings": 0},
        procurementMaturity={"score": 20, "level": "initial"},
        relationshipStrength={"score": min(emp * 2, 100), "connections": overview.total_contacts},
        buyingIntent={"score": 40, "confidence": 60},
        riskLevel={"score": max(0, 100 - resp.health_score * 100), "level": "low" if resp.health_score > 0.7 else "medium"},
        confidenceScore=resp.health_score,
        dataFreshness={
            "score": 80,
            "updatedAt": getattr(resp.enrichment, "last_enriched_at", None) or "",
        },
        goldenRecordStatus={
            "status": "clean" if resp.golden_record_id else "needs_review",
            "sources": len(getattr(resp.enrichment, "sources", None) or []),
        },
    )


def _build_ai_recommendation(resp: Company360Response) -> AIRecommendationDTO | None:
    if resp.health_score < 0.3:
        return AIRecommendationDTO(
            action="re_engage",
            actionLabel="إعادة التواصل",
            reasoning="الشركة لديها نقاط تفاعل منخفضة",
            confidence=0.7,
            expectedRevenue=resp.overview.total_revenue * 0.1,
            expectedImpact="medium",
            estimatedTime="2 أسابيع",
            alternatives=[],
            risks=["الشركة قد تكون غير نشطة"],
        )
    if resp.overview.total_opportunities > 0:
        return AIRecommendationDTO(
            action="advance_pipeline",
            actionLabel="تقدم الأنابيب",
            reasoning=f"يوجد {resp.overview.total_opportunities} فرصة نشطة",
            confidence=0.8,
            expectedRevenue=resp.overview.total_revenue * 0.2,
            expectedImpact="high",
            estimatedTime="1 أسبوع",
            alternatives=[],
            risks=[],
        )
    return AIRecommendationDTO(
        action="explore",
        actionLabel="استكشاف",
        reasoning="الشركة جديدة، يُنصح باستكشاف الاحتياجات",
        confidence=0.6,
        expectedRevenue=0,
        expectedImpact="low",
        estimatedTime="1 شهر",
        alternatives=[],
        risks=[],
    )


def _map_decision_makers(decision_makers: list[dict]) -> list[DecisionMakerDTO]:
    result = []
    for dm in decision_makers:
        result.append(DecisionMakerDTO(
            id=str(dm.get("id", "")),
            name=str(dm.get("name", "")),
            role=str(dm.get("role", "")),
            department=str(dm.get("department", "")),
            influence=str(dm.get("influence", "low")),
            connected=bool(dm.get("connected", False)),
            email=dm.get("email"),
            phone=dm.get("phone"),
            lastInteraction=dm.get("last_interaction"),
        ))
    return result


def _build_relationships(resp: Company360Response) -> RelationshipsDTO:
    nodes: list[RelationshipNodeDTO] = []
    edges: list[RelationshipEdgeDTO] = []

    for dm in resp.decision_makers:
        node_id = str(dm.get("id", ""))
        if node_id:
            nodes.append(RelationshipNodeDTO(
                id=node_id,
                type="person",
                label=str(dm.get("name", "")),
                strength=0.8,
            ))

    for ent in resp.related_entities:
        ent_id = str(ent.get("id", ""))
        if ent_id:
            nodes.append(RelationshipNodeDTO(
                id=ent_id,
                type=str(ent.get("type", "company")),
                label=str(ent.get("name", "")),
                strength=float(ent.get("strength", 0.5)),
            ))
            edges.append(RelationshipEdgeDTO(
                source=resp.company.id,
                target=ent_id,
                type="related",
                label=str(ent.get("relationship", "مرتبط")),
                direction="bidirectional",
            ))

    return RelationshipsDTO(nodes=nodes, edges=edges)


def _map_timeline(timeline: list[dict]) -> list[TimelineEventDTO]:
    result = []
    for item in timeline:
        result.append(TimelineEventDTO(
            id=str(item.get("id", "")),
            type=str(item.get("type", "crm")),
            summary=str(item.get("summary", item.get("action", ""))),
            detail=item.get("detail"),
            date=str(item.get("timestamp", item.get("date", ""))),
            source=str(item.get("source", "")),
            confidence=item.get("confidence"),
            aiHighlighted=bool(item.get("ai_highlighted", False)),
        ))
    return result


def _map_signals(signals: list[dict]) -> list[SignalItemDTO]:
    result = []
    for s in signals:
        result.append(SignalItemDTO(
            id=str(s.get("id", "")),
            type=str(s.get("type", "news")),
            title=str(s.get("title", "")),
            description=str(s.get("description", "")),
            source=str(s.get("source", "")),
            severity=str(s.get("severity", "low")),
            timestamp=str(s.get("timestamp", "")),
            aiConfidence=float(s.get("ai_confidence", s.get("confidence", 0.0))),
        ))
    return result


def _map_government(licenses: list) -> list[GovernmentRecordDTO]:
    result = []
    for lic in licenses:
        result.append(GovernmentRecordDTO(
            id=str(getattr(lic, "id", "")),
            type="license",
            title=str(getattr(lic, "license_type", "")),
            status=str(getattr(lic, "status", "active")),
            issueDate=str(getattr(lic, "issue_date", None) or ""),
            expiryDate=str(getattr(lic, "expiry_date", None) or ""),
            confidence=0.9,
            source="government",
            freshness="current",
        ))
    return result


def _map_documents(documents: list[dict]) -> list[DocumentItemDTO]:
    result = []
    for doc in documents:
        result.append(DocumentItemDTO(
            id=str(doc.get("id", "")),
            title=str(doc.get("title", "")),
            type=str(doc.get("type", "pdf")),
            date=str(doc.get("created_at", doc.get("date", ""))),
            aiSummary=doc.get("ai_summary"),
            confidence=float(doc.get("confidence", 0.8)),
        ))
    return result


def _build_buying_journey(resp: Company360Response) -> BuyingJourneyDTO:
    opps = resp.overview.total_opportunities
    if opps > 3:
        stage, progress = "decision", 80
    elif opps > 1:
        stage, progress = "evaluation", 50
    elif opps > 0:
        stage, progress = "interest", 30
    else:
        stage, progress = "awareness", 10

    return BuyingJourneyDTO(
        currentStage=stage,
        progress=progress,
        timeInStage="30 يوم",
        recommendedAction="تحديد نقاط التواصل الرئيسية",
        stageDescription=f"الشركة في مرحلة {_stage_label(stage)}",
    )


def _stage_label(stage: str) -> str:
    return {
        "awareness": "الوعي",
        "interest": "الاهتمام",
        "evaluation": "التقييم",
        "decision": "القرار",
        "expansion": "التوسع",
    }.get(stage, stage)


def _map_golden_record(resp: Company360Response) -> list[GoldenRecordEntryDTO]:
    result = []
    if resp.golden_record_id:
        sources = getattr(resp.enrichment, "sources", None) or []
        result.append(GoldenRecordEntryDTO(
            id=resp.golden_record_id,
            entityName=resp.company.name_ar or resp.company.name_en or "",
            source=sources[0] if sources else "system",
            confidence=float(getattr(resp.enrichment, "confidence_score", 0.0) or 0.0),
            conflicts=[],
            freshness="current",
            status="matched" if getattr(resp.enrichment, "is_golden_record", False) else "potential_duplicate",
        ))
    return result
