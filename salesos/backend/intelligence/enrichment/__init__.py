from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from ..business_objects import BusinessObject, EntityType
from ..company import CompanyIntelligenceEngine


@dataclass
class EnrichmentField:
    name: str
    source: str
    confidence: float
    value: Any
    overwrite: bool = False


@dataclass
class EnrichmentResult:
    company_id: str
    fields_enriched: list[EnrichmentField]
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = True


class EnrichmentService:
    """
    Enriches company data from multiple external and internal sources.
    Uses priority-based field filling - higher priority sources overwrite lower ones.
    """

    SOURCE_PRIORITY = {
        "manual": 100,
        "crm": 80,
        "erp": 75,
        "government": 70,
        "linkedin": 60,
        "website": 50,
        "news": 40,
        "enrichment_api": 30,
        "ai_extraction": 20,
    }

    def __init__(self, company_engine: CompanyIntelligenceEngine):
        self.company_engine = company_engine
        self._enrichment_history: list[EnrichmentResult] = []

    async def enrich_company(self, company_id: str, source: str = "enrichment_api") -> EnrichmentResult:
        """Attempt to enrich a company with available data."""
        ci = self.company_engine.get(company_id)
        if not ci:
            return EnrichmentResult(
                company_id=company_id, fields_enriched=[], source=source, success=False
            )

        fields: list[EnrichmentField] = []
        bo = ci.business_object
        source_priority = self.SOURCE_PRIORITY.get(source, 10)

        enriched = await self._call_enrichment_source(bo)

        for key, value in enriched.items():
            current_value = getattr(bo.profile, key, None) or bo.profile.data.get(key)
            current_priority = self._get_field_source_priority(key, bo)

            if value and (not current_value or source_priority > current_priority):
                if key in ["name_ar", "name_en", "description", "website", "logo_url", "status"]:
                    setattr(bo.profile, key, value)
                else:
                    bo.profile.data[key] = value

                fields.append(EnrichmentField(
                    name=key, source=source, value=value,
                    confidence=0.7, overwrite=bool(current_value)
                ))

        result = EnrichmentResult(
            company_id=company_id, fields_enriched=fields, source=source
        )
        self._enrichment_history.append(result)
        return result

    async def _call_enrichment_source(self, bo: BusinessObject) -> dict[str, Any]:
        """
        Simulated enrichment call. In production, this would call:
        - LinkedIn API for company details
        - Government registries for legal data
        - Credit bureaus for financial data
        - Web scraping for website data
        """
        name = bo.profile.name_en or bo.profile.name_ar or ""
        return {
            "description": f"{name} is a company operating in the business sector. "
                          f"Enriched from multiple sources.",
            "employees_range": "50-200",
            "industry": "Technology",
            "founded_year": 2020,
            "linkedin_url": f"https://linkedin.com/company/{name.lower().replace(' ', '')}",
        }

    def batch_enrich(self, company_ids: list[str], source: str = "enrichment_api") -> list[EnrichmentResult]:
        """Enrich multiple companies in batch."""
        import asyncio
        results = []
        for cid in company_ids:
            try:
                result = asyncio.run(self.enrich_company(cid, source))
                results.append(result)
            except Exception:
                results.append(EnrichmentResult(
                    company_id=cid, fields_enriched=[], source=source, success=False
                ))
        return results

    def get_history(self, company_id: Optional[str] = None) -> list[EnrichmentResult]:
        if company_id:
            return [r for r in self._enrichment_history if r.company_id == company_id]
        return self._enrichment_history

    def _get_field_source_priority(self, field: str, bo: BusinessObject) -> int:
        """Determine the priority of the current field value."""
        if field in bo.profile.data and "_source" in bo.profile.data:
            source_name = bo.profile.data.get(f"{field}_source", "manual")
            return self.SOURCE_PRIORITY.get(source_name, 10)
        return self.SOURCE_PRIORITY.get("manual", 100)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_enrichments": len(self._enrichment_history),
            "successful": sum(1 for r in self._enrichment_history if r.success),
            "failed": sum(1 for r in self._enrichment_history if not r.success),
            "average_fields_per_enrichment": round(
                sum(len(r.fields_enriched) for r in self._enrichment_history) / max(len(self._enrichment_history), 1),
                1
            ),
        }
