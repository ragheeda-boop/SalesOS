import '@testing-library/jest-dom'
import { toHaveNoViolations } from 'jest-axe'
expect.extend(toHaveNoViolations)

// jsdom omits Element scroll APIs used by chat UIs / combobox — stub no-ops.
if (typeof Element.prototype.scrollTo !== 'function') {
  Element.prototype.scrollTo = jest.fn()
}
if (typeof Element.prototype.scrollIntoView !== 'function') {
  Element.prototype.scrollIntoView = jest.fn()
}
if (typeof window.scrollTo !== 'function') {
  window.scrollTo = jest.fn()
}

// Default i18n for tests: resolve Arabic copy so suites asserting UI strings
// don't see raw keys (I18nContext fallback returns the key without a provider).
// Suites may still override via their own jest.mock("@/lib/i18n", ...).
jest.mock('@/lib/i18n', () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const ar = require('./src/lib/i18n/ar.json') as Record<string, string>
  const t = (key: string, params?: Record<string, string | number>) => {
    let value = ar[key] ?? key
    if (params) {
      value = Object.entries(params).reduce(
        (str, [k, v]) => str.replace(`{${k}}`, String(v)),
        value,
      )
    }
    return value
  }
  return {
    useTranslation: () => ({
      t,
      locale: 'ar' as const,
      setLocale: () => {},
      dir: 'rtl' as const,
    }),
    I18nProvider: ({ children }: { children: unknown }) => children,
  }
})

if (typeof globalThis.crypto !== 'undefined' && typeof globalThis.crypto.randomUUID !== 'function') {
  Object.defineProperty(globalThis.crypto, 'randomUUID', {
    value: () =>
      'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0
        return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
      }),
    writable: true,
    configurable: true,
  })
}
