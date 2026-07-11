import { cn } from "@salesos/ui"

type StackDirection = 'row' | 'column' | 'row-reverse' | 'column-reverse'
type StackAlign = 'start' | 'center' | 'end' | 'stretch' | 'baseline'
type StackJustify = 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly'
type StackGap = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 16 | 20
type StackWrap = 'wrap' | 'nowrap' | 'wrap-reverse'

interface StackProps {
  direction?: StackDirection
  gap?: StackGap
  align?: StackAlign
  justify?: StackJustify
  wrap?: StackWrap
  as?: React.ElementType
  children: React.ReactNode
  className?: string
}

const DIRECTION_MAP: Record<StackDirection, string> = {
  row: 'flex-row',
  column: 'flex-col',
  'row-reverse': 'flex-row-reverse',
  'column-reverse': 'flex-col-reverse',
}

const ALIGN_MAP: Record<StackAlign, string> = {
  start: 'items-start',
  center: 'items-center',
  end: 'items-end',
  stretch: 'items-stretch',
  baseline: 'items-baseline',
}

const JUSTIFY_MAP: Record<StackJustify, string> = {
  start: 'justify-start',
  center: 'justify-center',
  end: 'justify-end',
  between: 'justify-between',
  around: 'justify-around',
  evenly: 'justify-evenly',
}

const WRAP_MAP: Record<StackWrap, string> = {
  wrap: 'flex-wrap',
  nowrap: 'flex-nowrap',
  'wrap-reverse': 'flex-wrap-reverse',
}

export function Stack({ direction = 'row', gap = 3, align, justify, wrap, as: Component = 'div', className, children, ...props }: StackProps) {
  return (
    <Component
      className={cn(
        'flex',
        DIRECTION_MAP[direction],
        align && ALIGN_MAP[align],
        justify && JUSTIFY_MAP[justify],
        wrap && WRAP_MAP[wrap],
        gap !== undefined && `gap-${gap}`,
        className
      )}
      {...props}
    >
      {children}
    </Component>
  )
}
