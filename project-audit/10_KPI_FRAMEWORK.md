# 10 — KPI Framework — إطار قياس الأداء
> **أحدث متابعة 2026-09-20:** الصفحات المصادق عليها لبيانات SalesOS اختُبرت على `salesos_test` عند migration head `q9r0s1t2u3v4`؛ أُصلحت pagination في P3 وP1/P2. راجع التقرير [22](22_AUTHENTICATED_DATA_AND_BROWSER_VERIFICATION_2026-09-20.md) للأعداد والحدود الحالية.
> يحتفظ هذا المستند بتحليله المؤرخ. نتائج browser QA لا تفتح Phase 7 ولا تغيّر قرار الإنتاج؛ Phase 7 ما زالت BLOCKED والإنتاج NOT APPROVED.

**Principle:** measure only what changes decisions. Don't collect vanity metrics.

**Split:** 4 layers — North Star, Product, Engineering, Business.

---

## 1. North Star metric (single, top-level)

**Metric:** **Paying Tenants with ≥ 1 HITL-Approved AI Recommendation → Booked Activity per Week (PWAT-HITL)**

- Threshold to "count": 1 tenant, 1 recommendation, 1 approval, 1 booked activity, all in a rolling 7-day window
- Data source: `approval_requests` table (Phase 3 P3-5) joined with `commercial_events` (Phase 2 P2-1)
- Target trajectory:
  - Q4 2026: 0 → 1 (design partner)
  - Q2 2027: 3
  - Q4 2027: 10

**Why:** collapses product working + AI trusted + human engaged + real customer + real value. Un-gameable.

---

## 2. Product KPIs (weekly ops dashboard)

| Metric | Definition | Data source | Target |
|--------|------------|-------------|--------|
| Weekly Active Tenants | Distinct tenant_id with ≥ 1 authenticated user session in week | audit_logs / session store | Y1: 3; Y2: 15 |
| Weekly Active Users | Distinct user_id sessioned in week | audit_logs | Y1: 20; Y2: 100 |
| Copilot queries / week | count of Copilot invocations | quota-tracker events | Track only, no fixed target |
| **Groundedness Score (avg)** | EnhancedEvaluationRunner output on sampled Copilot answers | `intelligence/evaluation/quality_gates.py` | ≥ 0.85 |
| **Hallucination Detection Rate** | HallucinationDetector flags per 1k answers | quality_gates | < 5 / 1k |
| HITL Approvals Requested / week | count of `ApprovalRequest` created | `approval_requests` | Track |
| HITL Approvals Rate (Approved / Requested) | ratio | `approval_requests` | > 60% at healthy adoption |
| Time to Insight (TTI) | median seconds from tenant home load → first evidence-cited insight rendered | frontend telemetry | < 30s |
| Company 360 Engagement | median seconds per session on `/v3/companies/[id]` | frontend telemetry | > 5 min |
| Review Queue throughput | fuzzy pairs / short-CR / P0 dispositioned per week per reviewer | `md_review_queue_state` | staff-based; target: staffed FTE ≥ 1 |
| ICP fit distribution | HIGH/MEDIUM/LOW ratio for tenant's target list | ICP engine output | trend, not fixed |
| Signal delivery latency | median ms from signal_event created → tenant notification | signal bridge metrics | < 5s |

---

## 3. Engineering KPIs

| Metric | Definition | Data source | Target |
|--------|------------|-------------|--------|
| Backend availability | `/health` uptime per month | Prometheus (`/metrics`) | ≥ 99.5% Team; ≥ 99.9% Enterprise |
| p95 API latency | across `/api/v1/*` endpoints | Prometheus | < 500 ms |
| Error rate (5xx / total) | over rolling 24h | Prometheus | < 0.1% |
| Test pass rate (unit) | pytest green count / total | CI | 100% mandatory; 0 new failures per PR |
| Frontend build success | tsc 0 errors + lint 0 errors on main | CI | 100% |
| E2E Commercial Loop | Playwright suite green | CI | 42/42 (current baseline) |
| Alembic drift | `alembic current` == `alembic heads` on staging + prod | schema-drift-gate CI + `/api/v1/version` | 0 drift events / week |
| Cross-tenant isolation regressions | RLS tests + agent-B/C probes | pytest `test_rag_rls`, `test_icp_persistence` | 0 |
| LLM cost per active seat / month | cost from `llm_cost_entries` / active seats | `LLMCostTracker` DB | ≤ SAR 120 |
| Budget rejections / week | `PolicyGate` denials count | observability | trend |
| Circuit breaker transitions | `ReliableProvider` metrics | AIObservability | investigated if > 10 / week |
| Deploy frequency | production deploys / week | Railway history | ≥ 1 (safe change velocity) |
| Rollback events | rollbacks / month | Railway history | ≤ 1 |
| P0 open bugs | count | GitHub issues | 0 |
| P1 open bugs | count | GitHub issues | ≤ 5 |

---

## 4. Business KPIs

| Metric | Definition | Data source | Target Y1 | Target Y2 |
|--------|------------|-------------|-----------|-----------|
| Design Partners signed | signed MOUs | manual log | 3 | 3 maintained |
| Paying Tenants | active paid subscriptions | `subscriptions` table (Alembic `c3a9f12d4e80`) | 1 by end Y1 | 10 by end Y2 |
| ARR | annualized recurring revenue (SAR) | `subscriptions` × ACV | ≥ SAR 60k | ≥ SAR 1.45M |
| Net Revenue Retention | (ARR expansion − churn) / starting ARR | subscriptions | ≥ 100% |
| Gross Margin | (revenue − LLM cost − infra cost per tenant) / revenue | ledger + `llm_cost_entries` + Railway invoice | ≥ 30% at 5 tenants |
| Sales cycle (median days) | contract signed date − first meeting date | CRM (self-hosted) | ≤ 90 days for Team tier |
| CAC (customer acquisition cost) | GTM + sales cost / new paying tenants | ledger | tracked; not enforced early |
| LTV / CAC | LTV = ACV × avg lifetime years × gross margin; CAC as above | derived | > 3× at Y2 |
| Case studies published | count | website | Y1: 1; Y2: 3 |
| NPS (Design Partners) | 0–10 rating; NPS = %promoters − %detractors | quarterly survey | ≥ 40 |
| Referrals received | inbound intros from existing tenants | manual | ≥ 3 by end Y2 |

---

## 5. Security & compliance KPIs

| Metric | Data source | Target |
|--------|-------------|--------|
| Tenant isolation test pass | `test_rag_rls`, `test_icp_persistence`, `test_company_isolation` | 100% |
| Auth failures / week | audit_logs | investigated if > 20 |
| Failed CSRF / rate-limit denies / week | middleware metrics | trend |
| Webhook SSRF denies | `url_safety.py` metrics | trend |
| Data breach incidents | manual log | 0 |
| PII in prompt sends | Copilot audit `AIGovernanceAudit` | 0 |
| Approvals with missing evidence | HITL audit | 0 |
| SOC2 audit findings | annual attestation | 0 major |
| PDPL compliance findings | annual | 0 |

---

## 6. Data quality KPIs

| Metric | Data source | Target |
|--------|-------------|--------|
| Muhide-companies canonical entities | `md_global_companies` row count | ≥ 296,746 in staging; whatever tenant subset in prod |
| Orphan derived rows | `PHASE6_FINAL_DB_SAFETY_VALIDATION.md` check | 0 |
| Auto-merge count | `md_entity_merge_history` for automated merges | 0 (forever — human only) |
| Government-ID veto events | ER pipeline metric | tracked; healthy > 0 (shows policy firing) |
| Review Queue backlog | rows in `md_review_queue_state` where status = pending | trending down toward staffed capacity |
| Provenance rows / entity | `md_provenance` count / `md_global_companies` count | ≥ 5 average |
| Source immutability violations | `md_source_rows.raw_payload` diff detector | 0 |

---

## 7. Reporting cadence

| Cadence | Who owns | What is reported |
|---------|----------|------------------|
| Daily (async) | Founder | production health, error rate, deploys |
| Weekly | Founder + fractional CS | product usage, HITL approvals, Copilot cost, GTM funnel |
| Monthly | Founder + Board | ARR, gross margin, cycle time, security incidents |
| Quarterly | Founder + Legal + PO | roadmap gate closure evidence pack, compliance status, hiring plan |

---

## 8. Anti-metrics (do NOT track / do NOT reward)

- Vanity: "Total API calls" without grounding to value
- Vanity: "Total signups" without paid conversion signal
- Vanity: "Words generated by Copilot" — encourages hallucination
- Vanity: "Auto-executed AI actions" — violates HITL invariant

---

## 9. Dashboards to build in v3 admin

Recommended pages under `/v3/admin` to serve internal KPI reporting:
- `/v3/admin/health` — availability, error rate, deploys (extend Monitoring router)
- `/v3/admin/ai` — groundedness, hallucination flags, cost per tenant, budget events
- `/v3/admin/pipeline` — HITL requested / approved / rejected, aging
- `/v3/admin/data` — review queue depth, throughput, provenance health

Founder view only. Not part of tenant-facing surface.

---

## 10. Definition of "healthy" for 12-month check

At the end of Q4 2027, the platform is healthy if simultaneously:
- North Star (PWAT-HITL) ≥ 10
- Availability ≥ 99.5%
- Groundedness ≥ 0.85
- Zero data-breach
- Zero HITL bypass
- ARR ≥ SAR 1.5M
- LTV/CAC ≥ 3
- NPS ≥ 40

Anything less → hard board conversation.

---

*KPI framework — measurable, source-cited, un-gameable-first.*
**File-specific update:** KPI definitions remain; production KPI collection is not approved until monitoring and tenant-safe deployment are proven.


---

## Current audit addendum — 2026-09-22 / Audit Refresh 49

**Status authority:** This addendum supersedes stale progress percentages and current-state claims in this file while preserving the historical narrative above. The complete current snapshot is [Audit Refresh 49](49_AUDIT_REFRESH_2026-09-22.md), with execution evidence in [Production Readiness Loop 45](48_PRODUCTION_READINESS_LOOP_2026-09-22.md).

- Current code-scope roadmap: **85/113 = 75.2% (75%)**.
- Backend health: /health HTTP 200; database, cache, graph and Redis connected.
- Scoped evidence: focused product **69/69**, Phase 5 CR **7/7**, ER pipeline **10/10**, compileall and diff checks PASS.
- Phase 7 remains controlled and non-canonical: P2 sample 1,213 at 0.00% internal material error; P1 6,904 captured; Fuzzy 2,661 captured without merge; Short-CR 11 unresolved escalation; MA staging 1,114 rows on salesos_test only (792 PROPOSED / 322 ESCALATED).
- Production database remained read-only: 107 policies total, 106 tenant-isolation named; commercial contracts have RLS and FORCE RLS; no Phase 7 proposal table or write in salesos.
- Frontend source inventory is 49 V3 pages and 78 legacy pages. Local dependency repair failed with EISDIR/EPERM; TypeScript, Next build and authenticated browser are **not release evidence** in this checkout.
- No provider call, CRM apply, production migration, deployment, commit or push occurred.
- Production approval remains **NOT APPROVED** pending frontend toolchain, Phase 7 owner closure, staging connector E2E, backup/restore, monitoring/DR, SSO, Stripe, PDPL and final PO/Data/DevOps sign-off.

Current detailed evidence: report 49 and report 48.
