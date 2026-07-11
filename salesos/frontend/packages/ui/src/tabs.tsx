import { forwardRef, type ReactNode, type ComponentPropsWithoutRef } from 'react'
import * as TabsPrimitive from '@radix-ui/react-tabs'
import { cn } from './utils'

interface TabsProps {
  value?: string
  onValueChange?: (value: string) => void
  defaultValue?: string
  children: ReactNode
  className?: string
}

export function Tabs({ value, onValueChange, defaultValue, children, className }: TabsProps) {
  return (
    <TabsPrimitive.Root
      value={value}
      onValueChange={onValueChange}
      defaultValue={defaultValue}
      className={className}
    >
      {children}
    </TabsPrimitive.Root>
  )
}

export const TabsList = forwardRef<HTMLDivElement, ComponentPropsWithoutRef<typeof TabsPrimitive.List>>(
  ({ className, ...props }, ref) => {
    return (
      <TabsPrimitive.List
        ref={ref}
        className={cn('inline-flex items-center border-b border-[var(--border-default)] gap-0', className)}
        {...props}
      />
    )
  }
)
TabsList.displayName = 'TabsList'

export const Tab = forwardRef<HTMLButtonElement, ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>>(
  ({ className, ...props }, ref) => {
    return (
      <TabsPrimitive.Trigger
        ref={ref}
        className={cn(
          'px-4 py-2 text-sm font-medium border-b-2 border-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)] data-[state=active]:border-[var(--muhide-orange)] data-[state=active]:text-[var(--text-primary)]',
          className
        )}
        {...props}
      />
    )
  }
)
Tab.displayName = 'Tab'

export const TabsPanel = forwardRef<HTMLDivElement, ComponentPropsWithoutRef<typeof TabsPrimitive.Content>>(
  ({ className, ...props }, ref) => {
    return (
      <TabsPrimitive.Content
        ref={ref}
        className={cn('pt-4 outline-none', className)}
        {...props}
      />
    )
  }
)
TabsPanel.displayName = 'TabsPanel'
