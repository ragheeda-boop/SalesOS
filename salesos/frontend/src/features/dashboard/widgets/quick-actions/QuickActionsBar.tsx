"use client";

import Link from "next/link";
import { useTranslation } from "@/lib/i18n";
import { Building2, Search, Plus, FileText, CalendarClock } from "lucide-react";

interface QuickActionItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  variant: "primary" | "secondary";
}

export function QuickActionsBar() {
  const { t } = useTranslation();

  const actions: QuickActionItem[] = [
    {
      href: "/companies/new",
      label: t("dashboard.new_company"),
      icon: <Plus className="h-3.5 w-3.5" />,
      variant: "primary",
    },
    {
      href: "/search",
      label: t("common.search"),
      icon: <Search className="h-3.5 w-3.5" />,
      variant: "secondary",
    },
    {
      href: "/opportunities",
      label: "الصفقات",
      icon: <Building2 className="h-3.5 w-3.5" />,
      variant: "secondary",
    },
    {
      href: "/activities",
      label: "الأنشطة",
      icon: <CalendarClock className="h-3.5 w-3.5" />,
      variant: "secondary",
    },
    {
      href: "/decisions",
      label: "القرارات",
      icon: <FileText className="h-3.5 w-3.5" />,
      variant: "secondary",
    },
  ];

  return (
    <div className="flex flex-wrap items-center gap-2">
      {actions.map((action) => (
        <Link
          key={action.href}
          href={action.href}
          className={
            action.variant === "primary"
              ? "inline-flex items-center gap-1.5 rounded-lg bg-[var(--muhide-orange)] px-3 py-2 text-xs font-semibold text-white transition-colors hover:opacity-90"
              : "inline-flex items-center gap-1.5 rounded-lg border border-[var(--border-secondary)] bg-[var(--bg-primary)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-secondary)]"
          }
        >
          {action.icon}
          <span>{action.label}</span>
        </Link>
      ))}
    </div>
  );
}
