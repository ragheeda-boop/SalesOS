import { cn } from "@salesos/ui"

type ContainerSize = 'sm' | 'md' | 'lg' | 'xl' | 'full'

interface ContainerProps {
  size?: ContainerSize
  as?: React.ElementType
  children: React.ReactNode
  className?: string
}

const SIZE_MAP: Record<ContainerSize, string> = {
  sm: 'max-w-[640px]',
  md: 'max-w-[768px]',
  lg: 'max-w-[1024px]',
  xl: 'max-w-[1280px]',
  full: 'max-w-full',
}

export function Container({ size = 'xl', as: Component = 'div', className, children, ...props }: ContainerProps) {
  return (
    <Component
      className={cn(
        'mx-auto w-full px-4 sm:px-6 lg:px-8',
        SIZE_MAP[size],
        className
      )}
      {...props}
    >
      {children}
    </Component>
  )
}
