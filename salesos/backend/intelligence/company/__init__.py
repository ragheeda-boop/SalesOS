from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from ..business_objects import (
    BusinessObject, BusinessObjectRegistry, ObjectIdentity,
    ObjectProfile, ObjectSignal, ObjectKnowledge, ObjectAI,
    EntityType, SignalType,
)


@dataclass
class CompanySource:
    """A data source for company intelligence."""
    name: str
    priority: int = 0
    last_synced: Optional[datetime] = None
    status: str = "pending"
    records_found: int = 0
    error: Optional[str] = None


@dataclass
class CompanyIntelligence:
    """The unified intelligence model for a single company."""
    business_object: BusinessObject
    sources: dict[str, CompanySource] = field(default_factory=dict)
    enrichment_history: list[dict[str, Any]] = field(default_factory=list)
    data_completeness: float = 0.0
    last_full_sync: Optional[datetime] = None
    confidence_score: float = 0.0

    @property
    def id(self) -> str:
        return self.business_object.id


class CompanyIntelligenceEngine:
    """
    Builds and maintains the unified Company Model from all sources.
    Each company is a BusinessObject with intelligence layered on top.
    """

    def __init__(self, registry: Optional[BusinessObjectRegistry] = None):
        self.registry = registry or BusinessObjectRegistry()
        self._companies: dict[str, CompanyIntelligence] = {}

    def get_or_create(self, company_id: str, name_ar: Optional[str] = None, name_en: Optional[str] = None) -> CompanyIntelligence:
        existing = self._companies.get(company_id)
        if existing:
            return existing

        bo = self.registry.get_or_create(company_id, EntityType.COMPANY)
        if name_ar:
            bo.profile.name_ar = name_ar
        if name_en:
            bo.profile.name_en = name_en

        ci = CompanyIntelligence(business_object=bo)
        ci.sources = {
            "website": CompanySource(name="Website", priority=1),
            "linkedin": CompanySource(name="LinkedIn", priority=2),
            "government": CompanySource(name="Government", priority=3),
            "news": CompanySource(name="News", priority=4),
            "crm": CompanySource(name="CRM", priority=5),
            "erp": CompanySource(name="ERP", priority=6),
        }
        self._companies[company_id] = ci
        return ci

    def get(self, company_id: str) -> Optional[CompanyIntelligence]:
        return self._companies.get(company_id)

    async def ingest_from_source(self, company_id: str, source: str, data: dict[str, Any]) -> None:
        """Ingest raw data from any source into the company model."""
        ci = self.get(company_id)
        if not ci:
            raise ValueError(f"Company {company_id} not found. Call get_or_create first.")

        source_config = ci.sources.get(source)
        if source_config:
            source_config.last_synced = datetime.utcnow()
            source_config.status = "synced"
            source_config.records_found = len(data) if isinstance(data, dict) else 1

        bo = ci.business_object

        profile_updates = {}
        for key in ["name_ar", "name_en", "description", "website", "logo_url", "status"]:
            if key in data:
                profile_updates[key] = data[key]

        for key, value in data.items():
            if key not in ["name_ar", "name_en", "description", "website", "logo_url", "status"]:
                if not isinstance(value, (list, dict)):
                    bo.profile.data[key] = value
                elif isinstance(value, dict):
                    bo.profile.data.setdefault(key, {}).update(value)

        if profile_updates:
            for k, v in profile_updates.items():
                setattr(bo.profile, k, v)

        source_signals = data.get("signals", [])
        for sig in source_signals:
            signal = ObjectSignal(
                id=f"{company_id}_sig_{len(bo.signals)}",
                type=SignalType(sig.get("type", "news")),
                title=sig.get("title", ""),
                description=sig.get("description"),
                source=source,
                confidence=sig.get("confidence", 0.5),
            )
            bo.signals.append(signal)

        if "summary" in data:
            bo.knowledge.summary = data["summary"]
        if "key_facts" in data:
            bo.knowledge.key_facts = data["key_facts"]

        ci.enrichment_history.append({
            "source": source,
            "timestamp": datetime.utcnow(),
            "fields_updated": list(data.keys()),
        })
        ci.last_full_sync = datetime.utcnow()
        self._recalculate_completeness(ci)

    def get_all(self) -> list[CompanyIntelligence]:
        return list(self._companies.values())

    def search(self, query: str) -> list[CompanyIntelligence]:
        results = self.registry.search(query)
        cis = []
        for bo in results:
            ci = self._companies.get(bo.id)
            if ci:
                cis.append(ci)
        return cis

    def _recalculate_completeness(self, ci: CompanyIntelligence) -> None:
        """Calculate data completeness score for a company."""
        bo = ci.business_object
        filled = 0
        total = 0

        checks = [
            bo.profile.name_ar, bo.profile.name_en, bo.profile.description,
            bo.profile.website, bo.profile.logo_url, bo.profile.status,
        ]
        total += len(checks)
        filled += sum(1 for c in checks if c)

        if bo.profile.data:
            total += len(bo.profile.data)
            filled += sum(1 for v in bo.profile.data.values() if v)

        if bo.knowledge.summary:
            filled += 1
        if bo.knowledge.key_facts:
            filled += min(len(bo.knowledge.key_facts), 5)
        total += 6

        ci.data_completeness = round((filled / max(total, 1)) * 100, 1)

        total_signals = len(bo.signals)
        total_sources = sum(1 for s in ci.sources.values() if s.last_synced)
        ci.confidence_score = round(
            (ci.data_completeness * 0.4 +
             (total_sources / max(len(ci.sources), 1)) * 100 * 0.3 +
             min(total_signals * 5, 100) * 0.3),
            1
        )

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_companies": len(self._companies),
            "total_sources": 6,
            "avg_completeness": round(
                sum(c.data_completeness for c in self._companies.values()) / max(len(self._companies), 1), 1
            ),
            "avg_confidence": round(
                sum(c.confidence_score for c in self._companies.values()) / max(len(self._companies), 1), 1
            ),
            "total_signals": sum(
                len(c.business_object.signals) for c in self._companies.values()
            ),
        }
