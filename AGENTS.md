# AGENTS.md — AQLIYA / Muhide Workspace

> **Audience:** Humans and coding agents working in this repository.  
> **Last updated:** 2026-07-22 (Wave 7 governance)  
> **Authority chain:** Executable evidence → [ga-engineering-audit](docs/audit/ga-engineering-audit/) → this file → `docs/PROJECT_BIBLE.md` (SalesOS engineering bible; product scope notes below).

---

## 1. What this workspace is

**AQLIYA** is the intended **Private Governed Institutional Intelligence Platform**.

**Core principle:** AI assists. Humans decide. Evidence governs.

| Product | Role | Code reality (2026-07-22) |
|---------|------|---------------------------|
| **SalesOS** | First operational product on AQLIYA | Primary codebase under `salesos/` |
| **AuditOS** | Separate product on shared Core (vision) | Not a shipped product tree in this repo |
| **DecisionOS** | Separate product on shared Core (vision) | Not a shipped product tree in this repo |
| **LocalContentOS** | Separate product on shared Core (vision) | Not a shipped product tree in this repo |

**Do not** treat SalesOS GA work as “AQLIYA multi-product GA.”  
**Do not** describe the platform as AuditOS-only, SaaS-only, or a chatbot.

Canonical GA engineering source of truth:

- [docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md](docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md) — **NO-GO**
- [docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md](docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md) — Waves 0–14
- [docs/audit/ga-engineering-audit/AI_HONESTY.md](docs/audit/ga-engineering-audit/AI_HONESTY.md) — AI marketing honesty

Prior GO claims in `docs/vnext/reports/GO_NO_GO_DECISION.md` and `GA_CHECKLIST.md` are **SUPERSEDED**.

---

## 2. Repository map (agents)

| Path | Use |
|------|-----|
| `salesos/` | Product monorepo (FastAPI backend + Next.js frontend + infra) |
| `salesos/backend/` | API, domains, runtime, Alembic |
| `salesos/frontend/` | Next.js app + `@salesos/*` packages |
| `docs/` | Audits, ADRs, ops, vNext plans |
| `data/` | Notion/identity import pipelines — **not** SalesOS runtime GA path by default |
| `engineering-os/` | Governance submodule (if present) |
| Root scrapers / `sales-os/` | Legacy / adjacent — prefer `salesos/` |

---

## 3. Low-load protocol (mandatory)

Do **not** run heavy commands unless the user **explicitly approves**:

- `npm run build` / `npm run lint` / full `npm test` suites
- `npx prisma generate` / `migrate` (Prisma is **not** SalesOS core — Alembic is)
- `npm install` / `pnpm install` / `yarn install`
- Full `pytest` suites outside a narrow, approved path
- Production DB migrate / restore / deploy

Prefer:

- Read-only exploration (Grep/Read)
- Minimal patches following existing patterns
- Docker-based backend work when host Poetry/Python is broken (Windows host Poetry/asyncpg known fail per audit)

---

## 4. Security & governance — never weaken without approval

- Auth, CSRF, RBAC, tenant isolation, audit logging, evidence gates
- Do not disable security middleware “to unblock demos”
- Do not commit secrets (`.env`, credentials, kubeconfigs)
- Do not claim browser pass, production-ready, or tests passed without command evidence

---

## 5. Validation honesty labels

Use these labels; never invent a stronger claim:

| Label | Meaning |
|-------|---------|
| **not validated** | Not run / no evidence |
| **light validated** | Spot checks only |
| **build validated** | Install/lint/typecheck/build/test commands run with recorded outcome |
| **pilot-ready with conditions** | Narrow use after listed P0s closed |
| **production no-go** | Must not ship GA |

Current audit classification (2026-07-22): **production no-go** (Production Readiness 38, Security 48).

---

## 6. AI honesty

- Default: `feature_ai_copilot=False` (`salesos/backend/app/config.py`)
- FE Decision package is a **STUB** — see `AI_HONESTY.md`
- Do not market stubs as production AI
- Prefer Decision Center APIs over stub `@salesos` decision engine

---

## 7. Conflict resolution for agents

1. If docs disagree → prefer **executable evidence** + ga-engineering-audit.  
2. If `PROJECT_BIBLE.md` maturity scores conflict with audit → **audit wins** for GO/NO-GO.  
3. Parallel code agents may own `TenantList` / security endpoints — **do not conflict**; leave those files alone unless assigned.  
4. Only commit when the user explicitly asks.

---

## 8. Preferred local paths (when approved)

```text
# Backend (Docker)
cd salesos
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head   # non-prod only, after approval

# Frontend (from salesos/frontend) — requires explicit approval
npm run lint
npx tsc --noEmit
npm run build
```

Windows host Poetry is **not** the production path.

---

*Agents: keep patches minimal, report files changed + commands run + validation status honestly.*
