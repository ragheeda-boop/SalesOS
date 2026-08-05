"use client";

import { useEffect } from "react";
import { useBranding } from "@/lib/hooks/brandingStudioQueries";

const FALLBACK_NAME = "SalesOS";

/**
 * FE-S10-07b — Apply tip GET /api/v1/studio/branding to dashboard chrome.
 * In-memory tip branding only (name + colors). Logo URL remains Studio-only
 * until CDN/upload exists — do not invent object hosting. Not Production GO.
 */
export function useTenantBrandingChrome() {
  const brandingQuery = useBranding();
  const row = brandingQuery.data;

  useEffect(() => {
    const root = document.documentElement;
    if (!row) return;
    if (row.primary_color) {
      root.style.setProperty("--tenant-brand-primary", row.primary_color);
    }
    if (row.secondary_color) {
      root.style.setProperty("--tenant-brand-secondary", row.secondary_color);
    }
    return () => {
      root.style.removeProperty("--tenant-brand-primary");
      root.style.removeProperty("--tenant-brand-secondary");
    };
  }, [row]);

  const displayName = (row?.display_name || "").trim() || FALLBACK_NAME;
  const primaryColor = row?.primary_color || "";
  const secondaryColor = row?.secondary_color || "";
  const logoUrlHint = (row?.logo_url || "").trim();

  return {
    displayName,
    primaryColor,
    secondaryColor,
    logoUrlHint,
    isLoading: brandingQuery.isLoading,
    isError: brandingQuery.isError,
    fromTip: Boolean(row),
  };
}

export function TenantBrandMark({
  collapsed = false,
  className = "",
}: {
  collapsed?: boolean;
  className?: string;
}) {
  const { displayName, primaryColor, logoUrlHint } = useTenantBrandingChrome();
  const title = logoUrlHint ? `${displayName} · logo ${logoUrlHint}` : displayName;

  if (collapsed) {
    return (
      <span
        className={`flex h-8 w-8 items-center justify-center rounded text-xs font-bold text-white ${className}`}
        style={{
          backgroundColor: primaryColor || "var(--muhide-orange)",
        }}
        data-testid="tenant-brand-mark-collapsed"
        title={title}
      >
        {displayName.slice(0, 2).toUpperCase()}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex max-w-full items-center gap-2 ${className}`}
      data-testid="tenant-brand-mark"
      title={title}
    >
      {primaryColor ? (
        <span
          className="inline-block h-3 w-3 shrink-0 rounded-sm"
          style={{ backgroundColor: primaryColor }}
          aria-hidden
          data-testid="tenant-brand-swatch"
        />
      ) : null}
      <span
        className="truncate text-lg font-bold text-[var(--text-primary)]"
        data-testid="tenant-brand-name"
      >
        {displayName}
      </span>
    </span>
  );
}
