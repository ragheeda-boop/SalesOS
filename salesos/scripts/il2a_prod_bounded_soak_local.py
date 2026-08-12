"""Local public-API bounded IL-2A soak. Reads SOAK_EMAIL/SOAK_PASS from env."""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

try:
    import httpx
except ImportError:
    import urllib.request
    import urllib.error

    httpx = None

API = os.environ.get("SOAK_API", "https://salesos-production-96c0.up.railway.app")
EMAIL = os.environ["SOAK_EMAIL"]
PASSWORD = os.environ["SOAK_PASS"]

ACTIONABLE = {
    "recommend_demo", "recommend_call", "recommend_proposal", "recommend_sequence",
    "recommend_outreach", "recommend_campaign", "recommend_escalate",
}
NON_ACTIONABLE = {"alert", "task_suggested", "workflow_suggested", "crm_update"}


def utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def should_create(dtype: str) -> bool:
    return (dtype or "").lower() in ACTIONABLE


def main() -> int:
    ev = {
        "timestamp": utc(),
        "scope": "bounded_production_il2a_soak",
        "api": API,
        "not_staging_parity": True,
        "soak_complete_claim": False,
        "production_go_claim": False,
        "feature_ai_copilot_flipped": False,
        "alembic_upgrade_head": False,
        "cycles": [],
        "contract_checks": {
            "should_create_recommend_call": should_create("recommend_call"),
            "should_create_alert": should_create("alert"),
            "should_create_unknown": should_create("totally_unknown_type"),
            "pass": should_create("recommend_call") and not should_create("alert") and not should_create("unknown"),
        },
        "summary": {},
    }

    with httpx.Client(timeout=90.0) as client:
        login = client.post(
            f"{API}/api/v1/identity/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
        if login.status_code != 200:
            ev["error"] = f"login_{login.status_code}"
            ev["login_body"] = (login.text or "")[:200]
            print(json.dumps(ev, indent=2))
            return 1
        data = login.json()
        token = data["access_token"]
        tenant = data.get("tenant_id") or data.get("user", {}).get("tenant_id")
        ev["tenant_id_prefix"] = str(tenant)[:8]
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Tenant-ID": str(tenant),
        }

        # companies — try list endpoints
        company_ids = []
        for path in (
            "/api/v1/companies?limit=10",
            "/api/v1/crm/companies?limit=10",
            "/api/v1/search/companies?q=a&limit=10",
        ):
            r = client.get(f"{API}{path}", headers=headers)
            if r.status_code == 200:
                body = r.json()
                items = body if isinstance(body, list) else body.get("items") or body.get("data") or body.get("results") or []
                for it in items:
                    if isinstance(it, dict):
                        cid = it.get("id") or it.get("company_id")
                        if cid:
                            company_ids.append(str(cid))
                if company_ids:
                    ev["companies_source"] = path
                    break
        # fallback known from prior gate evidence prefixes — resolve via DB not available locally
        if len(company_ids) < 2:
            # seed from env CSV if provided
            extra = [x.strip() for x in os.environ.get("SOAK_COMPANY_IDS", "").split(",") if x.strip()]
            company_ids.extend(extra)
        company_ids = list(dict.fromkeys(company_ids))[:10]
        if len(company_ids) < 1:
            ev["error"] = "no_companies"
            print(json.dumps(ev, indent=2))
            return 1

        path = "/api/v1/decision-runtime/decision/evaluate"
        plan = [{"cid": company_ids[i % len(company_ids)], "label": f"cycle-{i+1}"} for i in range(6)]
        plan += [
            {"cid": company_ids[0], "label": "idempotency-1"},
            {"cid": company_ids[0], "label": "idempotency-2"},
        ]

        decision_ids = []
        for step in plan:
            cid = step["cid"]
            cr = client.get(f"{API}/api/v1/identity/csrf-token")
            csrf = (cr.json() or {}).get("csrf_token")
            h = {**headers, "X-CSRF-Token": csrf or "", "X-Request-ID": f"soak-{uuid.uuid4()}"}
            t0 = time.perf_counter()
            r = client.post(f"{API}{path}", headers=h, json={"company_id": cid})
            if r.status_code == 404:
                path = "/api/v1/decision/evaluate"
                r = client.post(f"{API}{path}", headers=h, json={"company_id": cid})
            ms = round((time.perf_counter() - t0) * 1000, 1)
            body = {}
            try:
                body = r.json()
            except Exception:
                body = {"raw": (r.text or "")[:240]}
            did = body.get("decision_id") or body.get("decisionId") or body.get("id")
            dtype = body.get("decision_type") or body.get("type") or body.get("action")
            if did:
                decision_ids.append(str(did))
            ev["cycles"].append({
                "label": step["label"],
                "company_id_prefix": cid[:8],
                "http_status": r.status_code,
                "latency_ms": ms,
                "decision_id_prefix": (str(did)[:8] if did else None),
                "decision_type": dtype,
                "contract_expects_agent_task": should_create(str(dtype or "")),
                "ok": r.status_code == 200,
                "body_keys": sorted(list(body.keys()))[:12] if isinstance(body, dict) else [],
            })
            time.sleep(1.5)

        ev["evaluate_path"] = path
        ev["decision_ids_count"] = len(decision_ids)

        # AgentTask verification via SSH-less: call agent tasks API if present
        task_snapshots = []
        for cid in list(dict.fromkeys([p["cid"] for p in plan]))[:5]:
            for tp in (
                f"/api/v1/agent-runtime/tasks?entity_id={cid}&limit=5",
                f"/api/v1/agents/tasks?entity_id={cid}&limit=5",
                f"/api/v1/agent/tasks?company_id={cid}&limit=5",
            ):
                cr = client.get(f"{API}/api/v1/identity/csrf-token")
                csrf = (cr.json() or {}).get("csrf_token")
                tr = client.get(
                    f"{API}{tp}",
                    headers={**headers, "X-CSRF-Token": csrf or ""},
                )
                if tr.status_code == 200:
                    task_snapshots.append({"company_id_prefix": cid[:8], "path": tp, "body": tr.json()})
                    break
                if tr.status_code != 404:
                    task_snapshots.append({"company_id_prefix": cid[:8], "path": tp, "status": tr.status_code})
                    break
        ev["task_api_snapshots"] = task_snapshots

    types = sorted({c.get("decision_type") for c in ev["cycles"] if c.get("decision_type")})
    idem = [c for c in ev["cycles"] if str(c.get("label")).startswith("idempotency")]
    ev["summary"] = {
        "cycles_total": len(ev["cycles"]),
        "cycles_http_200": sum(1 for c in ev["cycles"] if c.get("ok")),
        "decision_types_seen": types,
        "actionable_cycles": sum(1 for c in ev["cycles"] if c.get("contract_expects_agent_task")),
        "non_actionable_cycles": sum(
            1 for c in ev["cycles"]
            if c.get("decision_type") and (c.get("decision_type") or "").lower() in NON_ACTIONABLE
        ),
        "idempotency_cycles": len(idem),
        "contract_checks_pass": ev["contract_checks"]["pass"],
        "validation_label": "light validated",
        "claims": {
            "staging_parity_complete": False,
            "wave11_48h_soak_complete": False,
            "production_go": False,
            "bounded_prod_il2a_soak": True,
        },
    }
    print(json.dumps(ev, indent=2, default=str))
    return 0 if ev["summary"]["cycles_http_200"] >= 5 else 2


if __name__ == "__main__":
    if httpx is None:
        print("httpx required", file=sys.stderr)
        sys.exit(1)
    raise SystemExit(main())
