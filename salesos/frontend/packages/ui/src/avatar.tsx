import { forwardRef } from 'react'
import * as AvatarPrimitive from '@radix-ui/react-avatar'
import { cn } from './utils'

const avatarSizes = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
}

interface AvatarProps {
  src?: string
  alt?: string
  fallback?: string
  size?: keyof typeof avatarSizes
  className?: string
}

export const Avatar = forwardRef<HTMLSpanElement, AvatarProps>(
  ({ src, alt, fallback, size = 'md', className }, ref) => {
    return (
      <AvatarPrimitive.Root
        ref={ref}
        className={cn(
          'relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-[var(--bg-secondary)]',
          avatarSizes[size],
          className
        )}
      >
        <AvatarPrimitive.Image
          src={src}
          alt={alt}
          className="h-full w-full object-cover"
        />
        <AvatarPrimitive.Fallback
          className={cn(
            'flex h-full w-full items-center justify-center font-medium text-[var(--text-muted)]',
            !src && 'bg-[var(--bg-secondary)]'
          )}
        >
          {fallback}
        </AvatarPrimitive.Fallback>
      </AvatarPrimitive.Root>
    )
  }
)
Avatar.displayName = 'Avatar'
