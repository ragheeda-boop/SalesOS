"use client";

import React, { useEffect, useCallback, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@salesos/ui";
import { AppShell, useAppShell } from "@/components/foundation/app-shell";
import { ErrorBoundary } from "@/components/error-boundary";
import { Search, Settings, Bell, Menu, User, Shield, Bot, LogOut, X } from "lucide-react";
import { LazyCommandBar, LazySearchPanel, LazyCopilotPanel } from "@/components/lazy-exports";
import { MobileNav } from "@/components/foundation/MobileNav";
import { useTheme } from "@salesos/hooks";
import { registerBuiltinCommands } from "@/lib/commands";
import { useTranslation } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/foundation/LanguageSwitcher";
import { TenantBrandMark } from "@/features/tenant-studio/TenantBrandMark";
// ADR-102 / AI_HONESTY.md: AI Copilot requires evidence validation before GA activation.
// Conditions for enabling:
// 1. Backend must return feature_ai_copilot: true in /api/v1/copilot/status
// 2. AI response quality must be measured and validated
// 3. User feedback loop must be operational
// To enable: set NEXT_PUBLIC_FEATURE_AI_COPILOT=true in .env
import { useAiCopilotEnabled } from "@/lib/hooks/useAiCopilotEnabled";
import { logoutSession } from "@/lib/api/identity";
import { clearAuthTokens } from "@/lib/auth/session";
import { WorkspaceSwitcher } from "@/components/navigation/workspace-switcher";
import { GroupedSidebar } from "@/components/navigation/grouped-sidebar";
import { getWorkspaceByPath, type Workspace } from "@/lib/workspaces";

function DashboardContent({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { sidebarCollapsed, setSidebarCollapsed, commandOpen, setCommandOpen } = useAppShell();
  const [searchOpen, setSearchOpen] = React.useState(false);
  const [copilotOpen, setCopilotOpen] = React.useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const { toggle: toggleTheme } = useTheme();
  const { t, dir } = useTranslation();
  const { enabled: aiCopilotEnabled } = useAiCopilotEnabled();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace>(() =>
    getWorkspaceByPath(pathname)
  );

  const handleLogout = useCallback(() => {
    void (async () => {
      try {
        await logoutSession();
      } finally {
        clearAuthTokens();
        window.location.href = "/login";
      }
    })();
  }, []);

  useEffect(() => {
    const detected = getWorkspaceByPath(pathname);
    setActiveWorkspace(detected);
  }, [pathname]);

  const slideAnim = dir === "rtl" ? "animate-slide-in-right" : "animate-slide-in-left";

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
          aria-label={sidebarCollapsed ? t("a11y.expand_sidebar") : t("a11y.collapse_sidebar")}
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
              <div className="fixed inset-0 z-10" onClick={() => setUserMenuOpen(false)} />
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
              slideAnim
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
            <div className="p-2 border-b border-[var(--border-default)]">
              <WorkspaceSwitcher current={activeWorkspace} onSelect={setActiveWorkspace} />
            </div>
            <GroupedSidebar workspace={activeWorkspace} />
          </aside>
        </div>
      )}

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <aside
          className={cn(
            "hidden md:flex flex-col h-full shrink-0 border-e bg-[var(--bg-primary)] transition-all",
            sidebarCollapsed ? "w-16" : "w-64"
          )}
        >
          <div
            className={cn(
              "flex h-14 items-center border-b px-4",
              sidebarCollapsed && "justify-center px-0"
            )}
          >
            {sidebarCollapsed ? <TenantBrandMark collapsed /> : <TenantBrandMark />}
          </div>
          <div
            className={cn(
              "border-b border-[var(--border-default)]",
              sidebarCollapsed ? "p-2 flex justify-center" : "p-2"
            )}
          >
            <WorkspaceSwitcher
              current={activeWorkspace}
              onSelect={setActiveWorkspace}
              collapsed={sidebarCollapsed}
            />
          </div>
          <GroupedSidebar workspace={activeWorkspace} collapsed={sidebarCollapsed} />
        </aside>
        <main
          id="main-content"
          tabIndex={-1}
          className="min-w-0 flex-1 overflow-auto p-3 sm:p-4 lg:p-6"
        >
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
      <MobileNav />
      <LazyCommandBar open={commandOpen} onClose={() => setCommandOpen(false)} />
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
