#!/usr/bin/env python3
"""One-shot live probes for Phase 4F ops execution (A/B/C)."""
from __future__ import annotations

import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.request

API = "http://localhost:8000"
CO_PIF = "25ea3f23-a0a6-4bb5-b91e-59d8e5f402e5"
EMAIL = "ragheed@test.com"
PASSWORD = "Ragheed123!@#"


def _opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def fetch_csrf(opener: urllib.request.OpenerDirector) -> str:
    with opener.open(f"{API}/api/v1/identity/csrf-token", timeout=20) as resp:
        body = json.loads(resp.read().decode())
    return body.get("csrf_token") or ""


def login(opener: urllib.request.OpenerDirector) -> tuple[str, str]:
    csrf = fetch_csrf(opener)
    data = json.dumps({"email": EMAIL, "password": PASSWORD}).encode()
    req = urllib.request.Request(
        f"{API}/api/v1/identity/login",
        data=data,
        headers={"Content-Type": "application/json", "X-CSRF-Token": csrf},
        method="POST",
    )
    with opener.open(req, timeout=40) as resp:
        body = json.loads(resp.read().decode())
    return body["access_token"], fetch_csrf(opener)


def api_post(
    opener: urllib.request.OpenerDirector,
    path: str,
    token: str,
    csrf: str,
    payload: dict,
    timeout: float = 120,
) -> tuple[float, dict]:
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-CSRF-Token": csrf,
    }
    req = urllib.request.Request(f"{API}{path}", data=body, headers=headers, method="POST")
    t0 = time.time()
    with opener.open(req, timeout=timeout) as resp:
        return time.time() - t0, json.loads(resp.read().decode())


def api_get(
    opener: urllib.request.OpenerDirector, path: str, token: str, csrf: str
) -> tuple[float, dict | list]:
    headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf}
    req = urllib.request.Request(f"{API}{path}", headers=headers, method="GET")
    t0 = time.time()
    with opener.open(req, timeout=60) as resp:
        return time.time() - t0, json.loads(resp.read().decode())


def extract_fit(blob: str) -> str:
    for label in ("HIGH", "MEDIUM", "LOW", "UNKNOWN"):
        if f'"fit_level": "{label}"' in blob or f'"fit": "{label}"' in blob:
            return label
        if label in blob and "fit" in blob.lower():
            return label
    return "UNKNOWN"


def main() -> int:
    results: dict[str, dict] = {}
    opener = _opener()
    try:
        token, csrf = login(opener)
    except Exception as exc:
        print(json.dumps({"error": f"login failed: {exc}"}))
        return 1

    # Probe A — ICP fit for pif tenant
    try:
        lat, res = api_post(
            opener,
            "/api/v1/copilot/query",
            token,
            csrf,
            {
                "query": "icp evaluate recommend",
                "goal": "icp evaluate recommend",
                "company_id": CO_PIF,
                "company_name": "pif",
            },
        )
        blob = json.dumps(res)
        fit = extract_fit(blob)
        results["probe_a"] = {
            "status": "PASS" if fit not in ("UNKNOWN",) else "PARTIAL",
            "latency_s": round(lat, 2),
            "fit": fit,
            "excerpt": blob[:600],
        }
    except urllib.error.HTTPError as exc:
        results["probe_a"] = {"status": "FAIL", "http": exc.code, "body": exc.read().decode()[:400]}

    # Probe B — entity-confusion / cross-tenant bait name
    try:
        lat, res = api_post(
            opener,
            "/api/v1/copilot/query",
            token,
            csrf,
            {
                "query": "icp evaluate",
                "goal": "icp evaluate",
                "company_id": CO_PIF,
                "company_name": "Curl Search Co",
            },
        )
        blob = json.dumps(res)
        insufficient = "INSUFFICIENT" in blob.upper()
        results["probe_b"] = {
            "status": "PASS" if not insufficient else "WARN",
            "latency_s": round(lat, 2),
            "insufficient_evidence": insufficient,
            "excerpt": blob[:500],
        }
    except urllib.error.HTTPError as exc:
        results["probe_b"] = {"status": "FAIL", "http": exc.code, "body": exc.read().decode()[:400]}

    # Probe C — signal catalog + subscriptions feed (API layer)
    try:
        lat, catalog = api_get(opener, "/api/v1/signals", token, csrf)
        count = len(catalog) if isinstance(catalog, list) else catalog.get("total", 0)
        results["probe_c_catalog"] = {
            "status": "PASS" if count >= 3 else "WARN",
            "latency_s": round(lat, 2),
            "signal_count": count,
        }
        # subscribe to first signal with triggers
        sig_id = None
        items = catalog if isinstance(catalog, list) else catalog.get("items", [])
        for s in items:
            if isinstance(s, dict) and s.get("id"):
                sig_id = s.get("id")
                if s.get("domain") in ("construction", "regulatory"):
                    break
        if sig_id:
            lat2, sub = api_post(
                opener,
                "/api/v1/signals/subscribe",
                token,
                csrf,
                {"signal_id": sig_id, "company_id": CO_PIF},
            )
            lat3, feed = api_get(opener, f"/api/v1/signals/feed?company_id={CO_PIF}", token, csrf)
            feed_n = len(feed) if isinstance(feed, list) else feed.get("total", 0)
            results["probe_c"] = {
                "status": "PASS",
                "signal_id": sig_id,
                "subscribe_latency_s": round(lat2, 2),
                "feed_latency_s": round(lat3, 2),
                "feed_items": feed_n,
                "subscribe": sub,
            }
        else:
            results["probe_c"] = {"status": "SKIP", "detail": "no construction signal in catalog"}
    except urllib.error.HTTPError as exc:
        results["probe_c"] = {"status": "FAIL", "http": exc.code, "body": exc.read().decode()[:400]}
    except Exception as exc:
        results["probe_c"] = {"status": "FAIL", "error": str(exc)}

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
