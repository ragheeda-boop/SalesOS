type V3DomainStubProps = {
 title: string
 description: string
}

/** Minimal domain landing — placeholder until object screens land. */
export function V3DomainStub({ title, description }: V3DomainStubProps) {
 return (
 <div className="mx-auto max-w-3xl space-y-2">
 <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-[var(--text-muted)]">
 Domain
 </p>
 <h1
 className="text-2xl font-semibold tracking-tight text-[var(--text-primary)]"
 style={{ fontFamily: 'var(--font-display)' }}
 >
 {title}
 </h1>
 <p className="text-sm leading-relaxed text-[var(--text-secondary)]">{description}</p>
 <p className="pt-2 text-[12px] text-[var(--text-muted)]">
 Placeholder under <code className="font-mono">/v3</code> — not Production GO.
 </p>
 </div>
 )
}
