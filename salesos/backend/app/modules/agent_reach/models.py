"""Agent Reach domain models."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


class ChannelType(str, enum.Enum):
    """Supported Agent Reach channels."""

    WEB = "web"
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    GITHUB = "github"
    RSS = "rss"
    BILIBILI = "bilibili"
    WEB_SEARCH = "web_search"
    REDDIT = "reddit"
    LINKEDIN = "linkedin"
    XIAOHONGSHU = "xiaohongshu"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class ChannelStatus(str, enum.Enum):
    """Channel availability status."""

    READY = "ready"
    CONFIG_NEEDED = "config_needed"
    NOT_INSTALLED = "not_installed"
    ERROR = "error"


class EvidenceType(str, enum.Enum):
    """Types of evidence from external research."""

    WEB_SEARCH = "web_search"
    GITHUB_REPO = "github_repo"
    GITHUB_SEARCH = "github_search"
    LINKEDIN_COMPANY = "linkedin_company"
    LINKEDIN_PROFILE = "linkedin_profile"
    LINKEDIN_JOBS = "linkedin_jobs"
    NEWS_ARTICLE = "news_article"
    RSS_ENTRY = "rss_entry"
    TWEET = "tweet"
    VIDEO = "video"


class SignalType(str, enum.Enum):
    """Company signal types from external sources."""

    HIRING = "hiring"
    FUNDING = "funding"
    PARTNERSHIP = "partnership"
    EXPANSION = "expansion"
    LEADERSHIP = "leadership"
    PRODUCT = "product"
    REGULATORY = "regulatory"
    REBRAND = "rebrand"
    HIRING_SLOWDOWN = "hiring_slowdown"
    LAYOFFS = "layoffs"
    ACQUISITION = "acquisition"
    IPO = "ipo"
    INTEGRATION = "integration"
    SECURITY = "security"
    OTHER = "other"


class SignalConfidence(str, enum.Enum):
    """Confidence level for signals."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ChannelInfo:
    """Status of a single Agent Reach channel."""

    channel: ChannelType
    status: ChannelStatus
    backend: str | None = None
    message: str | None = None


@dataclass
class AgentReachRequest:
    """Request to Agent Reach."""

    channel: ChannelType
    action: str  # read, search, subtitles, etc.
    query: str | None = None
    url: str | None = None
    max_results: int = 10
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentReachResult:
    """Result from Agent Reach."""

    success: bool
    channel: ChannelType
    action: str
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EvidenceItem:
    """A single piece of external evidence."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = ""
    evidence_type: EvidenceType = EvidenceType.WEB_SEARCH
    channel: ChannelType = ChannelType.WEB
    source_url: str = ""
    title: str = ""
    summary: str = ""
    raw_data: Any = None
    confidence: float = 0.0
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_name": self.company_name,
            "evidence_type": self.evidence_type.value,
            "channel": self.channel.value,
            "source_url": self.source_url,
            "title": self.title,
            "summary": self.summary,
            "confidence": self.confidence,
            "collected_at": self.collected_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Signal:
    """A company signal derived from external evidence."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = ""
    signal_type: SignalType = SignalType.OTHER
    confidence: SignalConfidence = SignalConfidence.LOW
    title: str = ""
    description: str = ""
    source_urls: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_name": self.company_name,
            "signal_type": self.signal_type.value,
            "confidence": self.confidence.value,
            "title": self.title,
            "description": self.description,
            "source_urls": self.source_urls,
            "evidence_ids": self.evidence_ids,
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CompanyIntelSummary:
    """Aggregated intelligence for a company."""

    company_name: str = ""
    evidence_count: int = 0
    signal_count: int = 0
    evidence: list[EvidenceItem] = field(default_factory=list)
    signals: list[Signal] = field(default_factory=list)
    channels_searched: list[str] = field(default_factory=list)
    last_researched: datetime | None = None
