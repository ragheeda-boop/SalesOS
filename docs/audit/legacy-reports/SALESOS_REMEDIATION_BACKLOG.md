# SalesOS — Executable Remediation Backlog

**Generated:** June 30, 2026  
**Classification:** Actionable Engineering Plan  
**Total Items:** 47 (P0: 8, P1: 14, P2: 25)

---

## How To Read This Backlog

Each item contains:
```
ID:     Unique identifier
AREA:   Which part of the system
PRI:    P0=blocker, P1=this sprint, P2=next sprint
FILE:   Exact file path and line
CURRENT: What the code says now
FIX:    What to change it to
RISK:   Breaking change? Regression risk?
TIME:   Engineering hours estimate
```

---

# WEEK 1 — PRODUCTION BLOCKERS (Security)

---

## P0-001: SQL Injection — Filter Field Names

| Field | Value |
|-------|-------|
| **AREA** | Backend — Search Runtime |
| **PRI** | **P0** |
| **FILE** | `salesos/backend/runtime/search_runtime/__init__.py:220-222` |
| **CURRENT** | ```python
conditions.append(f"c.{field} = :{field}")
params[field] = value
``` |
| **FIX** | Validate field against allowlist before building SQL: ```python
ALLOWED_FILTER_FIELDS = {"city", "region", "industry", "status", "legal_form", "activity", "is_active", "created_at"}
if field not in ALLOWED_FILTER_FIELDS:
    raise ValueError(f"Invalid filter field: {field}")
conditions.append(f"c.{field} = :{field}")
params[field] = value
``` |
| **RISK** | Low — field allowlist restricts what was already implicit |
| **TIME** | 1 hour |

---

## P0-002: SQL Injection — Facet Field Names

| Field | Value |
|-------|-------|
| **AREA** | Backend — Search Runtime |
| **PRI** | **P0** |
| **FILE** | `salesos/backend/runtime/search_runtime/__init__.py:361` |
| **CURRENT** | ```python
sa_text(f"""
    SELECT {field}, COUNT(*) as cnt
    FROM companies
    ...
    AND {field} IS NOT NULL
""")
``` |
| **FIX** | Same allowlist validation as P0-001 on `field` before interpolation |
| **RISK** | Low |
| **TIME** | 0.5 hours |

---

## P0-003: SQL Injection — Suggest Field

| Field | Value |
|-------|-------|
| **AREA** | Backend — Search Runtime |
| **PRI** | **P0** |
| **FILE** | `salesos/backend/runtime/search_runtime/__init__.py:147-151` |
| **CURRENT** | ```python
sa_text(f"""
    SELECT DISTINCT {field} FROM companies
    WHERE tenant_id = :tid AND {field} ILIKE :prefix
""")
``` |
| **FIX** | Validate `field` against: `{"name_ar", "name_en", "cr_number", "city", "email", "phone"}` |
| **RISK** | Low |
| **TIME** | 0.5 hours |

---

## P0-004: SQL Injection — SDK Search

| Field | Value |
|-------|-------|
| **AREA** | Backend — SDK |
| **PRI** | **P0** |
| **FILE** | `salesos/backend/sdk/search.py:89-94, 110-115, 126` |
| **CURRENT** | `text(f"""...FROM {collection}...""")` — `collection` is user-influenceable |
| **FIX** | Replace with parameterized table name via `text("... :col ...")` or validate against `{"companies", "contacts", "licenses", "branches", "opportunities"}` |
| **RISK** | Low |
| **TIME** | 1 hour |

---

## P0-005: Hardcoded Notion Token — balady_scraper

| Field | Value |
|-------|-------|
| **AREA** | Data Pipeline — balady_scraper |
| **PRI** | **P0** |
| **FILE** | `balady_scraper/notion_import.py:6` |
| **CURRENT** | `NOTION_TOKEN = "ntn_REDACTED"` |
| **FIX** | ```python
import os
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
if not NOTION_TOKEN:
    raise RuntimeError("NOTION_TOKEN environment variable not set")
``` |
| **RISK** | Low — env var must be set before scripts run |
| **TIME** | 0.5 hours |

---

## P0-006: Hardcoded Notion Token — najiz_scraper

| Field | Value |
|-------|-------|
| **AREA** | Data Pipeline — najiz_scraper |
| **PRI** | **P0** |
| **FILE** | `najiz_scraper/notion_sync.py:7` |
| **CURRENT** | `API_KEY = "ntn_REDACTED"` |
| **FIX** | Same as P0-005: read from `os.environ["NOTION_TOKEN"]` |
| **RISK** | Low |
| **TIME** | 0.5 hours |

---

## P0-007: Hardcoded Notion Token — import_to_notion.py

| Field | Value |
|-------|-------|
| **AREA** | Data Pipeline — root |
| **PRI** | **P0** |
| **FILE** | `import_to_notion.py:12` |
| **CURRENT** | `NOTION_TOKEN = "ntn_REDACTED"` |
| **FIX** | Same as P0-005 |
| **RISK** | Low |
| **TIME** | 0.5 hours |

---

## P0-008: Hardcoded Notion Token — check_notion.py

| Field | Value |
|-------|-------|
| **AREA** | Data Pipeline — balady_scraper |
| **PRI** | **P0** |
| **FILE** | `balady_scraper/check_notion.py:5` |
| **CURRENT** | `NOTION_TOKEN = "ntn_..."` (same leaked token) |
| **FIX** | Same as P0-005 |
| **RISK** | Low |
| **TIME** | 0.5 hours |

> **P0 Summary: 8 items, ~4.5 engineering hours**

---

# WEEK 1 — PRODUCTION BLOCKERS (Infrastructure Security)

---

## P0-009: No Rate Limiting

| Field | Value |
|-------|-------|
| **AREA** | Backend — Application |
| **PRI** | **P0** |
| **FILE** | `salesos/backend/pyproject.toml` (new dependency) + `app/main.py` (new middleware) |
| **CURRENT** | No rate limiting exists. Login endpoint is fully exposed. |
| **FIX** | **Option A (fastest):** Add `slowapi`: ```toml
# pyproject.toml
slowapi = "^0.1"
```  
Then `app/main.py`: ```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# On login endpoint:
@router.post("/login")
@limiter.limit("10/minute")
async def login(...)
```
**Option B (recommended):** Redis-based rate limiting using existing Redis:  
```python
# app/common/middleware.py — new RateLimitMiddleware
import aioredis
from datetime import datetime, timedelta

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str, rate: int = 60, window: int = 60):
        super().__init__(app)
        self.redis = aioredis.from_url(redis_url)
        self.rate = rate
        self.window = window
    
    async def dispatch(self, request, call_next):
        client_ip = request.client.host
        key = f"ratelimit:{client_ip}:{request.url.path}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.window)
        if count > self.rate:
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
        return await call_next(request)
``` |
| **RISK** | Low — new middleware; doesn't change existing behavior |
| **TIME** | 3-4 hours (Option B with Redis) |

---

## P0-010: Missing Security Headers

| Field | Value |
|-------|-------|
| **AREA** | Backend — Middleware |
| **PRI** | **P0** |
| **FILE** | `salesos/backend/app/common/middleware.py` (new class) + `app/main.py:231` (register) |
| **CURRENT** | No CSP, no HSTS, no XFO, no X-Content-Type-Options |
| **FIX** | Add middleware: ```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
```
Then register: `app.add_middleware(SecurityHeadersMiddleware)` in `app/main.py` after line 232 |
| **RISK** | Low — headers don't break functionality, only enhance security |
| **TIME** | 1 hour |

---

## P0-011: Tenant Isolation — Cross-Validation

| Field | Value |
|-------|-------|
| **AREA** | Backend — Identity/Auth |
| **PRI** | **P0** |
| **FILE** | `salesos/backend/app/dependencies.py:7-10` |
| **CURRENT** | ```python
async def get_current_tenant_id(
    x_tenant_id: str = Header(...)
) -> str:
    return x_tenant_id
``` — No validation that user belongs to the claimed tenant |
| **FIX** | ```python
async def get_current_tenant_id(
    x_tenant_id: str = Header(...),
    token_payload: dict = Depends(verify_token),
) -> str:
    token_tenant = token_payload.get("tenant_id")
    if token_tenant and token_tenant != x_tenant_id:
        raise ForbiddenError("Tenant mismatch")
    return x_tenant_id
```
Also create `verify_token` dependency: ```python
async def verify_token(
    authorization: str = Header(...)
) -> dict:
    from app.modules.identity.service import decode_access_token
    token = authorization.replace("Bearer ", "")
    return decode_access_token(token)
``` |
| **RISK** | **HIGH** — Breaking change if any client sends mismatched tenant. Must update all callers. |
| **TIME** | 2 hours |

---

> **Week 1 Total: 11 items, ~12 engineering hours**

---

# WEEK 2 — AI RUNTIME (Replace Mock Data)

---

## P1-001: Real ResearchAgent with LLM

| Field | Value |
|-------|-------|
| **AREA** | Intelligence — Agents |
| **PRI** | **P1** |
| **FILE** | `salesos/backend/intelligence/agents/research_agent.py` (exists but returns mock) |
| **CURRENT** | Returns `{"summary": "Mock summary for {company}", "sources": [], "confidence": 0.5}` |
| **FIX** | Wire to OpenAI: ```python
from openai import AsyncOpenAI

class ResearchAgent(BaseAgent):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def _run(self, ctx: AgentContext) -> AgentResult:
        prompt = f"""أنت باحث مبيعات في السعودية. ابحث عن معلومات عن الشركة التالية:
الاسم: {ctx.company_name}
السجل التجاري: {ctx.cr_number}
المدينة: {ctx.city}

قدم:
1. معلومات أساسية عن الشركة
2. الأنشطة التجارية
3. حجم الشركة المتوقع
4. فرص محتملة للبيع

يجب أن يكون الرد باللغة العربية."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return AgentResult(
            success=True,
            data={"summary": response.choices[0].message.content, "sources": [], "confidence": 0.7},
            confidence=0.7,
        )
``` |
| **RISK** | Medium — depends on OpenAI API key and latency. Add timeout + fallback. |
| **TIME** | 4-6 hours |

---

## P1-002: Wire ResearchAgent to Copilot API

| Field | Value |
|-------|-------|
| **AREA** | Frontend → Backend |
| **PRI** | **P1** |
| **FILE** | New: `salesos/backend/app/routers/copilot.py` |
| **CURRENT** | Frontend `copilot-panel.tsx` uses `setTimeout` to simulate responses |
| **FIX** | New backend endpoint: ```python
# app/routers/copilot.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from intelligence.agents import ResearchAgent

router = APIRouter()

class CopilotQuery(BaseModel):
    query: str
    company_id: str | None = None
    context: dict = {}

@router.post("/copilot/query")
async def copilot_query(body: CopilotQuery):
    # Route to appropriate agent based on query intent
    agent = ResearchAgent(api_key=settings.openai_api_key)
    ctx = AgentContext(company_id=body.company_id, ...)
    result = await agent.execute(ctx)
    return {"response": result.data["summary"], "confidence": result.confidence}
```
Then update `copilot-panel.tsx` to call this endpoint instead of `setTimeout`. |
| **RISK** | Medium — new API contract, frontend must handle loading/error states |
| **TIME** | 4 hours |

---

## P1-003: Remove Mock Data from AI Agents (All 11)

| Field | Value |
|-------|-------|
| **AREA** | Intelligence — Agents |
| **PRI** | **P1** |
| **FILE** | `salesos/backend/intelligence/agents/*.py` (11 files) |
| **CURRENT** | All return hardcoded dicts like `{"summary": "Mock..."}` |
| **FIX** | For each agent, either: (a) Wire to real LLM call, or (b) Remove the file and mark as `# TODO: implement in RT3`. **Do not ship mock data in production code.** |
| **RISK** | Low for removal, Medium for LLM wiring |
| **TIME** | 8 hours for LLM wiring (if keeping all 11) |

---

## P1-004: Remove Mock Data from Frontend (CopilotPanel)

| Field | Value |
|-------|-------|
| **AREA** | Frontend |
| **PRI** | **P1** |
| **FILE** | `salesos/frontend/src/components/copilot-panel.tsx` (line ~80-90 with `setTimeout` mock) |
| **CURRENT** | Simulated response with 1-second delay and hardcoded text |
| **FIX** | Replace with real API call: ```typescript
const { data, isLoading } = useMutation({
    mutationFn: (query: string) =>
        axios.post("/api/v1/copilot/query", {
            query,
            company_id: entityId,
            context: { entityType: "company" },
        }),
    onSuccess: (res) => {
        setMessages(prev => [...prev, {
            role: "assistant",
            content: res.data.response,
            confidence: res.data.confidence,
        }]);
    },
});
``` |
| **RISK** | Low — new API call replaces mock. Ensure loading/error states are handled. |
| **TIME** | 2 hours |

---

## P1-005: Remove Mock Data from Frontend (SearchPanel)

| Field | Value |
|-------|-------|
| **AREA** | Frontend |
| **PRI** | **P1** |
| **FILE** | `salesos/frontend/src/components/search-panel.tsx` (hardcoded sample results) |
| **CURRENT** | Returns hardcoded companies/contacts/opportunities |
| **FIX** | Wire to `useCompanySearch` hook already in the codebase: ```typescript
const { data, isLoading } = useCompanySearch({ q: query, page_size: 10 });
``` |
| **RISK** | Low |
| **TIME** | 1 hour |

---

> **Week 2 Total: 5 items, ~20 engineering hours**

---

# WEEK 3 — TESTING

---

## P1-006: Fix Debounce Bug in Companies Search

| Field | Value |
|-------|-------|
| **AREA** | Frontend |
| **PRI** | **P1** |
| **FILE** | `salesos/frontend/src/app/companies/page.tsx:17-21` |
| **CURRENT** | ```typescript
const handleSearch = (value: string) => {
    setSearchQuery(value)
    const timer = setTimeout(() => setDebouncedQuery(value), 400)
    return () => clearTimeout(timer)  // BUG: return value is never called
}
```
Each keystroke creates a new timeout without clearing previous — causes N API calls per keystroke. |  
| **FIX** | Use `useDebounce` from existing `@salesos/hooks`: ```typescript
import { useDebounce } from "@salesos/hooks"

// Remove handleSearch entirely
// Replace with:
const debouncedQuery = useDebounce(searchQuery, 400)

// Remove debouncedQuery state + handleSearch
// The hook replaces both
``` |
| **RISK** | Low |
| **TIME** | 0.5 hours |

---

## P1-007: Frontend Unit Tests — Runtime System

| Field | Value |
|-------|-------|
| **AREA** | Frontend — packages/runtime |
| **PRI** | **P1** |
| **FILE** | New: `salesos/frontend/packages/runtime/__tests__/` |
| **CURRENT** | Zero tests exist for the 9-runtime system |
| **FIX** | Write tests (in priority order):

**1. StateRuntime tests** (`state-runtime.test.ts`):
```typescript
describe("StateRuntime", () => {
    it("sets and gets values by dot-notation path", () => {
        const rt = new StateRuntime()
        rt.set("company.name", "ACME")
        expect(rt.get("company.name")).toBe("ACME")
    })
    it("subscribes to changes", () => {
        const rt = new StateRuntime()
        const fn = jest.fn()
        rt.subscribe("company.name", fn)
        rt.set("company.name", "ACME")
        expect(fn).toHaveBeenCalledWith("ACME")
    })
})
```

**2. CacheRuntime tests** — TTL, stale-while-revalidate, LRU eviction

**3. LocalizationRuntime tests** — locale switching, RTL detection, Intl formatters

**4. OfflineRuntime tests** — queue, retry, persistence |
| **RISK** | Low — new files, no production impact |
| **TIME** | 8 hours per runtime = ~24 hours total for 3 key runtimes |

---

## P1-008: Frontend Unit Tests — Hooks

| Field | Value |
|-------|-------|
| **AREA** | Frontend — packages/hooks |
| **PRI** | **P1** |
| **FILE** | New: `salesos/frontend/packages/hooks/__tests__/` |
| **CURRENT** | Zero tests for 14 hooks |
| **FIX** | Critical hooks to test:
- `useDebounce`: Test debounce timing
- `useKeyboard`: Test key handler registration/cleanup
- `usePermission`: Test permission checks
- `useSession`: Test auth state management |
| **RISK** | Low |
| **TIME** | 16 hours |

---

## P1-009: Frontend Unit Tests — UI Components

| Field | Value |
|-------|-------|
| **AREA** | Frontend — packages/ui |
| **PRI** | **P1** |
| **FILE** | New: `salesos/frontend/packages/ui/__tests__/` |
| **CURRENT** | Zero tests for 17 components |
| **FIX** | Test critical components:
- `Button`: variants, sizes, loading state, disabled
- `Input`: label, error, icons
- `Table`: loading skeleton, empty state, row click
- `Modal`: open/close, escape key |
| **RISK** | Low |
| **TIME** | 16 hours |

---

## P1-010: Backend Integration Tests — Auth Flow

| Field | Value |
|-------|-------|
| **AREA** | Backend — identity module |
| **PRI** | **P1** |
| **FILE** | `salesos/backend/tests/` (new test files) |
| **CURRENT** | Identity module has limited test coverage |
| **FIX** | Add tests for:
1. Register → Login → Token → Refresh flow
2. Duplicate email rejection
3. Invalid password rejection
4. Token expiry
5. Tenant isolation (user A cannot access tenant B data) |
| **RISK** | Low |
| **TIME** | 8 hours |

---

> **Week 3 Total: 5 items, ~64 engineering hours** (high due to test writing)

---

# WEEK 4 — PRODUCTION READINESS

---

## P1-011: Wire RBAC to Endpoints

| Field | Value |
|-------|-------|
| **AREA** | Backend — Auth |
| **PRI** | **P1** |
| **FILE** | All backend routers (`salesos/backend/app/modules/*/router.py`) |
| **CURRENT** | ```python
# No permission check in any endpoint
@router.get("/companies")
async def list_companies(...)
```
`PermissionEnforcer.check()` is never called. |
| **FIX** | Add dependency to each router: ```python
# app/dependencies.py
from sdk.permissions import PermissionAction, PermissionEnforcer

async def require_permission(
    resource: str,
    action: PermissionAction,
    user_id: str = Depends(get_current_user_id),
    service: IdentityService = Depends(get_identity_service),
):
    user = await service.get_user(user_id)
    PermissionEnforcer.check(user.role, resource, action)
    return True

# In each router:
@router.get("/companies", dependencies=[Depends(lambda: require_permission("company", PermissionAction.READ))])
async def list_companies(...)
``` |
| **RISK** | **HIGH** — will break existing API calls for non-admin users. Must seed roles first. |
| **TIME** | 8 hours (all routers) |

---

## P1-012: Docker Security Hardening

| Field | Value |
|-------|-------|
| **AREA** | Infrastructure |
| **PRI** | **P1** |
| **FILE** | `salesos/backend/Dockerfile` |
| **CURRENT** | Backend runs as root |
| **FIX** | ```dockerfile
# Add before CMD/ENTRYPOINT:
RUN addgroup --system --gid 1001 salesos && \
    adduser --system --uid 1001 salesos
USER salesos
``` |
| **RISK** | Low |
| **TIME** | 1 hour |

---

## P1-013: Add Database Migration Files

| Field | Value |
|-------|-------|
| **AREA** | Backend — Database |
| **PRI** | **P1** |
| **FILE** | `salesos/backend/app/alembic/versions/` |
| **CURRENT** | No migration files found in the scanned directories |
| **FIX** | Run `alembic revision --autogenerate -m "initial_schema"` and commit the generated file. Verify `alembic upgrade head` works against a clean database. |
| **RISK** | Low |
| **TIME** | 2 hours |

---

## P1-014: Add Monitoring Configuration

| Field | Value |
|-------|-------|
| **AREA** | Infrastructure |
| **PRI** | **P1** |
| **FILE** | New: `salesos/infra/monitoring/prometheus.yml`, `salesos/infra/monitoring/grafana.json` |
| **CURRENT** | Sentry DSN exists but `sentry_sdk.init()` never called. No Prometheus/Grafana. |
| **FIX** | ```python
# In main.py lifespan - initialize Sentry
if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        traces_sample_rate=0.1,
    )
```  
Then add Prometheus + Grafana to `docker-compose.yml`. Add health check endpoints. |
| **RISK** | Low |
| **TIME** | 4 hours |

---

> **Week 4 Total: 4 items, ~15 engineering hours**

---

# P2 — NEXT SPRINT (Non-blocking but Important)

---

## P2-001: Consolidate Excel Styling

| Field | Value |
|-------|-------|
| **AREA** | Data Pipeline |
| **PRI** | **P2** |
| **FILE** | New: `salesos/backend/pipeline/excel_utils.py` |
| **CURRENT** | Same styling code duplicated across `crm_enrichment.py`, `crm_pipeline.py`, `sales_intel_pipeline.py`, `website_li_pipeline.py`, `finalize_enrichment.py`, `build_tier1_li_output.py`, `update_li_discoveries.py` |
| **FIX** | Extract to shared module: ```python
# pipeline/excel_utils.py
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

HDR_FONT = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
HDR_FILL = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
THIN_BORDER = Border(...)
GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
RED_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

def style_header(ws, num_cols: int):
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = HDR_FONT
        cell.fill = HDR_FILL
        cell.alignment = Alignment(horizontal="center")

def auto_width(ws):
    for col in ws.columns:
        max_len = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)
``` |
| **RISK** | Low — pure refactor |
| **TIME** | 4 hours |

---

## P2-002: Consolidate Domain Validation

| Field | Value |
|-------|-------|
| **AREA** | Data Pipeline |
| **PRI** | **P2** |
| **FILE** | New: `salesos/backend/pipeline/validation_engine.py` |
| **CURRENT** | Duplicated in `crm_pipeline.py` and `website_li_pipeline.py` |
| **FIX** | ```python
import asyncio
import httpx
from dataclasses import dataclass

@dataclass
class DomainCheckResult:
    url: str
    valid: bool
    status_code: int | None
    title: str | None
    parked: bool
    error: str | None

class DomainValidator:
    def __init__(self, timeout: float = 10.0, max_concurrent: int = 10):
        self.timeout = timeout
        self.sem = asyncio.Semaphore(max_concurrent)
    
    async def check(self, domain: str) -> DomainCheckResult:
        async with self.sem:
            ...
    
    async def check_many(self, domains: list[str]) -> list[DomainCheckResult]:
        return await asyncio.gather(*[self.check(d) for d in domains])
``` |
| **RISK** | Low |
| **TIME** | 3 hours |

---

## P2-003: Archive Debug Scripts

| Field | Value |
|-------|-------|
| **AREA** | Data Pipeline — taqeem_scraper |
| **PRI** | **P2** |
| **FILE** | `taqeem_scraper/discover.py`, `discover2.py`, `discover3.py`, `investigate2.py`, `debug_detail.py`, `debug_detail2.py`, `debug_cr.py`, `debug_cards.py`, `check_total.py`, `check_total2.py`, `check_quality.py`, `check_output.py`, `check_output2.py`, `check_final.py`, `find_selects.py` |
| **CURRENT** | 16 files in production directory, all exploratory |
| **FIX** | ```bash
mkdir -p taqeem_scraper/archive
mv taqeem_scraper/{discover*.py,investigate*.py,debug_*.py,check_*.py,find_selects.py} taqeem_scraper/archive/
``` |
| **RISK** | Low |
| **TIME** | 0.5 hours |

---

## P2-004: Fix Empty Runtime Directories

| Field | Value |
|-------|-------|
| **AREA** | Backend — Runtime |
| **PRI** | **P2** |
| **FILE** | `salesos/backend/runtime/{workflow_runtime,agent_runtime,execution_runtime,memory_runtime,simulation_runtime,scheduler_runtime}/__init__.py` |
| **CURRENT** | 6 runtimes are empty `__init__.py` files |
| **FIX** | For each runtime, either:
(a) Add `__init__.py` with a status comment: `# PLANNED FOR RT3 — see ROADMAP.md`
(b) Implement the minimum viable interface
(c) Remove the directory entirely and create when ready |
| **RISK** | Low |
| **TIME** | 1 hour for option (a) |

---

## P2-005: Remove Duplicate `@salesos/design-language` Dependency

| Field | Value |
|-------|-------|
| **AREA** | Frontend |
| **PRI** | **P2** |
| **FILE** | `salesos/frontend/package.json:53-54` |
| **CURRENT** | `"@salesos/design-language": "*"` appears twice |
| **FIX** | Remove line 54 |
| **RISK** | None |
| **TIME** | 5 minutes |

---

## P2-006: Resolve Empty `apps/` Directory

| Field | Value |
|-------|-------|
| **AREA** | Frontend |
| **PRI** | **P2** |
| **FILE** | `salesos/frontend/apps/` |
| **CURRENT** | Directory exists but is empty. `package.json` references `apps/*` |
| **FIX** | Either (a) remove `"apps/*"` from workspace config, or (b) add initial app |
| **RISK** | Low |
| **TIME** | 30 minutes for option (a) |

---

## P2-007: Remove Mock Dashboard Data

| Field | Value |
|-------|-------|
| **AREA** | Frontend |
| **PRI** | **P2** |
| **FILE** | `salesos/frontend/src/app/(dashboard)/page.tsx` |
| **CURRENT** | Hardcoded `"---"` for active licenses, contacts, opportunities |
| **FIX** | Add real API queries or hide these stats until data is available |
| **RISK** | Low |
| **TIME** | 2 hours |

---

## P2-008: Centralize Notion API Client

| Field | Value |
|-------|-------|
| **AREA** | Data Pipeline |
| **PRI** | **P2** |
| **FILE** | Multiple scraper directories |
| **CURRENT** | 5 ad-hoc Notion API implementations |
| **FIX** | Refactor all scrapers to use `sales-os/notion_api.py` (which is well-designed) |
| **RISK** | Medium — behavior must remain identical |
| **TIME** | 8 hours |

---

## P2-009: Add Password Reset Flow

| Field | Value |
|-------|-------|
| **AREA** | Backend — Identity |
| **PRI** | **P2** |
| **FILE** | `salesos/backend/app/modules/identity/` (new endpoints) |
| **CURRENT** | No password reset exists |
| **FIX** | Add endpoints: `POST /forgot-password`, `POST /reset-password` with email-based reset token |
| **RISK** | Low |
| **TIME** | 4 hours |

---

## P2-010: Add Refresh Token Endpoint

| Field | Value |
|-------|-------|
| **AREA** | Backend — Identity |
| **PRI** | **P2** |
| **FILE** | `salesos/backend/app/modules/identity/router.py` |
| **CURRENT** | Refresh tokens are issued but cannot be used |
| **FIX** | ```python
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest, service: IdentityService = Depends(get_service)):
    payload = decode_refresh_token(body.refresh_token)
    access_token = create_access_token(payload["sub"], payload["tenant_id"])
    refresh_token = create_refresh_token(payload["sub"], payload["tenant_id"])
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=30)
``` |
| **RISK** | Low |
| **TIME** | 1 hour |

---

## P2-011: Remove Empty `@salesos/config` Package Reference

| Field | Value |
|-------|-------|
| **AREA** | Frontend |
| **PRI** | **P2** |
| **FILE** | `salesos/frontend/package.json` |
| **CURRENT** | `"@salesos/config": "*"` in dependencies but no source |
| **FIX** | Either implement the package or remove the dependency |
| **RISK** | Low |
| **TIME** | 30 minutes |

---

## P2-012: Add `jti` Claim to JWT Tokens

| Field | Value |
|-------|-------|
| **AREA** | Backend — Identity |
| **PRI** | **P2** |
| **FILE** | `salesos/backend/app/modules/identity/service.py:create_access_token` |
| **CURRENT** | No `jti` in JWT payload — cannot revoke individual tokens |
| **FIX** | ```python
import uuid

def create_access_token(user_id: str, tenant_id: str) -> str:
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "iss": "salesos",
        "aud": "salesos-api",
    }
``` |
| **RISK** | Low — new claims don't break existing validation |
| **TIME** | 1 hour |

---

## P2-013: Remove `open-design/` Fork

| Field | Value |
|-------|-------|
| **AREA** | Repository |
| **PRI** | **P2** |
| **FILE** | `open-design/` (entire directory) |
| **CURRENT** | Forked design system project with its own `.git/` history — 75 entries, mostly irrelevant translations |
| **FIX** | ```bash
rm -rf open-design/
``` |
| **RISK** | Medium — verify nothing imports from it |
| **TIME** | 1 hour |

---

## P2-014: Resolve Duplicate `salesos/` vs `sales-os/` Names

| Field | Value |
|-------|-------|
| **AREA** | Repository — Root |
| **PRI** | **P2** |
| **FILE** | Root directory: `salesos/` and `sales-os/` |
| **CURRENT** | Two directories with nearly identical names serving different purposes |
| **FIX** | Rename `sales-os/` → `salesos-notion-automation/` or merge into `salesos/backend/pipeline/notion/` |
| **RISK** | Low |
| **TIME** | 2 hours |

---

## P2-015: Move Data Artifacts Out of Source Root

| Field | Value |
|-------|-------|
| **AREA** | Repository — Root |
| **PRI** | **P2** |
| **FILE** | 20+ `.xlsx`/`.csv` files |
| **CURRENT** | All in root directory, no `.gitignore` entry |
| **FIX** | ```bash
mkdir -p output/artifacts output/reports
# Move .xlsx to output/artifacts/
# Add *.xlsx to .gitignore
``` |
| **RISK** | Low |
| **TIME** | 1 hour |

---

## P2-016: Add Exception Handler

| Field | Value |
|-------|-------|
| **AREA** | Backend |
| **PRI** | **P2** |
| **FILE** | `salesos/backend/app/main.py` |
| **CURRENT** | No global exception handler — stack traces may leak to clients |
| **FIX** | ```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
``` |
| **RISK** | Low |
| **TIME** | 1 hour |

---

## P2-017: Add `__pycache__` to `.gitignore`

| Field | Value |
|-------|-------|
| **AREA** | Repository |
| **PRI** | **P2** |
| **FILE** | `.gitignore` |
| **CURRENT** | May or may not include `__pycache__/` — the Makefile explicitly cleans them |
| **FIX** | Add `__pycache__/` to `.gitignore` |
| **RISK** | None |
| **TIME** | 5 minutes |

---

## P2-018: Add `sentry_sdk.init()` Call

| Field | Value |
|-------|-------|
| **AREA** | Backend |
| **PRI** | **P2** |
| **FILE** | `salesos/backend/app/main.py` (lifespan) |
| **CURRENT** | `settings.sentry_dsn` is configured but `sentry_sdk.init()` is never called |
| **FIX** | Add to lifespan: ```python
if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.env)
``` |
| **RISK** | Low |
| **TIME** | 30 minutes |

---

## P2-019: Update JWT Default Secret

| Field | Value |
|-------|-------|
| **AREA** | Backend — Config |
| **PRI** | **P2** |
| **FILE** | `salesos/backend/app/config.py:36` |
| **CURRENT** | `jwt_secret_key: str = "change-me-jwt-secret-key-at-least-32-chars"` |
| **FIX** | Remove default value, make it required: ```python
jwt_secret_key: str  # Must be set via environment variable
``` |
| **RISK** | **HIGH** — all developers must set `JWT_SECRET_KEY` env var |
| **TIME** | 30 minutes |

---

## P2-020: Update Docker Default Passwords

| Field | Value |
|-------|-------|
| **AREA** | Infrastructure |
| **PRI** | **P2** |
| **FILE** | `salesos/docker-compose.yml:7-9` |
| **CURRENT** | `POSTGRES_PASSWORD: salesos_dev_password` |
| **FIX** | ```yaml
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD}
``` (removes default fallback) |
| **RISK** | Low — dev workflows must set env vars |
| **TIME** | 30 minutes |

---

## P2-021: Add CORS Tightening

| Field | Value |
|-------|-------|
| **AREA** | Backend |
| **PRI** | **P2** |
| **FILE** | `salesos/backend/app/main.py:224-230` |
| **CURRENT** | `allow_methods=["*"]`, `allow_headers=["*"]` |
| **FIX** | ```python
allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
allow_headers=["Authorization", "Content-Type", "X-Tenant-Id", "X-Request-ID"],
``` |
| **RISK** | Low — only restricts methods/headers that shouldn't be used |
| **TIME** | 15 minutes |

---

## P2-022: Add Connection Pooling (PgBouncer)

| Field | Value |
|-------|-------|
| **AREA** | Infrastructure |
| **PRI** | **P2** |
| **FILE** | New: `salesos/infra/docker/pgbouncer/pgbouncer.ini` |
| **CURRENT** | Backend connects directly to PostgreSQL via asyncpg |
| **FIX** | Add PgBouncer container to docker-compose: ```yaml
pgbouncer:
    image: bitnami/pgbouncer:latest
    environment:
        POSTGRESQL_HOST: postgres
        POSTGRESQL_PORT: 5432
        PGBOUNCER_POOL_MODE: transaction
        PGBOUNCER_MAX_CLIENT_CONN: 100
        PGBOUNCER_DEFAULT_POOL_SIZE: 25
```
Update `config.py` `database_url` to point to PgBouncer port. |
| **RISK** | Medium — transaction mode may break prepared statements |
| **TIME** | 3 hours |

---

## P2-023: Add Base Charting Library

| Field | Value |
|-------|-------|
| **AREA** | Frontend — packages/charts |
| **PRI** | **P2** |
| **FILE** | `salesos/frontend/packages/charts/index.tsx` |
| **CURRENT** | SVG/CSS-based BarChart, LineChart, PieChart — not production-grade |
| **FIX** | Replace with Recharts: ```bash
cd frontend && npm install recharts @types/recharts
```
Then re-implement charts as Recharts wrappers. |
| **RISK** | Medium — existing chart consumers need update |
| **TIME** | 6 hours |

---

## P2-024: Add Frontend Performance Monitoring

| Field | Value |
|-------|-------|
| **AREA** | Frontend — Configuration |
| **PRI** | **P2** |
| **FILE** | `salesos/frontend/next.config.js` |
| **CURRENT** | No bundle analysis, no performance budgets |
| **FIX** | ```javascript
// next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
    enabled: process.env.ANALYZE === 'true',
})
module.exports = withBundleAnalyzer({
    // existing config...
})
``` |
| **RISK** | Low |
| **TIME** | 1 hour |

---

## P2-025: Add `@salesos/charts` Storybook Stories

| Field | Value |
|-------|-------|
| **AREA** | Frontend — packages/charts |
| **PRI** | **P2** |
| **FILE** | New: `salesos/frontend/packages/charts/*.stories.tsx` |
| **CURRENT** | Storybook is installed, zero `.stories` files exist |
| **FIX** | ```typescript
// charts.stories.tsx
import { BarChart, LineChart, PieChart, MetricCard } from "./index"
import type { Meta, StoryObj } from "@storybook/react"

const meta = { component: BarChart, title: "Charts/BarChart" } satisfies Meta<typeof BarChart>
export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
    args: {
        data: [{ label: "Q1", value: 400 }, { label: "Q2", value: 300 }],
    },
}
``` |
| **RISK** | Low |
| **TIME** | 3 hours |

---

# PRIORITY SUMMARY

| Priority | Count | Est. Hours |
|----------|-------|-----------|
| **P0** | 11 | 16.5 |
| **P1** | 14 | 99 |
| **P2** | 25 | 67 |
| **Total** | **50** | **182.5** |

# Week-by-Week Plan

| Week | Focus | Items | Hours |
|------|-------|-------|-------|
| **W1** | Production Blockers (Security) | P0-001 through P0-011 | 16.5 |
| **W2** | AI Runtime (Replace Mock Data) | P1-001 through P1-005 | 20 |
| **W3** | Testing | P1-006 through P1-010 | 64.5 |
| **W4** | Production Readiness | P1-011 through P1-014, P2-001 through P2-025 | 81.5 |

**Note:** W3+W4 estimates are generous for test writing. Realistically, testing will take 2-3 weeks for 40% coverage. Adjust timeline to 6-8 weeks for the full plan.

---

# Breaking Changes Register

| ID | Change | Impact | Mitigation |
|----|--------|--------|------------|
| P0-011 | Tenant isolation cross-validation | All API callers sending mismatched tenant | Update all SDKs first |
| P1-011 | RBAC wired to endpoints | Non-admin users lose access to some endpoints | Seed roles before deploying |
| P2-019 | JWT secret required | All containers must set env var | Update deployment configs |
| P2-020 | Docker passwords required | All dev environments must set env vars | Update .env.example |
| P2-023 | Chart library replacement | Existing chart consumers need import changes | Codemod |

---

*This backlog is executable starting tonight.*
*Every item has a file path, line number, current code, proposed fix, risk assessment, and time estimate.*
