"use client";
/* eslint-disable custom-rules/no-tailwind-color-classes */

import { useEffect, useState } from "react";
import { Button, Input, Spinner, useToast } from "@salesos/ui";
import { useBranding, useUpsertBranding } from "@/lib/hooks/brandingStudioQueries";
import { BRANDING_LOCALES } from "@/lib/api/types/tenantStudio";
import {
  BRANDING_STUDIO_HONESTY,
  BRANDING_STUDIO_NON_GOALS,
} from "@/features/tenant-studio/brandingStudioHonesty";

function getApiError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

/**
 * FE-S10-07 — Branding & Languages Studio against tip STORY-10-07 HTTP.
 * In-memory logo/color/name/locales. Not Production GO / RAG GO. TenantList untouched.
 */
export function BrandingStudio() {
  const { toast } = useToast();
  const brandingQuery = useBranding();
  const upsertMutation = useUpsertBranding();

  const [displayName, setDisplayName] = useState("");
  const [logoUrl, setLogoUrl] = useState("");
  const [primaryColor, setPrimaryColor] = useState("#0F172A");
  const [secondaryColor, setSecondaryColor] = useState("#334155");
  const [defaultLocale, setDefaultLocale] = useState("ar");
  const [localeAr, setLocaleAr] = useState(true);
  const [localeEn, setLocaleEn] = useState(true);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const row = brandingQuery.data;
    if (!row || hydrated) return;
    setDisplayName(row.display_name ?? "");
    setLogoUrl(row.logo_url ?? "");
    setPrimaryColor(row.primary_color || "#0F172A");
    setSecondaryColor(row.secondary_color || "#334155");
    setDefaultLocale(row.default_locale || "ar");
    const supported = row.supported_locales ?? [];
    setLocaleAr(supported.includes("ar") || supported.length === 0);
    setLocaleEn(supported.includes("en") || supported.length === 0);
    setHydrated(true);
  }, [brandingQuery.data, hydrated]);

  const supportedLocales = [
    ...(localeAr ? (["ar"] as const) : []),
    ...(localeEn ? (["en"] as const) : []),
  ];

  return (
    <div className="space-y-4" data-testid="branding-studio">
      <p
        className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"
        data-testid="branding-studio-honesty"
      >
        {BRANDING_STUDIO_HONESTY} Non-goals: {BRANDING_STUDIO_NON_GOALS.join("; ")}. Not Production
        GO / RAG GO.
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          data-testid="branding-studio-refresh"
          disabled={brandingQuery.isFetching}
          onClick={() => {
            setHydrated(false);
            void brandingQuery.refetch();
          }}
        >
          {brandingQuery.isFetching ? "Refreshing…" : "Refresh branding"}
        </Button>
        <span className="text-sm text-[var(--text-muted)]" data-testid="branding-studio-status">
          {brandingQuery.isLoading ? (
            <Spinner className="h-5 w-5" />
          ) : brandingQuery.isError ? (
            <span className="text-[var(--text-danger)]">{getApiError(brandingQuery.error)}</span>
          ) : brandingQuery.data ? (
            <>
              tenant {brandingQuery.data.tenant_id} · v{brandingQuery.data.schema_version}
            </>
          ) : null}
        </span>
      </div>

      {brandingQuery.data ? (
        <div
          className="flex flex-wrap items-center gap-4 rounded border border-[var(--border-default)] p-3"
          data-testid="branding-studio-preview"
        >
          <div
            className="flex h-12 w-12 items-center justify-center rounded text-xs font-bold text-white"
            style={{ backgroundColor: brandingQuery.data.primary_color }}
            aria-hidden
          >
            {(brandingQuery.data.display_name || "?").slice(0, 2).toUpperCase()}
          </div>
          <div>
            <p className="text-sm font-semibold text-[var(--text-primary)]">
              {brandingQuery.data.display_name || "(unnamed tenant)"}
            </p>
            <p className="font-mono text-xs text-[var(--text-muted)]">
              primary {brandingQuery.data.primary_color} · secondary{" "}
              {brandingQuery.data.secondary_color} · default {brandingQuery.data.default_locale} ·
              supported {brandingQuery.data.supported_locales.join(",")}
              {brandingQuery.data.logo_url ? ` · logo ${brandingQuery.data.logo_url}` : ""}
            </p>
          </div>
          <span
            className="ml-auto inline-block h-6 w-6 rounded border border-[var(--border-default)]"
            style={{ backgroundColor: brandingQuery.data.secondary_color }}
            title="secondary_color"
          />
        </div>
      ) : null}

      <form
        className="space-y-3 rounded border border-[var(--border-default)] p-3"
        data-testid="branding-studio-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (supportedLocales.length === 0) {
            toast({
              variant: "error",
              title: "Locales required",
              description: "Select at least one of ar / en.",
            });
            return;
          }
          if (!supportedLocales.includes(defaultLocale as "ar" | "en")) {
            toast({
              variant: "error",
              title: "Default locale invalid",
              description: "default_locale must be in supported_locales.",
            });
            return;
          }
          upsertMutation.mutate(
            {
              display_name: displayName.trim(),
              logo_url: logoUrl.trim(),
              primary_color: primaryColor.trim(),
              secondary_color: secondaryColor.trim(),
              default_locale: defaultLocale,
              supported_locales: [...supportedLocales],
            },
            {
              onSuccess: (row) => {
                setHydrated(false);
                toast({
                  variant: "success",
                  title: "Branding saved",
                  description: `${row.display_name || row.tenant_id} · ${row.primary_color}`,
                });
              },
              onError: (err) => {
                toast({
                  variant: "error",
                  title: "Save failed",
                  description: getApiError(err),
                });
              },
            }
          );
        }}
      >
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Upsert branding (tip PUT)
        </h2>
        <Input
          label="display_name"
          data-testid="branding-display-name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          maxLength={200}
        />
        <Input
          label="logo_url (https:// or /path)"
          data-testid="branding-logo-url"
          value={logoUrl}
          onChange={(e) => setLogoUrl(e.target.value)}
          maxLength={512}
          placeholder="https://cdn.example/logo.png"
        />
        <div className="flex flex-wrap gap-3">
          <Input
            label="primary_color"
            data-testid="branding-primary-color"
            value={primaryColor}
            onChange={(e) => setPrimaryColor(e.target.value)}
            maxLength={7}
            className="max-w-[10rem]"
          />
          <input
            type="color"
            aria-label="primary color picker"
            data-testid="branding-primary-picker"
            className="mt-6 h-9 w-12 cursor-pointer rounded border border-[var(--border-default)] bg-transparent"
            value={/^#[0-9a-fA-F]{6}$/.test(primaryColor) ? primaryColor : "#0F172A"}
            onChange={(e) => setPrimaryColor(e.target.value.toUpperCase())}
          />
          <Input
            label="secondary_color"
            data-testid="branding-secondary-color"
            value={secondaryColor}
            onChange={(e) => setSecondaryColor(e.target.value)}
            maxLength={7}
            className="max-w-[10rem]"
          />
          <input
            type="color"
            aria-label="secondary color picker"
            data-testid="branding-secondary-picker"
            className="mt-6 h-9 w-12 cursor-pointer rounded border border-[var(--border-default)] bg-transparent"
            value={/^#[0-9a-fA-F]{6}$/.test(secondaryColor) ? secondaryColor : "#334155"}
            onChange={(e) => setSecondaryColor(e.target.value.toUpperCase())}
          />
        </div>
        <div>
          <label className="block text-xs text-[var(--text-muted)]">default_locale</label>
          <select
            data-testid="branding-default-locale"
            className="w-full max-w-xs rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
            value={defaultLocale}
            onChange={(e) => setDefaultLocale(e.target.value)}
          >
            {BRANDING_LOCALES.map((loc) => (
              <option key={loc} value={loc}>
                {loc}
              </option>
            ))}
          </select>
        </div>
        <fieldset className="space-y-1">
          <legend className="text-xs text-[var(--text-muted)]">
            supported_locales (ar / en only)
          </legend>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              data-testid="branding-locale-ar"
              checked={localeAr}
              onChange={(e) => setLocaleAr(e.target.checked)}
            />
            ar
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              data-testid="branding-locale-en"
              checked={localeEn}
              onChange={(e) => setLocaleEn(e.target.checked)}
            />
            en
          </label>
        </fieldset>
        <Button
          type="submit"
          data-testid="branding-studio-save"
          disabled={upsertMutation.isPending}
        >
          {upsertMutation.isPending ? "Saving…" : "Save branding"}
        </Button>
      </form>
    </div>
  );
}
