import { forwardRef, type HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "./utils";

export const cardVariants = cva("rounded-xl border", {
  variants: {
    variant: {
      default: "border-[var(--border-default)] bg-[var(--bg-primary)] shadow-muhide-1",
      dark: "border-[var(--border-default)] bg-[var(--muhide-ink)] text-white shadow-muhide-1",
      bordered: "border-[var(--border-default)] bg-[var(--bg-primary)]",
    },
    padding: {
      sm: "p-3",
      md: "p-4",
      lg: "p-5",
    },
    accent: {
      none: "",
      orange: "border-s-[3px] border-s-[var(--muhide-orange)]",
    },
  },
  defaultVariants: {
    variant: "default",
    accent: "none",
  },
});

export interface CardProps
  extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof cardVariants> {}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, padding, accent, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(cardVariants({ variant, padding, accent }), className)}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return <div ref={ref} className={cn("flex flex-col gap-1 p-6", className)} {...props} />;
  }
);
CardHeader.displayName = "CardHeader";

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />;
  }
);
CardContent.displayName = "CardContent";

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    return <div ref={ref} className={cn("flex items-center p-6 pt-0", className)} {...props} />;
  }
);
CardFooter.displayName = "CardFooter";
