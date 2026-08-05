import { type ReactNode } from "react";
import { cn } from "./utils";
import { ChevronRight, MoreHorizontal } from "lucide-react";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  maxItems?: number;
  separator?: ReactNode;
  className?: string;
}

export function Breadcrumbs({ items, maxItems = 0, separator, className }: BreadcrumbsProps) {
  const showOverflow = maxItems > 0 && items.length > maxItems;
  const visibleItems = showOverflow ? [items[0], ...items.slice(-(maxItems - 1))] : items;
  const hasOverflow = showOverflow;

  return (
    <nav aria-label="breadcrumb" className={cn("flex items-center", className)}>
      <ol className="flex items-center gap-1 text-sm text-[var(--text-muted)]">
        {(hasOverflow ? visibleItems : items).map((item, i) => {
          const isLast = i === (hasOverflow ? visibleItems.length - 1 : items.length - 1);
          const isOverflowIndicator = hasOverflow && i === 0 && i !== items.length - 1;

          return (
            <li key={i} className="flex items-center gap-1">
              {isOverflowIndicator && i === 0 && (
                <>
                  {item.href ? (
                    <a
                      href={item.href}
                      className="hover:text-[var(--text-primary)] transition-colors"
                    >
                      {item.label}
                    </a>
                  ) : (
                    <span>{item.label}</span>
                  )}
                  {hasOverflow && (
                    <span className="flex items-center" aria-hidden="true">
                      {separator ?? <ChevronRight className="h-4 w-4 rtl:rotate-180" />}
                    </span>
                  )}
                  <span className="flex items-center" aria-hidden="true">
                    <MoreHorizontal className="h-4 w-4" />
                  </span>
                  <span className="flex items-center" aria-hidden="true">
                    {separator ?? <ChevronRight className="h-4 w-4 rtl:rotate-180" />}
                  </span>
                </>
              )}
              {(!isOverflowIndicator || i !== 0) && (
                <>
                  {isLast ? (
                    <span className="text-[var(--text-primary)] font-medium" aria-current="page">
                      {item.label}
                    </span>
                  ) : item.href ? (
                    <a
                      href={item.href}
                      className="hover:text-[var(--text-primary)] transition-colors"
                    >
                      {item.label}
                    </a>
                  ) : (
                    <span>{item.label}</span>
                  )}
                  {!isLast && (
                    <span className="flex items-center" aria-hidden="true">
                      {separator ?? <ChevronRight className="h-4 w-4 rtl:rotate-180" />}
                    </span>
                  )}
                </>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
