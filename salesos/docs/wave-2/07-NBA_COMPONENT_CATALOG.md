# NBA Component Catalog

> **الهدف:** مكتبة المكونات القابلة لإعادة الاستخدام لـ NBA UI
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Phase 7 — Component Catalog

---

## Component Tree

```
NBAWidget (createWorkspaceWidget)
  │
  ├── RecommendationCard
  │     ├── ConfidenceBadge
  │     ├── ImpactMeter
  │     └── ActionLauncher
  │
  ├── EvidencePanel (expandable)
  │     └── EvidenceItem (per evidence entry)
  │
  ├── AlternativeActions
  │     └── AlternativeItem (per alternative)
  │
  ├── RiskPanel
  │     └── RiskItem (per risk factor)
  │
  └── FeedbackDialog (modal)
        └── DismissReasonSelect
```

---

## Component Catalog

### 1. RecommendationCard

**Purpose:** Display the primary NBA recommendation — action, reason, and confidence.

```typescript
interface RecommendationCardProps {
  action: string
  reason: string
  confidence: number
  confidenceLabel: 'high' | 'medium' | 'low'
  source: 'rule' | 'ai' | 'hybrid'
  dueBy?: string
  onAccept: () => void
  onDismiss: () => void
  onViewAlternatives: () => void
}

// States: ready, loading (skeleton), error, empty (no recommendation)
// Accessibility: role="region", aria-label="Next Best Action"
// Keyboard: Enter to accept, Esc to dismiss
// Arabic: RTL-aware layout
// Dark mode: CSS variables for all colors
```

**Empty State:** "لا توجد توصيات متاحة حاليًا. قم بتحديث بيانات الفرصة."

**Loading State:** Skeleton with card shape (title bar + 3 skeleton lines)

**Error State:** "تعذر تحميل التوصية. حاول مرة أخرى."

### 2. EvidencePanel

**Purpose:** Expandable panel showing the evidence trail for the recommendation.

```typescript
interface EvidencePanelProps {
  evidence: Evidence[]
  defaultOpen?: boolean
}

// Types: business_rule (📋), signal (🔔), ai_analysis (🤖), company_score (📊), activity (📝), risk_factor (⚠️)
// Each evidence item shows: type icon + description + source + confidence
// Expandable/collapsible: role="button", aria-expanded
```

**Empty State:** Collapsed by default. If no evidence, the panel is hidden.

### 3. ConfidenceBadge

**Purpose:** Visual indicator of recommendation confidence.

```typescript
interface ConfidenceBadgeProps {
  label: 'high' | 'medium' | 'low'
  score: number
  size?: 'sm' | 'md'
}

// high: green (#22c55e) / medium: amber (#f59e0b) / low: red (#ef4444)
// Tooltip shows exact score + breakdown
// aria-label: "High confidence: 92%"
```

### 4. ImpactMeter

**Purpose:** Estimated revenue impact visualization.

```typescript
interface ImpactMeterProps {
  estimatedRevenue?: number
  estimatedProbability?: number
  category: 'revenue' | 'relationship' | 'risk_mitigation' | 'information_gathering'
}

// Horizontal bar meter showing estimated revenue
// Category icon + label
// Format: SAR currency for revenue, percentage for probability
```

**Empty State:** If no estimated revenue, show "الأثر غير محدد كميًا"

### 5. RiskPanel

**Purpose:** Display risk factors affecting the recommendation.

```typescript
interface RiskPanelProps {
  risks: Risk[]
}

// RiskItem per risk: icon + type + severity badge + description
// Severity: low (gray), medium (amber), high (red)
// Compact list layout
```

**Empty State:** Hidden if no risks. "لا توجد مخاطر محددة."

### 6. AlternativeActions

**Purpose:** Show alternative actions ranked below the primary recommendation.

```typescript
interface AlternativeActionsProps {
  alternatives: Alternative[]
  onSelect: (action: string) => void
}

// List of alternative actions with confidence score
// Each item: action name + reason + confidence bar
// Click to select (expands in RecommendationCard)
// Max 5 alternatives shown
// Collapsible section: "بدائل (3)" — expand to see
```

**Empty State:** Hidden if no alternatives.

### 7. FeedbackDialog

**Purpose:** Collect user feedback when accepting or dismissing a recommendation.

```typescript
interface FeedbackDialogProps {
  open: boolean
  mode: 'accept' | 'dismiss'
  onConfirm: (reason?: string) => void
  onCancel: () => void
}

// Accept mode: simple confirmation "هل أنت متأكد من تنفيذ هذا الإجراء؟"
// Dismiss mode: reason selection (optional)
//   - "لست مستهدف هذه الفرصة"
//   - "الفرصة غير ناضجة بعد"
//   - "أخطط لإجراء مختلف"
//   - "أخرى" (text input)
// Modal overlay with keyboard trap
```

### 8. ActionLauncher

**Purpose:** Execute the recommended action (opens appropriate flow).

```typescript
interface ActionLauncherProps {
  action: string
  opportunityId: string
  onComplete?: () => void
}

// Maps action string to flow:
//   "send_introduction_email" → Email composer modal
//   "schedule_demo" → Calendar booking modal
//   "prepare_proposal" → Proposal generator
//   "send_follow_up" → Email composer with follow-up template
//   "escalate_to_manager" → Notification + task creation
//   "review_contract" → Contract viewer
```

### 9. DecisionTimeline

**Purpose:** Show history of NBA recommendations for an opportunity.

```typescript
interface DecisionTimelineProps {
  events: {
    timestamp: string
    action: string
    status: 'pending' | 'accepted' | 'dismissed' | 'completed'
    reason?: string
  }[]
}

// Vertical timeline layout
// Each event: icon + timestamp + action + status badge
// Staus colors: pending (blue), accepted (green), dismissed (gray), completed (green check)
```

## Widget Registration

```typescript
// NBAWidget registration in workspace
const NBAWidget = createWorkspaceWidget(
  { id: 'next-best-action', gridColumn: 'span 6' },
  useOpportunityContext,
  (widgets) => widgets.nba,
  {
    metadata: {
      title: 'الخطوة التالية',
      permissions: ['nba:read'],
      featureFlag: { enabled: true, tier: 'beta' },
      minHeight: '300px',
    },
    render: ({ data, onAction }) => (
      <NBAView
        recommendation={data?.recommendation}
        onAccept={() => onAction('accept')}
        onDismiss={() => onAction('dismiss')}
      />
    ),
  }
)
```

---

*NBA Component Catalog complete. Ready for Phase 8: Implementation Plan.*
