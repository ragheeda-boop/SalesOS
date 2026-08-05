"use client"

import { forwardRef, useCallback, useId } from 'react'
import { cn } from './utils'

interface CheckboxProps {
  checked?: boolean
  defaultChecked?: boolean
  onChange?: (checked: boolean) => void
  label?: string
  error?: boolean
  errorMessage?: string
  disabled?: boolean
  indeterminate?: boolean
  required?: boolean
  className?: string
  id?: string
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ checked, defaultChecked, onChange, label, error, errorMessage, disabled, indeterminate, required, className, id: externalId }, ref) => {
    const generatedId = useId()
    const id = externalId || generatedId
    const errorId = `${id}-error`
    const isControlled = checked !== undefined

    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange?.(e.target.checked)
      },
      [onChange]
    )

    const stateProps = isControlled
      ? { checked }
      : { defaultChecked }

    return (
      <div className={cn('flex flex-col', className)}>
        <label
          htmlFor={id}
          className={cn(
            'inline-flex items-center gap-2 cursor-pointer select-none',
            disabled && 'cursor-not-allowed opacity-50'
          )}
        >
          <span className="relative flex items-center justify-center">
            <input
              ref={ref}
              type="checkbox"
              id={id}
              disabled={disabled}
              required={required}
              role="checkbox"
              aria-checked={indeterminate ? 'mixed' : checked ?? false}
              aria-labelledby={label ? `${id}-label` : undefined}
              aria-describedby={error && errorMessage ? errorId : undefined}
              aria-invalid={error || undefined}
              className={cn(
                'peer h-4 w-4 shrink-0 appearance-none rounded border transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)] focus:ring-offset-2',
                error
                  ? 'border-danger-500 focus:border-danger-500 focus:ring-danger-500'
                  : 'border-[var(--border-default)]',
                'checked:border-[var(--muhide-orange)] checked:bg-[var(--muhide-orange)]',
                'indeterminate:border-[var(--muhide-orange)] indeterminate:bg-[var(--muhide-orange)]',
                disabled && 'cursor-not-allowed'
              )}
              {...stateProps}
              onChange={handleChange}
            />
            {(checked || (isControlled ? checked : false)) && !indeterminate && (
              <svg
                className="pointer-events-none absolute h-3 w-3 text-white"
                viewBox="0 0 12 12"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M2.5 6L5 8.5L9.5 3.5"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
            {indeterminate && (
              <svg
                className="pointer-events-none absolute h-3 w-3 text-white"
                viewBox="0 0 12 12"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M3 6H9"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            )}
          </span>
          {label && (
            <span id={`${id}-label`} className="text-sm text-[var(--text-primary)]">
              {label}
              {required && <span className="ms-1 text-danger-500" aria-hidden="true">*</span>}
            </span>
          )}
        </label>
        {error && errorMessage && (
          <p id={errorId} role="alert" className="mt-1 text-sm text-danger-600">
            {errorMessage}
          </p>
        )}
      </div>
    )
  }
)
Checkbox.displayName = 'Checkbox'
