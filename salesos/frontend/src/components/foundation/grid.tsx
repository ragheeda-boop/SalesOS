import { cn } from "@salesos/ui"

type GridCols = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12
type GridGap = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12
type GridAlign = 'start' | 'center' | 'end' | 'stretch'

interface GridProps {
  cols?: GridCols | { default?: GridCols; sm?: GridCols; md?: GridCols; lg?: GridCols; xl?: GridCols }
  gap?: GridGap
  align?: GridAlign
  as?: React.ElementType
  children: React.ReactNode
  className?: string
}

const ALIGN_MAP: Record<GridAlign, string> = {
  start: 'items-start',
  center: 'items-center',
  end: 'items-end',
  stretch: 'items-stretch',
}

function colsClass(cols: GridCols, breakpoint?: string): string {
  const prefix = breakpoint ? `${breakpoint}:` : ''
  return `${prefix}grid-cols-${cols}`
}

export function Grid({ cols = 1, gap = 4, align, as: Component = 'div', className, children, ...props }: GridProps) {
  const gridClasses = cn(
    'grid',
    typeof cols === 'number'
      ? colsClass(cols)
      : cn(
          cols.default && colsClass(cols.default),
          cols.sm && colsClass(cols.sm, 'sm'),
          cols.md && colsClass(cols.md, 'md'),
          cols.lg && colsClass(cols.lg, 'lg'),
          cols.xl && colsClass(cols.xl, 'xl'),
        ),
    gap !== undefined && `gap-${gap}`,
    align && ALIGN_MAP[align],
    className
  )

  return (
    <Component className={gridClasses} {...props}>
      {children}
    </Component>
  )
}
