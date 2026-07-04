import { useState, useEffect } from 'react'

type Theme = 'light' | 'dark' | 'system'

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>('system')
  const [resolved, setResolved] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const stored = localStorage.getItem('salesos_theme') as Theme | null
    const t = stored || 'system'
    setThemeState(t)
    if (t === 'system') {
      setResolved(window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    } else {
      setResolved(t)
    }
  }, [])

  useEffect(() => {
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(resolved)
  }, [resolved])

  useEffect(() => {
    if (theme === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)')
      setResolved(mq.matches ? 'dark' : 'light')
      const handler = (e: MediaQueryListEvent) => setResolved(e.matches ? 'dark' : 'light')
      mq.addEventListener('change', handler)
      return () => mq.removeEventListener('change', handler)
    }
  }, [theme])

  return {
    theme,
    resolved,
    setTheme: setThemeState,
    toggle: () => setThemeState((t) => (t === 'light' ? 'dark' : t === 'dark' ? 'light' : 'light')),
    isDark: resolved === 'dark',
  }
}
