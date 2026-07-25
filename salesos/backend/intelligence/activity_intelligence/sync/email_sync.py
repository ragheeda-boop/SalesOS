"""Email Sync Worker — provider-agnostic email synchronization (ADR-012 §12).

Operates against EmailProvider interface. Handles:
- Incremental fetch (since last_sync)
- Deduplication by message_id
- Mapping via MappingPipeline
- Activity recording via ActivityRuntime
"""

from __future__ import annotations

from datetime import datetime, timezone

from intelligence.activity_intelligence.contracts.events import (
    CommunicationReceived,
    CommunicationSynced,
)
from intelligence.activity_intelligence.contracts.models import RawEmail
from intelligence.activity_intelligence.contracts.provider import EmailProvider
from intelligence.activity_intelligence.mapping import MappingPipeline
from intelligence.activity_intelligence.sync.dedup import Deduplicator


class EmailSyncWorker:
    """Synchronizes emails from a provider to the platform."""

    def __init__(
        self,
        provider: EmailProvider,
        mapping: MappingPipeline,
        event_bus=None,
        activity_runtime=None,
    ):
        self.provider = provider
        self.mapping = mapping
        self.event_bus = event_bus
        self.activity_runtime = activity_runtime
        self.deduplicator = Deduplicator()
        self.last_sync: datetime | None = None

    async def sync(
        self,
        tenant_id: str,
        max_results: int = 50,
        known_message_ids: set[str] | None = None,
    ) -> dict:
        """Run a sync cycle. Returns summary dict."""
        known_ids = known_message_ids or set()

        emails = await self.provider.fetch_emails(
            since=self.last_sync, max_results=max_results
        )

        new_count = 0
        skipped_count = 0
        errors: list[str] = []

        for raw in emails:
            if self.deduplicator.is_duplicate(raw.message_id, known_ids):
                skipped_count += 1
                continue

            try:
                # Stage 1: Emit received event
                if self.event_bus:
                    event = CommunicationReceived(
                        tenant_id=tenant_id,
                        channel="email",
                        source_provider="gmail",
                        source_id=raw.message_id,
                        raw_data=self._raw_to_dict(raw),
                        aggregate_type="communication",
                        aggregate_id=raw.message_id,
                    )
                    await self.event_bus.publish(event)

                # Stage 2: Resolve company via Mapping Pipeline
                result = await self.mapping.resolve_email(
                    tenant_id=tenant_id, raw=raw, email_id=raw.message_id
                )

                # Stage 3: Record in Activity Runtime
                if self.activity_runtime and result.mapped:
                    await self.activity_runtime.ingest(
                        actor="system",
                        action="email.received" if raw.sent_at else "email.synced",
                        entity_type="communication",
                        entity_id=raw.message_id,
                        target_type=result.entity_type,
                        target_id=result.entity_id,
                        metadata={
                            "source_provider": "gmail",
                            "company_id": result.company_id,
                            "confidence": result.confidence,
                        },
                        tenant_id=tenant_id,
                    )

                new_count += 1
                known_ids.add(raw.message_id)

            except Exception as e:
                errors.append(f"Email {raw.message_id}: {e}")

        self.last_sync = datetime.now(timezone.utc)

        if self.event_bus:
            synced_event = CommunicationSynced(
                tenant_id=tenant_id,
                provider="gmail",
                channel="email",
                synced_count=len(emails),
                new_count=new_count,
                updated_count=0,
                errors=errors,
                aggregate_type="communication",
                aggregate_id=f"sync-email-{tenant_id}",
            )
            await self.event_bus.publish(synced_event)

        return {
            "synced_count": len(emails),
            "new_count": new_count,
            "skipped_count": skipped_count,
            "errors": errors,
        }

    @staticmethod
    def _raw_to_dict(raw: RawEmail) -> dict:
        return {
            "message_id": raw.message_id,
            "thread_id": raw.thread_id,
            "subject": raw.subject,
            "from": raw.from_address,
            "to": raw.to_addresses,
            "sent_at": raw.sent_at.isoformat() if raw.sent_at else None,
        }
