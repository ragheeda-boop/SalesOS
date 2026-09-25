"""Agent Reach service — hardened async wrappers.

Security model:
- Structural/local-destination validation on supplied URLs; RSS additionally
  resolves and pins the direct fetch to a public address
- Allowlisted operations only (no shell passthrough)
- Rate limiting per channel
- Timeout + output size limits
- Audit trail logging
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import re
import socket
import time
from dataclasses import dataclass, field
from typing import Sequence
from urllib.parse import urlparse

from .models import (
    AgentReachRequest,
    AgentReachResult,
    ChannelInfo,
    ChannelStatus,
    ChannelType,
    CompanyIntelSummary,
    EvidenceItem,
    Signal,
    SignalConfidence,
    SignalType,
)

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("agent_reach.audit")

# ── SSRF Protection ──────────────────────────────────────────────

_BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "169.254.169.254",  # AWS metadata
    "metadata.google.internal",  # GCP metadata
    "100.100.100.200",  # Alibaba metadata
}

_BLOCKED_SCHEMES = {"file", "ftp", "gopher", "dict", "javascript", "data"}

def _is_safe_url(url: str) -> bool:
    """Reject malformed URLs, local destinations, and ambiguous IP spellings."""
    if (
        not isinstance(url, str)
        or not url
        or len(url) > MAX_URL_LENGTH
        or "\\" in url
        or any(ord(character) < 33 or character.isspace() for character in url)
    ):
        return False

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return False

    try:
        port = parsed.port
    except ValueError:
        return False
    if port not in (None, 80 if scheme == "http" else 443):
        return False

    if parsed.username is not None or parsed.password is not None:
        return False

    hostname = (parsed.hostname or "").rstrip(".").lower()
    if not hostname or hostname in _BLOCKED_HOSTS:
        return False
    if hostname.endswith((".internal", ".localhost", ".local", ".home.arpa")):
        return False

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        # curl and other URL clients accept legacy decimal, octal, or hexadecimal
        # IPv4 forms even though ipaddress only recognizes canonical forms.
        if re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|[0-9]+)(?:\.(?:0[xX][0-9a-fA-F]+|[0-9]+))*", hostname):
            return False
        try:
            ascii_hostname = hostname.encode("idna").decode("ascii")
        except UnicodeError:
            return False
        if len(ascii_hostname) > 253 or "." not in ascii_hostname:
            return False
        labels = ascii_hostname.rstrip(".").split(".")
        if any(
            not label
            or len(label) > 63
            or label.startswith("-")
            or label.endswith("-")
            or not re.fullmatch(r"[a-z0-9-]+", label)
            for label in labels
        ):
            return False
        return True

    return address.is_global


# ── Rate Limiter ─────────────────────────────────────────────────


@dataclass
class _RateBucket:
    count: int = 0
    window_start: float = field(default_factory=time.time)


class RateLimiter:
    """Simple per-channel rate limiter."""

    def __init__(self, max_per_minute: int = 30):
        self._max = max_per_minute
        self._buckets: dict[str, _RateBucket] = {}

    def check(self, key: str) -> bool:
        """Return True if request is allowed."""
        now = time.time()
        bucket = self._buckets.get(key)
        if bucket is None or now - bucket.window_start > 60:
            self._buckets[key] = _RateBucket(count=1, window_start=now)
            return True
        if bucket.count >= self._max:
            return False
        bucket.count += 1
        return True


# Shared by all service instances in this worker. Routers construct a service
# per request, so an instance-owned limiter would reset on every call.
_PROCESS_RATE_LIMITER = RateLimiter(max_per_minute=30)


# ── Allowlisted Operations ───────────────────────────────────────

ALLOWED_OPERATIONS: dict[str, dict[str, list[str]]] = {
    "web": {"read": ["url"]},
    "twitter": {"search": ["query"], "read": ["url"]},
    "youtube": {"search": ["query"], "subtitles": ["url"], "info": ["url"]},
    "github": {"search": ["query"], "read": ["query"]},
    "rss": {"read": ["url"]},
    "bilibili": {"search": ["query"], "read": ["url"]},
    "web_search": {"search": ["query"]},
    "linkedin": {"company": ["query"], "profile": ["query"], "jobs": ["query"]},
}


# ── Output Limits ────────────────────────────────────────────────

MAX_OUTPUT_BYTES = 1 * 1024 * 1024  # 1 MB
DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120
MAX_QUERY_LENGTH = 500
MAX_URL_LENGTH = 2048
ALLOWED_EXECUTABLES = {
    "agent-reach",
    "bili-cli",
    "curl",
    "gh",
    "mcporter",
    "python",
    "twitter",
    "yt-dlp",
}


# ── Service ──────────────────────────────────────────────────────


class AgentReachService:
    """Hardened service for calling Agent Reach channels from SalesOS."""

    def __init__(self, timeout_seconds: int = DEFAULT_TIMEOUT):
        self._timeout = min(timeout_seconds, MAX_TIMEOUT)
        self._rate_limiter = _PROCESS_RATE_LIMITER

    async def _run_command(
        self,
        command: Sequence[str],
        timeout: int | None = None,
        channel: str = "unknown",
    ) -> tuple[bool, str, str]:
        """Run an allowlisted executable without invoking a shell."""
        timeout = min(timeout or self._timeout, MAX_TIMEOUT)

        argv = [str(arg) for arg in command]
        if (
            not argv
            or argv[0] not in ALLOWED_EXECUTABLES
            or any("\x00" in arg for arg in argv)
            or sum(len(arg) for arg in argv) > 16_384
        ):
            audit_logger.warning("command_rejected channel=%s", channel)
            return False, "", "Command rejected by execution policy"

        # Rate limit check
        if not self._rate_limiter.check(channel):
            audit_logger.warning("rate_limited channel=%s", channel)
            return False, "", "Rate limit exceeded (30/min per channel)"

        proc = None

        async def terminate_child() -> None:
            if proc is None:
                return
            if proc.returncode is None:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
            try:
                await asyncio.wait_for(proc.wait(), timeout=1)
            except (asyncio.TimeoutError, ProcessLookupError):
                pass

        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async def read_limited(stream) -> tuple[bytes, bool]:
                output = bytearray()
                while True:
                    read_size = min(64 * 1024, MAX_OUTPUT_BYTES + 1 - len(output))
                    chunk = await stream.read(read_size)
                    if not chunk:
                        return bytes(output), False
                    output.extend(chunk)
                    if len(output) > MAX_OUTPUT_BYTES:
                        if proc.returncode is None:
                            try:
                                proc.kill()
                            except ProcessLookupError:
                                pass
                        return bytes(output[:MAX_OUTPUT_BYTES]), True

            if proc.stdout is None or proc.stderr is None:
                raise RuntimeError("Subprocess output streams are unavailable")
            stdout_task = asyncio.create_task(read_limited(proc.stdout))
            stderr_task = asyncio.create_task(read_limited(proc.stderr))
            (stdout, stdout_exceeded), (stderr, stderr_exceeded) = await asyncio.wait_for(
                asyncio.gather(stdout_task, stderr_task), timeout=timeout
            )
            await proc.wait()

            stdout_decoded = stdout.decode("utf-8", errors="replace")[:MAX_OUTPUT_BYTES]
            stderr_decoded = stderr.decode("utf-8", errors="replace")[:MAX_OUTPUT_BYTES]

            if stdout_exceeded or stderr_exceeded:
                audit_logger.warning("command_output_limit channel=%s", channel)
                return (
                    False,
                    stdout_decoded,
                    f"Command output exceeded {MAX_OUTPUT_BYTES} bytes",
                )

            audit_logger.info(
                "command_executed channel=%s returncode=%d stdout_len=%d stderr_len=%d",
                channel,
                proc.returncode or 0,
                len(stdout_decoded),
                len(stderr_decoded),
            )

            return (
                proc.returncode == 0,
                stdout_decoded,
                stderr_decoded,
            )
        except asyncio.TimeoutError:
            audit_logger.warning("command_timeout channel=%s timeout=%d", channel, timeout)
            await terminate_child()
            return False, "", f"Command timed out after {timeout}s"
        except asyncio.CancelledError:
            await terminate_child()
            raise
        except Exception as e:
            await terminate_child()
            audit_logger.error("command_error channel=%s error=%s", channel, str(e))
            return False, "", str(e)

    def _validate_query(self, query: str) -> str:
        """Validate and sanitize query string."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if len(query) > MAX_QUERY_LENGTH:
            raise ValueError(f"Query too long (max {MAX_QUERY_LENGTH} chars)")
        # Block shell metacharacters
        dangerous = [";", "&&", "||", "|", "`", "$(", "${", "\n", "\r"]
        for d in dangerous:
            if d in query:
                raise ValueError(f"Query contains disallowed characters: {d}")
        return query.strip()

    def _validate_url(self, url: str) -> str:
        """Validate URL with SSRF protection."""
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        if len(url) > MAX_URL_LENGTH:
            raise ValueError(f"URL too long (max {MAX_URL_LENGTH} chars)")
        if not _is_safe_url(url):
            raise ValueError(f"URL blocked by SSRF protection: {url}")
        return url.strip()

    def _validate_provider_url(self, url: str, allowed_hosts: set[str]) -> str:
        """Restrict direct provider fetches to HTTPS on known public domains."""
        url = self._validate_url(url)
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").rstrip(".").lower()
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Provider URL has an invalid port") from exc
        if (
            parsed.scheme.lower() != "https"
            or parsed.username is not None
            or parsed.password is not None
            or port not in (None, 443)
            or not any(
                hostname == host or hostname.endswith(f".{host}")
                for host in allowed_hosts
            )
        ):
            raise ValueError("URL host or scheme is not allowed for this provider")
        return url

    async def _resolve_public_addresses(
        self, hostname: str, port: int
    ) -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        """Resolve a host once so network clients can pin its verified address."""
        loop = asyncio.get_running_loop()
        records = await loop.getaddrinfo(
            hostname, port, type=socket.SOCK_STREAM
        )
        addresses: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
        for record in records:
            address = ipaddress.ip_address(record[4][0])
            addresses.add(address)
        return addresses

    async def _resolve_safe_feed_target(
        self, feed_url: str
    ) -> tuple[str, str, int, ipaddress.IPv4Address | ipaddress.IPv6Address]:
        """Validate a feed URL and pin its curl connection to a public IP."""
        feed_url = self._validate_url(feed_url)
        parsed = urlparse(feed_url)
        hostname = (parsed.hostname or "").rstrip(".").lower()
        if (
            not hostname
            or parsed.username is not None
            or parsed.password is not None
            or "\\" in feed_url
            or any(ord(character) < 32 or character.isspace() for character in feed_url)
        ):
            raise ValueError("RSS URL is malformed or contains credentials")

        try:
            port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        except ValueError as exc:
            raise ValueError("RSS URL has an invalid port") from exc

        try:
            addresses = await self._resolve_public_addresses(hostname, port)
        except OSError as exc:
            raise ValueError("RSS host could not be resolved") from exc
        if not addresses or any(not address.is_global for address in addresses):
            raise ValueError("RSS host resolved to a non-public address")

        # Pin one verified address. curl keeps the original hostname for the
        # HTTP Host header and TLS certificate validation, but skips DNS lookup.
        address = sorted(addresses, key=lambda item: (item.version, int(item)))[0]
        return feed_url, hostname, port, address

    async def check_status(self) -> list[ChannelInfo]:
        """Check status of all Agent Reach channels."""
        success, stdout, _ = await self._run_command(
            ["agent-reach", "doctor"], timeout=15, channel="status"
        )
        channels = []
        if success:
            for line in stdout.splitlines():
                if "✅" in line:
                    channels.append(
                        ChannelInfo(
                            channel=ChannelType.WEB,
                            status=ChannelStatus.READY,
                            message=line.strip(),
                        )
                    )
                elif "[!]" in line:
                    channels.append(
                        ChannelInfo(
                            channel=ChannelType.WEB,
                            status=ChannelStatus.CONFIG_NEEDED,
                            message=line.strip(),
                        )
                    )
        return channels

    # ── Web ──────────────────────────────────────────────────────

    async def read_web_page(
        self, url: str, format: str = "markdown"
    ) -> AgentReachResult:
        """Read a structurally validated public web URL via Jina Reader."""
        url = self._validate_url(url)
        command = ["curl", "-s", f"https://r.jina.ai/{url}"]
        success, stdout, stderr = await self._run_command(command, channel="web")
        return AgentReachResult(
            success=success,
            channel=ChannelType.WEB,
            action="read",
            data=stdout if success else None,
            error=stderr if not success else None,
            metadata={"url": url, "format": format},
        )

    # ── Twitter ──────────────────────────────────────────────────

    async def search_twitter(
        self, query: str, max_results: int = 10
    ) -> AgentReachResult:
        """Search Twitter/X."""
        query = self._validate_query(query)
        command = ["twitter", "search", query]
        success, stdout, stderr = await self._run_command(command, channel="twitter")
        return AgentReachResult(
            success=success,
            channel=ChannelType.TWITTER,
            action="search",
            data=stdout if success else None,
            error=stderr if not success else None,
            metadata={"query": query, "max_results": max_results},
        )

    async def read_tweet(self, tweet_url: str) -> AgentReachResult:
        """Read a single tweet."""
        tweet_url = self._validate_provider_url(
            tweet_url, {"twitter.com", "x.com"}
        )
        command = ["twitter", "tweet", tweet_url]
        success, stdout, stderr = await self._run_command(command, channel="twitter")
        return AgentReachResult(
            success=success,
            channel=ChannelType.TWITTER,
            action="read",
            data=stdout if success else None,
            error=stderr if not success else None,
            metadata={"url": tweet_url},
        )

    # ── YouTube ──────────────────────────────────────────────────

    async def get_youtube_subtitles(
        self, video_url: str, lang: str = "en"
    ) -> AgentReachResult:
        """Get YouTube video subtitles."""
        video_url = self._validate_provider_url(
            video_url, {"youtube.com", "youtu.be"}
        )
        # Sanitize lang parameter
        lang = re.sub(r"[^a-z-]", "", lang.lower())[:10]
        command = [
            "yt-dlp",
            "--write-auto-sub",
            "--skip-download",
            "--sub-lang",
            lang,
            "--convert-subs",
            "srt",
            "-o",
            "/tmp/yt_%(id)s",
            video_url,
        ]
        success, stdout, stderr = await self._run_command(
            command, timeout=60, channel="youtube"
        )
        return AgentReachResult(
            success=success,
            channel=ChannelType.YOUTUBE,
            action="subtitles",
            data=stdout if success else None,
            error=stderr if not success else None,
            metadata={"url": video_url, "lang": lang},
        )

    async def search_youtube(
        self, query: str, max_results: int = 5
    ) -> AgentReachResult:
        """Search YouTube videos."""
        query = self._validate_query(query)
        max_results = min(max_results, 20)
        command = ["yt-dlp", "--dump-json", f"ytsearch{max_results}:{query}"]
        success, stdout, stderr = await self._run_command(
            command, timeout=30, channel="youtube"
        )
        data = None
        if success and stdout.strip():
            try:
                data = [
                    json.loads(line)
                    for line in stdout.strip().split("\n")
                    if line.strip()
                ]
            except json.JSONDecodeError:
                data = stdout
        return AgentReachResult(
            success=success,
            channel=ChannelType.YOUTUBE,
            action="search",
            data=data,
            error=stderr if not success else None,
            metadata={"query": query, "max_results": max_results},
        )

    # ── GitHub ───────────────────────────────────────────────────

    async def search_github(
        self, query: str, max_results: int = 10
    ) -> AgentReachResult:
        """Search GitHub repositories."""
        query = self._validate_query(query)
        max_results = min(max_results, 50)
        command = [
            "gh",
            "search",
            "repos",
            query,
            "--limit",
            str(max_results),
            "--json",
            "name,description,url,stargazerCount",
        ]
        success, stdout, stderr = await self._run_command(command, channel="github")
        data = None
        if success and stdout.strip():
            try:
                data = json.loads(stdout)
            except json.JSONDecodeError:
                data = stdout
        return AgentReachResult(
            success=success,
            channel=ChannelType.GITHUB,
            action="search",
            data=data,
            error=stderr if not success else None,
            metadata={"query": query, "max_results": max_results},
        )

    async def read_github_repo(self, repo: str) -> AgentReachResult:
        """Read GitHub repo info."""
        repo = self._validate_query(repo)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("Repository must use the owner/name format")
        command = [
            "gh",
            "repo",
            "view",
            repo,
            "--json",
            "name,description,url,stargazerCount,primaryLanguage",
        ]
        success, stdout, stderr = await self._run_command(command, channel="github")
        data = None
        if success and stdout.strip():
            try:
                data = json.loads(stdout)
            except json.JSONDecodeError:
                data = stdout
        return AgentReachResult(
            success=success,
            channel=ChannelType.GITHUB,
            action="read",
            data=data,
            error=stderr if not success else None,
            metadata={"repo": repo},
        )

    # ── RSS ──────────────────────────────────────────────────────

    async def read_rss_feed(
        self, feed_url: str, max_entries: int = 10
    ) -> AgentReachResult:
        """Read RSS/Atom feed without allowing DNS rebinding or redirects."""
        feed_url, hostname, port, address = await self._resolve_safe_feed_target(
            feed_url
        )
        max_entries = min(max_entries, 100)
        pinned_address = f"[{address.compressed}]" if address.version == 6 else address.compressed
        command = [
            "curl",
            "--disable",
            "--silent",
            "--show-error",
            "--fail",
            "--noproxy",
            "*",
            "--connect-timeout",
            "5",
            "--max-time",
            str(min(self._timeout, MAX_TIMEOUT)),
            "--max-filesize",
            str(MAX_OUTPUT_BYTES),
            "--max-redirs",
            "0",
            "--resolve",
            f"{hostname}:{port}:{pinned_address}",
            feed_url,
        ]
        success, stdout, stderr = await self._run_command(
            command, timeout=self._timeout, channel="rss"
        )
        data = None
        if success and stdout.strip():
            try:
                import feedparser

                parsed_feed = feedparser.parse(stdout)
                data = [
                    {
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", ""),
                    }
                    for entry in parsed_feed.entries[:max_entries]
                ]
            except ImportError:
                success = False
                stderr = "RSS parsing dependency is not installed"
        return AgentReachResult(
            success=success,
            channel=ChannelType.RSS,
            action="read",
            data=data,
            error=stderr if not success else None,
            metadata={"url": feed_url, "max_entries": max_entries},
        )

    # ── Bilibili ─────────────────────────────────────────────────

    async def search_bilibili(
        self, query: str, max_results: int = 10
    ) -> AgentReachResult:
        """Search Bilibili videos."""
        query = self._validate_query(query)
        max_results = min(max_results, 50)
        command = ["bili-cli", "search", query, "--limit", str(max_results)]
        success, stdout, stderr = await self._run_command(command, channel="bilibili")
        return AgentReachResult(
            success=success,
            channel=ChannelType.BILIBILI,
            action="search",
            data=stdout if success else None,
            error=stderr if not success else None,
            metadata={"query": query, "max_results": max_results},
        )

    # ── Web Search (Exa) ─────────────────────────────────────────

    async def search_web(
        self, query: str, max_results: int = 10
    ) -> AgentReachResult:
        """Semantic web search via Exa."""
        query = self._validate_query(query)
        max_results = min(max_results, 20)
        command = [
            "mcporter",
            "run",
            "exa",
            "search",
            query,
            "--limit",
            str(max_results),
        ]
        success, stdout, stderr = await self._run_command(command, channel="web_search")
        return AgentReachResult(
            success=success,
            channel=ChannelType.WEB_SEARCH,
            action="search",
            data=stdout if success else None,
            error=stderr if not success else None,
            metadata={"query": query, "max_results": max_results},
        )

    # ── LinkedIn (dedicated) ─────────────────────────────────────

    async def linkedin_company(self, company_name: str) -> AgentReachResult:
        """Read LinkedIn company page via Jina Reader."""
        company_name = self._validate_query(company_name)
        # Use Jina Reader for LinkedIn public pages
        url = f"https://www.linkedin.com/company/{company_name}"
        if not _is_safe_url(url):
            return AgentReachResult(
                success=False,
                channel=ChannelType.LINKEDIN,
                action="company",
                error="LinkedIn URL blocked by SSRF protection",
            )
        command = ["curl", "-s", f"https://r.jina.ai/{url}"]
        success, stdout, stderr = await self._run_command(command, channel="linkedin")
        return AgentReachResult(
            success=success,
            channel=ChannelType.LINKEDIN,
            action="company",
            data=stdout if success else None,
            error=stderr if not success else None,
            metadata={"company": company_name},
        )

    async def linkedin_profile(self, profile_id: str) -> AgentReachResult:
        """Read LinkedIn profile via Jina Reader."""
        profile_id = self._validate_query(profile_id)
        url = f"https://www.linkedin.com/in/{profile_id}"
        if not _is_safe_url(url):
            return AgentReachResult(
                success=False,
                channel=ChannelType.LINKEDIN,
                action="profile",
                error="LinkedIn URL blocked by SSRF protection",
            )
        command = ["curl", "-s", f"https://r.jina.ai/{url}"]
        success, stdout, stderr = await self._run_command(command, channel="linkedin")
        return AgentReachResult(
            success=success,
            channel=ChannelType.LINKEDIN,
            action="profile",
            data=stdout if success else None,
            error=stderr if not success else None,
            metadata={"profile": profile_id},
        )

    async def linkedin_jobs(self, query: str) -> AgentReachResult:
        """Search LinkedIn jobs via Jina Reader."""
        query = self._validate_query(query)
        url = f"https://www.linkedin.com/jobs/search/?keywords={query}"
        if not _is_safe_url(url):
            return AgentReachResult(
                success=False,
                channel=ChannelType.LINKEDIN,
                action="jobs",
                error="LinkedIn URL blocked by SSRF protection",
            )
        command = ["curl", "-s", f"https://r.jina.ai/{url}"]
        success, stdout, stderr = await self._run_command(command, channel="linkedin")
        return AgentReachResult(
            success=success,
            channel=ChannelType.LINKEDIN,
            action="jobs",
            data=stdout if success else None,
            error=stderr if not success else None,
            metadata={"query": query},
        )

    # ── Unified Research ─────────────────────────────────────────

    async def research_company(
        self, company_name: str, channels: list[str] | None = None
    ) -> dict[str, AgentReachResult]:
        """Research a company across multiple channels.

        Returns raw channel results. The tenant-aware API layer owns persistence.
        """
        channels = channels or ["web", "github", "linkedin"]
        results: dict[str, AgentReachResult] = {}

        tasks = []
        if "web" in channels:
            tasks.append(("web", self.read_web_page(f"https://{company_name}.com")))
        if "github" in channels:
            tasks.append(("github", self.search_github(company_name, max_results=3)))
        if "linkedin" in channels:
            tasks.append(("linkedin", self.linkedin_company(company_name)))
        if "twitter" in channels:
            tasks.append(("twitter", self.search_twitter(company_name, max_results=5)))
        if "youtube" in channels:
            tasks.append(("youtube", self.search_youtube(company_name, max_results=3)))

        if tasks:
            channel_names = [t[0] for t in tasks]
            coros = [t[1] for t in tasks]
            done_results = await asyncio.gather(*coros, return_exceptions=True)
            for ch_name, res in zip(channel_names, done_results):
                if isinstance(res, Exception):
                    results[ch_name] = AgentReachResult(
                        success=False,
                        channel=ChannelType.WEB,
                        action="research",
                        error=str(res),
                    )
                else:
                    results[ch_name] = res

        return results

    # ── Generic Execute (allowlisted only) ───────────────────────

    async def execute(self, request: AgentReachRequest) -> AgentReachResult:
        """Execute a generic Agent Reach request (allowlisted operations only)."""
        channel = request.channel.value
        action = request.action

        # Validate against allowlist
        if channel not in ALLOWED_OPERATIONS:
            return AgentReachResult(
                success=False,
                channel=request.channel,
                action=action,
                error=f"Unknown channel: {channel}",
            )
        if action not in ALLOWED_OPERATIONS[channel]:
            return AgentReachResult(
                success=False,
                channel=request.channel,
                action=action,
                error=f"Unknown action '{action}' for channel '{channel}'",
            )

        # Route to typed methods
        if channel == "web" and action == "read":
            return await self.read_web_page(request.url or request.query or "")
        elif channel == "twitter" and action == "search":
            return await self.search_twitter(request.query or "", request.max_results)
        elif channel == "twitter" and action == "read":
            return await self.read_tweet(request.url or request.query or "")
        elif channel == "youtube" and action == "subtitles":
            return await self.get_youtube_subtitles(request.url or "")
        elif channel == "youtube" and action == "search":
            return await self.search_youtube(request.query or "", request.max_results)
        elif channel == "github" and action == "search":
            return await self.search_github(request.query or "", request.max_results)
        elif channel == "github" and action == "read":
            return await self.read_github_repo(request.query or "")
        elif channel == "rss" and action == "read":
            return await self.read_rss_feed(
                request.url or request.query or "", request.max_results
            )
        elif channel == "bilibili" and action == "search":
            return await self.search_bilibili(request.query or "", request.max_results)
        elif channel == "web_search" and action == "search":
            return await self.search_web(request.query or "", request.max_results)
        elif channel == "linkedin" and action == "company":
            return await self.linkedin_company(request.query or "")
        elif channel == "linkedin" and action == "profile":
            return await self.linkedin_profile(request.query or "")
        elif channel == "linkedin" and action == "jobs":
            return await self.linkedin_jobs(request.query or "")
        else:
            return AgentReachResult(
                success=False,
                channel=request.channel,
                action=action,
                error=f"Unsupported: {channel}/{action}",
            )


# ── Evidence / Signals Storage ───────────────────────────────────


class EvidenceStore:
    """In-memory evidence + signals store with company-keyed lookups.

    Upgrade path: swap dict storage for Postgres tables
    (agent_evidence, agent_signals) with RLS tenant isolation.
    """

    def __init__(self) -> None:
        self._evidence: dict[str, list[EvidenceItem]] = {}  # company_name -> items
        self._signals: dict[str, list[Signal]] = {}  # company_name -> signals

    def add_evidence(self, item: EvidenceItem) -> None:
        """Store an evidence item."""
        key = item.company_name.lower().strip()
        self._evidence.setdefault(key, []).append(item)

    def add_signal(self, signal: Signal) -> None:
        """Store a signal."""
        key = signal.company_name.lower().strip()
        self._signals.setdefault(key, []).append(signal)

    def get_evidence(self, company_name: str) -> list[EvidenceItem]:
        """Get all evidence for a company."""
        return self._evidence.get(company_name.lower().strip(), [])

    def get_signals(self, company_name: str) -> list[Signal]:
        """Get all signals for a company."""
        return self._signals.get(company_name.lower().strip(), [])

    def get_summary(self, company_name: str) -> CompanyIntelSummary:
        """Get aggregated intelligence summary for a company."""
        key = company_name.lower().strip()
        evidence = self._evidence.get(key, [])
        signals = self._signals.get(key, [])
        channels = list({e.channel.value for e in evidence})
        last = max((e.collected_at for e in evidence), default=None)
        return CompanyIntelSummary(
            company_name=company_name,
            evidence_count=len(evidence),
            signal_count=len(signals),
            evidence=evidence,
            signals=signals,
            channels_searched=channels,
            last_researched=last,
        )

    def list_companies(self) -> list[str]:
        """List all companies with stored intelligence."""
        all_keys = set(self._evidence.keys()) | set(self._signals.keys())
        return sorted(all_keys)

    def clear(self, company_name: str | None = None) -> int:
        """Clear evidence/signals. Returns count of items removed."""
        if company_name:
            key = company_name.lower().strip()
            ev_count = len(self._evidence.pop(key, []))
            sig_count = len(self._signals.pop(key, []))
            return ev_count + sig_count
        total = sum(len(v) for v in self._evidence.values()) + sum(
            len(v) for v in self._signals.values()
        )
        self._evidence.clear()
        self._signals.clear()
        return total


# Global singleton (per-process; swap for DB in production)
evidence_store = EvidenceStore()


# ── Signal Extraction Helpers ────────────────────────────────────


def classify_signals_from_evidence(items: list[EvidenceItem]) -> list[Signal]:
    """Extract signals from evidence items using keyword heuristics.

    This is a deterministic first pass — no LLM needed.
    """
    signals: list[Signal] = []
    seen_titles: set[str] = set()

    for item in items:
        text = f"{item.title} {item.summary}".lower()

        # Hiring signals
        if any(w in text for w in ["hiring", "job opening", "recruit", "vacancy"]):
            sig_title = f"Hiring activity detected for {item.company_name}"
            if sig_title not in seen_titles:
                seen_titles.add(sig_title)
                signals.append(
                    Signal(
                        company_name=item.company_name,
                        signal_type=SignalType.HIRING,
                        confidence=SignalConfidence.MEDIUM,
                        title=sig_title,
                        source_urls=[item.source_url],
                        evidence_ids=[item.id],
                    )
                )

        # Layoff signals
        if any(w in text for w in ["layoff", "downsize", "restructur", "reduction in force"]):
            sig_title = f"Layoff/restructuring detected for {item.company_name}"
            if sig_title not in seen_titles:
                seen_titles.add(sig_title)
                signals.append(
                    Signal(
                        company_name=item.company_name,
                        signal_type=SignalType.LAYOFFS,
                        confidence=SignalConfidence.MEDIUM,
                        title=sig_title,
                        source_urls=[item.source_url],
                        evidence_ids=[item.id],
                    )
                )

        # Funding signals
        if any(w in text for w in ["funding", "series", "raise", "investment", "venture"]):
            sig_title = f"Funding activity detected for {item.company_name}"
            if sig_title not in seen_titles:
                seen_titles.add(sig_title)
                signals.append(
                    Signal(
                        company_name=item.company_name,
                        signal_type=SignalType.FUNDING,
                        confidence=SignalConfidence.MEDIUM,
                        title=sig_title,
                        source_urls=[item.source_url],
                        evidence_ids=[item.id],
                    )
                )

        # Partnership signals
        if any(w in text for w in ["partner", "collaborat", "alliance", "joint venture"]):
            sig_title = f"Partnership activity detected for {item.company_name}"
            if sig_title not in seen_titles:
                seen_titles.add(sig_title)
                signals.append(
                    Signal(
                        company_name=item.company_name,
                        signal_type=SignalType.PARTNERSHIP,
                        confidence=SignalConfidence.LOW,
                        title=sig_title,
                        source_urls=[item.source_url],
                        evidence_ids=[item.id],
                    )
                )

        # Expansion signals
        if any(w in text for w in ["expand", "new office", "enter", "market", "launch"]):
            sig_title = f"Expansion activity detected for {item.company_name}"
            if sig_title not in seen_titles:
                seen_titles.add(sig_title)
                signals.append(
                    Signal(
                        company_name=item.company_name,
                        signal_type=SignalType.EXPANSION,
                        confidence=SignalConfidence.LOW,
                        title=sig_title,
                        source_urls=[item.source_url],
                        evidence_ids=[item.id],
                    )
                )

    return signals
