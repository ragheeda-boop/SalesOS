'use client'

import { Fragment } from 'react'

interface SearchHighlightProps {
  text: string
  highlights?: string[]
  className?: string
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function SearchHighlight({ text, highlights, className }: SearchHighlightProps) {
  if (!highlights || highlights.length === 0) {
    return <span className={className}>{text}</span>
  }

  const pattern = highlights
    .filter(Boolean)
    .map((h) => escapeRegex(h.trim()))
    .join('|')

  if (!pattern) return <span className={className}>{text}</span>

  const regex = new RegExp(`(${pattern})`, 'gi')
  const parts = text.split(regex)

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
