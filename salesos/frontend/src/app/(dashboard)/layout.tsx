"use client";

import React, { useEffect, useCallback, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@salesos/ui";
import { AppShell, useAppShell } from "@/components/foundation/app-shell";
import {
  Building2,
  Users,
  UserCheck,
  DollarSign,
  Search,
  Settings,
  LayoutDashboard,
  Bell,
  Menu,
  User,
  Shield,
  Workflow,
  Activity,
  HeartHandshake,
  X,
  TrendingUp,
  BarChart3,
  Brain,
  CalendarClock,
  GitGraph,
  Video,
  LineChart,
  Radio,
  ListChecks,
  Bot,
  LogOut,
  Plug,
  FormInput,
  Gauge,
  KeyRound,
  Palette,
  MapPin,
  Cpu,
  Store,
  Target,
  Radar,
  Crosshair,
  UserRoundSearch,
  Layers,
  Globe2,
  BadgeCheck,
  Copy,
  Mail,
} from "lucide-react";
import {
  LazyCommandBar,
  LazySearchPanel,
  LazyCopilotPanel,
} from "@/components/lazy-exports";
import { MobileNav } from "@/components/foundation/MobileNav";
import { useTheme } from "@salesos/hooks";
import { registerBuiltinCommands } from "@/lib/commands";
import { useTranslation } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/foundation/LanguageSwitcher";
import { TenantBrandMark } from "@/features/tenant-studio/TenantBrandMark";
import { useAiCopilotEnabled } from "@/lib/hooks/useAiCopilotEnabled";
import { clearAuthTokens } from "@/lib/auth/session";

const NAV_KEYS = [
  { href: "/dashboard", key: "nav.dashboard", icon: LayoutDashboard },
  { href: "/companies", key: "nav.companies", icon: Building2 },
  { href: "/employees", key: "nav.employees", icon: UserCheck },
  { href: "/employees/me", key: "nav.profile", icon: User },
  { href: "/contacts", key: "nav.contacts", icon: Users },
  { href: "/opportunities", key: "nav.opportunities", icon: DollarSign },
  { href: "/activities", key: "nav.activities", icon: ListChecks },
  { href: "/revenue", key: "nav.revenue", icon: TrendingUp },
  { href: "/pipeline", key: "nav.pipeline", icon: BarChart3 },
  { href: "/forecast", key: "nav.forecast", icon: CalendarClock },
  { href: "/search", key: "nav.search", icon: Search },
  { href: "/decisions", key: "nav.decisions", icon: Brain },
  { href: "/meetings", key: "nav.meetings", icon: Video },
  { href: "/graph", key: "nav.graph", icon: GitGraph },
  // AI (/rag, /ai, /copilot) — not in sidebar; open via Ask AI popup / dedicated entry only
  { href: "/automation", key: "nav.workflows", icon: Workflow },
  { href: "/analytics", key: "nav.analytics", icon: LineChart },
  { href: "/signals", key: "nav.signals", icon: Radio },
  { href: "/rules", key: "nav.rules", icon: Shield },
  { href: "/monitoring", key: "nav.monitoring", icon: Activity },
  {
    href: "/customer-success",
    key: "nav.customer_success",
    icon: HeartHandshake,
  },
  { href: "/integrations", key: "nav.integrations", icon: Plug },
  { href: "/studio/custom-fields", key: "nav.custom_fields", icon: FormInput },
  { href: "/studio/scoring", key: "nav.scoring_rules", icon: Gauge },
  {
    href: "/studio/permissions",
    key: "nav.permissions_studio",
    icon: KeyRound,
  },
  { href: "/studio/workflows", key: "nav.workflow_studio", icon: Workflow },
  { href: "/studio/notifications", key: "nav.notification_rules", icon: Bell },
  { href: "/studio/branding", key: "nav.branding_studio", icon: Palette },
  { href: "/studio/territories", key: "nav.territories_studio", icon: MapPin },
  { href: "/studio/ai-model-tiers", key: "nav.ai_model_tiers", icon: Cpu },
  {
    href: "/marketplace/listings",
    key: "nav.marketplace_listings",
    icon: Store,
  },
  { href: "/gtm", key: "nav.gtm_hub", icon: Crosshair },
  { href: "/gtm/icp", key: "nav.icp_profiles", icon: UserRoundSearch },
  { href: "/gtm/market-sizing", key: "nav.market_sizing", icon: Target },
  { href: "/gtm/lead-discovery", key: "nav.lead_discovery", icon: Radar },
  { href: "/gtm/enrichment", key: "nav.enrichment", icon: Layers },
  {
    href: "/gtm/website-intelligence",
    key: "nav.website_intelligence",
    icon: Globe2,
  },
  { href: "/gtm/verification", key: "nav.verification", icon: BadgeCheck },
  { href: "/gtm/lookalikes", key: "nav.lookalikes", icon: Copy },
  { href: "/gtm/sequences", key: "nav.sequences", icon: Mail },
  { href: "/settings", key: "nav.settings", icon: Settings },
  { href: "/admin", key: "nav.admin", icon: Shield },
];

function DashboardContent({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { sidebarCollapsed, setSidebarCollapsed, commandOpen, setCommandOpen } =
    useAppShell();
  const [searchOpen, setSearchOpen] = React.useState(false);
  const [copilotOpen, setCopilotOpen] = React.useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const { toggle: toggleTheme } = useTheme();
  const { t, dir } = useTranslation();
  const { enabled: aiCopilotEnabled } = useAiCopilotEnabled();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = useCallback(() => {
    clearAuthTokens();
    window.location.href = "/login";
  }, []);

  // AI routes intentionally absent from NAV_KEYS — gated via Ask AI / feature flag only
  const navItems = NAV_KEYS;

  const slideAnim =
    dir === "rtl" ? "animate-slide-in-right" : "animate-slide-in-left";

  useEffect(() => {
    registerBuiltinCommands(router);
  }, [router]);

  useEffect(() => {
    const toggleCopilot = () => {
      if (!aiCopilotEnabled) return;
      setCopilotOpen((v) => !v);
    };
    const toggleSearch = () => setSearchOpen((v) => !v);
    window.addEventListener("salesos:toggle-copilot", toggleCopilot);
    window.addEventListener("salesos:toggle-search", toggleSearch);
    window.addEventListener("salesos:toggle-theme", toggleTheme);
    return () => {
      window.removeEventListener("salesos:toggle-copilot", toggleCopilot);
      window.removeEventListener("salesos:toggle-search", toggleSearch);
      window.removeEventListener("salesos:toggle-theme", toggleTheme);
    };
  }, [toggleTheme, aiCopilotEnabled]);

  useEffect(() => {
    if (!aiCopilotEnabled) setCopilotOpen(false);
  }, [aiCopilotEnabled]);

  useEffect(() => {
    if (mobileSidebarOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileSidebarOpen]);

  const closeMobileSidebar = useCallback(() => setMobileSidebarOpen(false), []);

  useEffect(() => {
    closeMobileSidebar();
  }, [pathname, closeMobileSidebar]);

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
      <header className="flex items-center h-14 px-3 sm:px-4 bg-[var(--bg-primary)] border-b border-[var(--border-default)] flex-shrink-0">
        <button
          onClick={() => setMobileSidebarOpen(true)}
          className="md:hidden rounded-lg p-2 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)] min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label={t("a11y.open_sidebar")}
        >
          <Menu className="h-5 w-5" />
        </button>
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="hidden md:flex rounded-lg p-1.5 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]"
          aria-label={
            sidebarCollapsed
              ? t("a11y.expand_sidebar")
              : t("a11y.collapse_sidebar")
          }
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex-1" />
        <button
          onClick={() => setCommandOpen(true)}
          className="hidden md:flex items-center gap-2 rounded-lg border border-[var(--border-hover)] px-3 py-1.5 text-sm text-[var(--text-muted)]"
        >
          <Search className="h-4 w-4" />
          <span>{t("common.quick_search")}</span>
          <kbd className="ms-auto rounded border border-[var(--border-hover)] px-1.5 py-0.5 text-[10px]">
            ⌘K
          </kbd>
        </button>
        {aiCopilotEnabled && (
          <button
            onClick={() => setCopilotOpen(!copilotOpen)}
            className="rounded-lg p-1.5 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)] min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label={t("a11y.open_copilot")}
          >
            <Bot className="h-5 w-5" />
          </button>
        )}
        <button
          className="rounded-lg p-1.5 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)] min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label={t("a11y.notifications")}
        >
          <Bell className="h-5 w-5" />
        </button>
        <LanguageSwitcher />
        <div className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="rounded-lg p-1.5 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)] min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label={t("a11y.user_menu")}
          >
            <User className="h-5 w-5" />
          </button>
          {userMenuOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setUserMenuOpen(false)}
              />
              <div className="absolute end-0 top-full mt-1 z-20 min-w-[180px] rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] shadow-muhide-4 py-1">
                <Link
                  href="/employees/me"
                  className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"
                  onClick={() => setUserMenuOpen(false)}
                >
                  <User className="h-4 w-4" />
                  {t("auth.profile")}
                </Link>
                <Link
                  href="/settings"
                  className="flex items-center gap-2 px-3 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"
                  onClick={() => setUserMenuOpen(false)}
                >
                  <Settings className="h-4 w-4" />
                  {t("settings.title")}
                </Link>
                <hr className="my-1 border-[var(--border-default)]" />
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-[var(--status-danger-text)] hover:bg-[var(--bg-tertiary)]"
                >
                  <LogOut className="h-4 w-4" />
                  {t("auth.logout")}
                </button>
              </div>
            </>
          )}
        </div>
      </header>

      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={closeMobileSidebar}
            aria-hidden="true"
          />
          <aside
            className={cn(
              "absolute top-0 bottom-0 w-72 max-w-[80vw] bg-[var(--bg-primary)] shadow-muhide-6 overflow-y-auto",
              "start-0",
              slideAnim,
            )}
          >
            <div className="flex items-center justify-between border-b border-[var(--border-default)] px-4 h-14">
              <TenantBrandMark />
              <button
                onClick={closeMobileSidebar}
                className="rounded-lg p-2 hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)] min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label={t("a11y.close_sidebar")}
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="p-3 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = pathname.startsWith(item.href);
                const label = t(item.key);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-3 text-sm transition min-h-[44px]",
                      active
                        ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] dark:bg-[var(--muhide-orange)]/20 dark:text-orange-300 font-medium"
                        : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]",
                    )}
                    {...(active ? { "aria-current": "page" as const } : {})}
                  >
                    <Icon className="h-5 w-5 shrink-0" />
                    <span>{label}</span>
                  </Link>
                );
              })}
            </nav>
          </aside>
        </div>
      )}

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <aside
          className={cn(
            "hidden md:flex flex-col h-full shrink-0 border-e bg-[var(--bg-primary)] transition-all",
            sidebarCollapsed ? "w-16" : "w-64",
          )}
        >
          <div
            className={cn(
              "flex h-14 items-center border-b px-4",
              sidebarCollapsed && "justify-center px-0",
            )}
          >
            {sidebarCollapsed ? (
              <TenantBrandMark collapsed />
            ) : (
              <TenantBrandMark />
            )}
          </div>
          <nav className="flex-1 space-y-1 p-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = pathname.startsWith(item.href);
              const label = t(item.key);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                    active
                      ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] dark:bg-[var(--muhide-orange)]/20 dark:text-orange-300"
                      : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]",
                    sidebarCollapsed && "justify-center px-2",
                  )}
                  title={sidebarCollapsed ? label : undefined}
                  {...(active ? { "aria-current": "page" as const } : {})}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {!sidebarCollapsed && <span>{label}</span>}
                </Link>
              );
            })}
          </nav>
        </aside>
        <main
          id="main-content"
          tabIndex={-1}
          className="min-w-0 flex-1 overflow-auto p-3 sm:p-4 lg:p-6"
        >
          {children}
        </main>
      </div>
      <MobileNav />
      <LazyCommandBar
        open={commandOpen}
        onClose={() => setCommandOpen(false)}
      />
      <LazySearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} />
      {aiCopilotEnabled && (
        <LazyCopilotPanel
          open={copilotOpen}
          onClose={() => setCopilotOpen(false)}
          entityType="company"
        />
      )}
    </div>
  );
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AppShell>
      <DashboardContent>{children}</DashboardContent>
    </AppShell>
  );
}
