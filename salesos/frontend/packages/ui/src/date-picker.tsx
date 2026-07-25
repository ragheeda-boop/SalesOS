"use client"

import { forwardRef, useCallback, useMemo, useState, useRef, useEffect, useId } from 'react'
import { cn } from './utils'

type DatePickerMode = 'single' | 'range'

interface DateRange {
  start: Date | null
  end: Date | null
}

interface DatePickerProps {
  value?: Date | DateRange | null
  defaultValue?: Date | DateRange | null
  onChange?: (value: Date | DateRange | null) => void
  mode?: DatePickerMode
  minDate?: Date
  maxDate?: Date
  disabled?: boolean
  locale?: string
  placeholder?: string
  label?: string
  error?: string
  className?: string
}

const DAYS_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}

function isWithinRange(date: Date, range: DateRange): boolean {
  if (!range.start || !range.end) return false
  return date >= range.start && date <= range.end
}

function addDays(date: Date, days: number): Date {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

function isDateDisabled(date: Date, minDate?: Date, maxDate?: Date): boolean {
  if (minDate && date < minDate) return true
  if (maxDate && date > maxDate) return true
  return false
}

export const DatePicker = forwardRef<HTMLDivElement, DatePickerProps>(
  ({ value, defaultValue, onChange, mode = 'single', minDate, maxDate, disabled, locale = 'en', placeholder = 'Select date...', label, error, className }, ref) => {
    const generatedId = useId()
    const id = `datepicker-${generatedId}`
    const errorId = `${id}-error`
    const [isOpen, setIsOpen] = useState(false)
    const [viewMonth, setViewMonth] = useState(new Date().getMonth())
    const [viewYear, setViewYear] = useState(new Date().getFullYear())
    const [hoveredDate, setHoveredDate] = useState<Date | null>(null)
    const isControlled = value !== undefined
    const [internalValue, setInternalValue] = useState<Date | DateRange | null>(defaultValue ?? null)
    const containerRef = useRef<HTMLDivElement>(null)
    const calendarRef = useRef<HTMLDivElement>(null)

    const currentValue = (isControlled ? value : internalValue) as Date | DateRange | null

    const formatDate = useCallback((d: Date): string => {
      return d.toLocaleDateString(locale === 'ar' ? 'ar-SA' : 'en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
      })
    }, [locale])

    const displayText = useMemo(() => {
      if (!currentValue) return ''
      if (mode === 'single') {
        return formatDate(currentValue as Date)
      }
      const range = currentValue as DateRange
      if (!range.start) return ''
      if (!range.end) return `${formatDate(range.start)} - ...`
      return `${formatDate(range.start)} - ${formatDate(range.end)}`
    }, [currentValue, mode, formatDate])

    const daysInMonth = useMemo(() => {
      return new Date(viewYear, viewMonth + 1, 0).getDate()
    }, [viewMonth, viewYear])

    const firstDayOfMonth = useMemo(() => {
      return new Date(viewYear, viewMonth, 1).getDay()
    }, [viewMonth, viewYear])

    const calendarDays = useMemo(() => {
      const days: (number | null)[] = []
      for (let i = 0; i < firstDayOfMonth; i++) {
        days.push(null)
      }
      for (let d = 1; d <= daysInMonth; d++) {
        days.push(d)
      }
      return days
    }, [firstDayOfMonth, daysInMonth])

    const handleSelect = useCallback((day: number) => {
      if (disabled) return
      const selected = new Date(viewYear, viewMonth, day)
      if (isDateDisabled(selected, minDate, maxDate)) return

      if (mode === 'single') {
        const newVal = isSameDay(selected, currentValue as Date) ? null : selected
        if (!isControlled) setInternalValue(newVal)
        onChange?.(newVal)
        setIsOpen(false)
      } else {
        const range = currentValue as DateRange | null
        if (!range?.start || (range.start && range.end)) {
          const newRange: DateRange = { start: selected, end: null }
          if (!isControlled) setInternalValue(newRange)
          onChange?.(newRange)
        } else {
          let start = range.start
          let end = selected
          if (end < start) { start = end; end = start }
          const newRange: DateRange = { start, end }
          if (!isControlled) setInternalValue(newRange)
          onChange?.(newRange)
        }
      }
    }, [disabled, viewYear, viewMonth, minDate, maxDate, mode, currentValue, isControlled, onChange])

    const navigateMonth = useCallback((delta: number) => {
      let m = viewMonth + delta
      let y = viewYear
      if (m < 0) { m = 11; y-- }
      if (m > 11) { m = 0; y++ }
      setViewMonth(m)
      setViewYear(y)
    }, [viewMonth, viewYear])

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
      const focusedDay = parseInt((e.target as HTMLElement)?.getAttribute('data-day') || '0', 10)
      let newDay = focusedDay

      switch (e.key) {
        case 'ArrowRight':
          e.preventDefault()
          newDay = Math.min(daysInMonth, focusedDay + 1)
          break
        case 'ArrowLeft':
          e.preventDefault()
          newDay = Math.max(1, focusedDay - 1)
          break
        case 'ArrowUp':
          e.preventDefault()
          newDay = Math.max(1, focusedDay - 7)
          break
        case 'ArrowDown':
          e.preventDefault()
          newDay = Math.min(daysInMonth, focusedDay + 7)
          break
        case 'Home':
          e.preventDefault()
          newDay = 1
          break
        case 'End':
          e.preventDefault()
          newDay = daysInMonth
          break
        case 'Enter':
        case ' ':
          e.preventDefault()
          if (focusedDay > 0) handleSelect(focusedDay)
          return
        case 'Escape':
          e.preventDefault()
          setIsOpen(false)
          return
        default:
          return
      }

      const focusEl = containerRef.current?.querySelector<HTMLButtonElement>(`[data-day="${newDay}"]`)
      focusEl?.focus()
    }, [daysInMonth, handleSelect])

    useEffect(() => {
      const handleClickOutside = (e: MouseEvent) => {
        if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
          setIsOpen(false)
        }
      }
      if (isOpen) {
        document.addEventListener('mousedown', handleClickOutside)
      }
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [isOpen])

    const today = new Date()

    return (
      <div ref={containerRef} className={cn('relative w-full', className)}>
        {label && (
          <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
            {label}
          </label>
        )}
        <button
          type="button"
          disabled={disabled}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          className={cn(
            'flex h-10 w-full items-center justify-between rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm',
            'focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)] focus:border-[var(--muhide-orange)]',
            'disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-danger-500 focus:ring-danger-500 focus:border-danger-500',
            !displayText && 'text-[var(--text-muted)]'
          )}
          aria-haspopup="dialog"
          aria-expanded={isOpen}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
        >
          <span>{displayText || placeholder}</span>
          <svg className="h-4 w-4 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>
        {error && (
          <p id={errorId} role="alert" className="mt-1 text-sm text-danger-600">
            {error}
          </p>
        )}

        {isOpen && (
          <div
            ref={calendarRef}
            role="dialog"
            aria-label="Date picker"
            className="absolute z-dropdown mt-1 w-[280px] rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-3 shadow-lg"
            onKeyDown={handleKeyDown}
          >
            <div className="mb-2 flex items-center justify-between">
              <button
                type="button"
                onClick={() => navigateMonth(-1)}
                className="rounded p-1 hover:bg-[var(--bg-secondary)]"
                aria-label="Previous month"
              >
                <svg className={cn('h-4 w-4', locale === 'ar' && 'rotate-180')} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <span className="text-sm font-medium text-[var(--text-primary)]">
                {MONTHS[viewMonth]} {viewYear}
              </span>
              <button
                type="button"
                onClick={() => navigateMonth(1)}
                className="rounded p-1 hover:bg-[var(--bg-secondary)]"
                aria-label="Next month"
              >
                <svg className={cn('h-4 w-4', locale === 'ar' && 'rotate-180')} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            <div className="mb-1 grid grid-cols-7 gap-0 text-center">
              {DAYS_SHORT.map((d, i) => {
                const dayIndex = locale === 'ar' ? (i + 1) % 7 : i
                return (
                  <div key={d} className="p-1 text-xs font-medium text-[var(--text-muted)]">
                    {DAYS_SHORT[dayIndex]}
                  </div>
                )
              })}
            </div>

            <div className="grid grid-cols-7 gap-0 text-center">
              {calendarDays.map((day, i) => {
                if (day === null) return <div key={`empty-${i}`} className="p-1" />

                const date = new Date(viewYear, viewMonth, day)
                const isDisabled = isDateDisabled(date, minDate, maxDate)
                const isToday = isSameDay(date, today)
                const isSelected = mode === 'single'
                  ? currentValue && isSameDay(date, currentValue as Date)
                  : (currentValue as DateRange)?.start && isSameDay(date, (currentValue as DateRange).start!)
                const isInRange = mode === 'range' && currentValue && (currentValue as DateRange).start && (currentValue as DateRange).end
                  ? isWithinRange(date, currentValue as DateRange)
                  : mode === 'range' && (currentValue as DateRange)?.start && !(currentValue as DateRange)?.end && hoveredDate
                    ? isWithinRange(date, { start: (currentValue as DateRange).start!, end: hoveredDate })
                    : false

                return (
                  <button
                    key={`day-${day}`}
                    type="button"
                    data-day={day}
                    disabled={isDisabled}
                    aria-current={isToday ? 'date' : undefined}
                    aria-selected={isSelected || undefined}
                    onClick={() => !isDisabled && handleSelect(day)}
                    onMouseEnter={() => mode === 'range' && !isDisabled && setHoveredDate(date)}
                    className={cn(
                      'h-8 w-8 rounded-full text-sm transition-colors',
                      isDisabled && 'cursor-not-allowed opacity-30',
                      isSelected && 'bg-[var(--muhide-orange)] text-white',
                      isInRange && !isSelected && 'bg-[var(--muhide-orange)]/10 text-[var(--text-primary)]',
                      !isSelected && !isInRange && !isDisabled && 'hover:bg-[var(--bg-secondary)] text-[var(--text-primary)]'
                    )}
                  >
                    {day}
                  </button>
                )
              })}
            </div>

            <div className="mt-2 flex justify-between border-t border-[var(--border-default)] pt-2">
              <button
                type="button"
                onClick={() => {
                  if (mode === 'single') {
                    const today = new Date()
                    if (!isControlled) setInternalValue(today)
                    onChange?.(today)
                    setIsOpen(false)
                  }
                }}
                className="text-xs text-[var(--muhide-orange)] hover:underline"
              >
                Today
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-xs text-[var(--text-muted)] hover:underline"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    )
  }
)
DatePicker.displayName = 'DatePicker'
