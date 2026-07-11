import { cn } from "@salesos/ui"

type SkeletonVariant = 'text' | 'title' | 'avatar' | 'card' | 'table-row' | 'chart'

interface SkeletonProps {
  variant?: SkeletonVariant
  width?: string | number
  height?: string | number
  className?: string
  count?: number
}

const VARIANT_DEFAULTS: Record<SkeletonVariant, { className: string; width?: string; height?: string }> = {
  text: { className: 'h-3 w-full', height: '12px' },
  title: { className: 'h-5 w-3/5', height: '20px' },
  avatar: { className: 'rounded-full', width: '40px', height: '40px' },
  card: { className: 'h-32 w-full rounded-lg', height: '128px' },
  'table-row': { className: 'h-10 w-full', height: '40px' },
  chart: { className: 'h-24 w-full rounded-lg', height: '96px' },
}

function SkeletonItem({ variant = 'text', width, height, className }: SkeletonProps) {
  const defaults = VARIANT_DEFAULTS[variant]
  return (
    <div
      className={cn(
        'animate-pulse motion-reduce:animate-none rounded-md bg-neutral-200',
        defaults.className,
        className
      )}
      style={{
        width: width ?? defaults.width,
        height: height ?? defaults.height,
      }}
      aria-hidden="true"
    />
  )
}

export function Skeleton({ variant = 'text', width, height, className, count = 1 }: SkeletonProps) {
  if (variant === 'table-row') {
    return (
      <div className={cn('flex flex-col gap-2', className)} role="status" aria-label="Loading content">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <SkeletonItem variant="avatar" width="32px" height="32px" />
            <div className="flex-1 space-y-1.5">
              <SkeletonItem variant="title" />
              <SkeletonItem variant="text" width="60%" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (variant === 'chart') {
    return (
      <div className={cn('flex items-end gap-2', className)} role="status" aria-label="Loading content">
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="animate-pulse motion-reduce:animate-none rounded-md bg-neutral-200 flex-1"
            style={{ height: `${40 + Math.random() * 60}px` }}
            aria-hidden="true"
          />
        ))}
      </div>
    )
  }

  return (
    <div className={cn('space-y-2', className)} role="status" aria-label="Loading content">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonItem key={i} variant={variant} width={width} height={height} />
      ))}
    </div>
  )
}
