"""Pydantic models matching the frontend CompanyIntelligenceDTO exactly."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyFirmographicDTO(BaseModel):
    nameAr: str = ""
    nameEn: str = ""
    crNumber: str = ""
    city: str = ""
    region: str = ""
    status: str = ""
    industry: str = ""
    employees: int = 0
    foundedYear: int = 0
    businessModel: str = "b2b"


class CompanyDNADTO(BaseModel):
    industry: str = ""
    businessModel: str = ""
    size: dict = Field(default_factory=lambda: {"employees": 0, "revenue": "0", "label": "small"})
    growthPattern: str = "stable"
    buyingBehaviour: dict = Field(default_factory=lambda: {"score": 0, "intent": "low"})
    technologyProfile: dict = Field(default_factory=dict)
    financialHealth: dict = Field(
        default_factory=lambda: {"score": 0, "revenue": 0, "growth": 0, "trend": "stable"}
    )
    governmentExposure: dict = Field(default_factory=lambda: {"level": "none", "contracts": 0})
    expansionPotential: dict = Field(default_factory=lambda: {"score": 0, "markets": []})
    digitalPresence: dict = Field(
        default_factory=lambda: {"score": 0, "website": "none", "social": "none"}
    )
    hiringTrend: dict = Field(default_factory=lambda: {"trend": "stable", "openings": 0})
    procurementMaturity: dict = Field(default_factory=lambda: {"score": 0, "level": "initial"})
    relationshipStrength: dict = Field(default_factory=lambda: {"score": 0, "connections": 0})
    buyingIntent: dict = Field(default_factory=lambda: {"score": 0, "confidence": 0})
    riskLevel: dict = Field(default_factory=lambda: {"score": 0, "level": "low"})
    confidenceScore: float = 0.0
    dataFreshness: dict = Field(default_factory=lambda: {"score": 0, "updatedAt": ""})
    goldenRecordStatus: dict = Field(default_factory=lambda: {"status": "clean", "sources": 0})


class AIRecommendationDTO(BaseModel):
    action: str = ""
    actionLabel: str = ""
    reasoning: str = ""
    confidence: float = 0.0
    expectedRevenue: float = 0.0
    expectedImpact: str = "low"
    estimatedTime: str = ""
    alternatives: list[dict] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class DecisionMakerDTO(BaseModel):
    id: str = ""
    name: str = ""
    role: str = ""
    department: str = ""
    influence: str = "low"
    connected: bool = False
    email: str | None = None
    phone: str | None = None
    lastInteraction: str | None = None


class RelationshipNodeDTO(BaseModel):
    id: str = ""
    type: str = "person"
    label: str = ""
    strength: float = 0.0


class RelationshipEdgeDTO(BaseModel):
    source: str = ""
    target: str = ""
    type: str = ""
    label: str = ""
    direction: str = "bidirectional"


class RelationshipsDTO(BaseModel):
    nodes: list[RelationshipNodeDTO] = Field(default_factory=list)
    edges: list[RelationshipEdgeDTO] = Field(default_factory=list)


class TimelineEventDTO(BaseModel):
    id: str = ""
    type: str = "crm"
    summary: str = ""
    detail: str | None = None
    date: str = ""
    source: str = ""
    confidence: float | None = None
    aiHighlighted: bool = False


class SignalItemDTO(BaseModel):
    id: str = ""
    type: str = "news"
    title: str = ""
    description: str = ""
    source: str = ""
    severity: str = "low"
    timestamp: str = ""
    aiConfidence: float = 0.0


class GovernmentRecordDTO(BaseModel):
    id: str = ""
    type: str = "cr"
    title: str = ""
    status: str = "active"
    issueDate: str | None = None
    expiryDate: str | None = None
    confidence: float = 0.0
    source: str = ""
    freshness: str = ""


class DocumentItemDTO(BaseModel):
    id: str = ""
    title: str = ""
    type: str = "pdf"
    date: str = ""
    aiSummary: str | None = None
    confidence: float = 0.0


class BuyingJourneyDTO(BaseModel):
    currentStage: str = "awareness"
    progress: float = 0.0
    timeInStage: str = ""
    recommendedAction: str = ""
    stageDescription: str = ""


class GoldenRecordEntryDTO(BaseModel):
    id: str = ""
    entityName: str = ""
    source: str = ""
    confidence: float = 0.0
    conflicts: list[str] = Field(default_factory=list)
    freshness: str = ""
    status: str = "matched"


class CompanyIntelligenceDTO(BaseModel):
    companyId: str
    generatedAt: str
    dna: CompanyDNADTO | None = None
    aiRecommendation: AIRecommendationDTO | None = None
    decisionMakers: list[DecisionMakerDTO] = Field(default_factory=list)
    relationships: RelationshipsDTO = Field(default_factory=RelationshipsDTO)
    timeline: list[TimelineEventDTO] = Field(default_factory=list)
    signals: list[SignalItemDTO] = Field(default_factory=list)
    government: list[GovernmentRecordDTO] = Field(default_factory=list)
    documents: list[DocumentItemDTO] = Field(default_factory=list)
    buyingJourney: BuyingJourneyDTO | None = None
    goldenRecord: list[GoldenRecordEntryDTO] = Field(default_factory=list)
    firmographic: CompanyFirmographicDTO | None = None
