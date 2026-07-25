import { cn } from './utils'

interface SkeletonProps {
  variant?: 'text' | 'circle' | 'rect' | 'card' | 'table-row'
  width?: string | number
  height?: string | number
  count?: number
  className?: string
}

function SkeletonEl({ variant, width, height, className }: Omit<SkeletonProps, 'count'>) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'motion-safe:animate-pulse bg-[var(--bg-tertiary)]',
        variant === 'text' && 'h-4 w-full rounded',
        variant === 'circle' && 'rounded-full',
        variant === 'rect' && 'rounded-lg',
        variant === 'card' && 'h-40 w-full rounded-xl',
        variant === 'table-row' && 'h-10 w-full rounded',
        className
      )}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
      }}
    />
  )
}

export function Skeleton({ variant = 'text', width, height, count = 1, className }: SkeletonProps) {
  const items = Array.from({ length: count }, (_, i) => i)
  return (
    <div className={cn('flex flex-col gap-3', className)} role="status" aria-label={`Loading ${count} items`}>
      {items.map((i) => (
        <SkeletonEl key={i} variant={variant} width={width} height={height} />
      ))}
    </div>
  )
}
