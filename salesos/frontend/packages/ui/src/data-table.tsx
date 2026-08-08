"use client";

import { useState, useCallback, useRef, useEffect, type ReactNode } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type RowSelectionState,
  type OnChangeFn,
} from "@tanstack/react-table";
import { cn } from "./utils";
import { Skeleton } from "./skeleton";
import { EmptyState } from "./empty-state";
import { ChevronsUpDown, ArrowUp, ArrowDown, MoreHorizontal } from "lucide-react";

interface DataTableAction {
  label: string;
  onClick: (row: unknown) => void;
  destructive?: boolean;
}

interface DataTableEmptyState {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  learnMoreLink?: string;
}

interface DataTableProps<TData> {
  columns: ColumnDef<TData>[];
  data: TData[];
  sortable?: boolean;
  selectable?: boolean;
  onSort?: (sorting: SortingState) => void;
  onSelect?: (selected: TData[]) => void;
  onRowClick?: (row: TData) => void;
  actions?: DataTableAction[];
  loading?: boolean;
  emptyState?: DataTableEmptyState;
  className?: string;
}

function HeaderCheckbox({
  checked,
  indeterminate,
  onChange,
}: {
  checked: boolean;
  indeterminate: boolean;
  onChange: (event: unknown) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.indeterminate = indeterminate;
  }, [indeterminate]);
  return (
    <input
      ref={ref}
      type="checkbox"
      className="h-4 w-4 rounded border-[var(--border-default)]"
      checked={checked}
      onChange={onChange as React.ChangeEventHandler<HTMLInputElement>}
      aria-label="Select all rows"
    />
  );
}

export function DataTable<TData>({
  columns: rawColumns,
  data,
  sortable = false,
  selectable = false,
  onSort,
  onSelect: _onSelect,
  onRowClick,
  actions,
  loading = false,
  emptyState,
  className,
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [openActionRow, setOpenActionRow] = useState<string | null>(null);
  const actionRef = useRef<HTMLDivElement>(null);

  const handleSortChange: OnChangeFn<SortingState> = useCallback(
    (updater) => {
      setSorting((prev) => {
        const next = typeof updater === "function" ? updater(prev) : updater;
        onSort?.(next);
        return next;
      });
    },
    [onSort]
  );

  const handleSelectChange: OnChangeFn<RowSelectionState> = useCallback((updater) => {
    setRowSelection((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      return next;
    });
  }, []);

  const columns: ColumnDef<TData>[] = [
    ...(selectable
      ? [
          {
            id: "select",
            header: ({ table }) => (
              <HeaderCheckbox
                checked={table.getIsAllRowsSelected()}
                indeterminate={table.getIsSomeRowsSelected()}
                onChange={table.getToggleAllRowsSelectedHandler()}
              />
            ),
            cell: ({ row }) => (
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-[var(--border-default)]"
                checked={row.getIsSelected()}
                onChange={row.getToggleSelectedHandler()}
                aria-label={`Select row ${row.index + 1}`}
              />
            ),
            size: 40,
          } as ColumnDef<TData>,
        ]
      : []),
    ...rawColumns,
    ...(actions
      ? [
          {
            id: "actions",
            header: "",
            cell: ({ row }) => (
              <div className="relative" ref={actionRef}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setOpenActionRow(openActionRow === row.id ? null : row.id);
                  }}
                  className="rounded-md p-1 text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
                  aria-label="Row actions"
                  aria-haspopup="true"
                  aria-expanded={openActionRow === row.id}
                >
                  <MoreHorizontal className="h-4 w-4" />
                </button>
                {openActionRow === row.id && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setOpenActionRow(null)} />
                    <div className="absolute end-0 z-20 min-w-[160px] rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-1 shadow-muhide-4">
                      {actions.map((action, ai) => (
                        <button
                          key={ai}
                          onClick={(e) => {
                            e.stopPropagation();
                            action.onClick(row.original);
                            setOpenActionRow(null);
                          }}
                          className={cn(
                            "flex w-full items-center rounded-md px-3 py-2 text-start text-sm hover:bg-[var(--bg-secondary)]",
                            action.destructive && "text-danger-600"
                          )}
                        >
                          {action.label}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            ),
            size: 48,
          } as ColumnDef<TData>,
        ]
      : []),
  ];

  const table = useReactTable({
    columns,
    data,
    state: { sorting, rowSelection },
    onSortingChange: handleSortChange,
    onRowSelectionChange: handleSelectChange,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: sortable ? getSortedRowModel() : undefined,
    enableSorting: sortable,
    enableRowSelection: selectable,
  });

  const selectedRows = selectable ? table.getSelectedRowModel().rows.map((r) => r.original) : [];

  if (loading) {
    return (
      <div className="w-full overflow-x-auto">
        <table className={cn("w-full border-collapse text-sm", className)}>
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="sticky top-0 border-b border-[var(--border-default)] bg-[var(--bg-secondary)] px-4 py-3 text-left font-medium text-[var(--text-secondary)]"
                    style={{ width: header.getSize() }}
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
            {Array.from({ length: 5 }).map((_, ri) => (
              <tr key={ri}>
                {table.getAllColumns().map((_, ci) => (
                  <td key={ci} className="px-4 py-3">
                    <Skeleton variant="text" className="h-4" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (!data.length) {
    return (
      <EmptyState
        icon={emptyState?.icon}
        title={emptyState?.title ?? "No data"}
        description={emptyState?.description}
        action={emptyState?.action}
        learnMoreLink={emptyState?.learnMoreLink}
        className={className}
      />
    );
  }

  return (
    <div className="w-full overflow-x-auto">
      {selectable && selectedRows.length > 0 && (
        <div
          role="status"
          aria-live="polite"
          className="flex items-center gap-2 border-b border-[var(--border-default)] bg-[var(--bg-secondary)] px-4 py-2 text-sm text-[var(--text-muted)]"
        >
          <span className="font-medium text-[var(--text-primary)]">
            {selectedRows.length} selected
          </span>
        </div>
      )}
      <table className={cn("w-full border-collapse text-sm", className)}>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className={cn(
                    "sticky top-0 border-b border-[var(--border-default)] bg-[var(--bg-secondary)] px-4 py-3 text-left font-medium text-[var(--text-secondary)]",
                    sortable &&
                      header.column.getCanSort() &&
                      "cursor-pointer select-none hover:bg-[var(--bg-tertiary)]"
                  )}
                  style={{ width: header.getSize() }}
                  onClick={sortable ? header.column.getToggleSortingHandler() : undefined}
                  aria-sort={
                    header.column.getIsSorted() === "asc"
                      ? "ascending"
                      : header.column.getIsSorted() === "desc"
                        ? "descending"
                        : undefined
                  }
                >
                  <div className="flex items-center gap-1">
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                    {sortable && header.column.getCanSort() && (
                      <span className="text-[var(--text-muted)]">
                        {header.column.getIsSorted() === "asc" ? (
                          <ArrowUp className="h-3.5 w-3.5" />
                        ) : header.column.getIsSorted() === "desc" ? (
                          <ArrowDown className="h-3.5 w-3.5" />
                        ) : (
                          <ChevronsUpDown className="h-3.5 w-3.5 opacity-50" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              onClick={() => onRowClick?.(row.original)}
              className={cn(
                "border-b border-[var(--border-default)] transition-colors motion-reduce:transition-none",
                onRowClick && "cursor-pointer hover:bg-[var(--bg-secondary)]",
                row.getIsSelected() && "bg-[var(--muhide-orange)]/5"
              )}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
