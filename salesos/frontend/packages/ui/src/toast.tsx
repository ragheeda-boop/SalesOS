import { forwardRef, type ReactNode } from 'react'
import * as ToastPrimitive from '@radix-ui/react-toast'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from './utils'
import { X } from 'lucide-react'

const toastVariants = cva(
  'group pointer-events-auto relative flex w-full items-center justify-between gap-2 rounded-lg border p-4 shadow-lg transition-all data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full',
  {
    variants: {
      variant: {
        default: 'border-gray-200 bg-white text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100',
        success: 'border-green-200 bg-green-50 text-green-900 dark:border-green-800 dark:bg-green-950 dark:text-green-200',
        error: 'border-red-200 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-200',
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
            className="shrink-0 rounded-md p-1 text-gray-500 opacity-0 transition-opacity hover:text-gray-900 focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100 dark:text-gray-400 dark:hover:text-gray-50"
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
