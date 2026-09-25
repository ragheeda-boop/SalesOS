from __future__ import annotations

import asyncio
import ipaddress
import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.modules.agent_reach import service as service_module
from app.modules.agent_reach.router import (
    clear_intel,
    execute_generic,
    get_evidence,
    get_intel_summary,
    get_signals,
    get_status,
    linkedin_company,
    linkedin_jobs,
    linkedin_profile,
    list_intel_companies,
    prune_expired,
    read_github_repo,
    read_rss_feed,
    read_tweet,
    read_web_page,
    ResearchRequest,
    research_company,
    router as agent_reach_router,
    search_bilibili,
    search_github,
    search_twitter,
    search_web,
    search_youtube,
    get_youtube_subtitles,
)
from app.modules.agent_reach.service import AgentReachService
from app.modules.agent_reach.models import AgentReachResult, ChannelType, EvidenceItem
from app.modules.agent_reach.persistence import (
    EvidenceWriteResult,
    PostgresEvidenceStore,
)
from sdk.permissions import PermissionAction


class _AllowAllRateLimiter:
    def check(self, _key: str) -> bool:
        return True


class _FakeStream:
    def __init__(self, payload: bytes):
        self._payload = payload

    async def read(self, size: int) -> bytes:
        payload, self._payload = self._payload[:size], self._payload[size:]
        return payload


@pytest.mark.asyncio
async def test_runner_passes_untrusted_text_as_one_exec_argument(monkeypatch):
    argv_seen: tuple[str, ...] | None = None

    async def fake_exec(*argv, stdout, stderr):
        nonlocal argv_seen
        argv_seen = argv
        return SimpleNamespace(
            returncode=0,
            stdout=_FakeStream(b"ok"),
            stderr=_FakeStream(b""),
            wait=AsyncMock(return_value=0),
        )

    def fail_shell(*_args, **_kwargs):
        raise AssertionError("Agent Reach must never invoke a shell")

    monkeypatch.setattr(service_module, "_PROCESS_RATE_LIMITER", _AllowAllRateLimiter())
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", fail_shell)

    payload = "company; touch /tmp/agent-reach-shell-injection"
    result = await AgentReachService()._run_command(
        ["python", "-c", payload], channel="test"
    )

    assert result == (True, "ok", "")
    assert argv_seen == ("python", "-c", payload)


@pytest.mark.asyncio
async def test_runner_kills_process_when_output_exceeds_memory_limit(monkeypatch):
    class FakeProcess:
        def __init__(self):
            self.returncode = None
            self.stdout = _FakeStream(b"x" * (service_module.MAX_OUTPUT_BYTES + 1))
            self.stderr = _FakeStream(b"")
            self.killed = False

        def kill(self):
            self.killed = True
            self.returncode = -9

        async def wait(self):
            self.returncode = self.returncode or -9
            return self.returncode

    process = FakeProcess()
    monkeypatch.setattr(service_module, "_PROCESS_RATE_LIMITER", _AllowAllRateLimiter())

    async def fake_exec(*_argv, **_kwargs):
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    success, stdout, error = await AgentReachService()._run_command(
        ["python", "-c", "produce-output"], channel="output-test"
    )

    assert success is False
    assert len(stdout.encode("utf-8")) <= service_module.MAX_OUTPUT_BYTES
    assert "output exceeded" in error
    assert process.killed is True


@pytest.mark.asyncio
async def test_runner_kills_and_reaps_process_on_timeout(monkeypatch):
    class BlockingStream:
        async def read(self, _size):
            await asyncio.Event().wait()

    class FakeProcess:
        def __init__(self):
            self.returncode = None
            self.stdout = BlockingStream()
            self.stderr = BlockingStream()
            self.killed = False
            self.reaped = False

        def kill(self):
            self.killed = True
            self.returncode = -9

        async def wait(self):
            self.reaped = True
            return self.returncode

    process = FakeProcess()
    monkeypatch.setattr(service_module, "_PROCESS_RATE_LIMITER", _AllowAllRateLimiter())

    async def fake_exec(*_argv, **_kwargs):
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    success, _stdout, error = await AgentReachService(timeout_seconds=1)._run_command(
        ["python", "-c", "wait-forever"], timeout=0.01, channel="timeout-test"
    )

    assert success is False
    assert "timed out" in error
    assert process.killed is True
    assert process.reaped is True


@pytest.mark.asyncio
async def test_runner_rejects_unapproved_executables_before_execution(monkeypatch):
    monkeypatch.setattr(service_module, "_PROCESS_RATE_LIMITER", _AllowAllRateLimiter())
    called = False

    async def fake_exec(*_argv, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("unapproved executable must not run")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    result = await AgentReachService()._run_command(
        ["/bin/sh", "-c", "echo unsafe"], channel="test"
    )

    assert result[0] is False
    assert "execution policy" in result[2]
    assert called is False


def _permission_action(endpoint) -> PermissionAction:
    dependency = inspect.signature(endpoint).parameters["_rbac"].default.dependency
    return inspect.getclosurevars(dependency).nonlocals["action"]


def test_research_and_generic_execution_require_create_permission():
    assert _permission_action(research_company) is PermissionAction.CREATE
    assert _permission_action(execute_generic) is PermissionAction.CREATE


def test_all_external_provider_posts_require_create_permission():
    endpoints = (
        read_web_page,
        search_twitter,
        read_tweet,
        search_youtube,
        get_youtube_subtitles,
        search_github,
        read_github_repo,
        read_rss_feed,
        search_bilibili,
        search_web,
        linkedin_company,
        linkedin_profile,
        linkedin_jobs,
        research_company,
        execute_generic,
    )
    assert all(_permission_action(endpoint) is PermissionAction.CREATE for endpoint in endpoints)


def test_status_check_remains_read_only():
    assert _permission_action(get_status) is PermissionAction.READ


def test_router_has_configured_per_user_rate_limit():
    dependency = agent_reach_router.dependencies[0].dependency
    policy = inspect.getclosurevars(dependency).nonlocals

    assert policy["resource"] == "agent_reach"
    assert policy["limit"] > 0
    assert policy["window"] == 60


def test_intelligence_reads_and_deletes_use_matching_permissions():
    assert _permission_action(get_evidence) is PermissionAction.READ
    assert _permission_action(get_signals) is PermissionAction.READ
    assert _permission_action(get_intel_summary) is PermissionAction.READ
    assert _permission_action(list_intel_companies) is PermissionAction.READ
    assert _permission_action(clear_intel) is PermissionAction.DELETE
    assert _permission_action(prune_expired) is PermissionAction.DELETE


@pytest.mark.asyncio
async def test_rss_rejects_private_dns_answers(monkeypatch):
    service = AgentReachService()

    async def resolve_private(_hostname, _port):
        return {ipaddress.ip_address("127.0.0.1")}

    monkeypatch.setattr(service, "_resolve_public_addresses", resolve_private)

    with pytest.raises(ValueError, match="non-public address"):
        await service.read_rss_feed("https://feed.example/rss")


@pytest.mark.asyncio
async def test_rss_pins_public_address_and_parses_without_following_redirects(monkeypatch):
    service = AgentReachService()
    argv_seen: list[str] | None = None
    feed_xml = (
        "<?xml version='1.0'?><rss version='2.0'><channel>"
        "<title>Example</title><item><title>Launch</title>"
        "<link>https://example.com/launch</link><description>New product</description>"
        "</item></channel></rss>"
    )

    async def resolve_public(_hostname, _port):
        return {ipaddress.ip_address("93.184.216.34")}

    async def fake_run(command, *, timeout, channel):
        nonlocal argv_seen
        argv_seen = list(command)
        assert timeout > 0
        assert channel == "rss"
        return True, feed_xml, ""

    monkeypatch.setattr(service, "_resolve_public_addresses", resolve_public)
    monkeypatch.setattr(service, "_run_command", fake_run)

    result = await service.read_rss_feed("https://feed.example/rss", max_entries=1)

    assert result.success is True
    assert result.data == [
        {
            "title": "Launch",
            "link": "https://example.com/launch",
            "summary": "New product",
        }
    ]
    assert argv_seen is not None
    assert "--resolve" in argv_seen
    assert "feed.example:443:93.184.216.34" in argv_seen
    assert argv_seen[argv_seen.index("--noproxy") + 1] == "*"
    assert "--disable" in argv_seen
    assert "-L" not in argv_seen


@pytest.mark.asyncio
async def test_research_persists_evidence_and_signals_with_tenant_evidence_ids(monkeypatch):
    persisted_item = None
    persisted_signal = None

    async def fake_research(_self, _company_name, _channels):
        return {
            "web": AgentReachResult(
                success=True,
                channel=ChannelType.WEB,
                action="read",
                data={
                    "title": "Hiring across engineering",
                    "description": "New vacancy announcement",
                    "url": "https://example.com/jobs",
                },
            ),
            "github": AgentReachResult(
                success=False,
                channel=ChannelType.GITHUB,
                action="search",
                error="provider unavailable",
            ),
        }

    async def save_evidence(tenant_id, item):
        nonlocal persisted_item
        assert tenant_id == "tenant-42"
        persisted_item = item
        return EvidenceWriteResult("canonical-evidence-id", True)

    async def add_signal(tenant_id, signal):
        nonlocal persisted_signal
        assert tenant_id == "tenant-42"
        persisted_signal = signal
        return True

    monkeypatch.setattr(AgentReachService, "research_company", fake_research)
    monkeypatch.setattr(
        "app.modules.agent_reach.router._pg_store",
        SimpleNamespace(save_evidence=save_evidence, add_signal=add_signal),
    )

    response = await research_company(
        ResearchRequest(company_name="Example Co", channels=["web", "github"]),
        tenant_id="tenant-42",
        _rbac=None,
    )

    assert response["evidence_stored"] == 1
    assert response["signals_stored"] == 1
    assert persisted_item is not None
    assert persisted_item.id == "canonical-evidence-id"
    assert persisted_signal is not None
    assert persisted_signal.evidence_ids == ["canonical-evidence-id"]
    assert response["channels"]["github"]["success"] is False


@pytest.mark.asyncio
async def test_research_service_does_not_write_tenant_results_to_global_memory(monkeypatch):
    async def fake_read(_self, _url):
        from app.modules.agent_reach.models import AgentReachResult, ChannelType

        return AgentReachResult(
            success=True,
            channel=ChannelType.WEB,
            action="read",
            data={
                "title": "Hiring now",
                "description": "New vacancy",
                "url": "https://example.com/jobs",
            },
        )

    monkeypatch.setattr(AgentReachService, "read_web_page", fake_read)
    service_module.evidence_store.clear()

    results = await AgentReachService().research_company("Example Co", ["web"])

    assert results["web"].success is True
    assert service_module.evidence_store.list_companies() == []


@pytest.mark.asyncio
async def test_evidence_dedup_returns_the_existing_database_identifier():
    calls = []

    class FakeResult:
        def __init__(self, row=None):
            self.row = row

        def one_or_none(self):
            return self.row

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def execute(self, statement, params=None):
            sql = str(statement)
            calls.append((sql, params))
            if "INSERT INTO agent_evidence" in sql:
                return FakeResult()
            if "SELECT id, FALSE AS inserted" in sql:
                return FakeResult(SimpleNamespace(id="db-evidence-id", inserted=False))
            return FakeResult()

        async def commit(self):
            return None

        async def rollback(self):
            raise AssertionError("deduplicated evidence lookup should succeed")

    item = EvidenceItem(
        company_name="Example Co",
        source_url="https://example.com/jobs",
        title="Hiring",
    )
    result = await PostgresEvidenceStore(lambda: FakeSession()).save_evidence(
        "tenant-42", item
    )

    assert result == EvidenceWriteResult("db-evidence-id", False)
    insert_sql, insert_params = calls[1]
    assert "ON CONFLICT (tenant_id, company_name, source_url, evidence_type)" in insert_sql
    assert insert_params["evidence_id"] == item.id
    assert calls[2][1]["tenant_id"] == "tenant-42"


@pytest.mark.parametrize(
    ("method_name", "url"),
    [
        ("read_tweet", "https://attacker.example/track/123"),
        ("read_tweet", "https://twitter.com.attacker.example/track/123"),
        ("get_youtube_subtitles", "https://attacker.example/video"),
        ("get_youtube_subtitles", "http://youtube.com/watch?v=123"),
    ],
)
@pytest.mark.asyncio
async def test_direct_social_fetches_reject_unapproved_domains(method_name, url):
    service = AgentReachService()
    method = getattr(service, method_name)

    with pytest.raises(ValueError, match="not allowed"):
        await method(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.1/",
        "http://2130706433/",
        "http://0x7f000001/",
        "http://0177.0.0.1/",
        "https://[::1]/",
        "https://[::ffff:127.0.0.1]/",
        "https://user:pass@example.com/",
        "https://example.com:8443/",
        "https://localhost./",
        "http://router.local/",
        "http://service.internal./",
        "https://example.com/path with spaces",
    ],
)
def test_url_validator_rejects_local_and_ambiguous_destinations(url):
    with pytest.raises(ValueError, match="SSRF protection"):
        AgentReachService()._validate_url(url)


def test_url_validator_accepts_normal_public_https_urls():
    url = "https://news.example.com/articles?id=12&topic=saas"

    assert AgentReachService()._validate_url(url) == url


@pytest.mark.parametrize(
    "channels",
    [
        [],
        ["web", "web"],
        ["web", "google_maps"],
        ["web", "github", "linkedin", "twitter", "youtube", "rss"],
    ],
)
def test_research_request_rejects_empty_duplicate_or_unknown_channels(channels):
    with pytest.raises(ValidationError):
        ResearchRequest(company_name="Example Co", channels=channels)
