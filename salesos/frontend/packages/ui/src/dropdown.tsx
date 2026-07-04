import { forwardRef, type ReactNode, type ComponentPropsWithoutRef } from 'react'
import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { cn } from './utils'

interface DropdownProps {
  children: ReactNode
}

export function Dropdown({ children }: DropdownProps) {
  return <DropdownMenu.Root>{children}</DropdownMenu.Root>
}

export const DropdownTrigger = forwardRef<HTMLButtonElement, ComponentPropsWithoutRef<typeof DropdownMenu.Trigger>>(
  ({ className, children, ...props }, ref) => {
    return (
      <DropdownMenu.Trigger ref={ref} className={cn(className)} {...props} asChild>
        {children}
      </DropdownMenu.Trigger>
    )
  }
)
DropdownTrigger.displayName = 'DropdownTrigger'

export const DropdownContent = forwardRef<HTMLDivElement, ComponentPropsWithoutRef<typeof DropdownMenu.Content>>(
  ({ className, children, ...props }, ref) => {
    return (
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          ref={ref}
          className={cn(
            'z-50 min-w-[200px] rounded-lg border bg-white p-1 shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 dark:border-gray-700 dark:bg-gray-900',
            className
          )}
          {...props}
        >
          {children}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    )
  }
)
DropdownContent.displayName = 'DropdownContent'

interface DropdownItemProps extends ComponentPropsWithoutRef<typeof DropdownMenu.Item> {
  disabled?: boolean
}

export const DropdownItem = forwardRef<HTMLDivElement, DropdownItemProps>(
  ({ className, disabled, ...props }, ref) => {
    return (
      <DropdownMenu.Item
        ref={ref}
        disabled={disabled}
        className={cn(
          'flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm outline-none hover:bg-gray-100 data-[disabled]:pointer-events-none data-[disabled]:opacity-50 dark:hover:bg-gray-800',
          className
        )}
        {...props}
      />
    )
  }
)
DropdownItem.displayName = 'DropdownItem'
