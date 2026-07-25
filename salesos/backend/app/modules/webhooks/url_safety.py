"""Webhook outbound URL safety — block SSRF to private/metadata networks."""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import httpcore
import httpx


class UnsafeWebhookURLError(Exception):
    """Raised when a webhook URL fails SSRF safety checks."""


_BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "metadata.google.internal",
        "metadata.google",
        "instance-data",
    }
)


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


@dataclass(frozen=True)
class SafeWebhookTarget:
    """Validated webhook destination with DNS-checked public IPs.

    ``allowed_ips`` is empty when ``resolve_dns=False`` (unit tests) — delivery
    then cannot pin and uses hostname connect (TOCTOU residual in that mode).
    """

    url: str
    hostname: str
    port: int
    allowed_ips: tuple[str, ...]


def validate_webhook_url(url: str, *, resolve_dns: bool = True) -> str:
    """Validate webhook destination URL for outbound delivery.

    Rules:
    - HTTPS only
    - No credentials in URL
    - Host must not be localhost / cloud metadata
    - Resolved IPs must not be RFC1918, link-local, loopback, or metadata ranges

    Returns the stripped URL string (stable for create/update persistence).
    Prefer ``analyze_webhook_url`` when connecting outbound.
    """
    return analyze_webhook_url(url, resolve_dns=resolve_dns).url


def analyze_webhook_url(url: str, *, resolve_dns: bool = True) -> SafeWebhookTarget:
    """Validate URL and return safe target metadata (including resolved public IPs)."""
    if not url or not isinstance(url, str):
        raise UnsafeWebhookURLError("Webhook URL is required")

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() != "https":
        raise UnsafeWebhookURLError("Webhook URL must use HTTPS")
    if not parsed.hostname:
        raise UnsafeWebhookURLError("Webhook URL must include a hostname")
    if parsed.username or parsed.password:
        raise UnsafeWebhookURLError("Webhook URL must not include credentials")

    host = parsed.hostname.lower().rstrip(".")
    if host in _BLOCKED_HOSTNAMES or host.endswith(".localhost"):
        raise UnsafeWebhookURLError("Webhook URL host is not allowed")

    port = parsed.port or 443
    allowed_ips: list[str] = []

    # Literal IP in hostname
    try:
        literal_ip: ipaddress.IPv4Address | ipaddress.IPv6Address | None = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None
    if literal_ip is not None:
        if _is_blocked_ip(literal_ip):
            raise UnsafeWebhookURLError("Webhook URL must not target private or link-local IPs")
        allowed_ips.append(str(literal_ip))
    elif resolve_dns:
        try:
            addrinfos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise UnsafeWebhookURLError(f"Webhook URL host could not be resolved: {host}") from exc
        if not addrinfos:
            raise UnsafeWebhookURLError(f"Webhook URL host could not be resolved: {host}")
        for info in addrinfos:
            ip = ipaddress.ip_address(info[4][0])
            if _is_blocked_ip(ip):
                raise UnsafeWebhookURLError(
                    "Webhook URL resolves to a private, link-local, or reserved address"
                )
            allowed_ips.append(str(ip))

    return SafeWebhookTarget(
        url=url.strip(),
        hostname=host,
        port=port,
        allowed_ips=tuple(dict.fromkeys(allowed_ips)),  # preserve order, dedupe
    )


class _PinnedIPBackend(httpcore.AsyncNetworkBackend):
    """TCP connect to a pre-validated IP; TLS SNI still uses request hostname."""

    def __init__(self, pinned_ip: str) -> None:
        self._pinned_ip = pinned_ip
        self._inner = httpcore.AnyIOBackend()

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: object | None = None,
    ) -> httpcore.AsyncNetworkStream:
        return await self._inner.connect_tcp(
            self._pinned_ip,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )

    async def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: object | None = None,
    ) -> httpcore.AsyncNetworkStream:
        raise RuntimeError("Unix sockets are not allowed for webhook delivery")

    async def sleep(self, seconds: float) -> None:
        await self._inner.sleep(seconds)


def build_pinned_async_transport(pinned_ip: str) -> httpx.AsyncHTTPTransport:
    """httpx transport that dials ``pinned_ip`` while keeping URL hostname for TLS/Host."""
    transport = httpx.AsyncHTTPTransport()
    old_pool = transport._pool
    ssl_context = getattr(old_pool, "_ssl_context", None)
    transport._pool = httpcore.AsyncConnectionPool(
        ssl_context=ssl_context,
        max_connections=getattr(old_pool, "_max_connections", 10),
        max_keepalive_connections=getattr(old_pool, "_max_keepalive_connections", None),
        keepalive_expiry=getattr(old_pool, "_keepalive_expiry", None),
        http1=True,
        http2=False,
        network_backend=_PinnedIPBackend(pinned_ip),
    )
    return transport
