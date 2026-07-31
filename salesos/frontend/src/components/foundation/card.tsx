import { forwardRef, type HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn, CardHeader, CardContent } from "@salesos/ui";

const cardVariants = cva("rounded-xl border", {
  variants: {
    variant: {
      default:
        "border-[var(--border-default)] bg-[var(--bg-primary)] shadow-muhide-1",
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
      orange: "border-l-[3px] border-l-[var(--muhide-orange)]",
    },
  },
  defaultVariants: {
    variant: "default",
    padding: undefined,
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
  },
);
Card.displayName = "Card";

export { CardHeader, CardContent };
