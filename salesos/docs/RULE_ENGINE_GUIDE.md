# Rule Engine Guide

> Practical guide for creating, evaluating, and managing business rules in the SalesOS Decision Intelligence Platform.

---

## 1. What the Rule Engine Is

The Rule Engine (`salesos/packages/platform/decision/rule-engine/index.ts`) evaluates structured business rules against evidence and context to produce fired/skipped/conflicted outcomes. It is a lower-level component than the Decision Engine — the Decision Engine has its own built-in rule set, while the Rule Engine provides a full registry, condition matching, conflict detection, and audit trail.

Key capabilities:

- **Rule registry** — register, retrieve, and list rules by category
- **Condition matching** — rich operators (gt, lt, gte, lte, contains, in) plus exact and array matching
- **Conflict detection** — detects when conflicting rules fire in the same category
- **Conflict resolution** — resolves via priority, then weight, then version
- **Audit trail** — logs every evaluation decision (fired, skipped, conflicted, winner)
- **Custom rules** — `createRule()` helper for quick rule authoring

---

## 2. Built-in Rules

Seven rules are registered automatically when the `RuleEngine` is instantiated:

| ID | Name | Category | Priority | Weight | Action | Condition |
|----|------|----------|----------|--------|--------|-----------|
| `rule_expired_license` | Expired License | risk | 90 | 0.9 | `flag_as_risk` | `licenseStatus === 'expired'` |
| `rule_no_decision_maker` | No Decision Maker | risk | 80 | 0.7 | `flag_as_risk` | `decisionMakersCount <= 0` |
| `rule_low_confidence` | Low Confidence | warning | 60 | 0.5 | `flag_warning` | `evidenceConfidence < 0.4` |
| `rule_high_revenue` | High Revenue | opportunity | 85 | 0.85 | `flag_high_priority` | `opportunityValue > 500000` |
| `rule_government_tender` | Government Tender | strategic | 75 | 0.8 | `flag_strategic` | `hasGovernmentContracts === true` |
| `rule_high_hiring_growth` | High Hiring Growth | intent | 70 | 0.75 | `flag_intent_signal` | `hiringTrend === 'growing'` |
| `rule_relationship_strength` | Relationship Strength | relationship | 65 | 0.7 | `flag_strong_relationship` | `relationshipScore > 0.7` |

---

## 3. Creating Custom Rules

### Using `createRule()`

```ts
import { createRule } from '@salesos/decision/rule-engine'

const myRule = createRule({
  name: 'Saudi Market Entry',
  description: 'Flag companies expanding into Saudi Arabia as strategic',
  action: 'flag_strategic',
  priority: 80,
  category: 'strategic',
  weight: 0.8,
  conditions: {
    region: 'Saudi Arabia',
    employeeCount: { gt: 100 },
  },
})
```

`createRule` requires `name`, `description`, and `action`. Everything else has defaults:

| Field | Default |
|-------|---------|
| `id` | Auto-generated UUID (`rule_<uuid>`) |
| `priority` | 50 |
| `category` | `'general'` |
| `version` | `'1.0.0'` |
| `conditions` | `{}` |
| `weight` | 0.5 |

### Registering Rules

```ts
import { RuleEngine } from '@salesos/decision/rule-engine'

const engine = new RuleEngine()

// Single rule
engine.register(myRule)

// Multiple rules
engine.registerMany([rule1, rule2, rule3])
```

- Duplicate IDs throw an error: `Rule with id '...' already registered`
- `registerMany` silently skips already-registered rules (no throw).

### Listing and Retrieving Rules

```ts
// Get a specific rule
const rule = engine.getRule('rule_expired_license')

// List all rules
const allRules = engine.listRules()

// List by category
const riskRules = engine.listRules('risk')
```

All returned rules are copies — mutating them does not affect the registry.

---

## 4. Rule Structure

```ts
interface DecisionRule {
  id: string                        // Unique identifier
  name: string                      // Human-readable name
  description: string               // What this rule does
  priority: number                  // Higher = evaluated first, wins conflicts
  category: string                  // Groups rules for conflict detection
  version: string                   // Semver string for version-based resolution
  conditions: Record<string, unknown>  // Key-value conditions to match
  action: string                    // Action identifier when rule fires
  weight: number                    // 0.0–1.0, used in scoring and conflict resolution
}
```

### Key Design Decisions

- **priority** — Rules are sorted by priority descending before evaluation. Higher priority rules are evaluated and logged first.
- **category** — Conflict detection is scoped to a single category. Two rules in different categories never conflict even if their actions are similar.
- **weight** — Used as a secondary sort in the Decision Engine's scoring formula (40% of combined score). Also used as a tiebreaker in conflict resolution.

---

## 5. How Conditions Work

Conditions are `Record<string, unknown>` where each key is looked up in evidence `data` fields or `context.metadata`. The value determines the match logic.

### Simple Matching

```ts
// Exact match
conditions: { licenseStatus: 'expired' }

// Array membership (actual must be one of these)
conditions: { entityType: ['company', 'opportunity'] }

// Boolean
conditions: { hasGovernmentContracts: true }
```

### Operator-Based Matching

Wrap the expected value in an object with an operator key:

```ts
// Greater than
conditions: { opportunityValue: { gt: 500000 } }

// Less than
conditions: { evidenceConfidence: { lt: 0.4 } }

// Greater than or equal
conditions: { relationshipScore: { gte: 0.7 } }

// Less than or equal
conditions: { decisionMakersCount: { lte: 0 } }

// String contains
conditions: { companyName: { contains: 'Tech' } }

// Value must be in array
conditions: { department: { in: ['sales', 'marketing', 'engineering'] } }
```

### Condition Resolution Order

For each condition key, the engine checks:

1. **`context.metadata`** — if the key exists in metadata, its value is compared. If it doesn't match, the rule is skipped immediately.
2. **Evidence `data`** — searches evidence items for a matching `data[key]`.
3. **`evidence.*` prefix** — if the key starts with `evidence.`, it strips the prefix and matches against `e.confidence`, `e.type`, `e.severity`, or `e.data[strippedKey]`.

### Complete Operator Reference

| Operator | Type | Example | Matches When |
|----------|------|---------|-------------|
| *(exact)* | any | `'expired'` | `actual === expected` |
| *(array)* | any | `['a', 'b']` | `expected.includes(actual)` |
| `gt` | number | `{ gt: 500 }` | `actual > 500` |
| `lt` | number | `{ lt: 0.4 }` | `actual < 0.4` |
| `gte` | number | `{ gte: 0.7 }` | `actual >= 0.7` |
| `lte` | number | `{ lte: 0 }` | `actual <= 0` |
| `contains` | string | `{ contains: 'Tech' }` | `actual.includes('Tech')` |
| `in` | array | `{ in: [1, 2, 3] }` | `[1,2,3].includes(actual)` |

---

## 6. Conflict Detection and Resolution

### How Conflicts Are Detected

The engine groups fired rules by `category`. Within each category, if two rules have **different actions** but those actions are semantically related, they conflict:

**Risk actions:** `flag_risk`, `escalate`, `block`, `flag_as_risk`
**Positive actions:** `flag_priority`, `flag_high_priority`, `flag_strategic`, `flag_strong_relationship`

Any combination of two risk actions, two positive actions, or one risk + one positive in the same category is a conflict.

### Resolution Strategy

1. **Priority wins** — higher `priority` value wins
2. **Weight wins** — if priorities are equal, higher `weight` wins
3. **Version wins** — if both are equal, newer `version` wins

### Example

```
Rule A: category=risk, priority=90, action=flag_as_risk
Rule B: category=risk, priority=80, action=escalate

Conflict detected in 'risk' category.
Resolution: priority_based → Rule A wins (90 > 80).
Rule B is excluded from final fired rules.
```

---

## 7. Audit Trail

Every evaluation produces a complete audit log:

```ts
const result = await engine.evaluate(context, evidence)

for (const entry of result.auditLog) {
  console.log(`[${entry.timestamp}] ${entry.ruleId}: ${entry.event}`)
  if (entry.reason) console.log(`  Reason: ${entry.reason}`)
}
```

### Audit Event Types

| Event | Description |
|-------|-------------|
| `evaluated` | Rule was evaluated against conditions |
| `fired` | Rule conditions matched — rule fires |
| `skipped` | Rule conditions did not match |
| `conflicted` | Rule was involved in a conflict with another rule |
| `winner` | Rule won a conflict resolution |

Each entry includes:
- `timestamp` — ISO string
- `ruleId` / `ruleName` — which rule
- `event` — what happened
- `context` — the full context snapshot
- `evidenceIds` — evidence items considered
- `reason` — optional human-readable explanation
- `conflictWinner` — optional, the winning rule ID in conflicts

---

## 8. Examples: Custom Rules for Saudi Market

### Example 1: CR Compliance Check

```ts
import { createRule, RuleEngine } from '@salesos/decision/rule-engine'

const crComplianceRule = createRule({
  name: 'CR Expiry Warning',
  description: 'Flag companies whose Commercial Registration expires within 90 days',
  action: 'flag_warning',
  priority: 85,
  category: 'risk',
  weight: 0.9,
  conditions: {
    crExpiryDays: { lte: 90 },
    crStatus: 'active',
  },
})

const engine = new RuleEngine()
engine.register(crComplianceRule)

// Evaluate
const result = await engine.evaluate(
  { tenantId: 't1', actorId: 'u1', companyId: 'c1', metadata: { crExpiryDays: 45, crStatus: 'active' } },
  [{ id: 'e1', type: 'government', description: 'CR data', source: 'gov-api', confidence: 0.95, freshness: 'current', timestamp: new Date().toISOString(), data: { crExpiryDays: 45, crStatus: 'active' } }],
)

console.log(result.rulesFired.map(r => r.name))  // ['CR Expiry Warning']
```

### Example 2: Vision 2030 Strategic Fit

```ts
const vision2030Rule = createRule({
  name: 'Vision 2030 Alignment',
  description: 'Flag companies aligned with Saudi Vision 2030 sectors',
  action: 'flag_strategic',
  priority: 78,
  category: 'strategic',
  weight: 0.85,
  conditions: {
    sector: { in: ['technology', 'renewable_energy', 'tourism', 'mining', 'healthcare'] },
    country: 'SA',
  },
})

engine.register(vision2030Rule)
```

### Example 3: ZATCA Tax Compliance

```ts
const zatcaRule = createRule({
  name: 'ZATCA Non-Compliant',
  description: 'Flag companies not compliant with ZATCA e-invoicing',
  action: 'flag_as_risk',
  priority: 88,
  category: 'risk',
  weight: 0.95,
  conditions: {
    zatcaStatus: 'non_compliant',
    businessType: 'b2b',
  },
})

engine.register(zatcaRule)
```

### Example 4: Multi-condition Relationship Rule

```ts
const saudiPartnerRule = createRule({
  name: 'Strong Saudi Partner',
  description: 'Flag companies with strong local partnerships in KSA',
  action: 'flag_priority',
  priority: 72,
  category: 'relationship',
  weight: 0.75,
  conditions: {
    partnershipScore: { gte: 0.8 },
    localPresence: true,
    yearsInMarket: { gte: 3 },
  },
})

engine.register(saudiPartnerRule)
```

---

## 9. Best Practices

### Rule Design

- **One concern per rule.** Don't bundle multiple conditions that address different business questions into one rule.
- **Use meaningful IDs.** The `id` field appears in audit logs — `rule_zatca_non_compliant` is clearer than `rule_7`.
- **Version your rules.** Use semver (`1.0.0`, `1.1.0`, `2.0.0`) so conflict resolution can pick the newer rule when priorities are tied.
- **Set priorities deliberately.** Higher priority = evaluated first and wins conflicts. Risk rules should generally outrank opportunity rules.

### Condition Design

- **Use operators for ranges.** `{ gt: 500000 }` is clearer and more maintainable than hardcoding magic numbers.
- **Keep conditions specific.** Broad conditions (`{}`) fire on every context — use them only for universal rules like the data quality gate.
- **Leverage the `in` operator** for enumerated values rather than multiple OR conditions.

### Conflict Avoidance

- **Scope rules to narrow categories.** Two rules in `risk` conflict on risk actions; one in `risk` and one in `strategic` don't.
- **Use different actions** for different concerns. If two rules should both fire, give them the same action.
- **Review audit logs** after registering new rules to verify no unexpected conflicts.

### Performance

- **Register rules at startup.** The registry is static after construction — avoid re-registering on every request.
- **Keep the registry under 100 rules** for optimal evaluation speed. The engine evaluates all rules sequentially.
- **Use `listRules(category)`** to inspect a focused subset when debugging.

### Testing

```ts
import { RuleEngine, createRule } from '@salesos/decision/rule-engine'

const engine = new RuleEngine()

const testRule = createRule({
  name: 'Test Rule',
  description: 'Test',
  action: 'test_action',
  conditions: { score: { gte: 0.8 } },
})

engine.register(testRule)

const result = await engine.evaluate(
  { tenantId: 'test', actorId: 'test', metadata: { score: 0.9 } },
  [{ id: 'e1', type: 'signal', description: 'test', source: 'test', confidence: 0.9, freshness: 'current', timestamp: new Date().toISOString(), data: { score: 0.9 } }],
)

// Assert
console.assert(result.rulesFired.some(r => r.name === 'Test Rule'))
console.assert(result.rulesSkipped.length === 0)
console.assert(result.rulesConflicted.length === 0)
console.assert(result.auditLog.length > 0)
```
