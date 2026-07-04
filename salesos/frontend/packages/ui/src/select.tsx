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
              'flex h-10 w-full items-center justify-between rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100 dark:placeholder:text-gray-500',
              error && 'border-red-500 focus:ring-red-500 focus:border-red-500',
              className
            )}
          >
            <SelectPrimitive.Value placeholder={placeholder || 'Select...'} />
            <SelectPrimitive.Icon>
              <ChevronDown className="h-4 w-4 text-gray-500 dark:text-gray-400" />
            </SelectPrimitive.Icon>
          </SelectPrimitive.Trigger>
          <SelectPrimitive.Portal>
            <SelectPrimitive.Content
              className={cn(
                'z-50 min-w-[200px] overflow-hidden rounded-lg border bg-white p-1 shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 dark:border-gray-700 dark:bg-gray-900'
              )}
            >
              <SelectPrimitive.Viewport>
                {options.map((opt) => (
                  <SelectPrimitive.Item
                    key={opt.value}
                    value={opt.value}
                    className={cn(
                      'relative flex cursor-pointer select-none items-center rounded-md px-3 py-2 text-sm outline-none hover:bg-gray-100 data-[disabled]:pointer-events-none data-[disabled]:opacity-50 dark:hover:bg-gray-800'
                    )}
                  >
                    <SelectPrimitive.ItemText>{opt.label}</SelectPrimitive.ItemText>
                  </SelectPrimitive.Item>
                ))}
              </SelectPrimitive.Viewport>
            </SelectPrimitive.Content>
          </SelectPrimitive.Portal>
        </SelectPrimitive.Root>
        {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
      </div>
    )
  }
)
Select.displayName = 'Select'
