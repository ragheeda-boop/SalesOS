"use client"

import { cn } from "@salesos/ui"
import type { NBARecommendation } from "./useNBA"

interface RecommendationCardProps {
  recommendation: NBARecommendation
  onAccept: () => void
  onDismiss: () => void
  onRefresh: () => void
}

const CONFIDENCE_COLORS = {
  high: "bg-success-500",
  medium: "bg-warning-500",
  low: "bg-danger-500",
}

const CONFIDENCE_LABELS = {
  high: "عالية",
  medium: "متوسطة",
  low: "منخفضة",
}

const SOURCE_LABELS = {
  rule: "قواعد الأعمال",
  ai: "الذكاء الاصطناعي",
  hybrid: "قواعد + ذكاء اصطناعي",
}

export function RecommendationCard({ recommendation, onAccept, onDismiss, onRefresh }: RecommendationCardProps) {
  const { recommendation: rec, evidence, explainability } = recommendation
  const action = rec?.actionLabel ?? rec?.action ?? ''
  const reason = rec?.reason ?? explainability?.why ?? ''
  const confidence = rec?.confidence ?? 0
  const confidenceLabel: 'high' | 'medium' | 'low' = confidence >= 0.7 ? 'high' : confidence >= 0.4 ? 'medium' : 'low'
  const source = (rec?.scores?.[0]?.type ?? 'rule') as keyof typeof SOURCE_LABELS
  const potentialRisks = rec?.risks ?? []
  const alternatives = rec?.alternatives ?? []

  return (
    <div
      className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 shadow-muhide-1"
      role="region"
      aria-label="Next Best Action"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">الخطوة التالية</h3>
        <span className={cn(
          "text-xs px-2 py-0.5 rounded-full font-medium",
          confidenceLabel === 'high' && "bg-success-100 text-success-700",
          confidenceLabel === 'medium' && "bg-warning-100 text-warning-700",
          confidenceLabel === 'low' && "bg-danger-100 text-danger-700",
        )}>
          {CONFIDENCE_LABELS[confidenceLabel]} ({Math.round(confidence * 100)}%)
        </span>
      </div>

      {/* Action + Reason */}
      <div className="mb-3">
        <p className="text-base font-medium text-[var(--text-primary)]">{reason}</p>
        <p className="text-xs text-[var(--text-muted)] mt-1">
          المصدر: {SOURCE_LABELS[source]}
        </p>
      </div>

      {/* Evidence Trail */}
      {evidence.length > 0 && (
        <details className="mb-3">
          <summary className="text-xs font-medium text-[var(--text-muted)] cursor-pointer hover:text-[var(--text-primary)]">
            الأدلة ({evidence.length})
          </summary>
          <div className="mt-2 space-y-1.5">
            {evidence.map((e, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]">
                <span className={cn(
                  "mt-0.5 w-1.5 h-1.5 rounded-full flex-shrink-0",
                  e.type === 'business_rule' && "bg-info-500",
                  e.type === 'signal' && "bg-warning-500",
                  e.type === 'ai_analysis' && "bg-purple-500",
                )} />
                <span>{e.description}</span>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* Risk Indicators */}
      {potentialRisks.length > 0 && (
        <div className="mb-3 space-y-1">
          {potentialRisks.map((r, i) => (
            <div key={i} className={cn(
              "flex items-center gap-2 text-xs px-2 py-1 rounded-md",
              r.level === 'high' && "bg-danger-50 text-danger-700",
              r.level === 'medium' && "bg-warning-50 text-warning-700",
              r.level === 'low' && "bg-neutral-50 text-neutral-600",
            )}>
              <span>⚠️</span>
              <span>{r.description}</span>
            </div>
          ))}
        </div>
      )}

      {/* Alternatives */}
      {alternatives.length > 0 && (
        <details className="mb-3">
          <summary className="text-xs font-medium text-[var(--text-muted)] cursor-pointer hover:text-[var(--text-primary)]">
            بدائل ({alternatives.length})
          </summary>
          <div className="mt-2 space-y-1">
            {alternatives.map((alt, i) => (
              <div key={i} className="flex items-center justify-between text-xs py-1 px-2 rounded-md hover:bg-[var(--bg-secondary)]">
                <span className="text-[var(--text-secondary)]">{alt.reason}</span>
                <span className="text-[var(--text-muted)]">{Math.round((alt.confidence ?? 0) * 100)}%</span>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-2 border-t border-[var(--border-default)]">
        <button
          onClick={onAccept}
          className="flex-1 h-8 text-sm font-medium text-white bg-[var(--muhide-orange)] rounded-lg hover:brightness-110 transition-all"
        >
          تنفيذ
        </button>
        <button
          onClick={onDismiss}
          className="px-3 h-8 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded-lg hover:bg-[var(--bg-secondary)] transition-all"
        >
          تجاهل
        </button>
        <button
          onClick={onRefresh}
          className="px-3 h-8 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded-lg hover:bg-[var(--bg-secondary)] transition-all"
          aria-label="تحديث التوصية"
        >
          ↻
        </button>
      </div>
    </div>
  )
}
