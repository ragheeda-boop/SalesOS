# Next Best Action Blueprint

> **الهدف:**蓝图 NBA — التصميم التفصيلي للهيكل المعماري والوحدات والتكامل
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Phase 4 — NBA Blueprint

---

## 1. Module Architecture

```text
next-best-action/
│
├── contracts/                    — Strongly typed interfaces (platform/contracts/ai + revenue)
│   ├── signal.ts
│   ├── recommendation.ts
│   ├── decision.ts
│   ├── evidence.ts
│   ├── confidence.ts
│   ├── impact.ts
│   ├── risk.ts
│   └── feedback.ts
│
├── engine/                       — Core NBA engine (backend)
│   ├── __init__.py
│   ├── pipeline.py               — Decision pipeline orchestrator
│   ├── normalizer.py             — Signal normalization
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── base.py               — BaseRule class
│   │   ├── stage_rules.py        — Stage-based rules
│   │   ├── time_rules.py         — Time-based rules
│   │   ├── signal_rules.py       — Signal-triggered rules
│   │   └── health_rules.py       — Deal health rules
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── opportunity_scorer.py — Opportunity scoring model
│   │   ├── urgency_scorer.py     — Urgency/time scoring
│   │   └── effort_estimator.py   — Effort estimation
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── reasoner.py           — AI reasoning engine
│   │   └── prompt.py             — LLM prompts for NBA
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── assessor.py           — Risk assessment engine
│   │   └── detectors.py          — Individual risk detectors
│   ├── confidence.py             — Confidence calculation
│   ├── ranker.py                 — Recommendation ranking
│   └── feedback.py               — Feedback collection + learning
│
├── api/                          — REST API layer (backend)
│   ├── __init__.py
│   ├── router.py                 — FastAPI router
│   ├── queries.py                — Query handlers
│   └── commands.py               — Command handlers
│
├── subscribers/                  — Event Runtime subscribers (backend)
│   ├── __init__.py
│   ├── opportunity_subscriber.py — Listen to opportunity events
│   ├── activity_subscriber.py    — Listen to activity events
│   ├── signal_subscriber.py      — Listen to company signal events
│   └── time_trigger.py           — Scheduled idle detection
│
├── frontend/                     — React components (frontend)
│   ├── components/
│   │   ├── RecommendationCard.tsx
│   │   ├── EvidencePanel.tsx
│   │   ├── ConfidenceBadge.tsx
│   │   ├── ImpactMeter.tsx
│   │   ├── RiskPanel.tsx
│   │   ├── AlternativeActions.tsx
│   │   ├── FeedbackDialog.tsx
│   │   └── ActionLauncher.tsx
│   ├── hooks/
│   │   ├── useNBA.ts
│   │   └── useNBAAction.ts
│   └── widget/
│       └── NBAWidget.tsx          — Workspace widget
│
├── tests/
│   ├── test_pipeline.py
│   ├── test_rules.py
│   ├── test_scoring.py
│   ├── test_risk.py
│   ├── test_confidence.py
│   ├── test_api.py
│   └── test_subscribers.py
│
└── config/
    ├── rules.yaml                — Business rule configuration
    └── scoring.yaml              — Scoring weights and factors
```

---

## 2. Workspace Interaction

```text
Opportunity Workspace
  │
  ├── NBA Widget (NBAWidget.tsx) ←── createWorkspaceWidget
  │     │                              selector: (w) => w.nba
  │     │                              metadata: permissions: ['nba:read']
  │     │                              render: <NBAWidget opportunity={data} />
  │     │
  │     ├── RecommendationCard    ←── Main NBA display (action + reason + confidence)
  │     ├── EvidencePanel         ←── Expandable evidence trail
  │     ├── AlternativeActions    ←── Other ranked actions
  │     ├── ImpactMeter           ←── Expected revenue impact
  │     ├── RiskPanel             ←── Risk factors (if any)
  │     ├── ConfidenceBadge       ←── High/Medium/Low badge
  │     ├── ActionLauncher        ←── Execute the action (opens modal/form)
  │     └── FeedbackDialog        ←── Accept/Dismiss with reason
  │
  └── Other widgets (Timeline, Playbook, Health) — independent, read-only from NBA
```

## 3. Application Layer (Backend)

### Query Layer

```python
@router.get("/opportunities/{opportunity_id}/nba")
async def get_nba(opportunity_id: str, tenant_id: str = Depends(get_tenant)):
    """Get current NBA for an opportunity. Returns cached or computes fresh."""
    engine = NBAEngine(...)
    nba = await engine.get_or_compute(opportunity_id, tenant_id)
    return nba
```

### Command Layer

```python
@router.post("/opportunities/{opportunity_id}/nba/refresh")
async def refresh_nba(opportunity_id: str, tenant_id: str = Depends(get_tenant)):
    """Force recompute NBA for an opportunity."""
    engine = NBAEngine(...)
    nba = await engine.recompute(opportunity_id, tenant_id)
    return nba

@router.post("/opportunities/{opportunity_id}/nba/accept")
async def accept_nba(opportunity_id: str, nba_id: str, tenant_id: str = Depends(get_tenant)):
    """Record user acceptance of NBA recommendation."""
    engine = NBAEngine(...)
    await engine.record_feedback(opportunity_id, nba_id, "accepted")

@router.post("/opportunities/{opportunity_id}/nba/dismiss")
async def dismiss_nba(opportunity_id: str, nba_id: str, reason: str = None, ...):
    """Record user dismissal with optional reason."""
    engine = NBAEngine(...)
    await engine.record_feedback(opportunity_id, nba_id, "dismissed", reason)
```

---

## 4. Scoring Engine Detail

### OpportunityScorer

```python
class OpportunityScorer:
    WEIGHTS = {
        "deal_value": 0.25,
        "stage_progression": 0.20,
        "engagement_level": 0.15,
        "company_icp_score": 0.15,
        "decision_maker_access": 0.10,
        "timeline_pressure": 0.10,
        "deal_health": 0.05,
    }

    async def score(self, opportunity: Opportunity, company: Company, activities: list[Activity]) -> float:
        """Return normalized score 0.0-1.0."""
        scores = {
            "deal_value": self._score_deal_value(opportunity.value),
            "stage_progression": self._score_stage(opportunity.stage, opportunity.stage_history),
            "engagement_level": self._score_engagement(activities),
            "company_icp_score": company.features.get("icp_score", 0.5),
            "decision_maker_access": self._score_dm_access(company.contacts),
            "timeline_pressure": self._score_timeline(opportunity.expected_close_date),
            "deal_health": {"healthy": 1.0, "at_risk": 0.5, "critical": 0.2}.get(opportunity.health, 0.5),
        }
        return sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS)
```

### UrgencyScorer

```python
class UrgencyScorer:
    async def score(self, opportunity: Opportunity, activities: list[Activity]) -> float:
        days_since_last_activity = self._days_since_last(activities)
        days_to_close = self._days_between(now(), opportunity.expected_close_date)

        urgency = 0.0
        if days_since_last_activity > 14: urgency += 0.4  # Stagnation urgency
        if days_since_last_activity > 7:  urgency += 0.2
        if days_to_close < 7:             urgency += 0.3  # Close deadline urgency
        if days_to_close < 30:            urgency += 0.1
        return min(urgency, 1.0)
```

---

## 5. AI Engine Detail

### Reasoner

```python
class NBAReasoner:
    async def evaluate(
        self, opportunity: Opportunity, company: Company,
        signals: list[Signal], activities: list[Activity],
        candidates: list[ScoredCandidate],
    ) -> AIEvaluation:
        prompt = self._build_prompt(opportunity, company, signals, activities, candidates)
        response = await self.llm.chat(prompt)
        return self._parse_response(response)
```

### LLM Prompt Structure

```
System: You are a senior sales strategist. Analyze the opportunity and recommend the next best action.

Context:
- Opportunity: {name}, stage: {stage}, value: {value}, health: {health}
- Company: {name_ar}, industry: {industry}, icp_score: {icp}
- Recent signals: {signals}
- Recent activities: {activities}
- Days since last activity: {idle_days}

Candidates (from business rules):
{rule_candidates}

Task:
1. Evaluate each candidate's relevance
2. Rank candidates by expected impact
3. Explain your reasoning
4. Identify any risks
5. Suggest the single Next Best Action

Output format: JSON
{
  "evaluation": "analysis text",
  "ranking": ["action_id_1", "action_id_2", ...],
  "explanation": "why this ranking",
  "confidence": 0.85,
  "signals_used": ["signal descriptions"],
  "risks": ["risk descriptions"]
}
```

---

## 6. Feedback & Learning Pipeline

```python
class FeedbackEngine:
    async def record_feedback(
        self, opportunity_id: str, nba_id: str,
        status: Literal["accepted", "dismissed", "completed"],
        reason: str | None = None,
    ):
        """Record user feedback on NBA recommendation."""
        feedback = NBAFeedback(
            nba_id=nba_id, opportunity_id=opportunity_id,
            status=status, reason=reason,
        )
        await self.store.save(feedback)
        await self.event_runtime.publish(DomainEvent(
            type="nba.feedback.recorded",
            aggregate_id=opportunity_id,
            data=asdict(feedback),
        ))

    async def update_rules_from_feedback(self):
        """Weekly job: Analyze feedback to adjust rule weights."""
        feedbacks = await self.store.get_feedback_since(days_ago=7)
        # Calculate acceptance rate per rule
        rule_stats = defaultdict(lambda: {"accepted": 0, "total": 0})
        for fb in feedbacks:
            nba = await self.store.get_nba(fb.nba_id)
            for ev in nba.evidence:
                if ev.type == "business_rule":
                    rule_stats[ev.source]["total"] += 1
                    if fb.status == "accepted":
                        rule_stats[ev.source]["accepted"] += 1
        # Adjust rule scores: +0.05 if acceptance > 70%, -0.05 if < 30%
        for rule_name, stats in rule_stats.items():
            rate = stats["accepted"] / max(stats["total"], 1)
            if rate > 0.7: self._boost_rule(rule_name, 0.05)
            elif rate < 0.3: self._reduce_rule(rule_name, 0.05)
```

---

*NBA Blueprint complete. Ready for Phase 5: NBA Contracts.*
