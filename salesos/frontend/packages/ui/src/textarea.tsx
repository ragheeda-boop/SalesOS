"use client"

import { forwardRef, useId } from 'react'
import { cn } from './utils'

type ResizeOption = 'none' | 'both' | 'vertical' | 'horizontal'

interface TextareaProps extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'size'> {
  label?: string
  error?: boolean
  errorMessage?: string
  resize?: ResizeOption
}

const resizeClasses: Record<ResizeOption, string> = {
  none: 'resize-none',
  both: 'resize',
  vertical: 'resize-y',
  horizontal: 'resize-x',
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, errorMessage, resize = 'vertical', id: externalId, required, value, maxLength, ...props }, ref) => {
    const generatedId = useId()
    const id = externalId || generatedId
    const errorId = `${id}-error`

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={id} className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
            {label}
            {required && <span className="ms-1 text-danger-500" aria-hidden="true">*</span>}
          </label>
        )}
        <textarea
          ref={ref}
          id={id}
          required={required}
          value={value}
          maxLength={maxLength}
          aria-invalid={error || undefined}
          aria-describedby={error && errorMessage ? errorId : undefined}
          className={cn(
            'flex min-h-[80px] w-full rounded-lg border bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]',
            'focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)] focus:border-[var(--muhide-orange)]',
            'disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-danger-500 focus:ring-danger-500 focus:border-danger-500',
            resizeClasses[resize],
            className
          )}
          {...props}
        />
        {maxLength !== undefined && typeof value === 'string' && (
          <div className="mt-1 text-end text-xs text-[var(--text-muted)]">
            {value.length}/{maxLength}
          </div>
        )}
        {error && errorMessage && (
          <p id={errorId} role="alert" className="mt-1 text-sm text-danger-600">
            {errorMessage}
          </p>
        )}
      </div>
    )
  }
)
Textarea.displayName = 'Textarea'
