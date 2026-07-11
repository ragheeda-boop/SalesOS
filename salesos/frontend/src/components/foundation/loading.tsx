import { cn } from "@salesos/ui"

type LoadingVariant = 'spinner' | 'dots' | 'pulse'
type LoadingSize = 'sm' | 'md' | 'lg'

interface LoadingProps {
  variant?: LoadingVariant
  size?: LoadingSize
  label?: string
  overlay?: boolean
  className?: string
}

const SIZE_MAP = { sm: 16, md: 24, lg: 36 }

export function Loading({ variant = 'spinner', size = 'md', label, overlay, className }: LoadingProps) {
  const dimension = SIZE_MAP[size]

  if (overlay) {
    return (
      <div className="fixed inset-0 z-overlay flex items-center justify-center bg-black/20">
        <LoadingInner variant={variant} dimension={dimension} label={label} />
      </div>
    )
  }

  return <LoadingInner variant={variant} dimension={dimension} label={label} className={className} />
}

function LoadingInner({ variant, dimension, label, className }: { variant: LoadingVariant; dimension: number; label?: string; className?: string }) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-2', className)} role="status" aria-label={label || 'Loading'} aria-live="polite">
      {variant === 'spinner' && (
        <svg className="animate-spin motion-reduce:animate-none text-[var(--muhide-orange)]" width={dimension} height={dimension} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.2" />
          <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        </svg>
      )}
      {variant === 'dots' && (
        <div className="flex gap-1.5" aria-hidden="true">
          {[0, 1, 2].map(i => (
            <div key={i} className="bg-[var(--muhide-orange)] rounded-full animate-bounce motion-reduce:animate-none" style={{ width: dimension * 0.3, height: dimension * 0.3, animationDelay: `${i * 150}ms` }} />
          ))}
        </div>
      )}
      {variant === 'pulse' && (
        <div className="relative" aria-hidden="true">
          <div className="bg-[var(--muhide-orange)]/20 rounded-full animate-ping motion-reduce:animate-none" style={{ width: dimension, height: dimension }} />
          <div className="absolute inset-0 bg-[var(--muhide-orange)] rounded-full" style={{ width: dimension * 0.6, height: dimension * 0.6, top: '20%', left: '20%' }} />
        </div>
      )}
      {label && <span className="text-sm text-[var(--text-muted)]">{label}</span>}
    </div>
  )
}
