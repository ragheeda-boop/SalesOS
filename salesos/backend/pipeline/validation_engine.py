"""Shared domain validation engine for data pipeline scripts.

Usage:
    from pipeline.validation_engine import DomainValidator

    validator = DomainValidator()
    result = await validator.check("example.com")
    results = await validator.check_many(["example.com", "test.org"])
"""

import asyncio
import socket
import ssl
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse


@dataclass
class DomainCheckResult:
    domain: str
    valid: bool
    status_code: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    parked: bool = False
    redirect_url: Optional[str] = None
    error: Optional[str] = None


PARKED_KEYWORDS = [
    "parked", "domain is not claim", "this domain is for sale",
    "sedo", "afternic", "buy this domain", "domain parking",
    "coming soon", "under construction", "hosted by",
]


class DomainValidator:
    """Validates domains via DNS + HTTP check with parked-domain detection."""

    def __init__(self, timeout: float = 10.0, max_concurrent: int = 20):
        self.timeout = timeout
        self._sem = asyncio.Semaphore(max_concurrent)

    async def check(self, domain: str) -> DomainCheckResult:
        """Validate a single domain (async with semaphore)."""
        async with self._sem:
            return await self._check_single(domain)

    async def check_many(self, domains: list[str]) -> list[DomainCheckResult]:
        """Validate multiple domains concurrently."""
        tasks = [self.check(d) for d in domains]
        return await asyncio.gather(*tasks)

    async def _check_single(self, domain: str) -> DomainCheckResult:
        if not domain or domain in ("-", "—", "", "N/A"):
            return DomainCheckResult(domain=domain, valid=False, error="Empty domain")

        domain = domain.strip().lower()
        if not domain.startswith(("http://", "https://")):
            domain = f"https://{domain}"

        parsed = urlparse(domain)
        hostname = parsed.hostname or domain

        try:
            sock = socket.getaddrinfo(hostname, 80, socket.AF_INET, socket.SOCK_STREAM)
            if not sock:
                return DomainCheckResult(domain=domain, valid=False, error="DNS resolution failed")
        except (socket.gaierror, OSError):
            return DomainCheckResult(domain=domain, valid=False, error="DNS resolution failed")

        import httpx
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, verify=False) as client:
                resp = await client.get(f"https://{hostname}")
                text = resp.text.lower()

                title = ""
                if "<title>" in text and "</title>" in text:
                    title = text[text.index("<title>") + 7 : text.index("</title>")].strip()

                desc = ""
                import re
                m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', text, re.IGNORECASE)
                if m:
                    desc = m.group(1)

                is_parked = any(kw in text[:5000] for kw in PARKED_KEYWORDS)

                return DomainCheckResult(
                    domain=domain,
                    valid=200 <= resp.status_code < 500 and not is_parked,
                    status_code=resp.status_code,
                    title=title[:200] if title else None,
                    description=desc[:300] if desc else None,
                    parked=is_parked,
                    redirect_url=str(resp.url) if resp.url else None,
                )
        except (httpx.TimeoutException, httpx.RequestError, ssl.SSLError) as e:
            return DomainCheckResult(domain=domain, valid=False, error=str(e)[:100])
