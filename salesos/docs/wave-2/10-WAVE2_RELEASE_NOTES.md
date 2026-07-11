# Wave 2 Release Notes — Revenue Execution Platform

> **Version:** v0.6.0
> **Release Date:** 2026-07-11
> **Codename:** Revenue Execution Platform

---

## Overview

Wave 2 transforms SalesOS from an intelligence platform into a **commercial execution engine**. It introduces six interconnected components that convert data into revenue through AI-driven decisions, pipeline management, and intelligence-driven meetings and emails.

### Wave 2 Components at a Glance

| Component | Status | Sprint | Key Capability |
|-----------|--------|--------|----------------|
| NBA Engine | ✅ Complete | 5-5.0 | Decision pipeline with AI reasoning |
| Opportunity Workspace | ✅ Complete | 6 | Full opportunity lifecycle management |
| Pipeline Intelligence | ✅ Complete | 7 | Velocity, conversion, forecast |
| Meeting Intelligence | ✅ Complete | 8 | Pre/post meeting AI briefs |
| Email Intelligence | ✅ Complete | 8 | Sentiment, topics, urgency |
| Revenue Workspace | ✅ Complete | 9 | Unified executive shell |

---

## 1. NBA Engine — Decision Intelligence

### What It Does

The NBA Engine is the **decision layer** that converts intelligence into commercial action. It answers three questions:
- What should happen next?
- Why?
- What impact will it create?

### How It Works

```
Signal → Normalization → Business Rules → Scoring → AI Reasoning
  → Risk Assessment → Confidence → Ranking → Recommendation
  → Feedback → Continuous Learning
```

**12 pipeline stages** process every signal through a deterministic pipeline:

1. **Signal Ingestion** — Receives events from opportunity changes, activity logs, company signals, or time triggers
2. **Normalization** — Standardizes signal format, enriches with opportunity + company context
3. **Business Rules** — 10+ rules evaluate stage, time, signal, and health conditions
4. **Scoring** — OpportunityScorer (7 weighted factors), UrgencyScorer, EffortEstimator
5. **AI Reasoning** — LLM evaluates context when rules produce low confidence or conflict
6. **Risk Assessment** — 6 risk detectors evaluate stagnation, competition, engagement, stakeholders, budget, timeline
7. **Confidence Calculation** — Aggregates rule + AI + risk into final confidence score
8. **Ranking** — Sorts candidates by confidence, applies business constraints
9. **Output** — Next Best Action with full evidence trail + alternatives
10. **Feedback Collection** — User accepts, dismisses, or completes the recommendation
11. **Learning** — Feedback adjusts rule weights weekly
12. **Audit** — Full pipeline trace recorded for every generation

### Key Features

- **Explainable by design** — Every recommendation includes `Evidence[]` array showing exactly why it was generated
- **Hybrid AI** — Business rules + LLM reasoning; AI can shift ranking by ±0.2 from rule score
- **Graceful degradation** — Works without OpenAI API key (rule-only mode)
- **Feedback loop** — Weekly rule weight adjustment based on acceptance rates
- **Performance budget** — < 200ms rule-only, < 3s with AI, timeout + fallback on AI failure

### Business Rules

| Category | Example | Score |
|----------|---------|-------|
| Stage-based | `qualification` → "Send introduction email" | 0.9 |
| Stage-based | `proposal` → "Send proposal document" | 0.9 |
| Time-based | No activity 14 days → "Send follow-up" | 0.7+ |
| Signal-based | New competitor → "Prepare competitive brief" | 0.8 |
| Health-based | Health is `critical` → "Escalate to manager" | 0.95 |
| Engagement | High engagement → "Schedule demo" | 0.75 |
| Milestone | Approaching close → "Review contract terms" | 0.85 |

### Risk Detection

| Factor | Detection Method | Trigger |
|--------|-----------------|---------|
| Stagnation | No activity for 7+ days | Time-based |
| Competition | Competitor signal linked to company | Event-based |
| Engagement Drop | Activity < 50% of previous period | Scheduled |
| Stakeholder Change | Contact change on account | Event-based |
| Budget Concern | Signal mentions budget/cost/pricing | Event-based |
| Timeline Slip | Close date pushed 2+ times | Event-based |

### Confidence Model

```
finalScore = ruleScore × 0.4 + opportunityScore × 0.25
           + urgencyScore × 0.2 + effortScore × 0.15
           + riskAdjustment (-0.3 to 0)
```

| Label | Threshold |
|-------|-----------|
| High | ≥ 0.8 |
| Medium | ≥ 0.5 |
| Low | < 0.5 |

---

## 2. Opportunity Workspace

### What It Does

The Opportunity Workspace is the **command center for a single deal**. It provides full lifecycle management from qualification through close.

### Key Features

- **Opportunity CRUD** — Create, read, update, delete, stage management
- **NBA Widget** — Embedded Next Best Action with full evidence trail
- **Timeline Widget** — Activity timeline specific to this opportunity
- **Company Snapshot** — Pulls from Wave 1 Company Intelligence
- **Deal Health** — Real-time health indicators (healthy / at_risk / critical)
- **Playbook Engine** — Assign playbooks with steps, triggers, and templates
- **Stage Management** — Advance/revert stages with reason tracking

### Opportunity Lifecycle

```
qualification → discovery → proposal → negotiation → closed_won / closed_lost
```

Each stage transition triggers:
- NBA recomputation for the opportunity
- Activity log entry
- Health recalculation
- Pipeline metrics update

### Deal Health Model

| Health | Conditions | Color |
|--------|-----------|-------|
| Healthy | Activity in last 7 days, stage progressing, no risks | Green |
| At Risk | Activity 7-14 days old, or 1+ medium risks | Amber |
| Critical | No activity 14+ days, or 1+ high risks, or close date passed | Red |

---

## 3. Pipeline Intelligence

### What It Does

Pipeline Intelligence provides **real-time visibility into the entire sales pipeline** — velocity, conversion rates, health distribution, and forecast accuracy.

### Key Features

- **Kanban View** — Drag-and-drop stage changes
- **List View** — Sortable, filterable table with all pipeline data
- **Velocity Metrics** — Average days per stage, overall cycle time
- **Conversion Rates** — Stage-to-stage conversion percentages
- **Health Map** — Traffic light visualization across all open opportunities
- **Forecast Engine** — Best Case, Commit, and Pipeline forecasts
- **Export** — CSV and PDF export of pipeline data

### Pipeline Metrics

| Metric | Description |
|--------|-------------|
| Total Value | Sum of all open opportunity values |
| Weighted Value | Sum of (value × probability) across pipeline |
| Win Rate | % of closed opportunities that are won |
| Avg Deal Size | Average value of closed-won deals |
| Velocity (days) | Average days from creation to close |
| Conversion Rate | % moving from each stage to the next |

### Forecast Model

| Forecast Type | Calculation |
|---------------|-------------|
| **Pipeline** | Total value of all open opportunities |
| **Best Case** | Sum of (value × probability) for all open |
| **Commit** | Sum of (value × probability) for opportunities with health ≥ at_risk and stage ≥ proposal |

### Health Map

| Status | Count | Traffic Light |
|--------|-------|---------------|
| Healthy | N opportunities | Green |
| At Risk | N opportunities | Amber |
| Critical | N opportunities | Red |

---

## 4. Meeting Intelligence

### What It Does

Meeting Intelligence transforms meetings from unstructured events into **actionable intelligence** through AI-powered pre-meeting briefs, post-meeting summaries, and action item extraction.

### Key Features

- **Pre-Meeting Brief** — Auto-generated company brief, talking points, and context
- **Post-Meeting Summary** — AI-generated summary with key decisions and next steps
- **Action Item Extraction** — Automatic extraction of commitments from meeting notes
- **Sentiment Analysis** — Meeting tone and engagement scoring
- **Activity Integration** — All meetings logged to Activity Runtime

### Pre-Meeting Brief Includes

- Company overview and recent signals
- Contact background and relationship history
- Previous meeting notes and action items
- Suggested talking points based on opportunity stage
- Related opportunities and pipeline context

### Post-Meeting Summary Includes

- Key discussion points
- Decisions made
- Action items with owners and due dates
- Sentiment and engagement score
- Follow-up recommendations (feeds into NBA)

---

## 5. Email Intelligence

### What It Does

Email Intelligence analyzes inbound and outbound emails to extract **sentiment, topics, and urgency** — feeding this intelligence into the NBA Engine and Activity Runtime.

### Key Features

- **Sentiment Analysis** — Positive / Neutral / Negative classification per email
- **Topic Extraction** — Automatic topic tagging and classification
- **Urgency Detection** — Priority flagging based on content analysis
- **Email Integration** — Gmail API and Outlook API connectors
- **Activity Integration** — All emails logged to Activity Runtime
- **NBA Integration** — Email signals feed into NBA decision pipeline

### Intelligence Output

| Field | Description |
|-------|-------------|
| Sentiment | Positive, Neutral, Negative (with score 0.0-1.0) |
| Topics | Array of extracted topics with confidence |
| Urgency | Low, Medium, High (with reasoning) |
| Key Phrases | Notable phrases extracted from content |
| Action Items | Any commitments or tasks identified |

---

## 6. Revenue Workspace

### What It Does

The Revenue Workspace is the **unified executive shell** that combines all Wave 2 components into a single view for revenue leaders.

### Key Features

- **Executive Summary** — Target vs Forecast with visual comparison
- **Team Performance** — Individual and team metrics dashboard
- **AI Insights** — At-risk deals, coaching recommendations
- **Pipeline Overview** — Aggregated pipeline health and velocity
- **NBA Dashboard** — Adoption rates, acceptance metrics
- **Meeting/Email Activity** — Communication volume and sentiment trends

### Dashboard Sections

| Section | Data Source |
|---------|------------|
| Revenue Target vs Forecast | Revenue Goals + Pipeline Forecast |
| Team Performance | Opportunity + Activity data |
| At-Risk Deals | NBA risk assessment + Health Map |
| Pipeline Velocity | Pipeline Intelligence metrics |
| NBA Adoption | Feedback analytics from NBA Engine |
| Communication Trends | Meeting + Email intelligence aggregates |

---

## Upgrade Guide

### From v0.5.0 to v0.6.0

1. **Database migrations** — Run `make migrate` to apply new tables:
   - `opportunities`, `opportunity_features`, `playbooks`
   - `meetings`, `meeting_action_items`
   - `emails`, `email_intelligence`
   - `revenue_goals`

2. **Environment variables** — Add to `.env`:
   ```
   OPENAI_API_KEY=sk-...          # Optional: enables AI reasoning in NBA
   GOOGLE_CLIENT_ID=...           # Optional: Gmail integration
   GOOGLE_CLIENT_SECRET=...       # Optional: Gmail integration
   OUTLOOK_CLIENT_ID=...          # Optional: Outlook integration
   OUTLOOK_CLIENT_SECRET=...      # Optional: Outlook integration
   ```

3. **Feature flags** — NBA, Pipeline, Meeting, and Email Intelligence ship behind tier-based feature flags:
   - `internal` — Development team only
   - `beta` — Early access customers
   - `enterprise` — General availability

4. **Permissions** — New permission resources:
   - `nba:read`, `nba:update`, `nba:admin`
   - `opportunity:read`, `opportunity:create`, `opportunity:update`, `opportunity:delete`
   - `pipeline:read`
   - `meeting:read`, `meeting:create`, `meeting:update`
   - `email:read`, `email:create`

---

## Breaking Changes

None. All Wave 2 endpoints are new. Wave 1 APIs remain unchanged.

## Deprecations

None. No Wave 1 APIs are deprecated in this release.

## Known Issues

| Issue | Status | Workaround |
|-------|--------|-----------|
| AI reasoning requires OpenAI API key | By design | NBA works in rule-only mode without key |
| Email sync may have 30s latency | Known limitation | Manual refresh available |
| Calendar integration is manual-first | Sprint 8 scope | Calendar sync in future release |
| Pipeline drag-and-drop on mobile | Limited touch support | Use list view on mobile |

---

*Release notes for Wave 2 — Revenue Execution Platform.*
