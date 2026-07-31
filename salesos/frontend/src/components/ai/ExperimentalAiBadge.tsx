"use client";

import { useTranslation } from "@/lib/i18n";

/** Honest preview/stub label — never implies production AI GA. */
export function ExperimentalAiBadge({ className }: { className?: string }) {
  const { t } = useTranslation();
  return (
    <span
      className={
        className ??
        "inline-flex items-center rounded border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-800"
      }
      title={t("ai.honesty_hint")}
    >
      {t("ai.experimental_badge")}
    </span>
  );
}
