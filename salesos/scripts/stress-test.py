#!/usr/bin/env python3
"""SalesOS Stress Test — Gradually increases load until failure.

Identifies breaking point (max concurrent users) and degradation curve.

Usage:
    python scripts/stress-test.py
    python scripts/stress-test.py --start 10 --step 10 --max 300 --ramp-interval 15
    SALESOS_BASE_URL=http://staging.example.com python scripts/stress-test.py
"""

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
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
    print("ERROR: pip install aiohttp httpx")
    sys.exit(1)

BASE_URL = os.getenv("SALESOS_BASE_URL", "http://localhost:8000")
USERNAME = os.getenv("SALESOS_USERNAME", "admin@test.com")
PASSWORD = os.getenv("SALESOS_PASSWORD", "password")


@dataclass
class RampResult:
    concurrency: int
    total_requests: int = 0
    errors: int = 0
    latencies: list = field(default_factory=list)
    elapsed: float = 0.0
    server_5xx: int = 0
    rate_limited: int = 0
    timeouts: int = 0

    @property
    def error_rate(self):
        return (self.errors / self.total_requests * 100) if self.total_requests else 0.0

    def percentile(self, p):
        if not self.latencies:
            return 0.0
        vals = sorted(self.latencies)
        return vals[min(int(len(vals) * p / 100), len(vals) - 1)]

    @property
    def p50(self): return self.percentile(50)
    @property
    def p95(self): return self.percentile(95)
    @property
    def p99(self): return self.percentile(99)
    @property
    def throughput_rps(self): return self.total_requests / self.elapsed if self.elapsed else 0

    def to_dict(self):
        return {
            "concurrency": self.concurrency,
            "total_requests": self.total_requests,
            "errors": self.errors,
            "error_rate_pct": round(self.error_rate, 2),
            "p50_ms": round(self.p50, 1),
            "p95_ms": round(self.p95, 1),
            "p99_ms": round(self.p99, 1),
            "throughput_rps": round(self.throughput_rps, 1),
            "elapsed_s": round(self.elapsed, 1),
            "server_5xx": self.server_5xx,
            "rate_limited": self.rate_limited,
            "timeouts": self.timeouts,
        }


class AioHttpClient:
    def __init__(self):
        self._session = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        conn = aiohttp.TCPConnector(limit=500, limit_per_host=300)
        self._session = aiohttp.ClientSession(timeout=timeout, connector=conn)
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    async def get(self, url, headers=None):
        start = time.perf_counter()
        try:
            async with self._session.get(url, headers=headers) as resp:
                await resp.read()
                return resp.status, (time.perf_counter() - start) * 1000
        except asyncio.TimeoutError:
            return 0, (time.perf_counter() - start) * 1000
        except Exception:
            return 0, (time.perf_counter() - start) * 1000

    async def post(self, url, json=None, headers=None):
        start = time.perf_counter()
        try:
            async with self._session.post(url, json=json, headers=headers) as resp:
                await resp.read()
                return resp.status, (time.perf_counter() - start) * 1000
        except asyncio.TimeoutError:
            return 0, (time.perf_counter() - start) * 1000
        except Exception:
            return 0, (time.perf_counter() - start) * 1000


class HttpxClient:
    def __init__(self):
        self._client = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=15.0, limits=httpx.Limits(max_connections=500))
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def get(self, url, headers=None):
        start = time.perf_counter()
        try:
            resp = await self._client.get(url, headers=headers)
            return resp.status_code, (time.perf_counter() - start) * 1000
        except Exception:
            return 0, (time.perf_counter() - start) * 1000

    async def post(self, url, json=None, headers=None):
        start = time.perf_counter()
        try:
            resp = await self._client.post(url, json=json, headers=headers)
            return resp.status_code, (time.perf_counter() - start) * 1000
        except Exception:
            return 0, (time.perf_counter() - start) * 1000


def make_client():
    return AioHttpClient() if aiohttp else HttpxClient()


async def get_token(client):
    status, _, body = await client.post(
        f"{BASE_URL}/api/v1/identity/login",
        json={"email": USERNAME, "password": PASSWORD},
    )
    if status == 200:
        import json as _json
        data = _json.loads(body) if isinstance(body, str) else body
        return data.get("access_token")
    return None


async def run_ramp(client, token, concurrency, duration_s, requests_per_user=3):
    """Execute one ramp at given concurrency level."""
    headers = {"Authorization": f"Bearer {token}"}
    result = RampResult(concurrency=concurrency)
    sem = asyncio.Semaphore(concurrency)
    total_requests = concurrency * requests_per_user

    endpoints = [
        ("GET", f"{BASE_URL}/api/v1/companies/1"),
        ("GET", f"{BASE_URL}/api/v1/dashboard"),
        ("GET", f"{BASE_URL}/health"),
        ("GET", f"{BASE_URL}/api/v1/contacts"),
        ("POST", f"{BASE_URL}/api/v1/search", {"query": "test", "limit": 5}),
    ]

    async def _request():
        async with sem:
            method, url, *rest = random.choice(endpoints)
            body = rest[0] if rest else None
            result.total_requests += 1
            t0 = time.perf_counter()
            try:
                if method == "GET":
                    status, elapsed = await client.get(url, headers=headers)
                else:
                    status, elapsed = await client.post(url, json=body, headers=headers)
                result.latencies.append(elapsed)
                if status >= 500:
                    result.server_5xx += 1
                    result.errors += 1
                elif status == 429:
                    result.rate_limited += 1
                    result.errors += 1
                elif status == 0:
                    result.timeouts += 1
                    result.errors += 1
                elif status >= 400:
                    result.errors += 1
            except Exception:
                result.errors += 1
                result.timeouts += 1

    import random
    t0 = time.perf_counter()
    tasks = [asyncio.create_task(_request()) for _ in range(total_requests)]
    await asyncio.gather(*tasks)
    result.elapsed = time.perf_counter() - t0
    return result


def print_ramp(r: RampResult):
    status = "OK"
    if r.error_rate > 50:
        status = "BROKEN"
    elif r.error_rate > 10:
        status = "DEGRADED"
    elif r.p95 > 2000:
        status = "SLOW"
    print(
        f"  {r.concurrency:>5} users | {r.total_requests:>5} reqs | "
        f"p50={r.p95:.0f}ms p95={r.p95:.0f}ms p99={r.p99:.0f}ms | "
        f"err={r.error_rate:.1f}% | 5xx={r.server_5xx} | 429={r.rate_limited} | "
        f"rps={r.throughput_rps:.0f} | [{status}]"
    )
    return status


def main():
    import random

    parser = argparse.ArgumentParser(description="SalesOS Stress Test")
    parser.add_argument("--start", type=int, default=10, help="Starting concurrency (default: 10)")
    parser.add_argument("--step", type=int, default=10, help="Concurrency increment per step (default: 10)")
    parser.add_argument("--max", type=int, default=200, help="Maximum concurrency (default: 200)")
    parser.add_argument("--ramp-interval", type=int, default=15, help="Seconds per ramp (default: 15)")
    parser.add_argument("--output", type=str, default="stress-test-results.json")
    args = parser.parse_args()

    print(f"\nSalesOS Stress Test")
    print(f"Target: {BASE_URL}")
    print(f"Range:  {args.start} -> {args.max} users (step={args.step})")
    print("-" * 70)

    async def run():
        all_results = []
        breaking_point = None

        async with make_client() as client:
            token = await get_token(client)
            if not token:
                print("ERROR: Authentication failed")
                sys.exit(1)
            print(f"Token acquired\n")

            for concurrency in range(args.start, args.max + 1, args.step):
                print(f"  [{concurrency} users] ", end="", flush=True)
                r = await run_ramp(client, token, concurrency, args.ramp_interval)
                status = print_ramp(r)
                all_results.append(r.to_dict())

                if status == "BROKEN" and breaking_point is None:
                    breaking_point = concurrency
                    print(f"\n  >>> BREAKING POINT: {concurrency} concurrent users")
                    print(f"  >>> Error rate {r.error_rate:.1f}% exceeds 50% threshold")
                    if concurrency < args.max:
                        print(f"  >>> Running 2 more ramps to confirm...")
                        continue

                if breaking_point and concurrency >= breaking_point + args.step * 2:
                    break

        report = {
            "meta": {
                "target": BASE_URL,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "start": args.start,
                "max": args.max,
                "step": args.step,
            },
            "breaking_point": breaking_point,
            "degradation_curve": all_results,
        }

        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n{'=' * 70}")
        print(f"  STRESS TEST COMPLETE")
        if breaking_point:
            print(f"  Breaking point: {breaking_point} concurrent users")
        else:
            print(f"  No breaking point found up to {args.max} users")
        print(f"  Report: {args.output}")
        print(f"{'=' * 70}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
