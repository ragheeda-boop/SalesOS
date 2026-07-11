import { forwardRef, type ReactNode, type ComponentPropsWithoutRef } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { cn } from './utils'

interface ModalProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  children: ReactNode
}

export function Modal({ open, onOpenChange, children }: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      {children}
    </Dialog.Root>
  )
}

export const ModalTrigger = forwardRef<HTMLButtonElement, ComponentPropsWithoutRef<typeof Dialog.Trigger>>(
  ({ className, children, ...props }, ref) => {
    return (
      <Dialog.Trigger ref={ref} className={cn(className)} {...props}>
        {children}
      </Dialog.Trigger>
    )
  }
)
ModalTrigger.displayName = 'ModalTrigger'

export const ModalContent = forwardRef<HTMLDivElement, ComponentPropsWithoutRef<typeof Dialog.Content>>(
  ({ className, children, ...props }, ref) => {
    return (
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-overlay bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content
          ref={ref}
          className={cn(
            'fixed left-1/2 top-1/2 z-modal w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-xl bg-[var(--bg-primary)] p-6 shadow-muhide-4 duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95',
            className
          )}
          {...props}
        >
          {children}
          <Dialog.Close className="absolute right-4 top-4 rounded-sm p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)]">
            <X className="h-4 w-4" />
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    )
  }
)
ModalContent.displayName = 'ModalContent'

export const ModalHeader = forwardRef<HTMLDivElement, ComponentPropsWithoutRef<'div'>>(
  ({ className, ...props }, ref) => {
    return <div ref={ref} className={cn('text-lg font-semibold', className)} {...props} />
  }
)
ModalHeader.displayName = 'ModalHeader'

export const ModalBody = forwardRef<HTMLDivElement, ComponentPropsWithoutRef<'div'>>(
  ({ className, ...props }, ref) => {
    return <div ref={ref} className={cn('py-4', className)} {...props} />
  }
)
ModalBody.displayName = 'ModalBody'

export const ModalFooter = forwardRef<HTMLDivElement, ComponentPropsWithoutRef<'div'>>(
  ({ className, ...props }, ref) => {
    return <div ref={ref} className={cn('flex justify-end gap-2 pt-4', className)} {...props} />
  }
)
ModalFooter.displayName = 'ModalFooter'
