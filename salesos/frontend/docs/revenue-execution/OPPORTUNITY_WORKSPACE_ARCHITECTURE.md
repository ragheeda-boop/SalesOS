# Opportunity Workspace — Architecture

> SalesOS Wave 2 · Revenue Execution Platform
> Last Updated: 2026-07-10

---

## Vision

The Opportunity Workspace is NOT a CRM deal view. It is a **Revenue Opportunity** — an AI-guided path from intelligence to revenue.

Every opportunity is created from a Next Best Action. Every opportunity has its own intelligence workspace.

---

## Data Model

```typescript
interface RevenueOpportunity {
  id: string
  companyId: string
  companyName: string
  title: string
  
  // Source
  source: 'nba' | 'manual' | 'import' | 'signal'
  sourceActionId?: string    // NBA action that created this
  
  // Value
  estimatedValue: number
  confidence: number
  stage: OpportunityStage
  
  // Timeline
  createdAt: string
  expectedCloseDate?: string
  stageChangedAt?: string
  
  // Intelligence (from Company DNA)
  buyingIntent: number
  relationshipStrength: number
  riskLevel: 'low' | 'medium' | 'high'
  
  // Assignment
  assignee?: string
  team?: string[]
  
  // Metadata
  tags: string[]
  notes: string[]
  lastActivityAt?: string
}
```

## Stages

| Stage | Label | Description |
|-------|-------|-------------|
| `identified` | تم التحديد | تم إنشاء الفرصة من NBA أو يدويًا |
| `qualifying` | قيد التأهيل | جمع المعلومات والتأكد من الملاءمة |
| `developing` | قيد التطوير | بناء العلاقة وتقديم القيمة |
| `proposing` | قيد العرض | تقديم العرض الرسمي |
| `negotiating` | قيد التفاوض | التفاوض على الشروط |
| `closing` | قيد الإغلاق | المراحل النهائية |
| `won` | فوز | تم إغلاق الصفقة بنجاح |
| `lost` | خسارة | تم إغلاق الصفقة بدون نجاح |

---

## Widget Architecture

### Opportunity List
```
OpportunityListContainer (createWidget)
  └── OpportunityListView
       ├── Filters (stage, confidence, assignee)
       ├── Sort (value, date, confidence)
       ├── OpportunityCard[]
       │    ├── Company name + stage badge
       │    ├── Value + confidence
       │    ├── Key metrics (intent, relationship, risk)
       │    └── Last activity
       ├── SearchEmpty
       └── SearchLoading
```

### Opportunity Detail
```
OpportunityDetailContainer (createWidget)
  └── OpportunityDetailView
       ├── Header (title, stage, value)
       ├── Intelligence Summary
       │    ├── Company DNA snapshot
       │    ├── Buying intent gauge
       │    └── Risk level
       ├── Activity Timeline
       ├── Notes Section
       └── Actions
            ├── Change Stage
            ├── Edit Value
            └── View Company Intelligence
```

---

## NBA Integration

```
User clicks "تنفيذ — إنشاء فرصة" on NBA widget
  → createOpportunity(nbaAction) called
    → RevenueOpportunity created
      → Stage: 'identified'
        → Estimated value from NBA
          → Confidence from NBA score
            → Navigate to Opportunity Workspace
```

---

## Scoring

Each opportunity has a **Winning Probability** score:

```
win_probability = 0.30 * stage_weight
                + 0.25 * buying_intent
                + 0.20 * relationship_strength
                + 0.15 * signal_activity
                + 0.10 * nba_confidence
```

Where `stage_weight`:
- identified: 0.10
- qualifying: 0.25
- developing: 0.45
- proposing: 0.65
- negotiating: 0.80
- closing: 0.90
