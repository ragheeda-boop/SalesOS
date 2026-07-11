import { type ColumnDef, useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table'
import { cn } from './utils'
import { Loader2 } from 'lucide-react'

interface TableProps<TData> {
  columns: ColumnDef<TData>[]
  data: TData[]
  loading?: boolean
  onRowClick?: (row: TData) => void
  className?: string
}

export function Table<TData>({ columns, data, loading, onRowClick, className }: TableProps<TData>) {
  const table = useReactTable({
    columns,
    data,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <div className="w-full overflow-x-auto">
      <table className={cn('w-full border-collapse text-sm', className)}>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="sticky top-0 border-b border-[var(--border-default)] bg-[var(--bg-secondary)] px-4 py-3 text-left font-medium text-[var(--text-secondary)]"
                >
                  {header.isPlaceholder
                    ? null
                    : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <tr key={i}>
                {columns.map((_, j) => (
                  <td key={j} className="px-4 py-3">
                    <div className="h-4 w-full animate-pulse rounded bg-[var(--bg-tertiary)]" />
                  </td>
                ))}
              </tr>
            ))
          ) : table.getRowModel().rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-[var(--text-muted)]">
                <div className="flex flex-col items-center gap-2">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>No results</span>
                </div>
              </td>
            </tr>
          ) : (
            table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                onClick={() => onRowClick?.(row.original)}
                className={cn(
                  'border-b border-[var(--border-default)] transition-colors',
                  onRowClick && 'cursor-pointer hover:bg-[var(--bg-secondary)]'
                )}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
