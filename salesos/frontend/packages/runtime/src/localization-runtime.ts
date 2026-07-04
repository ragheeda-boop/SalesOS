export type Locale = 'en' | 'ar' | 'fr' | 'es' | 'de' | 'tr' | 'zh' | 'ja'

export interface LocalizationOptions {
  locale?: Locale
  fallbackLocale?: Locale
  translations?: Record<string, Record<string, string>>
}

export class LocalizationRuntime {
  private locale: Locale
  private fallbackLocale: Locale
  private translations: Map<string, Map<string, string>> = new Map()
  private listeners = new Set<() => void>()

  constructor(options?: LocalizationOptions) {
    this.locale = options?.locale || 'en'
    this.fallbackLocale = options?.fallbackLocale || 'en'
    if (options?.translations) {
      for (const [lang, strings] of Object.entries(options.translations)) {
        this.addTranslations(lang as Locale, strings)
      }
    }
  }

  getLocale(): Locale {
    return this.locale
  }

  setLocale(locale: Locale): void {
    this.locale = locale
    document.documentElement.lang = locale
    document.documentElement.dir = this.isRTL() ? 'rtl' : 'ltr'
    this.listeners.forEach((fn) => fn())
  }

  getAvailableLocales(): Locale[] {
    return Array.from(this.translations.keys()) as Locale[]
  }

  isRTL(): boolean {
    return this.locale === 'ar'
  }

  t(key: string, params?: Record<string, string>): string {
    const langMap = this.translations.get(this.locale)
    let value = langMap?.get(key)
    if (!value && this.locale !== this.fallbackLocale) {
      value = this.translations.get(this.fallbackLocale)?.get(key)
    }
    if (!value) return key
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        value = value.replace(`{${k}}`, v)
      }
    }
    return value
  }

  addTranslations(locale: Locale, strings: Record<string, string>): void {
    if (!this.translations.has(locale)) {
      this.translations.set(locale, new Map())
    }
    const map = this.translations.get(locale)!
    for (const [key, value] of Object.entries(strings)) {
      map.set(key, value)
    }
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
    return new Intl.NumberFormat(this.locale, options).format(value)
  }

  formatDate(value: Date | string | number, options?: Intl.DateTimeFormatOptions): string {
    const date = value instanceof Date ? value : new Date(value)
    return new Intl.DateTimeFormat(this.locale, options).format(date)
  }

  formatCurrency(value: number, currency = 'USD'): string {
    return new Intl.NumberFormat(this.locale, { style: 'currency', currency }).format(value)
  }

  formatRelativeTime(value: number, unit: Intl.RelativeTimeFormatUnit): string {
    return new Intl.RelativeTimeFormat(this.locale, { numeric: 'auto' }).format(value, unit)
  }
}
