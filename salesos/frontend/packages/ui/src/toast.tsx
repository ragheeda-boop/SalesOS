import { forwardRef, createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import * as ToastPrimitive from '@radix-ui/react-toast'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from './utils'
import { X } from 'lucide-react'

const toastVariants = cva(
  'group pointer-events-auto relative flex w-full items-center justify-between gap-2 rounded-lg border p-4 shadow-muhide-4 transition-all data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full',
  {
    variants: {
      variant: {
        default: 'border-[var(--border-default)] bg-[var(--bg-primary)] text-[var(--text-primary)]',
        success: 'border-success-200 bg-success-50 text-success-900',
        error: 'border-danger-200 bg-danger-50 text-danger-900',
      },
    },
    defaultVariants: { variant: 'default' },
  }
)

interface ToastProps extends VariantProps<typeof toastVariants> {
  title?: string
  description?: string
  onClose?: () => void
  className?: string
}

export const Toast = forwardRef<HTMLLIElement, ToastProps>(
  ({ title, description, variant, onClose, className, ...props }, ref) => {
    return (
      <ToastPrimitive.Root
        ref={ref}
        className={cn(toastVariants({ variant }), className)}
        {...props}
      >
        <div className="flex flex-col gap-1">
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
            className="shrink-0 rounded-md p-1 text-[var(--text-muted)] opacity-0 transition-opacity hover:text-[var(--text-primary)] focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100"
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
      <ToastPrimitive.Viewport className="fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:max-w-[420px]" />
    </ToastPrimitive.Provider>
  )
}

type ToastVariant = 'default' | 'success' | 'error'

interface ToastMessage {
  id: string
  variant: ToastVariant
  title?: string
  description?: string
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

  const ctx = useMemo<ToastContextValue>(() => {
    function dismiss(id: string) {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }

    function toast(input: ToastInput) {
      const id = `toast_${++toastCounter}`
      const msg: ToastMessage = { id, variant: input.variant ?? 'default', title: input.title, description: input.description }
      setToasts((prev) => [...prev, msg].slice(-5))
      setTimeout(() => dismiss(id), input.duration ?? 5000)
      return id
    }

    return { toast, dismiss }
  }, [])

  return (
    <ToastContext.Provider value={ctx}>
      {children}
      <Toaster toasts={toasts} onDismiss={ctx.dismiss} />
    </ToastContext.Provider>
  )
}

function Toaster({ toasts, onDismiss }: { toasts: ToastMessage[]; onDismiss: (id: string) => void }) {
  if (!toasts.length) return null
  return (
    <div className="fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:max-w-[420px]">
      {toasts.map((t) => (
        <ToastPrimitive.Root
          key={t.id}
          className={cn(toastVariants({ variant: t.variant }))}
          open
          onOpenChange={(open) => { if (!open) onDismiss(t.id) }}
        >
          <div className="flex flex-col gap-1">
            {t.title && <ToastPrimitive.Title className="text-sm font-semibold">{t.title}</ToastPrimitive.Title>}
            {t.description && <ToastPrimitive.Description className="text-sm opacity-90">{t.description}</ToastPrimitive.Description>}
          </div>
          <ToastPrimitive.Close onClick={() => onDismiss(t.id)} className="shrink-0 rounded-md p-1 text-[var(--text-muted)] opacity-0 transition-opacity hover:text-[var(--text-primary)] focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100">
            <X className="h-4 w-4" />
          </ToastPrimitive.Close>
        </ToastPrimitive.Root>
      ))}
    </div>
  )
}

export function useToast(): ToastContextValue {
  return useContext(ToastContext)
}
