import { useState, useEffect } from 'react'
import { useRuntime } from './use-runtime'
import type { Locale } from '@salesos/runtime'

export function useLocalization() {
  const runtime = useRuntime()
  const [locale, setLocale] = useState<Locale>(runtime.localization.getLocale())

  useEffect(() => {
    const unsub = runtime.localization.subscribe(() => {
      setLocale(runtime.localization.getLocale())
    })
    return unsub
  }, [runtime])

  return {
    t: runtime.localization.t.bind(runtime.localization),
    locale,
    setLocale: (l: Locale) => runtime.localization.setLocale(l),
    isRTL: runtime.localization.isRTL(),
    formatNumber: runtime.localization.formatNumber.bind(runtime.localization),
    formatDate: runtime.localization.formatDate.bind(runtime.localization),
    formatCurrency: runtime.localization.formatCurrency.bind(runtime.localization),
    formatRelativeTime: runtime.localization.formatRelativeTime.bind(runtime.localization),
  }
}

export function useT() {
  const { t, isRTL, locale } = useLocalization()
  return { t, isRTL, locale }
}
