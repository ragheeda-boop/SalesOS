"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@salesos/ui";
import { ChevronRight } from "lucide-react";
import { type Workspace, type NavGroup, type NavItem } from "@/lib/workspaces";
import { useTranslation } from "@/lib/i18n";

interface GroupedSidebarProps {
  workspace: Workspace;
  collapsed?: boolean;
}

function GroupSection({
  group,
  collapsed,
  pathname,
  t,
  defaultOpen,
}: {
  group: NavGroup;
  collapsed?: boolean;
  pathname: string;
  t: (key: string) => string;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen ?? true);

  const hasActive = group.items.some((item) => pathname.startsWith(item.href));

  useEffect(() => {
    if (hasActive) setOpen(true);
  }, [hasActive]);

  if (collapsed) {
    return (
      <div className="space-y-0.5">
        {group.items.map((item) => (
          <SidebarLink key={item.href} item={item} collapsed pathname={pathname} t={t} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-0.5">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-1 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition"
      >
        <ChevronRight
          className={cn("h-3 w-3 shrink-0 transition-transform", open && "rotate-90")}
        />
        <span className="truncate">{t(group.key)}</span>
      </button>
      {open && (
        <div className="space-y-0.5">
          {group.items.map((item) => (
            <SidebarLink key={item.href} item={item} collapsed={false} pathname={pathname} t={t} />
          ))}
        </div>
      )}
    </div>
  );
}

function SidebarLink({
  item,
  collapsed,
  pathname,
  t,
}: {
  item: NavItem;
  collapsed?: boolean;
  pathname: string;
  t: (key: string) => string;
}) {
  const Icon = item.icon;
  const active = pathname.startsWith(item.href);
  const label = t(item.key);

  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
        active
          ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] dark:bg-[var(--muhide-orange)]/20 dark:text-orange-300"
          : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]",
        collapsed && "justify-center px-2"
      )}
      title={collapsed ? label : undefined}
      {...(active ? { "aria-current": "page" as const } : {})}
    >
      <Icon className="h-5 w-5 shrink-0" />
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}

export function GroupedSidebar({ workspace, collapsed = false }: GroupedSidebarProps) {
  const pathname = usePathname();
  const { t } = useTranslation();

  return (
    <nav
      aria-label={t(workspace.key)}
      className={cn("flex-1 space-y-2", collapsed ? "p-2" : "p-2 overflow-y-auto")}
    >
      {workspace.groups.map((group) => (
        <GroupSection
          key={group.key}
          group={group}
          collapsed={collapsed}
          pathname={pathname}
          t={t}
          defaultOpen={true}
        />
      ))}
    </nav>
  );
}
