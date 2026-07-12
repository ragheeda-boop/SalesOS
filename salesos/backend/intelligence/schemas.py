"""Pydantic output schemas for all AI agents."""

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    fact: str = Field(description="حقيقة محددة مستخرجة من التحليل")
    source: str = Field(description="مصدر المعلومة (قاعدة بيانات، علاقة، إشارة)")
    confidence: float = Field(ge=0, le=1, description="مدى الثقة في هذه الحقيقة (0-1)")


class AgentAnalysis(BaseModel):
    analysis: str = Field(description="التحليل النصي الكامل")
    confidence: float = Field(ge=0, le=1, description="درجة الثقة الإجمالية (0-1)")
    evidence: list[EvidenceItem] = Field(default_factory=list, description="قائمة الحقائق المستندة إلى بيانات")
    sources: list[str] = Field(default_factory=list, description="مصادر البيانات المستخدمة في التحليل")


class CompetitorAnalysis(AgentAnalysis):
    competitors: list[dict] = Field(default_factory=list, description="قائمة المنافسين مع تفاصيل")
    market_position: str = Field(default="", description="الوضع التنافسي للشركة")


class MeetingPreparation(AgentAnalysis):
    agenda: list[str] = Field(default_factory=list, description="جدول الأعمال")
    talking_points: list[str] = Field(default_factory=list, description="نقاط النقاش الرئيسية")
    decision_makers: list[dict] = Field(default_factory=list, description="صناع القرار")


class ProposalContent(AgentAnalysis):
    proposal: str = Field(default="", description="نص المقترح التجاري")
    status: str = Field(default="draft", description="حالة المقترح")


class ContractReview(AgentAnalysis):
    risks: list[str] = Field(default_factory=list, description="المخاطر التعاقدية")
    recommendations: list[str] = Field(default_factory=list, description="التوصيات")


class PricingAnalysis(AgentAnalysis):
    suggested_price: float | None = Field(default=None, description="السعر المقترح")
    price_range: dict[str, float] = Field(default_factory=dict, description="نطاق السعر (min, max)")


class ForecastAnalysis(AgentAnalysis):
    predicted_revenue: float | None = Field(default=None, description="الإيرادات المتوقعة")
    confidence_interval: dict[str, float] = Field(default_factory=dict, description="فاصل الثقة (lower, upper)")


class RenewalRisk(AgentAnalysis):
    risk_level: str = Field(default="medium", description="مستوى مخاطر التجديد")
    retention_strategies: list[str] = Field(default_factory=list, description="استراتيجيات الاحتفاظ")


class TenderAnalysis(AgentAnalysis):
    opportunities: list[dict] = Field(default_factory=list, description="فرص المناقصات")
    eligibility: str = Field(default="", description="أهلية الشركة")


class NewsSummary(AgentAnalysis):
    articles: list[dict] = Field(default_factory=list, description="قائمة المقالات")


class RelationshipMap(AgentAnalysis):
    network: list[dict] = Field(default_factory=list, description="شبكة العلاقات")
    key_contacts: list[dict] = Field(default_factory=list, description="جهات الاتصال الرئيسية")


class ResearchSummary(AgentAnalysis):
    key_facts: list[str] = Field(default_factory=list, description="حقائق رئيسية")
    opportunities: list[str] = Field(default_factory=list, description="فرص البيع")
    recommendations: list[str] = Field(default_factory=list, description="التوصيات")
