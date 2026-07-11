# Revenue Intelligence — Architecture

> SalesOS Wave 3
> Last Updated: 2026-07-10

## Components

| Component | Purpose |
|-----------|---------|
| Forecast Intelligence | AI-powered revenue forecasting |
| Territory Intelligence | Territory allocation & optimization |
| Revenue Health | Multi-company revenue scorecard |
| Expansion Intelligence | Cross-sell/up-sell detection |
| Churn Intelligence | At-risk account detection |

## Data Flow

Wave 2 Opportunities + Pipeline + Tasks
  → Revenue Intelligence Engine
    → Forecast (weighted pipeline + historical)
    → Territory (coverage gaps, concentration risk)
    → Health (score per company, portfolio view)
    → Expansion (cross-sell signals, adjacent segments)
    → Churn (engagement drop, risk signals)
