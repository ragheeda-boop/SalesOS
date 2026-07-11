# Analytics & Reporting Architecture

> **الهدف:** تصميم منصة تحليلات متكاملة — Data Warehouse, Pre-aggregated Cubes, تقارير قياسية ومخصصة
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Wave 3 — Sprint 13

---

## 1. Design Principles

1. **Operational DB ≠ Analytics DB** — Warehouse منفصل تمامًا عن OLTP database
2. **Pre-aggregate by Default** — 90% من الاستعلامات تجيب عليها Cubes
3. **Real-Time for Critical Metrics** — Pipeline value, win rate تبقى实时
4. **Self-Serve Reporting** — المستخدم يبني تقاريره بدون SQL
5. **Export in 3 Formats** — PDF, CSV, Scheduled Email

---

## 2. Data Warehouse Design

### Architecture

```
Operational DB (PostgreSQL)
      │
      │  Wave 1: companies, signals, contacts
      │  Wave 2: opportunities, activities, meetings, emails, nba, playbooks
      │  Wave 3: workflows, executions, documents, chunks, vectors
      │
      ▼
ETL Pipeline (Python + Kafka)
      │
      ├── Full Load (daily) — Static dimensions: companies, users
      ├── Incremental (hourly) — Transactions: opportunities, activities
      └── Real-Time (Kafka stream) — Critical metrics: pipeline value, stage changes
      │
      ▼
Data Warehouse (PostgreSQL — separate instance)
      │
      ├── Staging Layer (raw tables, mirror of operational DB)
      ├── Dimensions (time, company, user, opportunity, product)
      ├── Facts (pipeline_snapshot, activity_fact, workflow_fact)
      └── Cubes (pre-aggregated tables)
      │
      ▼
Analytics API (Python)
      │
      ├── Standard Reports (pre-defined queries)
      ├── Custom Report Builder (dynamic query generation)
      └── Export Engine (PDF, CSV, Email)
```

### Schema

```sql
-- ============================================================
-- Dimension: Date (for time-based analysis)
-- ============================================================
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,      -- YYYYMMDD
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,          -- 1-4
    month INTEGER NOT NULL,            -- 1-12
    month_name VARCHAR(20),
    month_name_ar VARCHAR(20),         -- "يناير"
    week INTEGER NOT NULL,             -- ISO week
    day_of_week INTEGER NOT NULL,      -- 1=Monday
    day_name VARCHAR(10),
    day_name_ar VARCHAR(10),
    is_weekend BOOLEAN NOT NULL,
    is_holiday_sa BOOLEAN DEFAULT FALSE -- Saudi holidays
);

-- ============================================================
-- Dimension: Company
-- ============================================================
CREATE TABLE dim_company (
    company_key SERIAL PRIMARY KEY,
    company_id UUID NOT NULL,
    name_ar VARCHAR(255),
    name_en VARCHAR(255),
    industry VARCHAR(100),
    city VARCHAR(100),
    region VARCHAR(100),
    country VARCHAR(100),
    employees_count INTEGER,
    annual_revenue NUMERIC(15,2),
    icp_score NUMERIC(3,2),
    created_at TIMESTAMPTZ,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    is_current BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- Dimension: User (Sales Rep, Manager)
-- ============================================================
CREATE TABLE dim_user (
    user_key SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    role VARCHAR(50),              -- rep / manager / vp
    team VARCHAR(100),
    region VARCHAR(100),
    manager_id UUID,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- Dimension: Opportunity
-- ============================================================
CREATE TABLE dim_opportunity (
    opportunity_key SERIAL PRIMARY KEY,
    opportunity_id UUID NOT NULL,
    name VARCHAR(500),
    company_key INTEGER REFERENCES dim_company(company_key),
    owner_key INTEGER REFERENCES dim_user(user_key),
    product VARCHAR(100),
    deal_size_category VARCHAR(20),  -- small / medium / large / enterprise
    created_date_key INTEGER REFERENCES dim_date(date_key),
    closed_date_key INTEGER REFERENCES dim_date(date_key),
    stage_at_close VARCHAR(50),
    is_won BOOLEAN,
    is_lost BOOLEAN,
    days_to_close INTEGER,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    is_current BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- Fact: Pipeline Snapshot (daily snapshot of pipeline state)
-- ============================================================
CREATE TABLE fact_pipeline_snapshot (
    snapshot_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    opportunity_key INTEGER NOT NULL REFERENCES dim_opportunity(opportunity_key),
    company_key INTEGER NOT NULL REFERENCES dim_company(company_key),
    owner_key INTEGER NOT NULL REFERENCES dim_user(user_key),
    stage VARCHAR(50) NOT NULL,
    value NUMERIC(15,2) NOT NULL,
    probability NUMERIC(3,2),
    weighted_value NUMERIC(15,2) GENERATED ALWAYS AS (value * probability) STORED,
    health VARCHAR(20),               -- healthy / at_risk / critical
    days_in_stage INTEGER,
    velocity NUMERIC(5,2),             -- avg days per stage
    forecast_category VARCHAR(20),     -- commit / best_case / pipeline
    PRIMARY KEY (snapshot_date_key, opportunity_key)
);

-- ============================================================
-- Fact: Activity (meetings, emails, calls, tasks)
-- ============================================================
CREATE TABLE fact_activity (
    activity_key SERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    opportunity_key INTEGER REFERENCES dim_opportunity(opportunity_key),
    company_key INTEGER REFERENCES dim_company(company_key),
    user_key INTEGER NOT NULL REFERENCES dim_user(user_key),
    activity_type VARCHAR(50) NOT NULL, -- meeting / email / call / task / note
    duration_minutes INTEGER,
    outcome VARCHAR(100),
    source VARCHAR(50)                 -- manual / workflow / ai
);

-- ============================================================
-- Fact: Workflow Execution
-- ============================================================
CREATE TABLE fact_workflow_execution (
    execution_key SERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    workflow_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    opportunity_key INTEGER REFERENCES dim_opportunity(opportunity_key),
    company_key INTEGER REFERENCES dim_company(company_key),
    trigger_type VARCHAR(20),
    state VARCHAR(20),                  -- completed / failed / cancelled
    total_duration_ms INTEGER,
    steps_total INTEGER,
    steps_failed INTEGER,
    error_category VARCHAR(100)
);
```

---

## 3. Pre-aggregated Cubes

### Cube Design

```python
class CubeBuilder:
    """Builds and refreshes pre-aggregated cubes."""

    CUBES = {
        "pipeline_cube": {
            "source": "fact_pipeline_snapshot",
            "dimensions": ["date_key", "stage", "owner_key", "company_key", "health"],
            "measures": {
                "total_value": "SUM(value)",
                "weighted_value": "SUM(weighted_value)",
                "opportunity_count": "COUNT(*)",
                "avg_probability": "AVG(probability)",
                "avg_velocity": "AVG(velocity)",
            },
            "refresh": "daily",      # Full refresh every day
            "retention_days": 730,   # 2 years
        },
        "team_cube": {
            "source": "fact_pipeline_snapshot",
            "dimensions": ["date_key", "owner_key", "stage"],
            "measures": {
                "pipeline_value": "SUM(weighted_value)",
                "deal_count": "COUNT(*)",
                "avg_deal_size": "AVG(value)",
                "win_count": "SUM(CASE WHEN stage = 'closed_won' THEN 1 ELSE 0 END)",
                "loss_count": "SUM(CASE WHEN stage = 'closed_lost' THEN 1 ELSE 0 END)",
            },
            "refresh": "daily",
            "retention_days": 365,
        },
        "forecast_cube": {
            "source": "fact_pipeline_snapshot",
            "dimensions": ["date_key", "owner_key", "forecast_category"],
            "measures": {
                "forecast_value": "SUM(weighted_value)",
                "opportunity_count": "COUNT(*)",
            },
            "refresh": "hourly",     # More frequent for forecast
            "retention_days": 180,
        },
        "activity_cube": {
            "source": "fact_activity",
            "dimensions": ["date_key", "user_key", "activity_type", "opportunity_key"],
            "measures": {
                "activity_count": "COUNT(*)",
                "total_duration": "SUM(duration_minutes)",
                "avg_duration": "AVG(duration_minutes)",
            },
            "refresh": "daily",
            "retention_days": 365,
        },
        "workflow_cube": {
            "source": "fact_workflow_execution",
            "dimensions": ["date_key", "workflow_id", "state", "trigger_type"],
            "measures": {
                "execution_count": "COUNT(*)",
                "success_count": "SUM(CASE WHEN state = 'completed' THEN 1 ELSE 0 END)",
                "failure_count": "SUM(CASE WHEN state = 'failed' THEN 1 ELSE 0 END)",
                "avg_duration_ms": "AVG(total_duration_ms)",
            },
            "refresh": "daily",
            "retention_days": 90,
        },
    }

    async def refresh_cube(self, cube_name: str):
        config = self.CUBES[cube_name]
        # Materialized view refresh
        await self.db.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY mv_{cube_name}")
```

### Cube Storage

```sql
-- Example: materialized view for pipeline cube
CREATE MATERIALIZED VIEW mv_pipeline_cube AS
SELECT
    snapshot_date_key,
    stage,
    owner_key,
    company_key,
    health,
    SUM(value) AS total_value,
    SUM(weighted_value) AS weighted_value,
    COUNT(*) AS opportunity_count,
    AVG(probability) AS avg_probability,
    AVG(velocity) AS avg_velocity
FROM fact_pipeline_snapshot
GROUP BY
    snapshot_date_key, stage, owner_key, company_key, health;

CREATE UNIQUE INDEX idx_mv_pipeline_cube
    ON mv_pipeline_cube (snapshot_date_key, stage, owner_key, company_key, health);
```

---

## 4. Standard Reports

### Report Catalog

| Report | Cube | Frequency | Description |
|--------|------|-----------|-------------|
| **Pipeline Health** | pipeline_cube | Real-time | Pipeline value by stage, weighted pipeline, deal count |
| **Team Performance** | team_cube | Daily | Per-rep metrics: pipeline, win rate, activity |
| **Forecast Accuracy** | forecast_cube | Weekly | Forecast vs actual by rep, category |
| **Activity Analysis** | activity_cube | Weekly | Activity types, trends, per-rep comparison |
| **Velocity Report** | pipeline_cube | Weekly | Avg days per stage, bottleneck detection |
| **Win/Loss Analysis** | pipeline_cube | Monthly | Win rate by industry, product, region |
| **Workflow Performance** | workflow_cube | Weekly | Workflow success rate, avg duration, common failures |

### Pipeline Health Report (Example)

```
═══════════════════════════════════════════════════════════════
                PIPELINE HEALTH REPORT
                SalesOS — Q3 2026
═══════════════════════════════════════════════════════════════

Pipeline Overview
─────────────────────────────────────────────────────────────
Total Pipeline Value:     SAR 12,450,000
Weighted Pipeline:        SAR 8,230,000
Deal Count:               47
Avg Deal Size:            SAR 264,893
Win Rate:                 42%

Pipeline by Stage
─────────────────────────────────────────────────────────────
Qualification     │  SAR 1,200,000  │  15 deals  │  ████████░░  80%
Discovery         │  SAR 2,800,000  │  12 deals  │  ██████░░░░  60%
Proposal          │  SAR 4,500,000  │  10 deals  │  ████████░░  80%
Negotiation       │  SAR 3,200,000  │   7 deals  │  ████████░░  80%
Closed Won        │  SAR   750,000  │   3 deals  │  ██████░░░░  60%

Team Performance (Top 5)
─────────────────────────────────────────────────────────────
Ahmed Al-Otaibi   │  SAR 2.1M  │  12 deals  │  55% win  │  🟢
Sara Al-Harbi     │  SAR 1.8M  │   9 deals  │  50% win  │  🟢
Mohammed Al-Qahtani│ SAR 1.5M  │   8 deals  │  38% win  │  🟡
Nora Al-Shehri    │  SAR 1.2M  │   7 deals  │  29% win  │  🟡
Khalid Al-Dossary │  SAR 0.8M  │   4 deals  │  25% win  │  🔴

At-Risk Deals
─────────────────────────────────────────────────────────────
opp_001  │  شركة الأمل  │  SAR 500K  │  Stagnation 14d   │  🔴
opp_015  │  شركة النور  │  SAR 300K  │  New Competitor  │  🟡
opp_032  │  شركة الفجر  │  SAR 200K  │  Timeline Slip   │  🟡

═══════════════════════════════════════════════════════════════
Generated: 2026-07-11 09:00 AST
```

---

## 5. Custom Report Builder

### Architecture

```
Report Builder (Frontend)
      │
      ├── Dimension Selector (date, company, user, stage, product, etc.)
      ├── Measure Selector (value, count, avg, win_rate, velocity, etc.)
      ├── Filter Builder (date range, stage, region, team, etc.)
      ├── Visualization Selector (table, bar, line, pie, funnel)
      └── Export Options (PDF, CSV, schedule)
      │
      ▼
Analytics API (Backend)
      │
      ├── Dynamic Query Builder (generates SQL from selections)
      ├── Cube Router (serves from cube if available, falls back to raw warehouse)
      └── Cache Layer (identical queries → cached response)
      │
      ▼
Warehouse / Cube
```

### Query Builder

```python
class DynamicQueryBuilder:
    """Builds warehouse queries from report builder selections."""

    def build(self, report_config: ReportConfig) -> str:
        # 1. Select data source (cube or raw fact table)
        source = self._select_source(report_config.measures, report_config.dimensions)

        # 2. Build SELECT
        selects = []
        for dim in report_config.dimensions:
            selects.append(f"d_{dim}.{dim}_name AS {dim}")
        for measure in report_config.measures:
            selects.append(measure.sql)

        # 3. Build WHERE
        filters = self._build_filters(report_config.filters)

        # 4. Build GROUP BY
        group_by = report_config.dimensions

        # 5. Build ORDER BY
        order_by = report_config.sort_by or report_config.dimensions

        return f"""
            SELECT {', '.join(selects)}
            FROM {source}
            WHERE snapshot_date_key BETWEEN {filters.date_from} AND {filters.date_to}
                {filters.extra}
            GROUP BY {', '.join(group_by)}
            ORDER BY {', '.join(order_by)}
            LIMIT {report_config.limit or 1000}
        """
```

---

## 6. Export Engine

### Formats

| Format | Library | Notes |
|--------|---------|-------|
| **PDF** | ReportLab / WeasyPrint | Arabic RTL support, company branding |
| **CSV** | Python csv module | UTF-8 BOM for Excel Arabic support |
| **Excel (XLSX)** | openpyxl | Multi-sheet with formatting |
| **Scheduled Email** | SMTP / SendGrid | Attachment + body summary |

### Export Pipeline

```python
class ReportExportService:
    async def export(self, report: Report, format: str, options: ExportOptions) -> ExportResult:
        # 1. Fetch data
        data = await self.query_builder.execute(report.config)

        # 2. Build output
        if format == 'pdf':
            output = await self._build_pdf(report, data, options)
        elif format == 'csv':
            output = self._build_csv(report, data, options)
        elif format == 'xlsx':
            output = self._build_xlsx(report, data, options)

        # 3. Store
        file_id = await self.store.save(output, format, report.id)

        # 4. Send if scheduled
        if options.schedule:
            await self._send_email(options.email, report.name, file_id, format)

        return ExportResult(file_id=file_id, format=format, size=len(output))

    async def _build_pdf(self, report: Report, data: list[dict], options: ExportOptions) -> bytes:
        """Build PDF with Arabic RTL support."""
        # Template-based PDF generation
        html = self._render_template(report.template, data, options)
        pdf = await self.html_to_pdf(html)
        return pdf
```

### Scheduled Reports

```sql
CREATE TABLE scheduled_reports (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    report_config JSONB NOT NULL,
    format VARCHAR(10) NOT NULL,          -- pdf / csv / xlsx
    schedule_cron VARCHAR(100) NOT NULL,   -- e.g., "0 9 * * 1" (weekly Monday)
    recipients TEXT[] NOT NULL,            -- Email addresses
    last_sent_at TIMESTAMPTZ,
    next_send_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 7. Real-Time vs Batch Tradeoffs

| Metric | Priority | Refresh | Source | Why |
|--------|----------|---------|--------|-----|
| Pipeline Total Value | High | Real-time (Kafka stream) | Operational DB | Reps check this constantly |
| Win Rate | Medium | Hourly | Warehouse | Changes slowly |
| Forecast Accuracy | High | Hourly | Warehouse + Cube | VP decisions |
| Team Performance | Medium | Daily | Cube | Weekly review cadence |
| Activity Trends | Low | Daily | Cube | Not time-sensitive |
| Workflow Analytics | Medium | Daily | Warehouse | Operational review |
| Executive Dashboard | High | Real-time + Daily | Hybrid | KMs real-time, trends daily |

### Streaming Pipeline (Real-Time)

```
Kafka Topic: pipeline.snapshot.changed
      │
      ▼
Stream Processor (Python / Kafka Streams)
      │
      ▼
Redis (Real-time Aggregates)
      │
      ├── pipeline_total_value:{tenant_id}
      ├── pipeline_deal_count:{tenant_id}
      ├── stage_value:{tenant_id}:{stage}
      └── health_count:{tenant_id}:{health}
      │
      ▼
WebSocket → Dashboard (real-time updates)
```

### Batch Pipeline (Daily/Hourly)

```
Cron (hourly)
      │
      ▼
ETL Worker
      │
      ├── Extract from operational DB (since last run)
      ├── Transform to warehouse schema
      └── Load to staging + dimension + fact tables
      │
      ▼
Cube Refresh
      │
      └── Refresh materialized views
      │
      ▼
Cache Invalidation
      │
      └── Clear report cache for affected cubes
```

---

## 8. Integration with Wave 1 & 2

| Wave Component | Analytics Integration |
|----------------|---------------------|
| Company Intelligence | `dim_company` includes ICP, signals, industry for segmentation |
| Search | Unified search across warehouse and operational DB |
| Pipeline Intelligence | `fact_pipeline_snapshot` powers Pipeline Workspace analytics |
| NBA Engine | NBA acceptance rates → `activity_cube` for effectiveness analysis |
| Workflow Engine | `fact_workflow_execution` for workflow analytics |
| Meeting Intelligence | `fact_activity` includes meeting data for engagement analysis |
| Revenue Workspace | All cubes power the Revenue Workspace dashboards |

---

## 9. Performance Budget

| Operation | Budget | Violation Action |
|-----------|--------|-----------------|
| Standard report (cube-based) | < 1s | Optimize cube indexing |
| Custom report (simple) | < 3s | Suggest cube pre-aggregation |
| Custom report (complex) | < 10s | Timeout with partial results |
| PDF export (1000 rows) | < 10s | Queue for async processing |
| CSV export (10000 rows) | < 5s | Stream response |
| Cube refresh (full) | < 30m | Partition large fact tables |
| Real-time metric read | < 100ms | Redis cache |

---

*Analytics & Reporting Architecture complete. Ready for Sprint 13 implementation.*
