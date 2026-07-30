"use client"

import { forwardRef, createContext, useContext, useMemo, useState, useCallback, type ReactNode } from 'react'
import * as ToastPrimitive from '@radix-ui/react-toast'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from './utils'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'

const toastVariants = cva(
  'group pointer-events-auto relative flex w-full items-start gap-3 rounded-lg border p-4 shadow-muhide-4 transition-all motion-safe:data-[state=open]:animate-in motion-safe:data-[state=closed]:animate-out motion-safe:data-[swipe=end]:animate-out motion-safe:data-[state=closed]:fade-out-80 motion-safe:data-[state=closed]:slide-out-to-right-full motion-safe:data-[state=open]:slide-in-from-top-full',
  {
    variants: {
      variant: {
        default: 'border-[var(--border-default)] bg-[var(--bg-primary)] text-[var(--text-primary)]',
        success: 'border-success-200 bg-success-50 text-success-900 dark:bg-success-950 dark:border-success-800 dark:text-success-100',
        error: 'border-danger-200 bg-danger-50 text-danger-900 dark:bg-danger-950 dark:border-danger-800 dark:text-danger-100',
        warning: 'border-warning-200 bg-warning-50 text-warning-900 dark:bg-warning-950 dark:border-warning-800 dark:text-warning-100',
        info: 'border-info-200 bg-info-50 text-info-900 dark:bg-info-950 dark:border-info-800 dark:text-info-100',
      },
    },
    defaultVariants: { variant: 'info' },
  }
)

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  info: Info,
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
}

interface ToastProps extends VariantProps<typeof toastVariants> {
  title?: string
  description?: string
  onClose?: () => void
  className?: string
}

const toastVariantKeys = ['default', 'success', 'error', 'warning', 'info'] as const
type ToastVariantKey = (typeof toastVariantKeys)[number]

function normalizeVariant(v?: string | null): ToastVariantKey {
  if (!v || v === 'default') return 'info'
  if (toastVariantKeys.includes(v as ToastVariantKey)) return v as ToastVariantKey
  return 'info'
}

export const Toast = forwardRef<HTMLLIElement, ToastProps>(
  ({ title, description, variant, onClose, className, ...props }, ref) => {
    const v = normalizeVariant(variant)
    const Icon = iconMap[v]
    return (
      <ToastPrimitive.Root
        ref={ref}
        className={cn(toastVariants({ variant: v as ToastVariantKey }), className)}
        role="alert"
        aria-live="polite"
        {...props}
      >
        <Icon className="mt-0.5 h-5 w-5 shrink-0" />
        <div className="flex flex-1 flex-col gap-1">
          {title && (
            <ToastPrimitive.Title className="text-sm font-semibold">
              {title}
            </ToastPrimitive.Title>
          )}
          {description && (
            <ToastPrimitive.Description className="text-sm opacity-90">
              {description}
            </ToastPrimitive.Description>
          )}
        </div>
        {onClose && (
          <ToastPrimitive.Close
            onClick={onClose}
            className="shrink-0 rounded-md p-1 opacity-0 transition-opacity hover:opacity-100 focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100"
          >
            <X className="h-4 w-4" />
          </ToastPrimitive.Close>
        )}
      </ToastPrimitive.Root>
    )
  }
)
Toast.displayName = 'Toast'

interface ToastProviderProps {
  children: ReactNode
}

export function ToastProvider({ children }: ToastProviderProps) {
  return (
    <ToastPrimitive.Provider>
      {children}
      <ToastPrimitive.Viewport className="fixed bottom-0 right-0 z-toast flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:max-w-[420px] rtl:left-0 rtl:right-auto" />
    </ToastPrimitive.Provider>
  )
}

export type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'info'

interface ToastMessage {
  id: string
  variant: ToastVariant
  title?: string
  description?: string
  duration?: number
}

interface ToastInput {
  variant?: ToastVariant
  title?: string
  description?: string
  duration?: number
}

interface ToastContextValue {
  toast: (input: ToastInput) => void
  dismiss: (id: string) => void
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {}, dismiss: () => {} })

let toastCounter = 0

export function ToastViewport({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const toast = useCallback((input: ToastInput) => {
    const id = `toast_${++toastCounter}`
    const variant = input.variant ?? 'info'
    const msg: ToastMessage = { id, variant, title: input.title, description: input.description, duration: input.duration }
    setToasts((prev) => [...prev, msg].slice(-5))

    if (variant === 'info' || variant === 'success' || variant === 'default') {
      setTimeout(() => dismiss(id), input.duration ?? 5000)
    }
    return id
  }, [dismiss])

  const ctx = useMemo<ToastContextValue>(() => ({ toast, dismiss }), [toast, dismiss])

  return (
    <ToastContext.Provider value={ctx}>
      {children}
      <Toaster toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}

function Toaster({ toasts, onDismiss }: { toasts: ToastMessage[]; onDismiss: (id: string) => void }) {
  if (!toasts.length) return null
  return (
    <div className="fixed bottom-0 right-0 z-toast flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:max-w-[420px] rtl:left-0 rtl:right-auto">
      {toasts.map((t) => {
        const variant = normalizeVariant(t.variant)
        const Icon = iconMap[variant]
        return (
          <ToastPrimitive.Root
            key={t.id}
            className={cn(toastVariants({ variant: variant as ToastVariantKey }))}
            role="alert"
            aria-live="polite"
            open
            onOpenChange={(open) => { if (!open) onDismiss(t.id) }}
          >
            <Icon className="mt-0.5 h-5 w-5 shrink-0" />
            <div className="flex flex-1 flex-col gap-1">
              {t.title && <ToastPrimitive.Title className="text-sm font-semibold">{t.title}</ToastPrimitive.Title>}
              {t.description && <ToastPrimitive.Description className="text-sm opacity-90">{t.description}</ToastPrimitive.Description>}
            </div>
            <ToastPrimitive.Close onClick={() => onDismiss(t.id)} className="shrink-0 rounded-md p-1 opacity-0 transition-opacity hover:opacity-100 focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100">
              <X className="h-4 w-4" />
            </ToastPrimitive.Close>
          </ToastPrimitive.Root>
        )
      })}
    </div>
  )
}

export function useToast(): ToastContextValue {
  return useContext(ToastContext)
}
