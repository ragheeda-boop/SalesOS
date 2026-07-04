import { useState, useEffect } from 'react'
import { useRuntime } from './use-runtime'

export function useAccessibility() {
  const runtime = useRuntime()
  const [options, setOptions] = useState(runtime.accessibility.getOptions())

  useEffect(() => {
    const unsub = runtime.accessibility.subscribe((opts) => setOptions({ ...opts }))
    return unsub
  }, [runtime])

  return {
    ...options,
    setReducedMotion: runtime.accessibility.setReducedMotion.bind(runtime.accessibility),
    setHighContrast: runtime.accessibility.setHighContrast.bind(runtime.accessibility),
    setFontSizeScale: runtime.accessibility.setFontSizeScale.bind(runtime.accessibility),
    announce: runtime.accessibility.announce.bind(runtime.accessibility),
  }
}
