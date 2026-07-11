import type { DecisionContext, DecisionResult } from '../contracts'

export interface AuditEntry {
  decisionId: string
  tenantId: string
  actorId: string
  context: DecisionContext
  rulesApplied: string[]
  scores: Record<string, number>
  evidenceCount: number
  recommendation: string
  confidence: number
  outcome: string | null
  timestamp: string
}

export class AuditLogger {
  private entries: AuditEntry[] = []

  log(result: DecisionResult): void {
    const scores: Record<string, number> = {}
    for (const s of result.scores) {
      scores[s.type] = s.value
    }
    this.entries.push({
      decisionId: result.decisionId,
      tenantId: result.context.tenantId,
      actorId: result.context.actorId,
      context: result.context,
      rulesApplied: result.rulesApplied.map((r) => r.id),
      scores,
      evidenceCount: result.evidence.length,
      recommendation: result.recommendation.action,
      confidence: result.recommendation.confidence,
      outcome: null,
      timestamp: result.timestamp,
    })
  }

  updateOutcome(decisionId: string, outcome: string): void {
    const entry = this.entries.find((e) => e.decisionId === decisionId)
    if (entry) {
      entry.outcome = outcome
    }
  }

  getByTenant(tenantId: string): AuditEntry[] {
    return this.entries.filter((e) => e.tenantId === tenantId)
  }

  getByDecision(decisionId: string): AuditEntry | undefined {
    return this.entries.find((e) => e.decisionId === decisionId)
  }

  getAll(): AuditEntry[] {
    return [...this.entries]
  }

  getRecent(limit = 50): AuditEntry[] {
    return this.entries.slice(-limit).reverse()
  }
}

export const auditLogger = new AuditLogger()
