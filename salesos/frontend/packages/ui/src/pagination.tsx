"use client"

import { useCallback, useMemo } from 'react'
import { cn } from './utils'

interface PaginationProps {
  currentPage: number
  totalPages: number
  totalItems: number
  pageSize: number
  onPageChange: (page: number) => void
  onPageSizeChange?: (pageSize: number) => void
  pageSizeOptions?: number[]
  className?: string
}

export function Pagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 50, 100],
  className,
}: PaginationProps) {
  const startItem = (currentPage - 1) * pageSize + 1
  const endItem = Math.min(currentPage * pageSize, totalItems)

  const visiblePages = useMemo(() => {
    const pages: (number | 'ellipsis')[] = []
    const maxVisible = 7

    if (totalPages <= maxVisible + 2) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)
      let start = Math.max(2, currentPage - 2)
      let end = Math.min(totalPages - 1, currentPage + 2)

      if (currentPage <= 3) {
        start = 2
        end = Math.min(totalPages - 1, maxVisible - 1)
      }
      if (currentPage >= totalPages - 2) {
        start = Math.max(2, totalPages - maxVisible + 2)
        end = totalPages - 1
      }

      if (start > 2) pages.push('ellipsis')
      for (let i = start; i <= end; i++) pages.push(i)
      if (end < totalPages - 1) pages.push('ellipsis')
      pages.push(totalPages)
    }

    return pages
  }, [currentPage, totalPages])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, targetPage: number) => {
      switch (e.key) {
        case 'ArrowRight':
          e.preventDefault()
          if (currentPage < totalPages) onPageChange(currentPage + 1)
          break
        case 'ArrowLeft':
          e.preventDefault()
          if (currentPage > 1) onPageChange(currentPage - 1)
          break
        case 'Home':
          e.preventDefault()
          onPageChange(1)
          break
        case 'End':
          e.preventDefault()
          onPageChange(totalPages)
          break
        case 'Enter':
        case ' ':
          e.preventDefault()
          onPageChange(targetPage)
          break
      }
    },
    [currentPage, totalPages, onPageChange]
  )

  if (totalPages <= 0) return null

  return (
    <nav
      role="navigation"
      aria-label="pagination"
      className={cn('flex flex-wrap items-center justify-between gap-4', className)}
    >
      <div className="text-sm text-[var(--text-muted)]">
        Showing {startItem}–{endItem} of {totalItems}
      </div>

      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => onPageChange(1)}
          disabled={currentPage <= 1}
          aria-label="First page"
          className="rounded-md p-2 text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
        <button
          type="button"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          aria-label="Previous page"
          className="rounded-md p-2 text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="flex items-center gap-1 mx-1">
          {visiblePages.map((page, i) => {
            if (page === 'ellipsis') {
              return (
                <span key={`ellipsis-${i}`} className="px-1 text-sm text-[var(--text-muted)]">
                  ...
                </span>
              )
            }
            return (
              <button
                key={page}
                type="button"
                onClick={() => onPageChange(page)}
                onKeyDown={(e) => handleKeyDown(e, page)}
                aria-current={page === currentPage ? 'page' : undefined}
                aria-label={`Page ${page}`}
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-md text-sm transition-colors',
                  page === currentPage
                    ? 'bg-[var(--muhide-orange)] text-white'
                    : 'text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]'
                )}
              >
                {page}
              </button>
            )
          })}
        </div>

        <button
          type="button"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          aria-label="Next page"
          className="rounded-md p-2 text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <button
          type="button"
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage >= totalPages}
          aria-label="Last page"
          className="rounded-md p-2 text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {onPageSizeChange && (
        <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="rounded border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1 text-sm text-[var(--text-primary)]"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>
      )}
    </nav>
  )
}
