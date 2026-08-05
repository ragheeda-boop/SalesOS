"use client";

import {
  useState,
  useCallback,
  useRef,
  useEffect,
  type ReactNode,
  type KeyboardEvent,
} from "react";
import { cn } from "./utils";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface SidebarBadge {
  count: number;
  variant?: "default" | "danger" | "warning";
}

interface SidebarItem {
  icon?: ReactNode;
  label: string;
  href?: string;
  active?: boolean;
  badge?: SidebarBadge | number;
  children?: SidebarItem[];
}

interface SidebarSection {
  title?: string;
  items: SidebarItem[];
}

interface SidebarProps {
  sections?: SidebarSection[];
  items?: SidebarItem[];
  collapsed?: boolean;
  onToggle?: () => void;
  activePath?: string;
  className?: string;
}

function resolveBadge(badge?: SidebarBadge | number): SidebarBadge | undefined {
  if (badge == null) return undefined;
  if (typeof badge === "number") return { count: badge, variant: "default" };
  return badge;
}

function isActive(item: SidebarItem, activePath?: string): boolean {
  if (item.active) return true;
  if (activePath && item.href && activePath.startsWith(item.href)) return true;
  if (item.children) return item.children.some((c) => isActive(c, activePath));
  return false;
}

export function Sidebar({
  sections,
  items,
  collapsed = false,
  onToggle,
  activePath,
  className,
}: SidebarProps) {
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const navRef = useRef<HTMLElement>(null);

  const resolvedSections: SidebarSection[] = sections ?? (items ? [{ items }] : []);
  const flatItems = resolvedSections.flatMap((s) => s.items);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!flatItems.length) return;
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setFocusedIndex((prev) => (prev + 1) % flatItems.length);
          break;
        case "ArrowUp":
          e.preventDefault();
          setFocusedIndex((prev) => (prev - 1 + flatItems.length) % flatItems.length);
          break;
        case "Enter":
        case " ":
          e.preventDefault();
          if (focusedIndex >= 0 && focusedIndex < flatItems.length) {
            const item = flatItems[focusedIndex];
            if (item.href) {
              if (item.href.startsWith("http")) {
                window.open(item.href, "_blank");
              } else {
                window.location.href = item.href;
              }
            }
          }
          break;
      }
    },
    [flatItems, focusedIndex]
  );

  useEffect(() => {
    if (focusedIndex >= 0 && navRef.current) {
      const items = navRef.current.querySelectorAll<HTMLButtonElement>("[data-sidebar-item]");
      items[focusedIndex]?.focus();
    }
  }, [focusedIndex]);

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-[var(--border-default)] bg-[var(--bg-primary)] transition-all duration-300 motion-reduce:transition-none rtl:border-l rtl:border-r-0",
        collapsed ? "w-sidebar-collapsed" : "w-sidebar",
        className
      )}
      dir="auto"
    >
      <div className="flex h-14 items-center justify-end px-4 rtl:justify-start">
        <button
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          onClick={onToggle}
          className="rounded-md p-1 text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5 rtl:rotate-180" />
          ) : (
            <ChevronLeft className="h-5 w-5 rtl:rotate-180" />
          )}
        </button>
      </div>
      <nav
        ref={navRef}
        className="flex-1 space-y-2 overflow-y-auto px-2 pb-4"
        onKeyDown={handleKeyDown}
        role="navigation"
        aria-label="Sidebar navigation"
      >
        {resolvedSections.map((section, si) => (
          <SidebarSectionComponent
            key={si}
            section={section}
            collapsed={collapsed}
            activePath={activePath}
            level={0}
          />
        ))}
      </nav>
    </aside>
  );
}

function SidebarSectionComponent({
  section,
  collapsed,
  activePath,
  level,
}: {
  section: SidebarSection;
  collapsed: boolean;
  activePath?: string;
  level: number;
}) {
  const [expanded, setExpanded] = useState(true);

  if (collapsed && level > 0) return null;

  return (
    <div className={cn(level > 0 && "ml-3 rtl:ml-0 rtl:mr-3")}>
      {section.title && !collapsed && (
        <button
          onClick={() => setExpanded((p) => !p)}
          className="flex w-full items-center gap-2 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
          aria-expanded={expanded}
        >
          <span className="flex-1 text-left">{section.title}</span>
          <ChevronRight
            className={cn(
              "h-3 w-3 transition-transform motion-reduce:transition-none",
              expanded && "rotate-90"
            )}
          />
        </button>
      )}
      {(expanded || collapsed) && (
        <div className={cn("space-y-1", section.title && !collapsed && "mt-1")}>
          {section.items.map((item, ii) => (
            <SidebarItemComponent
              key={ii}
              item={item}
              collapsed={collapsed}
              activePath={activePath}
              level={0}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SidebarItemComponent({
  item,
  collapsed,
  activePath,
  level,
}: {
  item: SidebarItem;
  collapsed: boolean;
  activePath?: string;
  level: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = item.children && item.children.length > 0;
  const itemActive = isActive(item, activePath);
  const badge = resolveBadge(item.badge);

  if (level >= 3) return null;

  const handleClick = () => {
    if (hasChildren) {
      setExpanded((p) => !p);
    } else if (item.href) {
      if (item.href.startsWith("http")) {
        window.open(item.href, "_blank");
      } else {
        window.location.href = item.href;
      }
    }
  };

  return (
    <div>
      <button
        data-sidebar-item
        onClick={handleClick}
        className={cn(
          "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors motion-reduce:transition-none",
          itemActive
            ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]"
            : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]",
          collapsed && "justify-center px-2"
        )}
        tabIndex={0}
        aria-current={itemActive ? "page" : undefined}
        aria-expanded={hasChildren ? expanded : undefined}
        title={collapsed ? item.label : undefined}
        aria-label={collapsed ? item.label : undefined}
      >
        {item.icon && <span className="shrink-0">{item.icon}</span>}
        {!collapsed && (
          <>
            <span className="flex-1 truncate text-left">{item.label}</span>
            {badge && (
              <span
                className={cn(
                  "inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-medium",
                  badge.variant === "danger" && "bg-danger-500 text-white",
                  badge.variant === "warning" && "bg-warning-500 text-white",
                  (!badge.variant || badge.variant === "default") &&
                    "bg-[var(--muhide-orange)] text-white"
                )}
              >
                {badge.count}
              </span>
            )}
            {hasChildren && (
              <ChevronRight
                className={cn(
                  "h-4 w-4 transition-transform motion-reduce:transition-none rtl:rotate-180",
                  expanded && "rotate-90 rtl:-rotate-90"
                )}
              />
            )}
          </>
        )}
      </button>
      {collapsed && (
        <div className="absolute left-full top-0 z-dropdown ml-2 hidden rounded-md bg-[var(--muhide-ink)] px-3 py-1.5 text-xs text-white shadow-muhide-4 group-hover:block rtl:left-auto rtl:right-full rtl:ml-0 rtl:mr-2">
          {item.label}
          {badge && (
            <span className="ml-2 rounded-full bg-[var(--muhide-orange)] px-1.5 text-xs text-white">
              {badge.count}
            </span>
          )}
        </div>
      )}
      {!collapsed && hasChildren && expanded && (
        <div className="ml-4 mt-1 space-y-1 rtl:ml-0 rtl:mr-4">
          {item.children!.map((child, ci) => (
            <SidebarItemComponent
              key={ci}
              item={child}
              collapsed={collapsed}
              activePath={activePath}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}
