# Release Notes — SalesOS vNext (v3.0.0-RC)

> ## SUPERSEDED FOR GA SHIPPING CLAIMS — 2026-07-22
>
> Do not treat feature lists below as production-ready GA. Audit classification: **production no-go**.  
> AI Copilot / Decision Platform language must follow [AI_HONESTY.md](../../audit/ga-engineering-audit/AI_HONESTY.md).  
> **Program:** [PRODUCTION_PLAN.md](../../audit/ga-engineering-audit/PRODUCTION_PLAN.md)

---

> **Status**: Release Candidate (not yet GA) — **not cleared for Production GA** (audit 2026-07-22)
> **Date**: 2026-07-16
> **RC Tag**: v3.0.0-RC

---


## Overview

SalesOS vNext is a major platform release adding 6 new domains, 5 new frontend modules, AI Copilot, Knowledge Graph V2, and production hardening across all 17 phases.

---

## New Features

### 🏢 Companies (Phase 3-4)
- Company list with keyset pagination, advanced filtering (industry, size, region, date range, status)
- Bulk operations: edit, delete (soft), CSV export
- Company360 page: Overview, Hierarchy, Financial, Activity, Insights tabs
- Knowledge Graph panel with entity relationships
- Decision Platform insights (deal score, NBAs, risk flags)

### 👥 Employees (Phase 5-6)
- Signal pipeline — collect from CRM activity, Timeline events, Workflow completions
- Employee scoring — 4 factors (volume, recency, diversity, completion) with confidence
- Employee list with keyset pagination, search, filter
- Bulk operations: edit, delete, export
- Employee360 page: Overview, Signals, Scoring, Timeline, Performance tabs
- Performance insights: trend analysis, peer comparison, risk flags

### 📊 Pipeline (Phase 7)
- ML-backed forecasting (weighted + historical velocity, confidence intervals)
- Pipeline analytics: conversion rates, velocity, stage duration, win/loss
- Deal scoring — 6 factors with health/risk assessment
- Kanban board with drag-and-drop stage management
- Deal cards with score badge, company, value, owner

### 💰 Revenue (Phase 8)
- Revenue forecasting (time-series + pipeline combined)
- Quota management: set targets, track attainment, forecast attainment
- Territory planning: assign accounts, coverage gap analysis, load balancing
- Revenue dashboard: ARR, NRR, churn, expansion

### 🧠 Decision Center (Phase 9)
- Unified decision view across all domains
- Audit trail: reasoning chain, confidence, provider, alternatives
- Feedback mechanism (thumbs up/down + comment)
- 4 decision templates: lead qualification, deal progression, renewal risk, pricing
- Multi-provider ensemble for >$100K deals

### 🔍 Search (Phase 10)
- Keyset pagination on all search endpoints
- Search caching (LRU + TTL + tenant invalidation)
- Search analytics: top queries, zero-result rate, latency tracking
- Arabic search: stemming, diacritics removal, stop words, normalization

### 🤖 Copilot (Phase 11)
- Fixed `search_companies` tool (< 1s latency)
- Conversation branching (explore alternatives without losing context)
- Tool telemetry dashboard (success rate, latency, result distribution)
- Arabic copilot support (RTL, Arabic NLP, Saudi business context)
- Feedback mechanism on copilot responses

### 🧩 Knowledge Graph (Phase 12)
- KG runtime decomposed (all modules < 500 lines)
- PGVector native VECTOR(n) type + HNSW index (~50x speed improvement)
- Embedding cache (LRU, > 40% hit rate)
- Hybrid retrieval (vector + BM25 + RRF, F1 > 0.85)
- Data Fabric connectors: CRM, ERP, Market Feed
- Knowledge graph viewer (SVG force-directed)
- Data Fabric connectors UI with sync status

### ⚙️ Automation (Phase 13)
- Advanced workflow engine: IF/ELSE, FOR loops, parallel branches, timeouts
- Webhook authentication (HMAC + JWT)
- Scheduled jobs: cron expressions, one-time delays, recurring intervals
- 9 workflow templates (lead assignment, deal escalation, renewal reminders, etc.)
- Workflow builder UI (visual canvas, 672 lines)

### 📈 Analytics (Phase 14)
- 5 domain dashboards: Sales, Revenue, Pipeline, Employee, Automation
- Custom report builder: metrics, dimensions, filters, visualization type
- CSV/PDF export engine
- Scheduled report delivery via email
- Report sharing with permissions

### 🛒 Marketplace (Phase 15)
- Plugin registry with manifest validation
- Plugin lifecycle: Install → Disable → Enable → Active → Uninstall
- Plugin sandboxing (iframe for widgets, import restrictions for backend)
- 2 internal plugins: Slack integration, Salesforce connector
- Marketplace UI with browse, search, install, configure

### 🔧 Administration (Phase 16)
- Persistent admin stores (PostgreSQL-backed)
- Tenant management: provision, configure, suspend, delete
- Feature flags: per-tenant enable/disable, gradual rollout
- Audit log viewer with filtering and CSV export
- YAML config editor with validation and version history

---

## Improvements

- 14 endpoints converted to keyset cursor pagination
- Search performance: partial ILIKE reduced from 2.6s to < 50ms (trigram indexes)
- AI test coverage: 98% (target 85%)
- Frontend bundle: ~130KB gzipped
- Accessibility: WCAG AA with 0 P0/P1 issues
- Cross-browser: Chromium, Firefox, WebKit, Mobile Safari
- RTL: full Arabic support with 150+ custom utilities

---

## Known Issues

See `OPEN_ISSUES.md` for complete list.
Key items:
- P0: Dual Widget SDK (ADR-003 violation) — blocks GA
- G-3: Middleware body cache fix pending
- G-7: Employee domain `metadata` column naming conflict
- G-11: PITR/WAL archiving not configured
- G-12: OTel collector and Loki shipping not deployed

---

## Migration Notes

- 37 database migrations (0035-0072), all reversible
- Trigram indexes require PostgreSQL 12+
- PGVector extension required for VECTOR(n) type
- Node.js 18+ required for frontend build
