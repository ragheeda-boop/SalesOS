import type {
  Feedback,
  LearningEvent,
} from '../contracts/index'

export interface FeedbackRecord extends Feedback {
  id: string
  createdAt: string
}

export interface FeedbackStats {
  total: number
  accepted: number
  rejected: number
  ignored: number
  acceptanceRate: number
  totalRevenueImpact: number
  averageTimeToExecution: number | null
}

interface ValidationProblem {
  field: string
  message: string
}

function validateFeedback(feedback: Feedback): ValidationProblem[] {
  const problems: ValidationProblem[] = []

  if (!feedback.decisionId) {
    problems.push({ field: 'decisionId', message: 'decisionId is required' })
  }
  if (!feedback.tenantId) {
    problems.push({ field: 'tenantId', message: 'tenantId is required' })
  }
  if (!feedback.actorId) {
    problems.push({ field: 'actorId', message: 'actorId is required' })
  }
  if (!feedback.outcome || !['accepted', 'rejected', 'ignored'].includes(feedback.outcome)) {
    problems.push({ field: 'outcome', message: 'outcome must be accepted, rejected, or ignored' })
  }
  if (feedback.revenueImpact !== undefined && feedback.revenueImpact < 0) {
    problems.push({ field: 'revenueImpact', message: 'revenueImpact cannot be negative' })
  }
  if (feedback.timeToExecution !== undefined && feedback.timeToExecution < 0) {
    problems.push({ field: 'timeToExecution', message: 'timeToExecution cannot be negative' })
  }

  return problems
}

function buildLearningEvent(
  feedback: FeedbackRecord,
): LearningEvent {
  return {
    id: crypto.randomUUID(),
    type: 'acceptance_rate',
    decisionId: feedback.decisionId,
    metric: feedback.outcome,
    value: feedback.outcome === 'accepted' ? 1 : feedback.outcome === 'rejected' ? 0 : 0.5,
    factors: {
      revenueImpact: feedback.revenueImpact ?? 0,
      timeToExecution: feedback.timeToExecution ?? 0,
    },
    timestamp: feedback.createdAt,
  }
}

export class FeedbackEngine {
  private feedbackStore: Map<string, FeedbackRecord> = new Map()
  private eventsByTenant: Map<string, LearningEvent[]> = new Map()

  async submit(feedback: Feedback): Promise<{ id: string; accepted: boolean }> {
    const problems = validateFeedback(feedback)
    if (problems.length > 0) {
      return { id: '', accepted: false }
    }

    const id = crypto.randomUUID()
    const now = new Date().toISOString()

    const record: FeedbackRecord = {
      ...feedback,
      id,
      createdAt: now,
    }

    this.feedbackStore.set(id, record)

    const event = buildLearningEvent(record)
    const existing = this.eventsByTenant.get(feedback.tenantId) ?? []
    existing.push(event)
    this.eventsByTenant.set(feedback.tenantId, existing)

    return { id, accepted: true }
  }

  async getByDecision(decisionId: string): Promise<Feedback | null> {
    for (const record of this.feedbackStore.values()) {
      if (record.decisionId === decisionId) {
        const { id: _id, createdAt: _createdAt, ...feedback } = record
        return feedback
      }
    }
    return null
  }

  async getByTenant(tenantId: string, limit: number = 50): Promise<Feedback[]> {
    const results: Feedback[] = []
    for (const record of this.feedbackStore.values()) {
      if (record.tenantId === tenantId) {
        const { id: _id, createdAt: _createdAt, ...feedback } = record
        results.push(feedback)
        if (results.length >= limit) break
      }
    }
    return results
  }

  async getStats(tenantId: string): Promise<FeedbackStats> {
    const records: FeedbackRecord[] = []
    for (const record of this.feedbackStore.values()) {
      if (record.tenantId === tenantId) {
        records.push(record)
      }
    }

    const total = records.length
    const accepted = records.filter(r => r.outcome === 'accepted').length
    const rejected = records.filter(r => r.outcome === 'rejected').length
    const ignored = records.filter(r => r.outcome === 'ignored').length

    const totalRevenueImpact = records.reduce(
      (sum, r) => sum + (r.revenueImpact ?? 0),
      0,
    )

    const timed = records.filter(
      (r): r is FeedbackRecord & { timeToExecution: number } =>
        r.timeToExecution !== undefined,
    )
    const averageTimeToExecution = timed.length > 0
      ? timed.reduce((sum, r) => sum + r.timeToExecution, 0) / timed.length
      : null

    return {
      total,
      accepted,
      rejected,
      ignored,
      acceptanceRate: total > 0 ? accepted / total : 0,
      totalRevenueImpact,
      averageTimeToExecution,
    }
  }
}
