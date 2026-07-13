"use client"

import { useEffect, useRef, useCallback } from "react"

const FOCUSABLE_SELECTORS =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

export function useFocusTrap<T extends HTMLElement>(active: boolean) {
  const containerRef = useRef<T>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  const trapFocus = useCallback(
    (e: KeyboardEvent) => {
      if (e.key !== "Tab" || !containerRef.current) return

      const focusable = containerRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS)
      if (focusable.length === 0) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault()
          last.focus()
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    },
    []
  )

  useEffect(() => {
    if (!active) return

    previousFocusRef.current = document.activeElement as HTMLElement

    const timer = setTimeout(() => {
      const focusable = containerRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS)
      if (focusable && focusable.length > 0) {
        focusable[0].focus()
      }
    }, 50)

    document.addEventListener("keydown", trapFocus)

    return () => {
      clearTimeout(timer)
      document.removeEventListener("keydown", trapFocus)
      previousFocusRef.current?.focus()
    }
  }, [active, trapFocus])

  return containerRef
}
