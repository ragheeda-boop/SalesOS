from __future__ import annotations

import pytest

from app.modules.signal_marketplace.models import Signal
from app.modules.signal_marketplace.repository import (
    InMemorySignalEventRepository,
    InMemorySignalRepository,
    InMemorySignalSubscriptionRepository,
)
from app.modules.signal_marketplace.service import SignalMarketplaceService


@pytest.fixture
def signal_repo():
    return InMemorySignalRepository()


@pytest.fixture
def sub_repo():
    return InMemorySignalSubscriptionRepository()


@pytest.fixture
def event_repo():
    return InMemorySignalEventRepository()


@pytest.fixture
def service(signal_repo, sub_repo, event_repo):
    return SignalMarketplaceService(
        signal_repo=signal_repo,
        sub_repo=sub_repo,
        event_repo=event_repo,
    )


@pytest.fixture
def sample_signal():
    return Signal(
        id="SIG-HC-001",
        name="Ministry of Health License Issuance",
        ar_name="إصدار ترخيص وزارة الصحة",
        description="New MOH license for a healthcare facility",
        domain="healthcare",
        category="license",
        severity="critical",
        source="MOH",
        pack_id="kp-healthcare",
        triggers=["new_facility", "market_entry"],
    )


@pytest.fixture
def another_signal():
    return Signal(
        id="SIG-FS-001",
        name="SAMA License Issuance",
        ar_name="إصدار ترخيص SAMA",
        description="New SAMA license for financial institution",
        domain="financial-services",
        category="license",
        severity="critical",
        source="SAMA",
        pack_id="kp-financial-services",
        triggers=["market_entry", "product_launch"],
    )


# ── Signal Library Tests ──


class TestSignalLibrary:
    @pytest.mark.asyncio
    async def test_list_signals_empty(self, service):
        signals = await service.list_signals()
        assert signals == []

    @pytest.mark.asyncio
    async def test_register_signal(self, service, sample_signal):
        await service.register_signal(sample_signal)
        signals = await service.list_signals()
        assert len(signals) == 1
        assert signals[0].id == "SIG-HC-001"

    @pytest.mark.asyncio
    async def test_register_signals_from_pack(self, service, sample_signal, another_signal):
        await service.register_signals_from_pack([sample_signal, another_signal])
        signals = await service.list_signals()
        assert len(signals) == 2

    @pytest.mark.asyncio
    async def test_list_signals_filter_by_domain(self, service, sample_signal, another_signal):
        await service.register_signals_from_pack([sample_signal, another_signal])
        signals = await service.list_signals(domain="healthcare")
        assert len(signals) == 1
        assert signals[0].id == "SIG-HC-001"

    @pytest.mark.asyncio
    async def test_list_signals_filter_by_pack(self, service, sample_signal, another_signal):
        await service.register_signals_from_pack([sample_signal, another_signal])
        signals = await service.list_signals(pack_id="kp-financial-services")
        assert len(signals) == 1
        assert signals[0].id == "SIG-FS-001"

    @pytest.mark.asyncio
    async def test_get_signal_by_id(self, service, sample_signal):
        await service.register_signal(sample_signal)
        signal = await service.get_signal("SIG-HC-001")
        assert signal is not None
        assert signal.name == "Ministry of Health License Issuance"

    @pytest.mark.asyncio
    async def test_get_signal_not_found(self, service):
        signal = await service.get_signal("NONEXISTENT")
        assert signal is None

    @pytest.mark.asyncio
    async def test_register_duplicate_signal(self, service, sample_signal):
        await service.register_signal(sample_signal)
        await service.register_signal(sample_signal)
        signals = await service.list_signals()
        assert len(signals) == 1


# ── Subscription Tests ──


class TestSubscription:
    @pytest.mark.asyncio
    async def test_subscribe_to_signal(self, service, sample_signal):
        await service.register_signal(sample_signal)
        sub = await service.subscribe(
            signal_id="SIG-HC-001",
            company_id="company-1",
            tenant_id="tenant-1",
            channel="in-app",
        )
        assert sub.signal_id == "SIG-HC-001"
        assert sub.company_id == "company-1"
        assert sub.tenant_id == "tenant-1"
        assert sub.active is True
        assert sub.channel == "in-app"

    @pytest.mark.asyncio
    async def test_subscribe_nonexistent_signal(self, service):
        with pytest.raises(ValueError, match="not found"):
            await service.subscribe(
                signal_id="NONEXISTENT",
                company_id="company-1",
                tenant_id="tenant-1",
            )

    @pytest.mark.asyncio
    async def test_subscribe_returns_existing(self, service, sample_signal):
        await service.register_signal(sample_signal)
        sub1 = await service.subscribe("SIG-HC-001", "company-1", "tenant-1")
        sub2 = await service.subscribe("SIG-HC-001", "company-1", "tenant-1")
        assert sub1.id == sub2.id

    @pytest.mark.asyncio
    async def test_list_subscriptions(self, service, sample_signal, another_signal):
        await service.register_signals_from_pack([sample_signal, another_signal])
        await service.subscribe("SIG-HC-001", "company-1", "tenant-1")
        await service.subscribe("SIG-FS-001", "company-2", "tenant-1")
        subs = await service.list_subscriptions("tenant-1")
        assert len(subs) == 2

    @pytest.mark.asyncio
    async def test_list_subscriptions_empty(self, service):
        subs = await service.list_subscriptions("tenant-1")
        assert subs == []

    @pytest.mark.asyncio
    async def test_subscription_tenant_isolation(self, service, sample_signal):
        await service.register_signal(sample_signal)
        await service.subscribe("SIG-HC-001", "company-1", "tenant-1")
        subs = await service.list_subscriptions("tenant-2")
        assert subs == []

    @pytest.mark.asyncio
    async def test_unsubscribe(self, service, sample_signal):
        await service.register_signal(sample_signal)
        sub = await service.subscribe("SIG-HC-001", "company-1", "tenant-1")
        ok = await service.unsubscribe(sub.id, "tenant-1")
        assert ok is True
        subs = await service.list_subscriptions("tenant-1")
        assert subs == []

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, service):
        ok = await service.unsubscribe("nonexistent", "tenant-1")
        assert ok is False

    @pytest.mark.asyncio
    async def test_unsubscribe_wrong_tenant(self, service, sample_signal):
        await service.register_signal(sample_signal)
        sub = await service.subscribe("SIG-HC-001", "company-1", "tenant-1")
        ok = await service.unsubscribe(sub.id, "tenant-2")
        assert ok is False


# ── Signal Detection & Feed Tests ──


class TestSignalDetection:
    @pytest.mark.asyncio
    async def test_create_signal_event(self, service, sample_signal):
        await service.register_signal(sample_signal)
        event = await service.create_signal_event(
            signal_id="SIG-HC-001",
            company_id="company-1",
            tenant_id="tenant-1",
            data={"license_number": "MOH-12345"},
        )
        assert event is not None
        assert event.signal_id == "SIG-HC-001"
        assert event.company_id == "company-1"
        assert event.data["license_number"] == "MOH-12345"
        assert event.acknowledged is False

    @pytest.mark.asyncio
    async def test_create_signal_event_nonexistent_signal(self, service):
        event = await service.create_signal_event(
            signal_id="NONEXISTENT",
            company_id="company-1",
            tenant_id="tenant-1",
        )
        assert event is None

    @pytest.mark.asyncio
    async def test_get_feed(self, service, sample_signal):
        await service.register_signal(sample_signal)
        await service.create_signal_event("SIG-HC-001", "company-1", "tenant-1", {"k": "v1"})
        await service.create_signal_event("SIG-HC-001", "company-2", "tenant-1", {"k": "v2"})
        feed = await service.get_feed("tenant-1")
        assert len(feed) == 2

    @pytest.mark.asyncio
    async def test_feed_tenant_isolation(self, service, sample_signal):
        await service.register_signal(sample_signal)
        await service.create_signal_event("SIG-HC-001", "company-1", "tenant-1")
        await service.create_signal_event("SIG-HC-001", "company-1", "tenant-2")
        feed = await service.get_feed("tenant-1")
        assert len(feed) == 1

    @pytest.mark.asyncio
    async def test_get_company_feed(self, service, sample_signal):
        await service.register_signal(sample_signal)
        await service.create_signal_event("SIG-HC-001", "company-1", "tenant-1")
        await service.create_signal_event("SIG-HC-001", "company-2", "tenant-1")
        feed = await service.get_company_feed("company-1", "tenant-1")
        assert len(feed) == 1

    @pytest.mark.asyncio
    async def test_acknowledge_event(self, service, sample_signal):
        await service.register_signal(sample_signal)
        event = await service.create_signal_event("SIG-HC-001", "company-1", "tenant-1")
        assert event is not None
        assert event.acknowledged is False

        acked = await service.acknowledge(event.id, "tenant-1")
        assert acked is not None
        assert acked.acknowledged is True
        assert acked.acknowledged_at is not None

    @pytest.mark.asyncio
    async def test_acknowledge_nonexistent(self, service):
        acked = await service.acknowledge("nonexistent", "tenant-1")
        assert acked is None

    @pytest.mark.asyncio
    async def test_count_unacknowledged(self, service, sample_signal):
        await service.register_signal(sample_signal)
        await service.create_signal_event("SIG-HC-001", "company-1", "tenant-1")
        await service.create_signal_event("SIG-HC-001", "company-2", "tenant-1")
        count = await service.count_unacknowledged("tenant-1")
        assert count == 2

    @pytest.mark.asyncio
    async def test_feed_filter_acknowledged(self, service, sample_signal):
        await service.register_signal(sample_signal)
        e1 = await service.create_signal_event("SIG-HC-001", "company-1", "tenant-1")
        await service.create_signal_event("SIG-HC-001", "company-2", "tenant-1")
        assert e1 is not None
        await service.acknowledge(e1.id, "tenant-1")

        unacked = await service.get_feed("tenant-1", acknowledged=False)
        assert len(unacked) == 1

        acked = await service.get_feed("tenant-1", acknowledged=True)
        assert len(acked) == 1

    @pytest.mark.asyncio
    async def test_feed_limit(self, service, sample_signal):
        await service.register_signal(sample_signal)
        for i in range(10):
            await service.create_signal_event("SIG-HC-001", f"company-{i}", "tenant-1")
        feed = await service.get_feed("tenant-1", limit=3)
        assert len(feed) == 3


# ── SignalDetectionEngine Tests ──


class TestSignalDetectionEngine:
    @pytest.mark.asyncio
    async def test_load_pack_with_no_packs_dir(self, monkeypatch, tmp_path):
        # Use an isolated empty dir — gettempdir() can be a shared host path
        # (e.g. /tmp/snap-private-tmp) that is not readable for pack iteration.
        monkeypatch.setenv("KNOWLEDGE_PACKS_PATH", str(tmp_path))
        from app.modules.signal_marketplace.engine import SignalDetectionEngine

        engine = SignalDetectionEngine(SignalMarketplaceService())
        signals = await engine.load_all_packs()
        # Temp dir is empty → no packs found
        assert signals == []

    @pytest.mark.asyncio
    async def test_engine_on_domain_event_matches_trigger(self, service, sample_signal):
        await service.register_signal(sample_signal)
        from app.modules.signal_marketplace.engine import SignalDetectionEngine

        engine = SignalDetectionEngine(service)
        engine._signal_map = {"SIG-HC-001": sample_signal}
        await engine.on_domain_event(
            event_type="new_facility",
            aggregate_id="company-1",
            tenant_id="tenant-1",
            data={"facility": "hospital"},
        )
        feed = await service.get_feed("tenant-1")
        assert len(feed) == 1
        assert feed[0].signal_id == "SIG-HC-001"

    @pytest.mark.asyncio
    async def test_engine_no_match(self, service, sample_signal):
        await service.register_signal(sample_signal)
        from app.modules.signal_marketplace.engine import SignalDetectionEngine

        engine = SignalDetectionEngine(service)
        engine._signal_map = {"SIG-HC-001": sample_signal}
        await engine.on_domain_event(
            event_type="irrelevant_event",
            aggregate_id="company-1",
            tenant_id="tenant-1",
        )
        feed = await service.get_feed("tenant-1")
        assert len(feed) == 0

    @pytest.mark.asyncio
    async def test_map_priority_to_severity(self):
        from app.modules.signal_marketplace.engine import SignalDetectionEngine

        assert SignalDetectionEngine._map_priority("high") == "critical"
        assert SignalDetectionEngine._map_priority("medium") == "warning"
        assert SignalDetectionEngine._map_priority("low") == "info"
        assert SignalDetectionEngine._map_priority("unknown") == "info"
