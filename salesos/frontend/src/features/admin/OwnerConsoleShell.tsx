"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@salesos/ui";
import { ACCESS_TOKEN_KEY } from "@/lib/auth/session";
import {
  OWNER_CONSOLE_HOST,
  OWNER_JWT_AUDIENCE,
  classifyJwtAudience,
  classifyOwnerHost,
  formatOwnerAudienceHonesty,
  formatOwnerHostHonesty,
  getJwtAudience,
  type JwtAudienceKind,
} from "@/lib/auth/ownerAudience";

const OWNER_NAV = [
  { href: "/admin", label: "Overview", testId: "owner-console-nav-overview" },
  {
    href: "/admin/tenants",
    label: "Tenants",
    testId: "owner-console-nav-tenants",
  },
  {
    href: "/admin/billing",
    label: "Billing",
    testId: "owner-console-nav-billing",
  },
  {
    href: "/admin/flags",
    label: "Flags",
    testId: "owner-console-nav-flags",
  },
  {
    href: "/admin/config",
    label: "Config",
    testId: "owner-console-nav-config",
  },
  {
    href: "/admin/audit",
    label: "Audit",
    testId: "owner-console-nav-audit",
  },
  {
    href: "/admin/integrations",
    label: "Integrations",
    testId: "owner-console-nav-integrations",
  },
] as const;

function navActive(pathname: string, href: string): boolean {
  if (href === "/admin") return pathname === "/admin";
  return pathname === href || pathname.startsWith(`${href}/`);
}

/**
 * STORY-07 + FE-S07/FE-S08-00 — Owner Console chrome + Integration Hub inventory.
 * Ops nav + page honesty. TenantList.tsx untouched. Not Production GO.
 */
export function OwnerConsoleShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() || "/admin";
  const [token, setToken] = useState<string | null>(null);
  const [hostname, setHostname] = useState<string>("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    setToken(localStorage.getItem(ACCESS_TOKEN_KEY));
    setHostname(window.location.hostname || "");
    const onStorage = () => setToken(localStorage.getItem(ACCESS_TOKEN_KEY));
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const kind: JwtAudienceKind = useMemo(
    () => classifyJwtAudience(token),
    [token],
  );
  const aud = useMemo(() => getJwtAudience(token), [token]);
  const honesty = useMemo(
    () => formatOwnerAudienceHonesty(kind, aud),
    [kind, aud],
  );
  const hostKind = useMemo(() => classifyOwnerHost(hostname), [hostname]);
  const hostHonesty = useMemo(
    () => formatOwnerHostHonesty(hostKind, hostname),
    [hostKind, hostname],
  );
  const ownerOk = kind === "owner";

  return (
    <div className="space-y-4" data-testid="owner-console-shell">
      <header
        className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)] px-4 py-3"
        data-testid="owner-console-header"
      >
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Owner Console (EPIC-07)
            </p>
            <h1 className="text-lg font-semibold text-[var(--text-primary)]">
              Platform Ops shell
            </h1>
            <p className="text-xs text-[var(--text-muted)]">
              Audience target: <code>{OWNER_JWT_AUDIENCE}</code>. Host target:{" "}
              <code>{OWNER_CONSOLE_HOST}</code> (separate deploy; not claimed
              live). Not Production GO.
            </p>
          </div>
          <nav
            className="flex flex-wrap gap-2"
            data-testid="owner-console-nav"
            aria-label="Owner Console"
          >
            {OWNER_NAV.map((item) => {
              const active = navActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  data-testid={item.testId}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-sm min-h-[36px] inline-flex items-center",
                    active
                      ? "bg-[var(--muhide-orange)]/15 text-[var(--muhide-orange)] font-medium"
                      : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <p
          className={
            ownerOk
              ? "mt-2 text-xs text-[var(--text-secondary)]"
              : "mt-2 text-xs text-amber-800 dark:text-amber-200"
          }
          data-testid="owner-console-audience-banner"
        >
          {honesty}
        </p>
        <p
          className="mt-1 text-xs text-[var(--text-muted)]"
          data-testid="owner-console-host-banner"
        >
          {hostHonesty}
        </p>
        <p
          className="mt-1 text-xs text-[var(--text-muted)]"
          data-testid="owner-console-readpath-honesty"
        >
          Phase 1 Ops surfaces: tenants + billing + flags/config/audit. Deferred
          write actions (manual refund, suspend override beyond existing
          lifecycle APIs) stay later-increment. Owner login mint is DEC-093
          follow-up — not invented here. Not Production GO.
        </p>
      </header>

      {!ownerOk ? (
        <div
          className="mx-4 rounded-md border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100"
          data-testid="owner-console-audience-gate"
        >
          <p className="font-medium">Owner audience required for admin APIs</p>
          <p className="mt-1">{honesty}</p>
          <p className="mt-2 text-xs">
            STORY-07-03: shell + nav stay available for Ops UX; BE `owner_auth`
            still rejects tenant `salesos-api` tokens on `/api/v1/admin/*`.
            Owner login mint remains DEC-093 follow-up.
          </p>
        </div>
      ) : null}

      <div data-testid="owner-console-content">{children}</div>
    </div>
  );
}
