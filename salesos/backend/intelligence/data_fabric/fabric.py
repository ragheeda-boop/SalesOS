from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from .connectors import ConnectorEngine, SyncResult
from .identity_resolution import IdentityResolver, IdentityFragment
from .entity_matching import EntityMatcher
from .quality import DataQualityEngine, QualityScore, TrustScore
from ..company import CompanyIntelligenceEngine


@dataclass
class DataPipeline:
    """End-to-end data pipeline: Connector → Resolve → Match → Quality → Company Engine."""
    connector_id: str
    records_synced: int
    identities_resolved: int
    entities_matched: int
    quality_scores: list[QualityScore]
    trust_scores: list[TrustScore]
    errors: list[str]
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = True


class DataFabric:
    """
    The unified data layer that orchestrates:
    Connectors → Identity Resolution → Entity Matching → Data Quality → Company Engine
    """

    def __init__(self, company_engine: Optional[CompanyIntelligenceEngine] = None):
        self.connectors = ConnectorEngine()
        self.identity_resolver = IdentityResolver()
        self.entity_matcher = EntityMatcher()
        self.quality = DataQualityEngine()
        self.company_engine = company_engine
        self._pipelines: list[DataPipeline] = []

    async def run_pipeline(self, connector_id: str) -> DataPipeline:
        """Run the full data pipeline for a connector."""
        pipeline = DataPipeline(
            connector_id=connector_id,
            records_synced=0, identities_resolved=0,
            entities_matched=0, quality_scores=[],
            trust_scores=[], errors=[], started_at=datetime.utcnow(),
        )

        try:
            sync_result = await self.connectors.sync(connector_id)
            pipeline.records_synced = sync_result.records_imported

            if not sync_result.success:
                pipeline.errors = sync_result.errors
                pipeline.success = False
                pipeline.completed_at = datetime.utcnow()
                self._pipelines.append(pipeline)
                return pipeline

            for record in sync_result.data:
                fragment = IdentityFragment(
                    source=connector_id,
                    name=record.get("name"),
                    name_en=record.get("name_en"),
                    email=record.get("email"),
                    domain=record.get("domain"),
                    phone=record.get("phone"),
                    cr_number=record.get("cr_number"),
                    external_id=record.get("id"),
                    metadata=record,
                )

                resolved = self.identity_resolver.resolve(fragment)
                pipeline.identities_resolved += 1

                quality = self.quality.evaluate(
                    resolved.id, record, source=connector_id
                )
                pipeline.quality_scores.append(quality)

                trust = self.quality.calculate_trust(
                    resolved.id, connector_id,
                    cross_references=len(resolved.fragments)
                )
                pipeline.trust_scores.append(trust)

                if self.company_engine and quality.overall > 0.3:
                    company_id = resolved.id
                    ci = self.company_engine.get_or_create(company_id)
                    await self.company_engine.ingest_from_source(
                        company_id, connector_id, record
                    )

            pipeline.completed_at = datetime.utcnow()

        except Exception as e:
            pipeline.errors.append(str(e))
            pipeline.success = False
            pipeline.completed_at = datetime.utcnow()

        self._pipelines.append(pipeline)
        return pipeline

    async def run_all_pipelines(self) -> dict[str, DataPipeline]:
        """Run pipelines for all connected connectors."""
        results = {}
        for connector in self.connectors.get_all_connectors():
            if connector.status.value == "connected":
                results[connector.id] = await self.run_pipeline(connector.id)
        return results

    def get_pipelines(self, connector_id: Optional[str] = None) -> list[DataPipeline]:
        if connector_id:
            return [p for p in self._pipelines if p.connector_id == connector_id]
        return self._pipelines

    def get_data_health(self) -> dict[str, Any]:
        """Overall data health dashboard."""
        all_quality = []
        all_trust = []
        for p in self._pipelines:
            all_quality.extend(p.quality_scores)
            all_trust.extend(p.trust_scores)

        return {
            "total_pipelines": len(self._pipelines),
            "successful_pipelines": sum(1 for p in self._pipelines if p.success),
            "total_records": sum(p.records_synced for p in self._pipelines),
            "total_identities": self.identity_resolver.stats["total_resolved"],
            "total_matches": self.entity_matcher.stats["total_matches"],
            "avg_quality": round(
                sum(q.overall for q in all_quality) / max(len(all_quality), 1), 2
            ),
            "avg_trust": round(
                sum(t.score for t in all_trust) / max(len(all_trust), 1), 2
            ),
            "connectors": self.connectors.stats,
            "quality": self.quality.stats,
        }
