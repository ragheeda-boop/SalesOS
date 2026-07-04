from typing import Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from ..business_objects import SignalType
from ..company import CompanyIntelligenceEngine


@dataclass
class MarketSignal:
    id: str
    type: SignalType
    title: str
    description: Optional[str] = None
    source: str = ""
    source_url: Optional[str] = None
    company_name: Optional[str] = None
    company_id: Optional[str] = None
    relevance_score: float = 0.5
    detected_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketTrend:
    topic: str
    signal_count: int
    avg_relevance: float
    first_detected: datetime
    last_detected: datetime
    momentum: float


class MarketIntelligenceEngine:
    """
    Monitors external data sources for market signals:
    - News, funding, projects, hiring, tenders, expansions
    - Government announcements, competitor moves
    - Industry trends, regulatory changes
    """

    def __init__(self, company_engine: Optional[CompanyIntelligenceEngine] = None):
        self.company_engine = company_engine
        self._signals: list[MarketSignal] = []
        self._sources = {
            "news_api": {"enabled": True, "last_poll": None, "interval_minutes": 60},
            "linkedin": {"enabled": True, "last_poll": None, "interval_minutes": 120},
            "government_portal": {"enabled": True, "last_poll": None, "interval_minutes": 360},
            "tender_portal": {"enabled": True, "last_poll": None, "interval_minutes": 180},
            "crunchbase": {"enabled": True, "last_poll": None, "interval_minutes": 240},
            "web_scraper": {"enabled": True, "last_poll": None, "interval_minutes": 60},
        }

    async def poll_source(self, source: str) -> list[MarketSignal]:
        """Poll a specific data source for new signals."""
        source_config = self._sources.get(source)
        if not source_config or not source_config["enabled"]:
            return []

        signals = await self._fetch_source_data(source)
        source_config["last_poll"] = datetime.utcnow()

        for signal in signals:
            self._signals.append(signal)
            if self.company_engine and signal.company_id:
                ci = self.company_engine.get(signal.company_id)
                if ci:
                    await self.company_engine.ingest_from_source(
                        signal.company_id, f"market_{source}",
                        {"signals": [{
                            "type": signal.type.value,
                            "title": signal.title,
                            "description": signal.description,
                            "confidence": signal.relevance_score,
                        }]}
                    )
        return signals

    async def _fetch_source_data(self, source: str) -> list[MarketSignal]:
        """Simulated source polling. Production would use real APIs."""
        now = datetime.utcnow()
        mock_signals = {
            "news_api": [
                MarketSignal(
                    id=f"news_{i}_{now.timestamp()}", type=SignalType.NEWS,
                    title=f"Market news article {i}", source="news_api",
                    relevance_score=0.6, detected_at=now,
                ) for i in range(3)
            ],
            "government_portal": [
                MarketSignal(
                    id=f"gov_{now.timestamp()}", type=SignalType.CONTRACT,
                    title="New government contract opportunity",
                    source="government_portal", relevance_score=0.8,
                    detected_at=now,
                ),
            ],
            "linkedin": [
                MarketSignal(
                    id=f"hiring_{now.timestamp()}", type=SignalType.HIRING,
                    title="Hiring surge detected", source="linkedin",
                    relevance_score=0.7, detected_at=now,
                ),
            ],
        }
        return mock_signals.get(source, [])

    async def poll_all_sources(self) -> list[MarketSignal]:
        """Poll all enabled sources."""
        all_signals = []
        for source in self._sources:
            signals = await self.poll_source(source)
            all_signals.extend(signals)
        return all_signals

    def get_signals(self, company_id: Optional[str] = None,
                    signal_type: Optional[SignalType] = None,
                    days_back: int = 30) -> list[MarketSignal]:
        """Get signals with optional filtering."""
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        results = [s for s in self._signals if s.detected_at >= cutoff]

        if company_id:
            results = [s for s in results if s.company_id == company_id]
        if signal_type:
            results = [s for s in results if s.type == signal_type]

        return sorted(results, key=lambda s: s.detected_at, reverse=True)

    def get_trends(self, days_back: int = 30) -> list[MarketTrend]:
        """Identify market trends from signals."""
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        recent = [s for s in self._signals if s.detected_at >= cutoff]

        topic_groups: dict[str, list[MarketSignal]] = {}
        for signal in recent:
            topic = signal.type.value
            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append(signal)

        trends = []
        for topic, signals in topic_groups.items():
            dates = [s.detected_at for s in signals]
            trends.append(MarketTrend(
                topic=topic,
                signal_count=len(signals),
                avg_relevance=round(sum(s.relevance_score for s in signals) / len(signals), 2),
                first_detected=min(dates),
                last_detected=max(dates),
                momentum=round(len(signals) / max(days_back, 1), 2),
            ))

        return sorted(trends, key=lambda t: t.signal_count, reverse=True)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_signals": len(self._signals),
            "active_sources": sum(1 for s in self._sources.values() if s["enabled"]),
            "signal_types": list(set(s.type.value for s in self._signals)),
            "signals_last_24h": len(self.get_signals(days_back=1)),
            "signals_last_7d": len(self.get_signals(days_back=7)),
        }
