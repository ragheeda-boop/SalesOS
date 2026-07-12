"""PostgreSQL ScoreCard repository implementation."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base
from sdk.scoring.interfaces import ScoreCardRepository
from domains.scoring.models import (
    ConfidenceLevel, Score, ScoreCard, ScoringDimension,
    ScoringFactor, SignalEvidence,
)


class ScoreCardModel(Base):
    __tablename__ = "scoring_scorecards"

    id: Mapped[str] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(index=True)
    target_id: Mapped[str] = mapped_column(index=True)
    target_type: Mapped[str] = mapped_column(default="company")
    overall_score: Mapped[float] = mapped_column(default=0.0)
    overall_confidence: Mapped[str] = mapped_column(default="low")
    scores_json: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class PostgresScoreCardRepository(ScoreCardRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, scorecard: ScoreCard) -> ScoreCard:
        scores_data = []
        for s in scorecard.scores:
            factors_data = []
            for f in s.factors:
                factors_data.append({
                    "dimension": f.dimension.value,
                    "key": f.key,
                    "value": f.value,
                    "weight": f.weight,
                    "label": f.label,
                    "evidence": [
                        {
                            "source_layer": e.source_layer,
                            "source_domain": e.source_domain,
                            "signal_id": e.signal_id,
                            "signal_type": e.signal_type,
                            "intensity": e.intensity,
                            "narrative": e.narrative,
                            "detected_at": e.detected_at.isoformat() if e.detected_at else None,
                        }
                        for e in f.evidence
                    ],
                })
            scores_data.append({
                "dimension": s.dimension.value,
                "raw_score": s.raw_score,
                "normalized_score": s.normalized_score,
                "confidence": s.confidence.value,
                "factors": factors_data,
                "narrative": s.narrative,
            })
        stmt = select(ScoreCardModel).where(ScoreCardModel.id == scorecard.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.overall_score = scorecard.overall_score
            model.overall_confidence = scorecard.overall_confidence.value
            model.scores_json = {"scores": scores_data}
        else:
            model = ScoreCardModel(
                id=scorecard.id,
                tenant_id=scorecard.tenant_id,
                target_id=scorecard.target_id,
                target_type=scorecard.target_type,
                overall_score=scorecard.overall_score,
                overall_confidence=scorecard.overall_confidence.value,
                scores_json={"scores": scores_data},
            )
            self.session.add(model)
        await self.session.flush()
        return scorecard

    async def get(self, card_id: str) -> Optional[ScoreCard]:
        stmt = select(ScoreCardModel).where(ScoreCardModel.id == card_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_for_target(
        self, tenant_id: str, target_id: str, target_type: str = "company"
    ) -> Optional[ScoreCard]:
        stmt = (
            select(ScoreCardModel)
            .where(
                ScoreCardModel.tenant_id == tenant_id,
                ScoreCardModel.target_id == target_id,
                ScoreCardModel.target_type == target_type,
            )
            .order_by(ScoreCardModel.generated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_tenant(self, tenant_id: str, limit: int = 20) -> list[ScoreCard]:
        stmt = (
            select(ScoreCardModel)
            .where(ScoreCardModel.tenant_id == tenant_id)
            .order_by(ScoreCardModel.generated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    def _to_domain(self, model: ScoreCardModel) -> ScoreCard:
        scores = []
        for sd in (model.scores_json or {}).get("scores", []):
            factors = []
            for fd in sd.get("factors", []):
                evidence = [
                    SignalEvidence(
                        source_layer=e.get("source_layer", ""),
                        source_domain=e.get("source_domain", ""),
                        signal_id=e.get("signal_id", ""),
                        signal_type=e.get("signal_type", ""),
                        intensity=e.get("intensity", 0.5),
                        narrative=e.get("narrative", ""),
                        detected_at=(
                            datetime.fromisoformat(e["detected_at"])
                            if e.get("detected_at") else datetime.now(timezone.utc)
                        ),
                    )
                    for e in fd.get("evidence", [])
                ]
                factors.append(ScoringFactor(
                    dimension=ScoringDimension(fd["dimension"]),
                    key=fd.get("key", ""),
                    value=fd.get("value", 0.0),
                    weight=fd.get("weight", 1.0),
                    label=fd.get("label", ""),
                    evidence=evidence,
                ))
            scores.append(Score(
                dimension=ScoringDimension(sd["dimension"]),
                raw_score=sd.get("raw_score", 0.0),
                normalized_score=sd.get("normalized_score", 0.0),
                confidence=ConfidenceLevel(sd.get("confidence", "low")),
                factors=factors,
                narrative=sd.get("narrative", ""),
            ))
        return ScoreCard(
            id=model.id,
            tenant_id=model.tenant_id,
            target_id=model.target_id,
            target_type=model.target_type,
            scores=scores,
            overall_score=model.overall_score,
            overall_confidence=ConfidenceLevel(model.overall_confidence),
            generated_at=model.generated_at,
        )