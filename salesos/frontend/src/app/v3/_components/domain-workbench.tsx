'use client'

import { useState, type ReactNode } from 'react'
import { cn } from '@salesos/ui'

export type DomainSection = {
 id: string
 label: string
 description: string
 /** Audience hint shown in the panel header */
 audience?: string
 body?: ReactNode
}

/**
 * Left subnav + content panel for Settings/Admin-style domain IA.
 * No AI rail — Ask AI stays in the topbar popup.
 */
export function DomainWorkbench({
 sections,
 defaultId,
 emptyHint = 'Connect data or open the matching legacy surface when ready. Nothing here invents live metrics.',
}: {
 sections: DomainSection[]
 defaultId?: string
 emptyHint?: string
}) {
 const initial = defaultId && sections.some((s) => s.id === defaultId) ? defaultId : sections[0]?.id
 const [activeId, setActiveId] = useState(initial ?? '')
 const active = sections.find((s) => s.id === activeId) ?? sections[0]

 if (!active) return null

 return (
 <div className="flex min-h-[420px] flex-col gap-4 lg:flex-row lg:gap-6">
 <nav
 aria-label="Domain sections"
 className="flex shrink-0 gap-1 overflow-x-auto lg:w-52 lg:flex-col lg:overflow-visible"
 >
 {sections.map((section) => {
 const selected = section.id === active.id
 return (
 <button
 key={section.id}
 type="button"
 onClick={() => setActiveId(section.id)}
 aria-current={selected ? 'page' : undefined}
 className={cn(
 'whitespace-nowrap rounded-[var(--radius-md)] px-3 py-2 text-left text-[13px] transition-colors',
 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]',
 selected
 ? 'bg-[var(--muhide-orange)]/10 font-medium text-[var(--muhide-orange)]'
 : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]',
 )}
 >
 {section.label}
 </button>
 )
 })}
 </nav>

 <section
 className="min-w-0 flex-1 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-5"
 aria-labelledby={`section-${active.id}-title`}
 >
 <div className="space-y-1 border-b border-[var(--border-default)] pb-4">
 <div className="flex flex-wrap items-center gap-2">
 <h2
 id={`section-${active.id}-title`}
 className="text-base font-semibold text-[var(--text-primary)]"
 >
 {active.label}
 </h2>
 {active.audience ? (
 <span className="rounded-full border border-[var(--border-default)] bg-[var(--bg-secondary)] px-2 py-0.5 text-[11px] text-[var(--text-muted)]">
 {active.audience}
 </span>
 ) : null}
 </div>
 <p className="text-sm text-[var(--text-secondary)]">{active.description}</p>
 </div>

 <div className="pt-4">
 {active.body ?? (
 <p className="text-sm leading-relaxed text-[var(--text-muted)]">{emptyHint}</p>
 )}
 </div>
 </section>
 </div>
 )
}
