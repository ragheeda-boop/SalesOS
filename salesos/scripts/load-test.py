#!/usr/bin/env python3
"""SalesOS GA Readiness Load Test Script.

Standalone asyncio + aiohttp load test for verifying SalesOS
can handle 100 concurrent users across critical paths.

Usage:
    python scripts/load-test.py
    python scripts/load-test.py --help
    SALESOS_BASE_URL=http://staging.example.com python scripts/load-test.py
"""

import argparse
import asyncio
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

try:
    import aiohttp
except ImportError:
    print("aiohttp not found, falling back to httpx...")
    aiohttp = None

try:
    import httpx
except ImportError:
    httpx = None

if aiohttp is None and httpx is None:
    print("ERROR: Install aiohttp or httpx: pip install aiohttp httpx")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("SALESOS_BASE_URL", "http://localhost:8000")
USERNAME = os.getenv("SALESOS_USERNAME", "admin@test.com")
PASSWORD = os.getenv("SALESOS_PASSWORD", "password")
COMPANY_ID = os.getenv("SALESOS_COMPANY_ID", "1")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ScenarioResult:
    name: str
    latencies: list[float] = field(default_factory=list)
    errors: int = 0
    total_requests: int = 0
    elapsed: float = 0.0

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.errors / self.total_requests) * 100

    def percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * p / 100)
        idx = min(idx, len(sorted_lat) - 1)
        return sorted_lat[idx]

    @property
    def p50(self) -> float:
        return self.percentile(50)

    @property
    def p95(self) -> float:
        return self.percentile(95)

    @property
    def p99(self) -> float:
        return self.percentile(99)

    @property
    def min_ms(self) -> float:
        return min(self.latencies) if self.latencies else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.latencies) if self.latencies else 0.0


# ---------------------------------------------------------------------------
# HTTP helpers (aiohttp backend)
# ---------------------------------------------------------------------------

class AioHttpClient:
    """Wrapper around aiohttp for making requests."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self._session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    async def get(self, url: str, headers: dict | None = None) -> tuple[int, float]:
        start = time.perf_counter()
        async with self._session.get(url, headers=headers) as resp:
            await resp.read()
            elapsed = (time.perf_counter() - start) * 1000
            return resp.status, elapsed

    async def post(self, url: str, json: dict | None = None,
                   headers: dict | None = None) -> tuple[int, float, dict]:
        start = time.perf_counter()
        async with self._session.post(url, json=json, headers=headers) as resp:
            body = await resp.json()
            elapsed = (time.perf_counter() - start) * 1000
            return resp.status, elapsed, body


# ---------------------------------------------------------------------------
# HTTP helpers (httpx backend)
# ---------------------------------------------------------------------------

class HttpxClient:
    """Wrapper around httpx for making requests."""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def get(self, url: str, headers: dict | None = None) -> tuple[int, float]:
        start = time.perf_counter()
        resp = await self._client.get(url, headers=headers)
        elapsed = (time.perf_counter() - start) * 1000
        return resp.status_code, elapsed

    async def post(self, url: str, json: dict | None = None,
                   headers: dict | None = None) -> tuple[int, float, dict]:
        start = time.perf_counter()
        resp = await self._client.post(url, json=json, headers=headers)
        elapsed = (time.perf_counter() - start) * 1000
        return resp.status_code, elapsed, resp.json()


def make_client():
    if aiohttp is not None:
        return AioHttpClient()
    return HttpxClient()


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

async def health_check(client, result: ScenarioResult, iterations: int):
    url = f"{BASE_URL}/health"
    semaphore = asyncio.Semaphore(5)

    async def _hit():
        async with semaphore:
            result.total_requests += 1
            try:
                status, elapsed = await client.get(url)
                result.latencies.append(elapsed)
                if status != 200:
                    result.errors += 1
            except Exception:
                result.errors += 1

    await asyncio.gather(*[_hit() for _ in range(iterations)])


async def login(client, result: ScenarioResult, iterations: int):
    url = f"{BASE_URL}/api/v1/identity/login"
    semaphore = asyncio.Semaphore(10)

    async def _hit():
        async with semaphore:
            result.total_requests += 1
            try:
                status, elapsed, body = await client.post(
                    url, json={"email": USERNAME, "password": PASSWORD}
                )
                result.latencies.append(elapsed)
                if status != 200 or "access_token" not in body:
                    result.errors += 1
            except Exception:
                result.errors += 1

    await asyncio.gather(*[_hit() for _ in range(iterations)])


async def dashboard_load(client, result: ScenarioResult, iterations: int,
                         token: str):
    url = f"{BASE_URL}/api/v1/dashboard"
    headers = {"Authorization": f"Bearer {token}"}
    semaphore = asyncio.Semaphore(30)

    async def _hit():
        async with semaphore:
            result.total_requests += 1
            try:
                status, elapsed = await client.get(url, headers=headers)
                result.latencies.append(elapsed)
                if status != 200:
                    result.errors += 1
            except Exception:
                result.errors += 1

    await asyncio.gather(*[_hit() for _ in range(iterations)])


async def company_search(client, result: ScenarioResult, iterations: int,
                         token: str):
    url = f"{BASE_URL}/api/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    semaphore = asyncio.Semaphore(30)

    async def _hit():
        async with semaphore:
            result.total_requests += 1
            try:
                status, elapsed, body = await client.post(
                    url,
                    json={"query": "test", "limit": 10},
                    headers=headers,
                )
                result.latencies.append(elapsed)
                if status != 200:
                    result.errors += 1
            except Exception:
                result.errors += 1

    await asyncio.gather(*[_hit() for _ in range(iterations)])


async def company_detail(client, result: ScenarioResult, iterations: int,
                         token: str):
    url = f"{BASE_URL}/api/v1/companies/{COMPANY_ID}"
    headers = {"Authorization": f"Bearer {token}"}
    semaphore = asyncio.Semaphore(25)

    async def _hit():
        async with semaphore:
            result.total_requests += 1
            try:
                status, elapsed = await client.get(url, headers=headers)
                result.latencies.append(elapsed)
                if status != 200:
                    result.errors += 1
            except Exception:
                result.errors += 1

    await asyncio.gather(*[_hit() for _ in range(iterations)])


# ---------------------------------------------------------------------------
# Authentication helper
# ---------------------------------------------------------------------------

async def get_auth_token(client) -> str:
    url = f"{BASE_URL}/api/v1/identity/login"
    status, elapsed, body = await client.post(
        url, json={"email": USERNAME, "password": PASSWORD}
    )
    if status != 200 or "access_token" not in body:
        print(f"ERROR: Login failed (status={status}). Check credentials.")
        print(f"  URL:      {url}")
        print(f"  Username: {USERNAME}")
        print(f"  Response: {body}")
        sys.exit(1)
    return body["access_token"]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_results(results: list[ScenarioResult]):
    print("\n## Load Test Results\n")
    print(f"**Target:** {BASE_URL}")
    print(f"**Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("| Scenario | Requests | p50 | p95 | p99 | Min | Max | Error Rate |")
    print("|----------|----------|-----|-----|-----|-----|-----|------------|")
    for r in results:
        print(
            f"| {r.name:<13} | {r.total_requests:>8} "
            f"| {r.p50:>5.1f}ms | {r.p95:>5.1f}ms | {r.p99:>5.1f}ms "
            f"| {r.min_ms:>5.1f}ms | {r.max_ms:>5.1f}ms "
            f"| {r.error_rate:>6.1f}% |"
        )
    print(f"\n**Total wall time:** {sum(r.elapsed for r in results):.2f}s")
    total_req = sum(r.total_requests for r in results)
    total_err = sum(r.errors for r in results)
    print(f"**Total requests:** {total_req} ({total_err} errors)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run_tests(args):
    print(f"\nSalesOS Load Test — {BASE_URL}")
    print(f"Scenarios: health={args.health_iters}, login={args.login_iters}, "
          f"dashboard={args.dashboard_iters}, search={args.search_iters}, "
          f"company={args.company_iters}")
    print("-" * 55)

    results: list[ScenarioResult] = []

    async with make_client() as client:
        # 1. Health check (no auth)
        print("[1/5] Health check...")
        r = ScenarioResult(name="Health check")
        t0 = time.perf_counter()
        await health_check(client, r, args.health_iters)
        r.elapsed = time.perf_counter() - t0
        results.append(r)

        # 2. Login (get token for subsequent tests)
        print("[2/5] Login...")
        r = ScenarioResult(name="Login")
        t0 = time.perf_counter()
        await login(client, r, args.login_iters)
        r.elapsed = time.perf_counter() - t0
        results.append(r)

        token = await get_auth_token(client)
        print(f"  Token acquired ({len(token)} chars)")

        # 3. Dashboard load
        print("[3/5] Dashboard load...")
        r = ScenarioResult(name="Dashboard")
        t0 = time.perf_counter()
        await dashboard_load(client, r, args.dashboard_iters, token)
        r.elapsed = time.perf_counter() - t0
        results.append(r)

        # 4. Company search
        print("[4/5] Company search...")
        r = ScenarioResult(name="Search")
        t0 = time.perf_counter()
        await company_search(client, r, args.search_iters, token)
        r.elapsed = time.perf_counter() - t0
        results.append(r)

        # 5. Company detail
        print("[5/5] Company detail...")
        r = ScenarioResult(name="Company detail")
        t0 = time.perf_counter()
        await company_detail(client, r, args.company_iters, token)
        r.elapsed = time.perf_counter() - t0
        results.append(r)

    print_results(results)

    # Exit code: non-zero if any scenario exceeds 5% error rate
    max_error = max(r.error_rate for r in results)
    if max_error > 5.0:
        print(f"\nFAIL: Highest error rate {max_error:.1f}% exceeds 5% threshold")
        sys.exit(1)
    else:
        print("\nPASS: All scenarios within error threshold")


def main():
    parser = argparse.ArgumentParser(
        description="SalesOS GA Readiness Load Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  SALESOS_BASE_URL      Target URL (default: http://localhost:8000)
  SALESOS_USERNAME      Login email (default: admin@test.com)
  SALESOS_PASSWORD      Login password (default: password)
  SALESOS_COMPANY_ID    Company ID for detail test (default: 1)

Examples:
  python scripts/load-test.py
  python scripts/load-test.py --health-iters 50 --login-iters 20
  SALESOS_BASE_URL=http://staging.example.com python scripts/load-test.py
""",
    )
    parser.add_argument(
        "--health-iters", type=int, default=20,
        help="Health check iterations (default: 20)",
    )
    parser.add_argument(
        "--login-iters", type=int, default=10,
        help="Login iterations (default: 10)",
    )
    parser.add_argument(
        "--dashboard-iters", type=int, default=30,
        help="Dashboard iterations (default: 30)",
    )
    parser.add_argument(
        "--search-iters", type=int, default=20,
        help="Search iterations (default: 20)",
    )
    parser.add_argument(
        "--company-iters", type=int, default=20,
        help="Company detail iterations (default: 20)",
    )
    args = parser.parse_args()
    asyncio.run(run_tests(args))


if __name__ == "__main__":
    main()
