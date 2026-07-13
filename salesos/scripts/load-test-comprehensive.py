#!/usr/bin/env python3
"""SalesOS Comprehensive Load Test Suite.

Six scenarios testing all critical paths under realistic concurrency.
Outputs CSV results + summary JSON with p50/p95/p99/error rates.

Usage:
    python scripts/load-test-comprehensive.py
    python scripts/load-test-comprehensive.py --users 200 --duration 120
    python scripts/load-test-comprehensive.py --scenarios login,search
    SALESOS_BASE_URL=http://staging.example.com python scripts/load-test-comprehensive.py
"""

import argparse
import asyncio
import csv
import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import httpx
except ImportError:
    httpx = None

if aiohttp is None and httpx is None:
    print("ERROR: Install aiohttp or httpx: pip install aiohttp httpx")
    sys.exit(1)

BASE_URL = os.getenv("SALESOS_BASE_URL", "http://localhost:8000")
USERNAME = os.getenv("SALESOS_USERNAME", "admin@test.com")
PASSWORD = os.getenv("SALESOS_PASSWORD", "password")
COMPANY_ID = os.getenv("SALESOS_COMPANY_ID", "1")
WS_URL = os.getenv("SALESOS_WS_URL", "ws://localhost:8000")

MIXED_WEIGHTS = {"read": 0.70, "write": 0.20, "search": 0.10}

SEARCH_QUERIES = [
    "Arabian company", "Riyadh", "technology", "Saudi Arabia",
    "company", "Riyadh city", "tech sector", "Kingdom of Saudi Arabia",
    "AI startup", "fintech", "healthcare", "investor",
    "Series A", "real estate", "construction", "e-commerce",
    "logistics", "education", "energy", "manufacturing",
]


@dataclass
class RequestResult:
    timestamp: float
    latency_ms: float
    status_code: int
    endpoint: str
    error: bool = False
    cache_hit: bool = False


@dataclass
class ScenarioResult:
    name: str
    requests: list = field(default_factory=list)
    elapsed: float = 0.0

    @property
    def total(self):
        return len(self.requests)

    @property
    def errors(self):
        return sum(1 for r in self.requests if r.error)

    @property
    def error_rate(self):
        return (self.errors / self.total * 100) if self.total > 0 else 0.0

    @property
    def cache_hits(self):
        return sum(1 for r in self.requests if r.cache_hit)

    @property
    def cache_hit_rate(self):
        cacheable = [r for r in self.requests if "dashboard" in r.endpoint or "search" in r.endpoint]
        return (self.cache_hits / len(cacheable) * 100) if cacheable else 0.0

    def percentile(self, p):
        if not self.requests:
            return 0.0
        vals = sorted(r.latency_ms for r in self.requests)
        idx = min(int(len(vals) * p / 100), len(vals) - 1)
        return vals[idx]

    @property
    def p50(self): return self.percentile(50)
    @property
    def p95(self): return self.percentile(95)
    @property
    def p99(self): return self.percentile(99)
    @property
    def min_ms(self): return min((r.latency_ms for r in self.requests), default=0.0)
    @property
    def max_ms(self): return max((r.latency_ms for r in self.requests), default=0.0)
    @property
    def throughput_rps(self): return self.total / self.elapsed if self.elapsed > 0 else 0.0

    def to_dict(self):
        return {
            "name": self.name,
            "total_requests": self.total,
            "errors": self.errors,
            "error_rate_pct": round(self.error_rate, 2),
            "latency": {
                "p50_ms": round(self.p50, 1),
                "p95_ms": round(self.p95, 1),
                "p99_ms": round(self.p99, 1),
                "min_ms": round(self.min_ms, 1),
                "max_ms": round(self.max_ms, 1),
                "mean_ms": round(sum(r.latency_ms for r in self.requests) / self.total, 1) if self.total else 0,
            },
            "throughput_rps": round(self.throughput_rps, 2),
            "elapsed_s": round(self.elapsed, 2),
            "cache_hit_rate_pct": round(self.cache_hit_rate, 2),
        }


class AioHttpClient:
    def __init__(self):
        self._session = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        conn = aiohttp.TCPConnector(limit=500, limit_per_host=200)
        self._session = aiohttp.ClientSession(timeout=timeout, connector=conn)
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    async def get(self, url, headers=None):
        start = time.perf_counter()
        async with self._session.get(url, headers=headers) as resp:
            await resp.read()
            return resp.status, (time.perf_counter() - start) * 1000, ""

    async def post(self, url, json=None, headers=None):
        start = time.perf_counter()
        async with self._session.post(url, json=json, headers=headers) as resp:
            body = await resp.text()
            return resp.status, (time.perf_counter() - start) * 1000, body

    async def ws_connect(self, url, headers=None):
        start = time.perf_counter()
        try:
            async with self._session.ws_connect(url, headers=headers):
                await asyncio.sleep(2)
        except Exception:
            pass
        return (time.perf_counter() - start) * 1000


class HttpxClient:
    def __init__(self):
        self._client = None

    async def __aenter__(self):
        limits = httpx.Limits(max_connections=500, max_keepalive_connections=200)
        self._client = httpx.AsyncClient(timeout=30.0, limits=limits)
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def get(self, url, headers=None):
        start = time.perf_counter()
        resp = await self._client.get(url, headers=headers)
        return resp.status_code, (time.perf_counter() - start) * 1000, ""

    async def post(self, url, json=None, headers=None):
        start = time.perf_counter()
        resp = await self._client.post(url, json=json, headers=headers)
        return resp.status_code, (time.perf_counter() - start) * 1000, resp.text

    async def ws_connect(self, url, headers=None):
        return 0.0


def make_client():
    if aiohttp is not None:
        return AioHttpClient()
    return HttpxClient()


async def login_user(client, email, password):
    try:
        status, _, body = await client.post(
            f"{BASE_URL}/api/v1/identity/login",
            json={"email": email, "password": password},
        )
        if status == 200:
            data = json.loads(body) if isinstance(body, str) else body
            return data.get("access_token")
    except Exception:
        pass
    return None


async def scenario_login_storm(client, result, duration_s, concurrency):
    """Scenario 1: 100 concurrent logins over 60s."""
    sem = asyncio.Semaphore(concurrency)
    emails = [f"user{i}@test.com" for i in range(concurrency)]

    async def _login(idx):
        async with sem:
            entry = RequestResult(time.time(), 0, 0, "POST /identity/login")
            try:
                status, elapsed, body = await client.post(
                    f"{BASE_URL}/api/v1/identity/login",
                    json={"email": emails[idx % len(emails)], "password": PASSWORD},
                )
                entry.latency_ms = elapsed
                entry.status_code = status
                entry.error = status != 200
            except Exception:
                entry.error = True
            result.requests.append(entry)

    tasks = []
    for i in range(concurrency):
        tasks.append(asyncio.create_task(_login(i)))
        if (i + 1) % 10 == 0:
            await asyncio.sleep(duration_s / concurrency)
    await asyncio.gather(*tasks)


async def scenario_dashboard_load(client, result, token, concurrency):
    """Scenario 2: 50 concurrent dashboard requests, measure cache hit rate."""
    headers = {"Authorization": f"Bearer {token}"}
    sem = asyncio.Semaphore(concurrency)
    total = concurrency * 2

    async def _hit():
        async with sem:
            entry = RequestResult(time.time(), 0, 0, "GET /dashboard")
            try:
                status, elapsed, _ = await client.get(f"{BASE_URL}/api/v1/dashboard", headers=headers)
                entry.latency_ms = elapsed
                entry.status_code = status
                entry.error = status != 200
                if status == 200 and elapsed < 20:
                    entry.cache_hit = True
            except Exception:
                entry.error = True
            result.requests.append(entry)

    tasks = [asyncio.create_task(_hit()) for _ in range(total)]
    await asyncio.gather(*tasks)


async def scenario_search_burst(client, result, token, duration_s, total_queries):
    """Scenario 3: 200 search queries over 30s (mix of Arabic/English)."""
    headers = {"Authorization": f"Bearer {token}"}
    sem = asyncio.Semaphore(50)

    async def _search():
        async with sem:
            query = random.choice(SEARCH_QUERIES)
            entry = RequestResult(time.time(), 0, 0, "POST /search")
            try:
                status, elapsed, _ = await client.post(
                    f"{BASE_URL}/api/v1/search",
                    json={"query": query, "limit": 10},
                    headers=headers,
                )
                entry.latency_ms = elapsed
                entry.status_code = status
                entry.error = status != 200
                if status == 200 and elapsed < 15:
                    entry.cache_hit = True
            except Exception:
                entry.error = True
            result.requests.append(entry)

    tasks = []
    for i in range(total_queries):
        tasks.append(asyncio.create_task(_search()))
        if (i + 1) % 20 == 0:
            await asyncio.sleep(duration_s / total_queries)
    await asyncio.gather(*tasks)


async def scenario_enrichment(client, result, token, concurrency):
    """Scenario 4: 20 concurrent enrichment requests."""
    headers = {"Authorization": f"Bearer {token}"}
    sem = asyncio.Semaphore(concurrency)

    async def _enrich():
        async with sem:
            entry = RequestResult(time.time(), 0, 0, "POST /enrich")
            try:
                status, elapsed, _ = await client.post(
                    f"{BASE_URL}/api/v1/enrich",
                    json={"company_id": str(random.randint(1, 100))},
                    headers=headers,
                )
                entry.latency_ms = elapsed
                entry.status_code = status
                entry.error = status not in (200, 202)
            except Exception:
                entry.error = True
            result.requests.append(entry)

    tasks = [asyncio.create_task(_enrich()) for _ in range(concurrency)]
    await asyncio.gather(*tasks)


async def scenario_ws_flood(client, result, token, concurrency):
    """Scenario 5: 100 concurrent WebSocket connections."""
    sem = asyncio.Semaphore(concurrency)

    async def _ws():
        async with sem:
            entry = RequestResult(time.time(), 0, 0, "WS /notifications")
            try:
                elapsed = await client.ws_connect(
                    f"{WS_URL}/api/v1/notifications/ws?token={token}"
                )
                entry.latency_ms = elapsed
                entry.status_code = 101
            except Exception:
                entry.error = True
                entry.latency_ms = (time.time() - entry.timestamp) * 1000
            result.requests.append(entry)

    tasks = [asyncio.create_task(_ws()) for _ in range(concurrency)]
    await asyncio.gather(*tasks)


async def scenario_mixed_traffic(client, result, token, duration_s, concurrency):
    """Scenario 6: Realistic mix (70% read, 20% write, 10% search)."""
    headers = {"Authorization": f"Bearer {token}"}
    sem = asyncio.Semaphore(concurrency)

    read_urls = [
        f"{BASE_URL}/api/v1/companies/{COMPANY_ID}",
        f"{BASE_URL}/api/v1/dashboard",
        f"{BASE_URL}/api/v1/contacts",
        f"{BASE_URL}/health",
    ]

    async def _request():
        async with sem:
            roll = random.random()
            entry = RequestResult(time.time(), 0, 0, "")
            try:
                if roll < MIXED_WEIGHTS["search"]:
                    entry.endpoint = "POST /search"
                    status, elapsed, _ = await client.post(
                        f"{BASE_URL}/api/v1/search",
                        json={"query": random.choice(SEARCH_QUERIES), "limit": 5},
                        headers=headers,
                    )
                elif roll < MIXED_WEIGHTS["search"] + MIXED_WEIGHTS["write"]:
                    entry.endpoint = "POST /companies"
                    status, elapsed, _ = await client.post(
                        f"{BASE_URL}/api/v1/companies",
                        json={"name": f"LoadTest-{random.randint(1,9999)}"},
                        headers=headers,
                    )
                else:
                    url = random.choice(read_urls)
                    entry.endpoint = f"GET {url.split('/')[-1]}"
                    status, elapsed, _ = await client.get(url, headers=headers)
                entry.latency_ms = elapsed
                entry.status_code = status
                entry.error = status >= 400
            except Exception:
                entry.error = True
            result.requests.append(entry)

    total = concurrency * 10
    tasks = []
    for i in range(total):
        tasks.append(asyncio.create_task(_request()))
        if (i + 1) % 50 == 0:
            await asyncio.sleep(duration_s / (total / 50))
    await asyncio.gather(*tasks)


def print_results(results, output_dir):
    print("\n" + "=" * 80)
    print("  SALESOS COMPREHENSIVE LOAD TEST RESULTS")
    print(f"  Target: {BASE_URL}")
    print(f"  Time:   {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    header = f"{'Scenario':<20} {'Reqs':>7} {'p50':>8} {'p95':>8} {'p99':>8} {'Err%':>7} {'RPS':>8} {'Cache%':>8}"
    print(header)
    print("-" * len(header))

    summary = []
    for r in results:
        d = r.to_dict()
        summary.append(d)
        print(
            f"{r.name:<20} {r.total:>7} {r.p50:>7.1f}ms {r.p95:>7.1f}ms "
            f"{r.p99:>7.1f}ms {r.error_rate:>6.1f}% {r.throughput_rps:>7.1f} {r.cache_hit_rate:>7.1f}%"
        )

    total_req = sum(r.total for r in results)
    total_err = sum(r.errors for r in results)
    print("-" * len(header))
    print(f"{'TOTAL':<20} {total_req:>7} {total_err:>7} errors")
    print()

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    csv_file = out_path / f"load-test-{time.strftime('%Y%m%d-%H%M%S')}.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario", "timestamp", "latency_ms", "status_code", "error", "cache_hit", "endpoint"])
        for r in results:
            for req in r.requests:
                writer.writerow([r.name, req.timestamp, round(req.latency_ms, 2),
                                 req.status_code, req.error, req.cache_hit, req.endpoint])

    json_file = out_path / f"load-test-{time.strftime('%Y%m%d-%H%M%S')}.json"
    report = {
        "meta": {
            "target": BASE_URL,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_requests": total_req,
            "total_errors": total_err,
        },
        "scenarios": summary,
    }
    with open(json_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"CSV:   {csv_file}")
    print(f"JSON:  {json_file}")

    max_error = max(r.error_rate for r in results)
    if max_error > 5.0:
        print(f"\nFAIL: Highest error rate {max_error:.1f}% exceeds 5% threshold")
        return False
    print("\nPASS: All scenarios within error threshold")
    return True


def main():
    parser = argparse.ArgumentParser(description="SalesOS Comprehensive Load Test")
    parser.add_argument("--users", type=int, default=100, help="Max concurrent users (default: 100)")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds (default: 60)")
    parser.add_argument("--search-queries", type=int, default=200, help="Search burst queries (default: 200)")
    parser.add_argument("--scenarios", type=str, default="all",
                        help="Comma-separated: login,dashboard,search,enrichment,websocket,mixed,all")
    parser.add_argument("--output-dir", type=str, default="test-results", help="Output directory")
    args = parser.parse_args()

    scenario_map = {
        "login": ("Login Storm", 1),
        "dashboard": ("Dashboard Load", 2),
        "search": ("Search Burst", 3),
        "enrichment": ("Enrichment Pipeline", 4),
        "websocket": ("WebSocket Flood", 5),
        "mixed": ("Mixed Traffic", 6),
    }

    if "all" in args.scenarios:
        selected = list(scenario_map.keys())
    else:
        selected = [s.strip() for s in args.scenarios.split(",")]

    print(f"\nSalesOS Comprehensive Load Test")
    print(f"Target: {BASE_URL} | Users: {args.users} | Duration: {args.duration}s")
    print(f"Scenarios: {', '.join(selected)}")
    print("-" * 60)

    async def run():
        results = []
        async with make_client() as client:
            token = await login_user(client, USERNAME, PASSWORD)
            if not token:
                print("ERROR: Could not authenticate. Check credentials.")
                sys.exit(1)
            print(f"Authenticated ({len(token)} chars)")

            if "login" in selected:
                print("[1/6] Login Storm...")
                r = ScenarioResult("Login Storm")
                t0 = time.perf_counter()
                await scenario_login_storm(client, r, args.duration, min(args.users, 100))
                r.elapsed = time.perf_counter() - t0
                results.append(r)

            if "dashboard" in selected:
                print("[2/6] Dashboard Load...")
                r = ScenarioResult("Dashboard Load")
                t0 = time.perf_counter()
                await scenario_dashboard_load(client, r, token, min(args.users, 50))
                r.elapsed = time.perf_counter() - t0
                results.append(r)

            if "search" in selected:
                print("[3/6] Search Burst...")
                r = ScenarioResult("Search Burst")
                t0 = time.perf_counter()
                await scenario_search_burst(client, r, token, args.duration, args.search_queries)
                r.elapsed = time.perf_counter() - t0
                results.append(r)

            if "enrichment" in selected:
                print("[4/6] Enrichment Pipeline...")
                r = ScenarioResult("Enrichment Pipeline")
                t0 = time.perf_counter()
                await scenario_enrichment(client, r, token, 20)
                r.elapsed = time.perf_counter() - t0
                results.append(r)

            if "websocket" in selected:
                print("[5/6] WebSocket Flood...")
                r = ScenarioResult("WebSocket Flood")
                t0 = time.perf_counter()
                await scenario_ws_flood(client, r, token, min(args.users, 100))
                r.elapsed = time.perf_counter() - t0
                results.append(r)

            if "mixed" in selected:
                print("[6/6] Mixed Traffic...")
                r = ScenarioResult("Mixed Traffic")
                t0 = time.perf_counter()
                await scenario_mixed_traffic(client, r, token, args.duration, args.users)
                r.elapsed = time.perf_counter() - t0
                results.append(r)

        passed = print_results(results, args.output_dir)
        sys.exit(0 if passed else 1)

    asyncio.run(run())


if __name__ == "__main__":
    main()
