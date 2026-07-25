/** Shared display helpers for v3 dual-run surfaces. */

export function formatCurrencySAR(value: number | null | undefined): string {
 if (value == null || Number.isNaN(value)) return '—'
 return new Intl.NumberFormat('en-SA', {
 style: 'currency',
 currency: 'SAR',
 maximumFractionDigits: 0,
 }).format(value)
}

export function formatPercent(value: number | null | undefined, { ratio = false } = {}): string {
 if (value == null || Number.isNaN(value)) return '—'
 const pct = ratio ? value * 100 : value
 return `${Math.round(pct)}%`
}

export function formatCount(value: number | null | undefined): string {
 if (value == null || Number.isNaN(value)) return '—'
 return new Intl.NumberFormat('en-SA').format(value)
}

export function stageLabel(stage: string | undefined | null): string {
 if (!stage) return '—'
 return stage.replace(/_/g, ' ')
}

export function formatWhen(iso: string | null | undefined): string {
 if (!iso) return '—'
 const d = new Date(iso)
 if (Number.isNaN(d.getTime())) return '—'
 return d.toLocaleString('en-SA', {
 dateStyle: 'medium',
 timeStyle: 'short',
 })
}
