import { cn } from "@salesos/ui"
import { Typography } from "./typography"
import { Divider } from "./divider"
import { Stack } from "./stack"
import { useId } from "react"

interface SectionProps {
  title?: string
  description?: string
  actions?: React.ReactNode
  divider?: boolean
  as?: React.ElementType
  children: React.ReactNode
  className?: string
}

export function Section({ title, description, actions, divider = false, as: Component = 'section', className, children, ...props }: SectionProps) {
  const titleId = useId()

  return (
    <Component
      className={cn(
        'space-y-5',
        className
      )}
      aria-labelledby={title ? titleId : undefined}
      {...props}
    >
      {(title || description || actions) && (
        <Stack direction="row" justify="between" align="start" gap={4}>
          <div className="space-y-1 flex-1">
            {title && (
              <Typography variant="h4" color="primary" id={titleId}>
                {title}
              </Typography>
            )}
            {description && (
              <Typography variant="body-sm" color="muted">
                {description}
              </Typography>
            )}
          </div>
          {actions && (
            <Stack gap={2} align="center">
              {actions}
            </Stack>
          )}
        </Stack>
      )}
      {children}
      {divider && <Divider variant="full" />}
    </Component>
  )
}
