'use client'

import { cn } from '@salesos/ui'
import { Sparkles, Lightbulb, AlertTriangle, TrendingUp } from 'lucide-react'
import type { AIAnswer } from '@salesos/search'

interface AIAnswerCardProps {
  answer: AIAnswer
  className?: string
}

export function AIAnswerCard({ answer, className }: AIAnswerCardProps) {
  return (
    <div className={cn('overflow-hidden rounded-xl border border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-900/10', className)}>
      <div className="flex items-center gap-2 border-b border-purple-200 px-4 py-2 dark:border-purple-800">
        <Sparkles className="h-4 w-4 text-purple-600" />
        <span className="text-xs font-semibold text-purple-700 dark:text-purple-300">AI Answer</span>
        <span className="mr-auto text-[10px] text-purple-500">%{Math.round(answer.confidence * 100)} ثقة</span>
      </div>
      <div className="space-y-3 px-4 py-3">
        <p className="text-sm leading-relaxed text-purple-900 dark:text-purple-100">
          {answer.summary}
        </p>

        {answer.explanation && (
          <div className="flex items-start gap-2">
            <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600" />
            <p className="text-xs text-purple-800 dark:text-purple-200">{answer.explanation}</p>
          </div>
        )}

        {answer.recommendations && answer.recommendations.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-medium text-purple-700 dark:text-purple-300">
              <TrendingUp className="h-3.5 w-3.5" />
              توصيات
            </div>
            <ul className="mt-1 space-y-1">
              {answer.recommendations.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-purple-800 dark:text-purple-200">
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-purple-400" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {answer.risks && answer.risks.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-medium text-red-600 dark:text-red-400">
              <AlertTriangle className="h-3.5 w-3.5" />
              مخاطر
            </div>
            <ul className="mt-1 space-y-1">
              {answer.risks.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-red-700 dark:text-red-300">
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-400" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {answer.sources.length > 0 && (
          <div className="border-t border-purple-200 pt-2 dark:border-purple-800">
            <p className="text-[10px] font-medium text-purple-600 dark:text-purple-400">المصادر:</p>
            <div className="mt-1 flex flex-wrap gap-1">
              {answer.sources.map((s, i) => (
                <span key={i} className="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] text-purple-700 dark:bg-purple-900/50 dark:text-purple-300">
                  {s.title}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
