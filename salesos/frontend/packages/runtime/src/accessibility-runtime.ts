export interface AccessibilityOptions {
  reducedMotion?: boolean
  highContrast?: boolean
  fontSizeScale?: number
  screenReaderAnnouncements?: boolean
}

type AccessibilityListener = (options: AccessibilityOptions) => void

export class AccessibilityRuntime {
  private options: AccessibilityOptions = {
    reducedMotion: false,
    highContrast: false,
    fontSizeScale: 1,
    screenReaderAnnouncements: true,
  }
  private listeners = new Set<AccessibilityListener>()
  private announcerElement: HTMLDivElement | null = null

  constructor(options?: AccessibilityOptions) {
    if (options) this.options = { ...this.options, ...options }
    if (typeof window !== 'undefined') {
      this.detectPreferences()
      this.createAnnouncer()
    }
  }

  private detectPreferences() {
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    this.options.reducedMotion = motionQuery.matches
    motionQuery.addEventListener('change', (e) => {
      this.options.reducedMotion = e.matches
      this.notify()
    })

    const contrastQuery = window.matchMedia('(prefers-contrast: high)')
    this.options.highContrast = contrastQuery.matches
    contrastQuery.addEventListener('change', (e) => {
      this.options.highContrast = e.matches
      this.notify()
    })
  }

  private createAnnouncer() {
    this.announcerElement = document.createElement('div')
    this.announcerElement.setAttribute('aria-live', 'polite')
    this.announcerElement.setAttribute('aria-atomic', 'true')
    this.announcerElement.className = 'sr-only'
    document.body.appendChild(this.announcerElement)
  }

  private notify() {
    this.listeners.forEach((fn) => fn(this.options))
  }

  getOptions(): AccessibilityOptions {
    return { ...this.options }
  }

  setReducedMotion(value: boolean): void {
    this.options.reducedMotion = value
    document.documentElement.classList.toggle('reduce-motion', value)
    this.notify()
  }

  setHighContrast(value: boolean): void {
    this.options.highContrast = value
    document.documentElement.classList.toggle('high-contrast', value)
    this.notify()
  }

  setFontSizeScale(scale: number): void {
    this.options.fontSizeScale = Math.max(0.5, Math.min(2, scale))
    document.documentElement.style.fontSize = `${this.options.fontSizeScale * 16}px`
    this.notify()
  }

  announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
    if (!this.options.screenReaderAnnouncements || !this.announcerElement) return
    this.announcerElement.setAttribute('aria-live', priority)
    this.announcerElement.textContent = ''
    requestAnimationFrame(() => {
      this.announcerElement!.textContent = message
    })
  }

  focusElement(element: HTMLElement | null): void {
    element?.focus()
  }

  trapFocus(container: HTMLElement, activeElement?: HTMLElement): () => void {
    const focusableSelector =
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return
      const focusable = Array.from(container.querySelectorAll<HTMLElement>(focusableSelector))
      if (!focusable.length) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }
    container.addEventListener('keydown', handleKeyDown)
    activeElement?.focus()
    return () => container.removeEventListener('keydown', handleKeyDown)
  }

  subscribe(listener: AccessibilityListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  destroy(): void {
    this.announcerElement?.remove()
    this.listeners.clear()
  }
}
