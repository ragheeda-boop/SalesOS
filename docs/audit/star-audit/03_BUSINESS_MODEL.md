# 03 — BUSINESS MODEL: What SalesOS Actually Does

> Source: Source code + documentation synthesis (Phase 3)
> Classification: VERIFIED (where both agree), DOCUMENTATION ONLY (where only docs claim)

---

## Executive Summary

SalesOS is a **B2B SaaS revenue intelligence platform** that helps sales teams in Saudi Arabia manage their pipeline, track companies and contacts, and make data-driven decisions. In its current state, it is a **partially-functional CRM with intelligence features** — not the AI-native operating system described in the vision documents.

---

## 1. What the Product ACTUALLY Does Today

### 1.1 Core Value Delivery

| Capability | What Users Can Actually Do | Status |
|------------|--------------------------|--------|
| **Company Management** | Create, search, filter, edit, delete companies with Arabic/English names, CR numbers, industry, city | ✅ Functional |
| **Contact Management** | Create, link contacts to companies | ⚠️ Basic CRUD |
| **Employee Management** | View employee 360 profiles, signals, scoring, timeline | ✅ Functional |
| **Pipeline Management** | View opportunities, advance/won/lost stages | ⚠️ Backend exists, FE partial |
| **Search** | Unified search across companies, contacts, employees | ✅ Functional (trigram + pgvector) |
| **Dashboard** | Executive dashboard with mission center, decision queue, intelligence feed | ⚠️ Feature module exists |
| **AI Copilot** | Natural language chat about companies (if enabled) | ⚠️ Gated, search-only tool |
| **GTM Intelligence** | ICP profiles, market sizing, lead discovery, enrichment | ⚠️ Backend exists, FE pages exist |
| **Tenant Studio** | Custom fields, workflows, scoring, territories, permissions, branding | ⚠️ Backend exists, FE pages exist |
| **Admin** | Tenant management, user management, feature flags, billing | ✅ Backend functional |

### 1.2 What Users CANNOT Do Today

| Missing Capability | Impact |
|-------------------|--------|
| Revenue forecasting | No ML forecasting; demo hardcodes `demo-1` |
| AI-powered recommendations | Agent runtime is placeholder |
| Digital twin / simulation | Zero components |
| Real-time collaboration | Collaboration runtime exists but not wired |
| Offline mode | Offline runtime exists but not wired |
| Marketplace extensions | Stub only |
| Multi-product | Only SalesOS exists |
| Arabic-first NLP | Normalization only; no sentiment, extraction, or understanding |
| Real Data Fabric | Scrapers exist but ETL is mock |
| Stripe billing | State machine works but no payment processing |

---

## 2. Actors & User Journeys

### 2.1 Primary Actors

| Actor | How They Interact |
|-------|-------------------|
| **Sales Rep** | Logs in → searches companies → views pipeline → updates opportunities |
| **Sales Manager** | Logs in → views dashboard → reviews team pipeline → coaches via employee 360 |
| **Customer Success** | Logs in → views customer health → monitors signals |
| **VP Sales / CRO** | Logs in → views executive dashboard → reviews revenue analytics |
| **Platform Admin** | Logs in via Owner Console → manages tenants, plans, billing, feature flags |
| **AI Copilot** | (If enabled) User asks question → copilot searches companies → returns insights |

### 2.2 User Journey: Sales Rep

```
1. Login (email/password or SSO)
2. Dashboard loads (mission center, decision queue, intelligence feed)
3. Search for a company (unified search)
4. View company detail (360 view)
5. Create/update opportunity
6. View pipeline (kanban)
7. Ask copilot for recommendation (if enabled)
```

---

## 3. Revenue Mechanics

### 3.1 Documented Revenue Streams

| Stream | Documented | Implemented |
|--------|-----------|-------------|
| SaaS subscriptions (Free → Enterprise) | ✅ Documented | ⚠️ Entitlements exist; no Stripe |
| Marketplace (20% rev share) | ✅ Documented | ❌ Stub only |
| Data enrichment (usage-based) | ✅ Documented | ❌ Not started |
| Knowledge packs | ✅ Documented | ❌ Not started |

### 3.2 Subscription Model (Documented)

| Dimension | Metered Unit |
|-----------|-------------|
| Seats | Named users per month |
| AI consumption | Tokens (input+output) by model tier |
| Connector syncs | Sync-runs or records-synced per month |
| Storage | GB (documents, embeddings, timeline) |
| Marketplace apps | Per-install or revenue-share |

### 3.3 What's Actually Billing-Ready

- ✅ Plan definitions (free, starter, growth, enterprise)
- ✅ Entitlement enforcement (domain gating, quota checks)
- ✅ Subscription state machine (trial → active → past_due → suspended → churned)
- ✅ Usage metering models
- ❌ No Stripe API integration
- ❌ No payment processing
- ❌ No invoice generation
- ❌ No dunning automation (model exists, no Stripe webhook processing)

---

## 4. Customer Experience (If Released Today)

### 4.1 What Customers Would Experience

1. **Login works** — Email/password auth with JWT, refresh rotation
2. **Company management works** — Full CRUD with Arabic/English
3. **Search works** — Trigram + vector search across entities
4. **Employee 360 works** — Profiles, signals, scoring, timeline
5. **Dashboard loads** — With mission center, decision queue
6. **Admin panel works** — Tenant/user/plan management
7. **AI Copilot** — Disabled by default; if enabled, basic company search only
8. **No billing** — Can't process payments
9. **No forecasting** — Demo data only
10. **No real AI recommendations** — Agent runtime is placeholder
11. **No marketplace** — Stub
12. **No Arabic NLP** — Basic normalization only
13. **Tenant isolation unverified** — Critical security gap

### 4.2 Customer Satisfaction Prediction

| Aspect | Prediction | Reason |
|--------|-----------|--------|
| Core CRM functionality | ⚠️ Moderate | Companies work; pipeline partial |
| AI intelligence | ❌ Poor | Copilot gated, agent runtime placeholder |
| Arabic experience | ⚠️ Moderate | RTL works; NLP is basic |
| Billing/payment | ❌ Non-existent | No Stripe integration |
| Security confidence | ❌ Low | Tenant isolation unverified |
| Overall | ⚠️ Early beta quality | Functional core, missing platform layer |

---

## 5. Business Model Assessment

### 5.1 What's Real

- ✅ Company intelligence (search, enrichment, 360 view)
- ✅ Employee 360 (profiles, signals, scoring)
- ✅ Pipeline management (backend)
- ✅ Admin platform (tenants, plans, entitlements)
- ✅ Multi-tenant architecture (RLS, dual-engine)
- ✅ Security foundation (JWT RS256, RBAC, CSRF, rate limiting)

### 5.2 What's Missing for Business Viability

- ❌ Payment processing (Stripe)
- ❌ Real AI recommendations
- ❌ Revenue forecasting
- ❌ Arabic NLP understanding
- ❌ Marketplace extensibility
- ❌ Verified tenant isolation
- ❌ Production monitoring/alerting
- ❌ Customer onboarding flow
- ❌ Self-service signup with payment

---

*This model represents the BUSINESS REALITY of what SalesOS delivers today. The vision is captured in 01_THEORY_MODEL.md.*
