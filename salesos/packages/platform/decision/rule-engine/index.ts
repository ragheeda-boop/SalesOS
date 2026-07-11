import type {
  DecisionContext,
  DecisionRule,
  EvidenceItem,
} from '../contracts/index'

export interface RuleEvaluationResult {
  rulesApplied: DecisionRule[]
  rulesFired: DecisionRule[]
  rulesConflicted: RuleConflict[]
  rulesSkipped: DecisionRule[]
  auditLog: AuditEntry[]
}

export interface RuleConflict {
  ruleA: DecisionRule
  ruleB: DecisionRule
  resolution: 'priority_based' | 'category_based'
  winner: DecisionRule
}

interface AuditEntry {
  timestamp: string
  ruleId: string
  ruleName: string
  event: 'evaluated' | 'fired' | 'skipped' | 'conflicted' | 'winner'
  context: DecisionContext
  evidenceIds: string[]
  reason?: string
  conflictWinner?: string
}

function createAuditEntry(
  event: AuditEntry['event'],
  rule: DecisionRule,
  context: DecisionContext,
  evidenceIds: string[],
  reason?: string,
  conflictWinner?: string,
): AuditEntry {
  return {
    timestamp: new Date().toISOString(),
    ruleId: rule.id,
    ruleName: rule.name,
    event,
    context,
    evidenceIds,
    reason,
    conflictWinner,
  }
}

function matchesCondition(
  conditions: Record<string, unknown>,
  evidence: EvidenceItem[],
  context: DecisionContext,
): boolean {
  for (const [key, expected] of Object.entries(conditions)) {
    const evidenceMatch = evidence.find((e) => {
      if (e.data && key in e.data) {
        return matchValue(e.data[key], expected)
      }
      return false
    })

    const contextMatch =
      context.metadata && key in context.metadata
        ? matchValue(context.metadata[key], expected)
        : undefined

    if (contextMatch !== undefined) {
      if (!contextMatch) return false
      continue
    }

    if (!evidenceMatch) {
      const evKey = key.replace(/^evidence\./, '')
      const fromEvidence = evidence.find((e) => {
        if (evKey === 'confidence') return matchValue(e.confidence, expected)
        if (evKey === 'type') return matchValue(e.type, expected)
        if (evKey === 'severity') return matchValue(e.severity, expected)
        if (e.data && evKey in e.data) return matchValue(e.data[evKey], expected)
        return false
      })
      if (!fromEvidence) return false
    }
  }
  return true
}

function matchValue(actual: unknown, expected: unknown): boolean {
  if (typeof expected === 'object' && expected !== null && !Array.isArray(expected)) {
    const op = expected as Record<string, unknown>
    if ('gt' in op && typeof actual === 'number' && typeof op.gt === 'number') {
      return actual > op.gt
    }
    if ('lt' in op && typeof actual === 'number' && typeof op.lt === 'number') {
      return actual < op.lt
    }
    if ('gte' in op && typeof actual === 'number' && typeof op.gte === 'number') {
      return actual >= op.gte
    }
    if ('lte' in op && typeof actual === 'number' && typeof op.lte === 'number') {
      return actual <= op.lte
    }
    if ('contains' in op && typeof actual === 'string') {
      return actual.includes(op.contains as string)
    }
    if ('in' in op && Array.isArray(op.in)) {
      return op.in.includes(actual)
    }
  }
  if (Array.isArray(expected)) {
    return expected.includes(actual as never)
  }
  return actual === expected
}

function detectConflicts(
  firedRules: DecisionRule[],
): { conflicts: RuleConflict[]; winners: Set<string> } {
  const conflicts: RuleConflict[] = []
  const winners = new Set<string>()
  const byCategory = new Map<string, DecisionRule[]>()

  for (const rule of firedRules) {
    const existing = byCategory.get(rule.category) || []
    existing.push(rule)
    byCategory.set(rule.category, existing)
  }

  for (const category of byCategory.keys()) {
    const categoryRules = byCategory.get(category)!

    for (let i = 0; i < categoryRules.length; i++) {
      for (let j = i + 1; j < categoryRules.length; j++) {
        const a = categoryRules[i]
        const b = categoryRules[j]

        if (conflictingActions(a, b)) {
          let winner: DecisionRule
          let resolution: 'priority_based' | 'category_based'

          if (a.priority !== b.priority) {
            winner = a.priority > b.priority ? a : b
            resolution = 'priority_based'
          } else if (a.weight !== b.weight) {
            winner = a.weight > b.weight ? a : b
            resolution = 'category_based'
          } else {
            winner = a.version >= b.version ? a : b
            resolution = 'category_based'
          }

          conflicts.push({ ruleA: a, ruleB: b, resolution, winner })
          winners.add(winner.id)
        }
      }
    }
  }

  return { conflicts, winners }
}

function conflictingActions(a: DecisionRule, b: DecisionRule): boolean {
  if (a.action === b.action) return false

  const riskActions = new Set(['flag_risk', 'escalate', 'block', 'flag_as_risk'])
  const positiveActions = new Set(['flag_priority', 'flag_high_priority', 'flag_strategic', 'flag_strong_relationship'])

  const aIsRisk = riskActions.has(a.action)
  const bIsRisk = riskActions.has(b.action)
  const aIsPositive = positiveActions.has(a.action)
  const bIsPositive = positiveActions.has(b.action)

  if (aIsRisk && bIsRisk) return true
  if (aIsPositive && bIsPositive) return true
  if (aIsRisk && bIsPositive) return true
  if (aIsPositive && bIsRisk) return true

  return false
}

function createBuiltInRules(): DecisionRule[] {
  return [
    {
      id: 'rule_expired_license',
      name: 'Expired License',
      description: 'If company license status is expired, flag as risk',
      priority: 90,
      category: 'risk',
      version: '1.0.0',
      conditions: { licenseStatus: 'expired' },
      action: 'flag_as_risk',
      weight: 0.9,
    },
    {
      id: 'rule_no_decision_maker',
      name: 'No Decision Maker',
      description: 'If no decision makers identified, flag as risk',
      priority: 80,
      category: 'risk',
      version: '1.0.0',
      conditions: { decisionMakersCount: { lte: 0 } },
      action: 'flag_as_risk',
      weight: 0.7,
    },
    {
      id: 'rule_low_confidence',
      name: 'Low Confidence',
      description: 'If confidence < 0.4, flag as warning',
      priority: 60,
      category: 'warning',
      version: '1.0.0',
      conditions: { evidenceConfidence: { lt: 0.4 } },
      action: 'flag_warning',
      weight: 0.5,
    },
    {
      id: 'rule_high_revenue',
      name: 'High Revenue',
      description: 'If opportunity value > 500000, flag as high priority',
      priority: 85,
      category: 'opportunity',
      version: '1.0.0',
      conditions: { opportunityValue: { gt: 500000 } },
      action: 'flag_high_priority',
      weight: 0.85,
    },
    {
      id: 'rule_government_tender',
      name: 'Government Tender',
      description: 'If company has government contracts, flag as strategic',
      priority: 75,
      category: 'strategic',
      version: '1.0.0',
      conditions: { hasGovernmentContracts: true },
      action: 'flag_strategic',
      weight: 0.8,
    },
    {
      id: 'rule_high_hiring_growth',
      name: 'High Hiring Growth',
      description: 'If hiring trend is growing, flag as buying intent signal',
      priority: 70,
      category: 'intent',
      version: '1.0.0',
      conditions: { hiringTrend: 'growing' },
      action: 'flag_intent_signal',
      weight: 0.75,
    },
    {
      id: 'rule_relationship_strength',
      name: 'Relationship Strength',
      description: 'If relationship score > 0.7, flag as strong relationship',
      priority: 65,
      category: 'relationship',
      version: '1.0.0',
      conditions: { relationshipScore: { gt: 0.7 } },
      action: 'flag_strong_relationship',
      weight: 0.7,
    },
  ]
}

export class RuleEngine {
  private registry: Map<string, DecisionRule> = new Map()
  private version = '1.0.0'

  constructor() {
    this.registerMany(createBuiltInRules())
  }

  register(rule: DecisionRule): void {
    if (this.registry.has(rule.id)) {
      throw new Error(`Rule with id '${rule.id}' already registered`)
    }
    this.registry.set(rule.id, { ...rule })
  }

  registerMany(rules: DecisionRule[]): void {
    for (const rule of rules) {
      if (!this.registry.has(rule.id)) {
        this.registry.set(rule.id, { ...rule })
      }
    }
  }

  getRule(id: string): DecisionRule | undefined {
    const rule = this.registry.get(id)
    return rule ? { ...rule } : undefined
  }

  listRules(category?: string): DecisionRule[] {
    const all = Array.from(this.registry.values())
    if (!category) return all.map((r) => ({ ...r }))
    return all.filter((r) => r.category === category).map((r) => ({ ...r }))
  }

  getVersion(): string {
    return this.version
  }

  async evaluate(
    context: DecisionContext,
    evidence: EvidenceItem[],
  ): Promise<RuleEvaluationResult> {
    const sortedRules = Array.from(this.registry.values()).sort(
      (a, b) => b.priority - a.priority,
    )

    const rulesApplied: DecisionRule[] = []
    const rulesFired: DecisionRule[] = []
    const rulesSkipped: DecisionRule[] = []
    const auditLog: AuditEntry[] = []

    for (const rule of sortedRules) {
      rulesApplied.push(rule)

      const evidenceIds = evidence.map((e) => e.id)

      if (matchesCondition(rule.conditions, evidence, context)) {
        rulesFired.push(rule)
        auditLog.push(
          createAuditEntry('fired', rule, context, evidenceIds),
        )
      } else {
        rulesSkipped.push(rule)
        auditLog.push(
          createAuditEntry('skipped', rule, context, evidenceIds, 'conditions not met'),
        )
      }
    }

    const { conflicts, winners } = detectConflicts(rulesFired)

    const rulesConflicted: RuleConflict[] = []
    for (const conflict of conflicts) {
      rulesConflicted.push(conflict)
      const evidenceIds = evidence.map((e) => e.id)

      auditLog.push(
        createAuditEntry(
          'conflicted',
          conflict.winner,
          context,
          evidenceIds,
          `${conflict.resolution} conflict between '${conflict.ruleA.name}' and '${conflict.ruleB.name}'`,
        ),
      )
    }

    const finalFired = rulesFired.filter(
      (r) => winners.size === 0 || winners.has(r.id) || !rulesConflicted.some((c) => c.ruleA.id === r.id || c.ruleB.id === r.id),
    )

    for (const rule of finalFired) {
      if (winners.has(rule.id)) {
        const evidenceIds = evidence.map((e) => e.id)
        auditLog.push(
          createAuditEntry('winner', rule, context, evidenceIds, 'won conflict resolution', rule.id),
        )
      }
    }

    return {
      rulesApplied,
      rulesFired: finalFired,
      rulesConflicted,
      rulesSkipped,
      auditLog,
    }
  }
}

export function createRule(overrides: Partial<DecisionRule> & Pick<DecisionRule, 'name' | 'description' | 'action'>): DecisionRule {
  return {
    id: `rule_${crypto.randomUUID()}`,
    priority: 50,
    category: 'general',
    version: '1.0.0',
    conditions: {},
    weight: 0.5,
    ...overrides,
  }
}
