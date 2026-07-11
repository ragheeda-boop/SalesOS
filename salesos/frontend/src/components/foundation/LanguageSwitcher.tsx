"use client"

import { useTranslation } from "@/lib/i18n"
import { cn } from "@salesos/ui"

interface LanguageSwitcherProps {
  className?: string
}

export function LanguageSwitcher({ className }: LanguageSwitcherProps) {
  const { locale, setLocale, dir } = useTranslation()

  const toggle = () => {
    setLocale(locale === "ar" ? "en" : "ar")
  }

  return (
    <button
      onClick={toggle}
      className={cn(
        "flex items-center gap-1.5 h-8 px-2.5 rounded-md text-sm font-medium transition-all duration-200",
        "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]",
        "border border-[var(--border-default)] hover:border-[var(--border-hover)]",
        className
      )}
      aria-label={locale === "ar" ? "Switch to English" : "التبديل إلى العربية"}
      title={locale === "ar" ? "English" : "العربية"}
    >
      <span className={cn(
        "inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold",
        locale === "ar"
          ? "bg-[var(--muhide-orange)]/20 text-[var(--muhide-orange)]"
          : "bg-[var(--muhide-orange)] text-white"
      )}>
        {locale === "ar" ? "EN" : "AR"}
      </span>
      <span className="hidden sm:inline">{locale === "ar" ? "English" : "العربية"}</span>
    </button>
  )
}
