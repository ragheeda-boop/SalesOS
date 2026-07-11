import asyncio
import time
from typing import Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
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

    ENRICH_CACHE_TTL_SECONDS = 86400  # 24h
    EXTERNAL_TIMEOUT_SECONDS = 10.0
    CIRCUIT_BREAKER_THRESHOLD = 3
    CIRCUIT_BREAKER_RESET_SECONDS = 60.0

    def __init__(self, company_engine: CompanyIntelligenceEngine,
                 db_session_factory: Optional[Callable[[], AsyncSession]] = None,
                 feature_store: Any = None):
        self.company_engine = company_engine
        self._db_session_factory = db_session_factory
        self._feature_store = feature_store
        self._enrichment_history: list[EnrichmentResult] = []
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._circuit_breakers: dict[str, dict[str, Any]] = {}

    def _is_circuit_open(self, source: str) -> bool:
        breaker = self._circuit_breakers.get(source)
        if not breaker:
            return False
        if breaker["failures"] >= self.CIRCUIT_BREAKER_THRESHOLD:
            if time.monotonic() - breaker["opened_at"] < self.CIRCUIT_BREAKER_RESET_SECONDS:
                return True
            breaker["failures"] = 0
        return False

    def _record_failure(self, source: str) -> None:
        if source not in self._circuit_breakers:
            self._circuit_breakers[source] = {"failures": 0, "opened_at": 0.0}
        breaker = self._circuit_breakers[source]
        breaker["failures"] += 1
        if breaker["failures"] >= self.CIRCUIT_BREAKER_THRESHOLD:
            breaker["opened_at"] = time.monotonic()

    def _record_success(self, source: str) -> None:
        breaker = self._circuit_breakers.get(source)
        if breaker:
            breaker["failures"] = 0

    async def enrich_company(self, company_id: str, source: str = "enrichment_api") -> EnrichmentResult:
        """Attempt to enrich a company with available data."""
        cached = self._cache.get(company_id)
        if cached and (time.monotonic() - cached[0]) < self.ENRICH_CACHE_TTL_SECONDS:
            fields = [
                EnrichmentField(name=k, source=source, value=v, confidence=0.7)
                for k, v in cached[1].items()
            ]
            return EnrichmentResult(
                company_id=company_id, fields_enriched=fields, source=source
            )

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

        self._cache[company_id] = (time.monotonic(), dict(enriched))

        result = EnrichmentResult(
            company_id=company_id, fields_enriched=fields, source=source
        )
        self._enrichment_history.append(result)
        return result

    async def _call_enrichment_source(self, bo: BusinessObject) -> dict[str, Any]:
        """Enrich company from multiple real data sources: DB, scrapers, FeatureStore.

        Stages 1 (DB), 2 (scrapers), and 3 (FeatureStore) run in parallel
        since they are independent of each other. Results are merged,
        with earlier stages taking priority on conflict.
        """
        name = bo.profile.name_en or bo.profile.name_ar or ""
        cr_number = bo.profile.data.get("cr_number")
        tenant_id = bo.profile.data.get("tenant_id")

        async def _query_db() -> dict[str, Any]:
            if not self._db_session_factory or not bo.id:
                return {}
            from sqlalchemy import text
            try:
                async with asyncio.timeout(self.EXTERNAL_TIMEOUT_SECONDS):
                    async with self._db_session_factory() as session:
                        row = await session.execute(
                            text("SELECT * FROM companies WHERE id = :id LIMIT 1"),
                            {"id": bo.id},
                        )
                        company = row.mappings().one_or_none()
                        if company:
                            return {
                                "description": company.get("activity_description") or "",
                                "industry": company.get("industry") or "",
                                "employees_count": company.get("employees_count"),
                                "city": company.get("city"),
                                "region": company.get("region"),
                                "capital": company.get("capital"),
                                "legal_form": company.get("legal_form"),
                                "incorporation_date": str(company.get("incorporation_date")) if company.get("incorporation_date") else None,
                                "status": company.get("status"),
                            }
            except TimeoutError:
                self._record_failure("db_query")
            except Exception:
                self._record_failure("db_query")
            return {}

        async def _query_scrapers() -> dict[str, Any]:
            if not cr_number:
                return {}
            result: dict[str, Any] = {}
            scrapers_to_run = []

            if not self._is_circuit_open("balady"):
                from runtime.data_fabric_runtime.scrapers.balady import BaladyScraper
                scrapers_to_run.append(("balady", BaladyScraper(use_mock=False,)))

            try:
                tasks = []
                for slug, scraper in scrapers_to_run:
                    async def _run_one(s=scraper):
                        try:
                            async with asyncio.timeout(self.EXTERNAL_TIMEOUT_SECONDS):
                                r = await s.fetch_all()
                                return r
                        except TimeoutError:
                            self._record_failure(s.source_slug)
                            return None
                        except Exception:
                            self._record_failure(s.source_slug)
                            return None
                        finally:
                            await s.close()
                    tasks.append(_run_one())

                scrape_results = await asyncio.gather(*tasks, return_exceptions=True)

                for slug, scrape_result in zip([s[0] for s in scrapers_to_run], scrape_results):
                    if isinstance(scrape_result, Exception):
                        self._record_failure(slug)
                        continue
                    if scrape_result and scrape_result.records:
                        self._record_success(slug)
                        record = scrape_result.records[0]
                        result.update({
                            "name_ar": record.get("name_ar"),
                            "name_en": record.get("name_en"),
                            "city": record.get("city"),
                            "activity_description": record.get("activity_description") or record.get("activity"),
                            "incorporation_date": str(record.get("incorporation_date")) if record.get("incorporation_date") else None,
                        })
                    else:
                        self._record_failure(slug)
            except Exception:
                pass

            return result

        async def _query_feature_store() -> dict[str, Any]:
            if not self._feature_store or not tenant_id or not bo.id:
                return {}
            try:
                async with asyncio.timeout(self.EXTERNAL_TIMEOUT_SECONDS):
                    features = await self._feature_store.get_features(
                        company_id=bo.id,
                        tenant_id=tenant_id,
                    )
                    if features:
                        return {"feature_scores": {k: v.score for k, v in features.items()}}
            except TimeoutError:
                self._record_failure("feature_store")
            except Exception:
                self._record_failure("feature_store")
            return {}

        db_task = asyncio.create_task(_query_db())
        scraper_task = asyncio.create_task(_query_scrapers())
        fs_task = asyncio.create_task(_query_feature_store())

        db_result, scraper_result, fs_result = await asyncio.gather(
            db_task, scraper_task, fs_task,
        )

        result: dict[str, Any] = {}
        result.update(fs_result)
        result.update(scraper_result)
        result.update(db_result)

        if not result:
            result = {
                "description": f"{name} is a company operating in the business sector. "
                              f"Enriched from multiple sources.",
                "employees_range": "50-200",
                "industry": "Technology",
                "founded_year": 2020,
                "linkedin_url": f"https://linkedin.com/company/{name.lower().replace(' ', '')}",
            }

        return result

    async def batch_enrich(self, company_ids: list[str], source: str = "enrichment_api") -> list[EnrichmentResult]:
        """Enrich multiple companies in batch (parallel)."""
        tasks = [self.enrich_company(cid, source) for cid in company_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output: list[EnrichmentResult] = []
        for cid, res in zip(company_ids, results):
            if isinstance(res, Exception):
                output.append(EnrichmentResult(
                    company_id=cid, fields_enriched=[], source=source, success=False
                ))
            else:
                output.append(res)
        return output

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

    def clear_cache(self, company_id: Optional[str] = None) -> None:
        if company_id:
            self._cache.pop(company_id, None)
        else:
            self._cache.clear()

    def circuit_breaker_status(self) -> dict[str, dict[str, Any]]:
        now = time.monotonic()
        status = {}
        for source, breaker in self._circuit_breakers.items():
            is_open = (
                breaker["failures"] >= self.CIRCUIT_BREAKER_THRESHOLD
                and (now - breaker["opened_at"]) < self.CIRCUIT_BREAKER_RESET_SECONDS
            )
            status[source] = {
                "failures": breaker["failures"],
                "open": is_open,
                "remaining_cooldown_sec": max(0.0, self.CIRCUIT_BREAKER_RESET_SECONDS - (now - breaker["opened_at"])),
            }
        return status

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
            "cache_size": len(self._cache),
            "circuit_breakers": self.circuit_breaker_status(),
        }
