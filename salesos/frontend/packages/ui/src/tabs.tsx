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
        className={cn('inline-flex items-center border-b gap-0 dark:border-gray-700', className)}
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
          'px-4 py-2 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700 data-[state=active]:border-blue-600 data-[state=active]:text-blue-600 dark:text-gray-400 dark:hover:text-gray-200 dark:data-[state=active]:text-blue-400',
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
