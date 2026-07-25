"use client"

import { forwardRef, useCallback, useState, useId } from 'react'
import { cn } from './utils'

type SwitchSize = 'sm' | 'md' | 'lg'

interface SwitchProps {
  checked?: boolean
  defaultChecked?: boolean
  onChange?: (checked: boolean) => void
  label?: string
  disabled?: boolean
  size?: SwitchSize
  className?: string
  id?: string
}

const sizeClasses: Record<SwitchSize, { track: string; thumb: string }> = {
  sm: { track: 'h-4 w-7', thumb: 'h-3 w-3 data-[state=checked]:translate-x-3' },
  md: { track: 'h-5 w-9', thumb: 'h-4 w-4 data-[state=checked]:translate-x-4' },
  lg: { track: 'h-6 w-11', thumb: 'h-5 w-5 data-[state=checked]:translate-x-5' },
}

export const Switch = forwardRef<HTMLButtonElement, SwitchProps>(
  ({ checked, defaultChecked, onChange, label, disabled, size = 'md', className, id: externalId }, ref) => {
    const generatedId = useId()
    const id = externalId || generatedId
    const isControlled = checked !== undefined
    const [internalChecked, setInternalChecked] = useState(defaultChecked ?? false)

    const currentChecked = isControlled ? checked : internalChecked

    const handleClick = useCallback(() => {
      if (disabled) return
      const newChecked = !currentChecked
      if (!isControlled) {
        setInternalChecked(newChecked)
      }
      onChange?.(newChecked)
    }, [disabled, isControlled, onChange, currentChecked])

    const { track, thumb } = sizeClasses[size]

    return (
      <div className={cn('inline-flex items-center gap-2', className)}>
        <button
          ref={ref}
          type="button"
          role="switch"
          id={id}
          aria-checked={currentChecked}
          aria-labelledby={label ? `${id}-label` : undefined}
          disabled={disabled}
          onClick={handleClick}
          className={cn(
            'relative inline-flex shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200',
            'focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)] focus:ring-offset-2',
            currentChecked
              ? 'bg-[var(--muhide-orange)]'
              : 'bg-[var(--border-default)]',
            disabled && 'cursor-not-allowed opacity-50',
            track
          )}
        >
          <span
            data-state={currentChecked ? 'checked' : 'unchecked'}
            className={cn(
              'inline-block transform rounded-full bg-white shadow-sm transition-transform duration-200',
              'data-[state=checked]:bg-white',
              thumb
            )}
          />
        </button>
        {label && (
          <span id={`${id}-label`} className="text-sm text-[var(--text-primary)]">
            {label}
          </span>
        )}
      </div>
    )
  }
)
Switch.displayName = 'Switch'
