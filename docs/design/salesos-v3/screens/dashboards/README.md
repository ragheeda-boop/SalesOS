# Dashboard Library (Phase 4)

All homes use [Dashboard Engine](../../engines/dashboard-engine.md) + Widget SDK slots.

Shared widget set: KPI · AI Insight (Preview) · Alert · Trend · Chart · Quick Action · Recommendation · Timeline · Activity Feed.

| Dashboard | Primary persona | Key widgets |
|-----------|-----------------|-------------|
| Executive Cockpit | Executive | Revenue, Risk, Decisions due, AI brief |
| Sales | Sales Leader / AE | Pipeline, Forecast, My Work, NBA |
| Operations | RevOps | SLA, Workflow health, Data quality |
| Customer Success | CS | Health, Renewals, NPS |
| Finance | Finance | Invoices, Cash, Margin |
| Marketing | Marketing | Funnel, Campaigns (module gated) |
| Support | Support | Tickets, CSAT |
| Data Quality | RevOps | Completeness, Duplicates, Connector status |
| AI Ops | Admin | Agent health, Preview flags, Eval scores |

## Spec pattern (applies to each)

1. Purpose: role home. 2. Goals: answer “what needs me?”. 3. IA: filters + grid. 4. Layout: 12-col. 5. Wireframe: header + filter bar + widgets. 6. Components: PageHeader, WidgetGrid, Filters. 7. Flow: land → drill → object. 8–10. Stack widgets mobile; 2-col tablet; full desktop. 11. AI insights Preview. 12–15. Empty/Error/Loading/Permission per widget. 16. Lazy widgets. 17. h1 + live regions. 18. Marketplace installs.
