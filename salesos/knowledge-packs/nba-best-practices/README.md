# NBA (Next Best Action) Best Practices — Knowledge Pack

> Patterns, scoring methodology, and implementation guidelines for the SalesOS Next Best Action engine.

---

## NBA Patterns for B2B SaaS

### Core Pattern: Score → Rank → Recommend → Learn

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Signals    │───▶│   Scoring    │───▶│  AI Reasoner │───▶│  Recommend   │
│  (Input)     │    │  (Rule-based)│    │  (LLM layer) │    │  (Output)    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                   │
                                                              ┌────▼────┐
                                                              │ Feedback│
                                                              │  Loop   │
                                                              └─────────┘
```

### Pattern 1: Event-Driven NBA
**Trigger**: New signal detected (hiring, funding, expansion, contract, tender)
**Action**: Re-evaluate all opportunities for the signal's company
**Cadence**: Real-time on signal ingestion

### Pattern 2: Time-Based NBA
**Trigger**: Periodic timer (daily/weekly)
**Action**: Scan all active opportunities for stagnation, risk changes
**Cadence**: Daily at 06:00 UTC

### Pattern 3: User-Initiated NBA
**Trigger**: User requests recommendation for specific opportunity
**Action**: Fresh computation with full context
**Cadence**: On-demand via API (`GET /opportunities/{id}/nba`)

### Pattern 4: Coordinated Multi-Agent NBA
**Trigger**: Complex goal (e.g., "prepare for meeting with Aramco")
**Action**: Coordinator dispatches to specialized agents in sequence
**Cadence**: On-demand via `AgentCoordinator`

---

## Scoring Methodology

### Composite Health Score (from DealHealthComputer)

```python
risk_score = stagnation * 0.4 + (1 - engagement) * 0.3 + timeline_risk * 0.3
health_score = max(0, 1 - risk_score)
```

### Factor Weights

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Stagnation | 0.40 | `min(1.0, days_since_last_activity / 30)` if >14 days, else 0 |
| Engagement | 0.30 | `min(1.0, total_activities / 20)` — inverted in composite |
| Timeline Risk | 0.30 | 1.0 if overdue, 0.5 if <7 days, 0.2 if <30 days, 0 otherwise |

### Signal-Based Scoring

| Signal Type | Weight | Decay | Impact |
|-------------|--------|-------|--------|
| FUNDING | 0.9 | 30 days | High — budget availability |
| EXPANSION | 0.8 | 60 days | High — growth intent |
| HIRING | 0.7 | 14 days | Medium — scaling indicator |
| LEADERSHIP | 0.6 | 90 days | Medium — decision-maker changes |
| CONTRACT | 0.8 | 30 days | High — procurement cycle |
| TENDER | 0.9 | 14 days | High — active buying signal |
| PARTNERSHIP | 0.5 | 60 days | Low-Medium — ecosystem moves |
| NEWS | 0.4 | 7 days | Low — information only |
| REGULATORY | 0.6 | 180 days | Medium — compliance needs |
| COMPETITOR_MOVE | 0.7 | 30 days | Medium — competitive pressure |

### Confidence Calculation

```python
# From GroundedBaseAgent fallback:
evidence_count = len(contacts) + len(opportunities) + len(signals)
fallback_confidence = min(0.3 + evidence_count * 0.05, 0.7)

# From NBA API:
confidence_label = "high" if confidence >= 0.8
                 else "medium" if confidence >= 0.5
                 else "low"
```

---

## Trigger Event Types & Weights

### High-Priority Triggers (Score >= 0.8)
1. **New Funding Round**: Company raised capital → budget available
2. **Government Tender Published**: Active procurement → respond quickly
3. **Executive Change**: New C-suite → new relationships needed
4. **Competitor Contract Loss**: Window of opportunity
5. **Company Expansion**: New office/market → new needs

### Medium-Priority Triggers (Score 0.5-0.79)
1. **Hiring Surge**: Scaling team → tool needs
2. **Partnership Announced**: Ecosystem integration needs
3. **Regulatory Change**: Compliance tool requirements
4. **Product Launch**: Go-to-market support needs
5. **Earnings Report**: Financial health indicator

### Low-Priority Triggers (Score < 0.5)
1. **News Mention**: Information gathering
2. **Social Media Activity**: Brand monitoring
3. **Minor Personnel Changes**: Watch list
4. **Industry Report**: Market intelligence

### Trigger Response Time SLAs

| Priority | Response SLA | Action |
|----------|-------------|--------|
| Critical (0.9-1.0) | 1 hour | Immediate outreach recommended |
| High (0.7-0.89) | 4 hours | Schedule follow-up within 24h |
| Medium (0.5-0.69) | 24 hours | Add to next review cycle |
| Low (<0.5) | 7 days | Monitor and reassess |

---

## A/B Testing Framework for NBA Recommendations

### Experiment Setup

```python
@dataclass
class NBAExperiment:
    id: str
    name: str
    variant_a: dict  # Control (current algorithm)
    variant_b: dict  # Treatment (new algorithm)
    traffic_split: float = 0.5  # 50/50 default
    start_date: datetime
    end_date: datetime
    min_sample_size: int = 100
    confidence_level: float = 0.95
```

### Metrics to Track

| Metric | Definition | Target |
|--------|-----------|--------|
| Acceptance Rate | % of NBA recommendations accepted | > 40% |
| Time to Action | Hours from recommendation to action | < 24h |
| Revenue Impact | Revenue from NBA-influenced deals | +15% |
| False Positive Rate | Bad recommendations / total | < 20% |
| User Satisfaction | Post-action feedback score | > 4.0/5.0 |
| Deal Velocity | Days from recommendation to close | -10% |

### Experiment Lifecycle

1. **Hypothesis**: "New scoring weight for FUNDING signals will increase acceptance by 10%"
2. **Design**: Random 50/50 split, 2-week run, minimum 100 opportunities per variant
3. **Execute**: Track all metrics, ensure no contamination
4. **Analyze**: Chi-squared test for acceptance rate, t-test for revenue
5. **Decide**: Ship winner or iterate

### Guardrails

- **Minimum sample**: 100 opportunities per variant
- **Maximum duration**: 30 days per experiment
- **Kill switch**: Auto-stop if acceptance rate drops > 20% vs baseline
- **No overlap**: One experiment per opportunity at a time

---

## Common Failure Modes & Mitigations

### 1. Cold Start Problem
**Symptom**: No signals → no recommendations
**Mitigation**:
- Use company profile data (industry, size, location) as fallback
- Apply industry benchmarks for similar companies
- Default to "research" action when data is insufficient

### 2. Signal Noise
**Symptom**: Too many low-quality signals → recommendation overload
**Mitigation**:
- Signal deduplication (same signal type within 24h)
- Confidence threshold filtering (min 0.5)
- Source reliability weighting
- User feedback loop to penalize noisy sources

### 3. Stale Data
**Symptom**: Recommendations based on outdated information
**Mitigation**:
- Freshness scores per data field (see Data Quality section)
- Automatic re-enrichment when freshness degrades
- Stale data warnings in recommendation output
- Time-decay on signal relevance

### 4. Confirmation Bias
**Symptom**: AI reinforces existing beliefs, misses contrarian signals
**Mitigation**:
- Include "devil's advocate" candidate actions
- Monitor for balanced signal representation
- Periodic audit of recommendation diversity
- Include negative evidence in prompts

### 5. Overfitting to Historical Patterns
**Symptom**: Works great on past data, fails on new patterns
**Mitigation**:
- Regular A/B testing against baseline
- Decay factors on historical patterns
- Market trend incorporation (not just company data)
- Human review for novel situations

### 6. Prompt Injection in AI Layer
**Symptom**: Malicious input corrupts LLM reasoning
**Mitigation**:
- Input sanitization (strip special tokens)
- Harmful pattern detection (regex-based)
- Output JSON validation
- Fallback to rule-only scoring when LLM fails

### 7. Score Gaming
**Symptom**: Users manipulate signals to get desired recommendations
**Mitigation**:
- Multi-source signal validation
- Cross-reference scoring (signal vs. activity vs. outcome)
- Manual override requires justification
- Audit trail for all feedback actions

---

## NBA API Reference

### Endpoints

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| GET | `/opportunities/{id}/nba` | Get current NBA | 30/min |
| POST | `/opportunities/{id}/nba/refresh` | Force recompute | 10/min |
| POST | `/opportunities/{id}/nba/feedback` | Record feedback | 30/min |

### Response Schema

```json
{
  "id": "string",
  "opportunity_id": "string",
  "action": "string (recommended action)",
  "reason": "string (explanation)",
  "confidence": 0.85,
  "confidence_label": "high|medium|low",
  "source": "rule_based|ai_enhanced",
  "alternatives": [
    {"action": "string", "reason": "string", "confidence": 0.7}
  ],
  "evidence": [
    {"type": "string", "description": "string", "source": "string", "confidence": 0.9}
  ],
  "potential_risks": [
    {"type": "string", "level": "high|medium|low", "description": "string"}
  ],
  "status": "pending|accepted|dismissed",
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
}
```

### Feedback Schema

```json
{
  "nba_id": "string (max 100 chars)",
  "action": "accepted|dismissed",
  "reason": "string (optional, max 1000 chars)"
}
```

---

## AI Reasoning Layer (from NBAReasoner)

### Prompt Structure

```json
{
  "system": "You are a senior sales strategist evaluating sales opportunities. "
            "Analyze the context and recommend the single Next Best Action. "
            "Output valid JSON only.",
  "user": {
    "opportunity": {"name": "...", "stage": "...", "value": 50000, "health": "healthy"},
    "company": {"name": "...", "industry": "..."},
    "days_since_last_activity": 7,
    "candidate_actions": [...],
    "task": "1. Evaluate each candidate's relevance\n2. Rank by expected revenue impact\n3. Explain reasoning\n4. Identify risks\n5. Suggest single NBA\nOutput: {ranking, explanation, confidence, risks}"
  }
}
```

### Output Validation

```python
# Validate LLM response
confidence = max(0.0, min(1.0, float(content.get("confidence", 0.5))))
ranking = [r for r in ranking if isinstance(r, dict) and "action" in r][:10]
risks = [str(r)[:200] for r in risks[:10]]
explanation = str(content.get("explanation", ""))[:2000]
```

### Fallback Strategy

```
LLM Available? ──Yes──▶ AI-Enhanced Recommendation
      │                        │
      No                       │
      │                        ▼
      ▼                  Validate Output
Rule-Only Score       ────Valid────▶ Return AI Recommendation
                                    │
                                  Invalid
                                    │
                                    ▼
                              Rule-Only Fallback
```

---

*Last updated: 2026-07-13*
*Version: 1.0*
