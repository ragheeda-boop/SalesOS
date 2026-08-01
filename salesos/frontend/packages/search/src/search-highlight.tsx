'use client'

import { Fragment } from 'react'

interface SearchHighlightProps {
  text: string
  highlights?: string[]
  className?: string
}

/** Split `text` on case-insensitive literal highlight terms without RegExp (ReDoS-safe). */
function splitByHighlights(text: string, highlights: string[]): string[] {
  const terms = highlights.map((h) => h.trim()).filter(Boolean)
  if (terms.length === 0) return [text]

  const lower = text.toLowerCase()
  const parts: string[] = []
  let cursor = 0

  while (cursor < text.length) {
    let bestIdx = -1
    let bestLen = 0
    for (const term of terms) {
      const idx = lower.indexOf(term.toLowerCase(), cursor)
      if (idx === -1) continue
      if (bestIdx === -1 || idx < bestIdx || (idx === bestIdx && term.length > bestLen)) {
        bestIdx = idx
        bestLen = term.length
      }
    }
    if (bestIdx === -1) {
      parts.push(text.slice(cursor))
      break
    }
    if (bestIdx > cursor) {
      parts.push(text.slice(cursor, bestIdx))
    }
    parts.push(text.slice(bestIdx, bestIdx + bestLen))
    cursor = bestIdx + bestLen
  }

  return parts
}

export function SearchHighlight({ text, highlights, className }: SearchHighlightProps) {
  if (!highlights || highlights.length === 0) {
    return <span className={className}>{text}</span>
  }

  const parts = splitByHighlights(text, highlights)
  if (parts.length === 1 && parts[0] === text) {
    return <span className={className}>{text}</span>
  }

  return (
    <span className={className}>
      {parts.map((part, i) => {
        if (highlights.some((h) => h.toLowerCase() === part.toLowerCase())) {
          return (
            <mark key={i} className="rounded-sm bg-amber-200 px-0.5 dark:bg-amber-800/50">
              {part}
            </mark>
          )
        }
        return <Fragment key={i}>{part}</Fragment>
      })}
    </span>
  )
}

export function extractSnippets(text: string, query: string, maxLength = 120): string[] {
  if (!query || !text) return [text.slice(0, maxLength)]
  const lower = text.toLowerCase()
  const qLower = query.toLowerCase()
  const snippets: string[] = []
  let idx = 0

  while (idx < text.length && snippets.length < 3) {
    const matchIdx = lower.indexOf(qLower, idx)
    if (matchIdx === -1) break
    const start = Math.max(0, matchIdx - 40)
    const end = Math.min(text.length, matchIdx + qLower.length + 40)
    snippets.push(text.slice(start, end))
    idx = end
  }

  if (snippets.length === 0) snippets.push(text.slice(0, maxLength))
  return snippets.map((s) => (s.length < maxLength ? s : s.slice(0, maxLength) + '…'))
}
