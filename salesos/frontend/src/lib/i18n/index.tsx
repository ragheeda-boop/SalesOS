"use client"

import { createContext, useContext, useState, useEffect, useCallback, useMemo, type ReactNode } from "react"
import en from "./en.json"
import ar from "./ar.json"

type TranslationMap = Record<string, string>
type Locale = "en" | "ar"

const translations: Record<Locale, TranslationMap> = { en, ar }

interface I18nContextType {
  t: (key: string, params?: Record<string, string | number>) => string
  locale: Locale
  setLocale: (locale: Locale) => void
  dir: "ltr" | "rtl"
}

const I18nContext = createContext<I18nContextType>({
  t: (key: string) => key,
  locale: "en",
  setLocale: () => {},
  dir: "ltr",
})

function detectBrowserLocale(): Locale {
  if (typeof window === "undefined") return "en"
  const stored = localStorage.getItem("salesos-locale") as Locale | null
  if (stored === "en" || stored === "ar") return stored
  const browserLang = navigator.language?.toLowerCase() || ""
  if (browserLang.startsWith("ar")) return "ar"
  return "en"
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en")
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setLocaleState(detectBrowserLocale())
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    const root = document.documentElement
    root.setAttribute("dir", locale === "ar" ? "rtl" : "ltr")
    root.setAttribute("lang", locale)
  }, [locale, mounted])

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale)
    try {
      localStorage.setItem("salesos-locale", newLocale)
    } catch {}
  }, [])

  const t = useCallback(
    (key: string, params?: Record<string, string | number>): string => {
      const map = translations[locale]
      let value = map[key]
      if (value === undefined) {
        const enValue = translations.en[key]
        value = enValue ?? key
      }
      if (params) {
        value = Object.entries(params).reduce(
          (str, [k, v]) => str.replace(`{${k}}`, String(v)),
          value
        )
      }
      return value
    },
    [locale]
  )

  const dir = useMemo<"ltr" | "rtl">(() => (locale === "ar" ? "rtl" : "ltr"), [locale])

  const value = useMemo(() => ({ t, locale, setLocale, dir }), [t, locale, setLocale, dir])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useTranslation() {
  return useContext(I18nContext)
}
