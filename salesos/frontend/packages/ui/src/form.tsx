"use client"

import { createContext, useContext, forwardRef, type ReactNode, type FormHTMLAttributes } from 'react'
import { cn } from './utils'

// --- Form Context ---

interface FormContextValue {
  onSubmit?: (e: React.FormEvent) => void
}

const FormContext = createContext<FormContextValue>({})

function useFormContext() {
  return useContext(FormContext)
}

// --- Form ---

interface FormProps extends FormHTMLAttributes<HTMLFormElement> {
  onSubmit?: (e: React.FormEvent) => void
}

export const Form = forwardRef<HTMLFormElement, FormProps>(
  ({ className, onSubmit, children, ...props }, ref) => {
    return (
      <FormContext.Provider value={{ onSubmit }}>
        <form
          ref={ref}
          onSubmit={onSubmit}
          className={cn('w-full', className)}
          noValidate
          {...props}
        >
          {children}
        </form>
      </FormContext.Provider>
    )
  }
)
Form.displayName = 'Form'

// --- FormSection ---

interface FormSectionProps {
  label?: string
  description?: string
  children: ReactNode
  className?: string
}

export function FormSection({ label, description, children, className }: FormSectionProps) {
  return (
    <div className={cn('space-y-4', className)} role="group" aria-labelledby={label ? 'form-section-label' : undefined}>
      {label && (
        <div className="mb-1">
          <h3 id="form-section-label" className="text-base font-semibold text-[var(--text-primary)]">
            {label}
          </h3>
          {description && (
            <p className="mt-1 text-sm text-[var(--text-muted)]">{description}</p>
          )}
        </div>
      )}
      <div className="space-y-4">
        {children}
      </div>
    </div>
  )
}

// --- FormRow ---

interface FormRowProps {
  children: ReactNode
  className?: string
  columns?: 2 | 3
}

export function FormRow({ children, className, columns = 2 }: FormRowProps) {
  return (
    <div
      className={cn(
        'grid gap-4',
        columns === 2 ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1 md:grid-cols-3',
        className
      )}
    >
      {children}
    </div>
  )
}

// --- FormActions ---

interface FormActionsProps {
  children: ReactNode
  className?: string
  align?: 'left' | 'center' | 'right'
}

export function FormActions({ children, className, align = 'right' }: FormActionsProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 border-t border-[var(--border-default)] pt-4',
        align === 'left' && 'justify-start',
        align === 'center' && 'justify-center',
        align === 'right' && 'justify-end',
        className
      )}
    >
      {children}
    </div>
  )
}

// --- FormField ---

interface FormFieldProps {
  label?: string
  name?: string
  error?: string
  required?: boolean
  helperText?: string
  children: ReactNode
  className?: string
}

export function FormField({
  label,
  name,
  error,
  required,
  helperText,
  children,
  className,
}: FormFieldProps) {
  const errorId = name ? `${name}-error` : undefined
  const helperId = name ? `${name}-helper` : undefined

  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {label && (
        <label
          htmlFor={name}
          className="text-sm font-medium text-[var(--text-secondary)]"
        >
          {label}
          {required && <span className="ms-1 text-danger-500" aria-hidden="true">*</span>}
        </label>
      )}
      <div
        aria-invalid={error ? true : undefined}
        aria-describedby={
          error && errorId
            ? errorId
            : helperText && helperId
              ? helperId
              : undefined
        }
      >
        {children}
      </div>
      {error && (
        <p id={errorId} role="alert" className="text-sm text-danger-600">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={helperId} className="text-sm text-[var(--text-muted)]">
          {helperText}
        </p>
      )}
    </div>
  )
}
