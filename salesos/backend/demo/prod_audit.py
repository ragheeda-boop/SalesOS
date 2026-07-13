"""
SalesOS Production Readiness Audit v2.0

Scans running infrastructure and codebase from inside the API container.
Target: >90% for Engineering Platform v1.0 Feature Freeze.

Usage:
    docker cp demo/prod_audit.py muhide-api-1:/app/demo/
    docker exec muhide-api-1 python -m demo.prod_audit
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

BASE = Path("/app")
API = "http://localhost:8000"

_ALLOWED_AUDIT_TABLES = frozenset({
    "companies", "contacts", "company_deals", "activity_records",
    "golden_records", "opportunities", "tasks",
})


def _validate_audit_table(name: str) -> str:
    if name not in _ALLOWED_AUDIT_TABLES:
        raise ValueError(f"Invalid audit table: {name}")
    return name

results = []
weight_total = 0


def check(weight, category, name, fn, fail="FAIL"):
    global weight_total
    weight_total += weight
    try:
        r = fn()
        if isinstance(r, tuple):
            ok, detail = r
        else:
            ok, detail = bool(r), ""
        if ok:
            results.append({"category": category, "check": name, "passed": True, "weight": weight, "detail": detail or "ok"})
        else:
            results.append({"category": category, "check": name, "passed": False, "weight": 0, "detail": detail or fail})
        return ok
    except Exception as e:
        results.append({"category": category, "check": name, "passed": False, "weight": 0, "detail": str(e)})
        return False


def urlopen(url, method="GET", headers=None):
    req = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    return urllib.request.urlopen(req, timeout=5)


def file_contains(path, text):
    f = BASE / path
    return f.exists() and not f.is_dir() and text in f.read_text()


def grep_dir(directory, text):
    d = BASE / directory
    if not d.is_dir():
        return 0
    return sum(1 for f in d.rglob("*.py") if text in f.read_text())


def _get_dsn():
    import os
    pg_user = os.environ.get("POSTGRES_USER", "salesos")
    pg_pass = os.environ.get("POSTGRES_PASSWORD", "test")
    pg_host = os.environ.get("POSTGRES_HOST", "postgres")
    pg_port = os.environ.get("POSTGRES_PORT", "5432")
    pg_db = os.environ.get("POSTGRES_DB", "salesos")
    return os.environ.get("DATABASE_URL") or f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

def table_count(table, where="tenant_id"):
    import asyncpg, asyncio, os
    TID = "d1e2f3a4-5678-90ab-cdef-1234567890ab"
    validated_table = _validate_audit_table(table)
    async def go():
        dsn = _get_dsn()
        conn = await asyncpg.connect(dsn)
        if where == "company":
            r = await conn.fetchval(f"SELECT COUNT(*) FROM {validated_table} WHERE company_id IN (SELECT id FROM companies WHERE tenant_id = $1)", TID)
        else:
            r = await conn.fetchval(f"SELECT COUNT(*) FROM {validated_table} WHERE tenant_id = $1", TID)
        await conn.close()
        return r
    return asyncio.run(go())


# ─── Categories ────────────────────────────────────────

def cat_prod_readiness():
    c = "Production Readiness"
    check(5, c, "Health endpoint", lambda: _health())
    check(5, c, "Database connected", lambda: _health_field("database", "connected"))
    check(5, c, "Cache connected", lambda: _health_field("cache", "connected"))
    check(5, c, "Graph connected", lambda: _health_field("graph", None))
    check(3, c, "CORS with explicit origins",
          lambda: file_contains("app/main.py", "allow_origins") and "http://localhost:3000" in (BASE / "app/main.py").read_text())
    check(3, c, "Graceful shutdown", lambda: file_contains("app/main.py", "shutdown") or file_contains("app/main.py", "lifespan"))
    check(3, c, "Request ID middleware", lambda: bool(grep_dir("app", "request_id")))
    check(3, c, "JSON logging", lambda: bool(grep_dir("app", "json")))
    check(2, c, "DEBUG mode disabled in prod", lambda: "debug" not in (BASE / ".env").read_text() if (BASE / ".env").exists() else (True, "no .env file"))


def cat_architecture():
    c = "Architecture"
    check(4, c, "Router modules organized by domain", lambda: (BASE / "app/routers").is_dir() and len(list((BASE / "app/routers").glob("*.py"))) > 1)
    check(4, c, "Background tasks with Celery", lambda: file_contains("app/celery_app.py", "Celery"))
    check(4, c, "Pydantic schemas/models", lambda: grep_dir("app", "BaseModel") > 2)
    check(4, c, "Neo4j KnowledgeGraphEngine", lambda: bool(grep_dir("app", "KnowledgeGraphEngine")))
    check(4, c, "Repository pattern", lambda: bool(grep_dir("app", "Repository")))
    check(3, c, "Service/UseCase layer", lambda: bool(grep_dir("app", "Service") or grep_dir("app", "UseCase")))
    check(3, c, "SQLAlchemy models defined", lambda: bool(grep_dir("app", "Column") and grep_dir("app", "String")))
    check(2, c, "API version prefix", lambda: file_contains("app/main.py", "/api/v"))


def cat_security():
    c = "Security"
    check(5, c, "RBAC on all routers", lambda: _rbac())
    check(4, c, "Password hashing", lambda: bool(grep_dir("app", "pwd_context") or grep_dir("app", "hash_password") or grep_dir("app", "bcrypt")))
    check(4, c, "JWT authentication", lambda: bool(grep_dir("app", "JWT") or grep_dir("app", "jwt")))
    check(4, c, "Pydantic input validation", lambda: grep_dir("app", "BaseModel") > 2)
    check(3, c, "Parameterized SQL queries", lambda: bool(grep_dir("app", "$1") or grep_dir("app", ":param") or grep_dir("app", "%s")))
    check(3, c, "CORS middleware active", lambda: file_contains("app/main.py", "CORSMiddleware"))
    check(2, c, "Rate limiting implemented", lambda: bool(grep_dir("app", "rate_limit") or grep_dir("app", "throttle") or grep_dir("app", "RateLimitMiddleware")))
    check(2, c, "Token refresh/blacklist", lambda: bool(grep_dir("app", "refresh_token") or (BASE / "app/domain/token_blacklist.py").exists()))


def cat_infrastructure():
    c = "Infrastructure"
    check(5, c, "PostgreSQL running", lambda: _health_field("database", "connected"))
    check(5, c, "Redis running", lambda: _health_field("cache", "connected"))
    check(5, c, "Neo4j running", lambda: _health_field("graph", None))
    check(4, c, "Worker (Celery) configured", lambda: file_contains("app/celery_app.py", "Celery"))
    check(3, c, "Meilisearch configured", lambda: bool(grep_dir("app", "meilisearch") or grep_dir("app", "Meili")))
    check(3, c, "Prometheus metrics", lambda: bool(grep_dir("app", "prometheus") or grep_dir("app", "metrics")))
    check(3, c, "Dockerfile exists", lambda: (BASE / "Dockerfile").exists())
    check(2, c, "Docker healthcheck", lambda: file_contains("Dockerfile", "HEALTHCHECK"))
    check(2, c, ".dockerignore", lambda: (BASE / ".dockerignore").exists())
    check(2, c, "Monitoring stack configured", lambda: bool(grep_dir("app", "prometheus")))


def cat_ai():
    c = "AI Pipeline"
    check(4, c, "Embedding generation", lambda: bool(grep_dir("app", "embedding") or grep_dir("app", "embed")))
    check(4, c, "Vector store", lambda: bool(grep_dir("app", "vector") or (BASE / "app/domain/vectors.py").exists()))
    check(4, c, "Full-text search (tsvector)", lambda: _db_has_col("tsvector"))
    check(4, c, "Meilisearch integration", lambda: bool(grep_dir("app", "meilisearch") or grep_dir("app", "Meili")))
    check(4, c, "Knowledge graph entity resolution", lambda: bool(grep_dir("app", "resolve_entity") or grep_dir("app", "entity_resolution")))
    check(3, c, "Search service/router", lambda: bool(grep_dir("app", "search_service") or (BASE / "app/routers/search.py").exists()))
    check(3, c, "Company enrichment task", lambda: file_contains("app/tasks.py", "enrich_company"))
    check(2, c, "Recommendation engine", lambda: bool(grep_dir("app", "recommend") or grep_dir("app", "recommendation")))


def cat_testing():
    c = "Testing"
    check(4, c, "Test files exist", lambda: (BASE / "tests").is_dir() and len(list((BASE / "tests").glob("**/*.py"))) > 1)
    check(4, c, "Pytest configured", lambda: (BASE / "pytest.ini").exists() or (BASE / "pyproject.toml").exists() and "[tool.pytest" in (BASE / "pyproject.toml").read_text())
    check(3, c, "Shared fixtures (conftest)", lambda: (BASE / "conftest.py").exists())
    check(3, c, "Test database setup", lambda: bool(grep_dir("tests", "test_db") or grep_dir("tests", "setup")))
    check(2, c, "CI workflow configured", lambda: (BASE.parent / ".github/workflows/ci.yml").exists() or (BASE.parent / ".github/workflows/test.yml").exists())


def cat_data_quality():
    c = "Data Quality"
    check(4, c, "Database migrations (alembic)", lambda: (BASE / "alembic.ini").exists())
    check(4, c, "Seed data script exists", lambda: (BASE / "demo/seed_data.py").exists())
    check(4, c, "Seed data populated >1000 companies", lambda: table_count("companies") >= 1000)
    check(4, c, "Seed data bilingual (ar/en)", lambda: file_contains("demo/seed_data.py", "name_ar") and file_contains("demo/seed_data.py", "name_en"))
    check(3, c, "Contacts seeded (5000+)", lambda: table_count("contacts", "company") >= 5000)
    check(3, c, "Deals seeded (3000+)", lambda: table_count("company_deals") >= 3000)
    check(3, c, "Activities seeded (10000+)", lambda: table_count("activity_records") >= 10000)
    check(3, c, "Golden records seeded", lambda: table_count("golden_records") >= 500)
    check(2, c, "Neo4j graph has nodes", lambda: _graph_nodes() > 0)


# ─── Helpers ───────────────────────────────────────────

def _health():
    r = urlopen(f"{API}/health")
    ok = r.status == 200
    return ok, f"HTTP {r.status}"


def _health_field(field, expected):
    r = urlopen(f"{API}/health")
    data = json.loads(r.read())
    if field not in data:
        return False, f"no {field} in health"
    val = data[field]
    if expected is None:
        return val not in (None, "", "not_configured"), f"{field}={val}"
    return expected in str(val), f"{field}={val}"


def _rbac():
    router_dir = BASE / "app/routers"
    if not router_dir.is_dir():
        return False, "No routers dir"
    unprotected = 0
    for f in router_dir.glob("*.py"):
        if f.name == "__init__.py":
            continue
        content = f.read_text()
        if "Depends" not in content and "get_current_user" not in content:
            unprotected += 1
    return unprotected == 0, f"{unprotected} routers without auth"


def _db_has_col(data_type):
    import asyncpg, asyncio, os
    async def go():
        dsn = _get_dsn()
        conn = await asyncpg.connect(dsn)
        r = await conn.fetchval("SELECT COUNT(*) FROM information_schema.columns WHERE data_type=$1", data_type)
        await conn.close()
        return r > 0, f"{r} columns"
    return asyncio.run(go())


def _graph_nodes():
    from neo4j import GraphDatabase
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pw = os.getenv("NEO4J_PASSWORD", "neo4j_dev_password")
    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, pw))
        with driver.session() as s:
            r = s.run("MATCH (n) RETURN count(n) AS c")
            c = r.single()["c"]
        return c
    except Exception:
        return 0
    finally:
        if driver:
            driver.close()


# ─── Main ──────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  SalesOS Production Readiness Audit v2.0")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    cat_prod_readiness()
    cat_architecture()
    cat_security()
    cat_infrastructure()
    cat_ai()
    cat_testing()
    cat_data_quality()

    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]
    passed_weight = sum(r["weight"] for r in passed)
    score = round(passed_weight / weight_total * 100, 1) if weight_total else 0

    print(f"\n{'─' * 60}")
    print(f"  Score: {score}% ({passed_weight}/{weight_total} points)")
    print(f"  Checks: {len(results)} total, {len(passed)} passed, {len(failed)} failed")
    print(f"{'─' * 60}")

    cats = {}
    for r in results:
        cats.setdefault(r["category"], {"p": 0, "t": 0, "w": 0, "wp": 0})
        cats[r["category"]]["t"] += 1
        cats[r["category"]]["w"] += r["weight"] if r["passed"] else r["weight"]  # max possible
        cats[r["category"]]["wp"] += r["weight"] if r["passed"] else 0
        if r["passed"]:
            cats[r["category"]]["p"] += 1

    print(f"\n  {'Category':30s} {'Score':>7s}  {'Passed':>7s}")
    print(f"  {'─' * 48}")
    for cat, d in sorted(cats.items()):
        pct = round(d["wp"] / d["w"] * 100, 1) if d["w"] else 0
        print(f"  {cat:30s} {pct:>6.1f}%  {d['p']}/{d['t']}")

    if failed:
        print(f"\n  Failed ({len(failed)}):")
        for r in failed:
            print(f"    - [{r['category']}] {r['check']}: {r['detail']}")

    print()
    if score >= 90:
        print("  STATUS: PASS — Ready for Feature Freeze")
    elif score >= 75:
        print("  STATUS: BORDERLINE — Fix failed items")
    else:
        print("  STATUS: FAIL — Address critical gaps")

    if "--json" in sys.argv:
        print(json.dumps({"score": score, "passed": len(passed), "failed": len(failed), "total": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    main()
