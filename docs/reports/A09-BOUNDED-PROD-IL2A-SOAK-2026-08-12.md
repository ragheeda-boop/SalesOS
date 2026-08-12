# A-09 / Wave 11 — Bounded production IL-2A soak (2026-08-12)

**Validation label:** **light validated** (bounded prod HTTP + DB verify)  
**Does NOT claim:** staging parity complete · Wave 11 48–72h soak complete · Production GO  
**`soak_complete_claim`:** **false**  
**Constraints honored:** `feature_ai_copilot` left `false` · no `alembic upgrade head` on prod · no SSH env secret dumps

---

## Why production (not staging) for this path

| Staging fact (live 2026-08-12) | Implication |
|--------------------------------|-------------|
| Host `https://salesos-staging.up.railway.app` `/health` **200** | Staging **exists** |
| Empty / near-empty business data historically; Google OAuth residual OPEN | Decision→AgentTask functional soak needs tenant+companies |
| No dedicated `staging` git branch (`git branch -a`) | Deploy via Railway env + `deploy-staging.yml`, not branch parity |
| Health-loop 72h evidence finished 2026-08-10 (`loop-summary…`, 854 iters, **82 failures**, claim still false) | Health soak ≠ Decision/AgentTask soak; claim not flipped |

Per job approval: **bounded production soak** of Decision→AgentTask→worker is allowed when staging cannot exercise the path honestly.

---

## Staging GO-gap list (A-09 residual — still OPEN)

| # | Gap | Status |
|---|-----|--------|
| G1 | Signed staging↔prod parity table with **zero critical diffs** (PROD-W11-001) | **OPEN** — machine baseline 2026-08-07 exists; Human-Gate residuals remain |
| G2 | Staging Google OAuth app (`SSO_GOOGLE_CLIENT_ID/SECRET`) | **OPEN** (Human-Gate) |
| G3 | Staging WAL/PITR + offsite backup posture | **OPEN** / accept-or-enable |
| G4 | Staging Postgres `max_connections` 100 vs prod 500 | **OPEN** / accept-or-raise |
| G5 | `deploy-staging.yml` exercised end-to-end (not only manual CLI) | **PARTIAL** — workflow exists; CI exercise evidence thin |
| G6 | Dedicated `staging` git branch | **MISSING** |
| G7 | Wave 11 **48–72h** soak claim (`soak_complete_claim=true`) after human review | **OPEN** — 72h health harness finished with failures; K2–K6 not closed |
| G8 | Seeded staging tenant/companies for Decision→AgentTask | **MISSING** for functional parity |

Authoritative parity snapshot: [`STAGING-vs-PRODUCTION-DIFF.md`](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/STAGING-vs-PRODUCTION-DIFF.md) · checklist: [`staging-parity-checklist.md`](../audit/ga-engineering-audit/runbooks/staging-parity-checklist.md)

---

## Bounded prod soak results (this run)

| Field | Value |
|-------|--------|
| API | `https://salesos-production-96c0.up.railway.app` |
| Path | `POST /api/v1/decision-runtime/decision/evaluate` |
| Deploy SHA (container) | `f99da41758b7e70c4c8075af9471381aa0010109` |
| `FEATURE_AI_COPILOT` | `false` |
| Cycles | **8/8 HTTP 200** (~302–368 ms) |
| Decision types seen | `recommend_call` (actionable) only |
| AgentTasks (DB) | **5 new** `research_company` **COMPLETED** in soak window on distinct companies; company `2f3b1426` remained **1** task (prior gate task) across re-evaluates |
| Isolation | **PASS** (`isolation_cross_refs=0`) |
| Idempotency | **PASS** (company0 `rows=1` / `distinct_keys=1` after 3 evaluates) |
| Non-actionable live types | **Not observed** from engine on these companies; **contract checks PASS** (`alert` / unknown → no AgentTask) |
| Ephemeral soak users | Created for login only; **deactivated** after run |

### Evidence files

- [`il2a-prod-bounded-soak.json`](../audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/il2a-prod-bounded-soak.json) — HTTP cycles  
- [`il2a-agenttask-db-verify.json`](../audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/il2a-agenttask-db-verify.json) — AgentTask isolation/idempotency  

### Tooling

- `salesos/scripts/il2a_prod_bounded_soak_local.py` — public-API bounded soak (env: `SOAK_EMAIL`, `SOAK_PASS`, optional `SOAK_COMPANY_IDS`)

---

## Incident note (honest)

During earlier SSH JWKS mint attempts, prod briefly returned **502** and showed a **fresh process uptime (~33s)** — treat as soak-adjacent instability, not a green long soak. Subsequent health recovered; this bounded run completed after recovery. **Do not** mint JWKS from one-off SSH sessions on prod (risk of key regeneration).

---

## Claims

| Claim | Value |
|-------|-------|
| Staging parity complete (A-09 / PROD-W11-001) | **false** |
| Wave 11 48–72h soak complete (PROD-W11-002) | **false** |
| Production GO | **false** |
| Bounded prod IL-2A Decision→AgentTask evidence | **true** (light validated) |
