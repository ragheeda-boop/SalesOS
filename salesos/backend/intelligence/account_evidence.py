"""Idempotent persistence for account intelligence evidence snapshots."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domains.commercial.evidence.contracts.models import (
    ConfidenceLevel,
    EvidenceItem,
    EvidenceKind,
    EvidenceSource,
    EvidenceType,
    Insight,
    InsightCategory,
)

RULE_VERSION = "account-signals-v1"


def _confidence_level(value: float) -> ConfidenceLevel:
    if value >= 0.8:
        return ConfidenceLevel.HIGH
    if value >= 0.5:
        return ConfidenceLevel.MEDIUM
    if value >= 0.2:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.UNKNOWN


async def persist_account_insight(
    db: AsyncSession,
    *,
    tenant_id: str,
    company_id: str,
    company_name: str,
    facts: dict[str, Any],
) -> dict[str, Any]:
    """Persist a deterministic account insight and its CRM evidence rows.

    Repeating a write with the same source snapshot and rule version returns the
    original insight. The caller supplies tenant context through DEC-085.
    """
    account_signals = facts["account_signals"]
    source_snapshot = {
        "rule_version": RULE_VERSION,
        "company_id": company_id,
        "total_opportunities": facts["total_opportunities"],
        "active_opportunities": facts["active_opportunities"],
        "won_deals": facts["won_deals"],
        "lost_deals": facts["lost_deals"],
        "activity_count": facts["activity_count"],
        "last_activity_at": facts["last_activity_at"],
        "signals": [signal["code"] for signal in account_signals["signals"]],
    }
    canonical_snapshot = json.dumps(source_snapshot, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical_snapshot.encode("utf-8")).hexdigest()
    idempotency_key = f"{RULE_VERSION}:{digest}"
    insight_id = uuid5(NAMESPACE_URL, f"{tenant_id}:{idempotency_key}").hex

    evidence_items = []
    for signal in account_signals["signals"]:
        evidence_type = (
            EvidenceType.ACTIVITY_SIGNAL
            if signal["source"] == "activity_records"
            else EvidenceType.DATA_AGGREGATE
            if signal["polarity"] == "neutral"
            else EvidenceType.BUSINESS_RULE
        )
        evidence_items.append(
            EvidenceItem(
                id=uuid5(NAMESPACE_URL, f"{insight_id}:{signal['code']}").hex,
                evidence_type=evidence_type,
                source=EvidenceSource(
                    source_domain=signal["source"],
                    source_type="tenant_crm_snapshot",
                    source_id=company_id,
                    source_name="SalesOS CRM",
                ),
                description=signal["detail"],
                confidence=0.55,
                confidence_level=_confidence_level(0.55),
                evidence_kind=EvidenceKind.CRM_SYSTEM_RECORD,
                data={"signal_code": signal["code"], "rule_version": RULE_VERSION},
            )
        )

    insight = Insight(
        id=insight_id,
        tenant_id=tenant_id,
        category=InsightCategory.ACCOUNT_HEALTH,
        title=f"Account signals: {account_signals['status'].replace('_', ' ')}",
        description=f"Deterministic CRM signals for {company_name}.",
        target_id=company_id,
        target_type="company",
        overall_confidence=0.0,
        confidence_level=ConfidenceLevel.UNKNOWN,
        evidence_items=evidence_items,
        metadata={
            "rule_version": RULE_VERSION,
            "account_signal_status": account_signals["status"],
            "recommendations": account_signals["recommendations"],
            "source_snapshot": source_snapshot,
            "idempotency_key": idempotency_key,
        },
    )
    insight.recompute_confidence()

    inserted = await db.execute(
        text("""
            INSERT INTO commercial_insights (
                id, tenant_id, category, title, description, target_id, target_type,
                overall_confidence, confidence_level, metadata, idempotency_key,
                created_at, updated_at
            ) VALUES (
                :id, :tenant_id, :category, :title, :description, :target_id, :target_type,
                :confidence, :confidence_level, CAST(:metadata AS JSON), :idempotency_key,
                now(), now()
            )
            ON CONFLICT (tenant_id, idempotency_key) DO NOTHING
            RETURNING id
        """),
        {
            "id": insight.id,
            "tenant_id": tenant_id,
            "category": insight.category.value,
            "title": insight.title,
            "description": insight.description,
            "target_id": insight.target_id,
            "target_type": insight.target_type,
            "confidence": insight.overall_confidence,
            "confidence_level": insight.confidence_level.value,
            "metadata": json.dumps(insight.metadata, ensure_ascii=False),
            "idempotency_key": idempotency_key,
        },
    )
    stored_id = inserted.scalar_one_or_none()
    created = stored_id is not None
    if not created:
        existing = await db.execute(
            text("""
                SELECT id FROM commercial_insights
                WHERE tenant_id = :tenant_id AND idempotency_key = :idempotency_key
            """),
            {"tenant_id": tenant_id, "idempotency_key": idempotency_key},
        )
        stored_id = existing.scalar_one()

    for evidence in evidence_items:
        await db.execute(
            text("""
                INSERT INTO commercial_evidence_items (
                    id, insight_id, tenant_id, evidence_type, source_domain, source_type,
                    source_id, source_name, description, confidence, confidence_level,
                    data, created_at, updated_at
                ) VALUES (
                    :id, :insight_id, :tenant_id, :evidence_type, :source_domain, :source_type,
                    :source_id, :source_name, :description, :confidence, :confidence_level,
                    CAST(:data AS JSON), now(), now()
                )
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": evidence.id,
                "insight_id": str(stored_id),
                "tenant_id": tenant_id,
                "evidence_type": evidence.evidence_type.value,
                "source_domain": evidence.source.source_domain,
                "source_type": evidence.source.source_type,
                "source_id": evidence.source.source_id,
                "source_name": evidence.source.source_name,
                "description": evidence.description,
                "confidence": evidence.confidence,
                "confidence_level": evidence.confidence_level.value,
                "data": json.dumps(
                    {**evidence.data, "evidence_kind": evidence.evidence_kind.value},
                    ensure_ascii=False,
                ),
            },
        )

    return {
        "insight_id": str(stored_id),
        "created": created,
        "evidence_count": len(evidence_items),
        "overall_confidence": insight.overall_confidence,
        "confidence_level": insight.confidence_level.value,
        "idempotency_key": idempotency_key,
    }
