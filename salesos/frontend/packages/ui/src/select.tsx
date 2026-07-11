import { forwardRef } from 'react'
import * as SelectPrimitive from '@radix-ui/react-select'
import { ChevronDown } from 'lucide-react'
import { cn } from './utils'

interface SelectOption {
  label: string
  value: string
}

interface SelectProps {
  options: SelectOption[]
  placeholder?: string
  error?: string
  className?: string
  value?: string
  onChange?: (value: string) => void
}

export const Select = forwardRef<HTMLButtonElement, SelectProps>(
  ({ options, placeholder, error, className, value, onChange }, ref) => {
    return (
      <div className="w-full">
        <SelectPrimitive.Root value={value} onValueChange={onChange}>
          <SelectPrimitive.Trigger
            ref={ref}
            className={cn(
              'flex h-10 w-full items-center justify-between rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)] focus:border-[var(--muhide-orange)] disabled:cursor-not-allowed disabled:opacity-50',
              error && 'border-danger-500 focus:ring-danger-500 focus:border-danger-500',
              className
            )}
          >
            <SelectPrimitive.Value placeholder={placeholder || 'Select...'} />
            <SelectPrimitive.Icon>
              <ChevronDown className="h-4 w-4 text-[var(--text-muted)]" />
            </SelectPrimitive.Icon>
          </SelectPrimitive.Trigger>
          <SelectPrimitive.Portal>
            <SelectPrimitive.Content
              className={cn(
                'z-dropdown min-w-[200px] overflow-hidden rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-1 shadow-muhide-4 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95'
              )}
            >
              <SelectPrimitive.Viewport>
                {options.map((opt) => (
                  <SelectPrimitive.Item
                    key={opt.value}
                    value={opt.value}
                    className={cn(
                      'relative flex cursor-pointer select-none items-center rounded-md px-3 py-2 text-sm outline-none hover:bg-[var(--bg-secondary)] data-[disabled]:pointer-events-none data-[disabled]:opacity-50'
                    )}
                  >
                    <SelectPrimitive.ItemText>{opt.label}</SelectPrimitive.ItemText>
                  </SelectPrimitive.Item>
                ))}
              </SelectPrimitive.Viewport>
            </SelectPrimitive.Content>
          </SelectPrimitive.Portal>
        </SelectPrimitive.Root>
        {error && <p className="mt-1 text-sm text-danger-600">{error}</p>}
      </div>
    )
  }
)
Select.displayName = 'Select'
