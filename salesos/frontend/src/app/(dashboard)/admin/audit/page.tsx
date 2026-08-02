"use client";

import { useState, useCallback } from "react";
import { Input, Button, Badge, Card, Spinner, useToast } from "@salesos/ui";
import {
  Search,
  Download,
  ChevronLeft,
  ChevronRight,
  FileText,
  Filter,
  RefreshCw,
  X,
} from "lucide-react";
import { useAdminAuditLogs } from "@/lib/hooks/adminQueries";
import type { AuditLogEntry } from "@/lib/api";
import { OwnerOpsPageHonesty } from "@/features/admin/OwnerOpsPageHonesty";

const ACTION_TYPE_LABELS: Record<string, string> = {
  create: "Create",
  update: "Update",
  delete: "Delete",
  read: "Read",
  login: "Login",
  logout: "Logout",
  export: "Export",
  import: "Import",
  assign: "Assign",
  revoke: "Revoke",
};

const RESOURCE_LABELS: Record<string, string> = {
  user: "User",
  tenant: "Tenant",
  role: "Role",
  permission: "Permission",
  company: "Company",
  contact: "Contact",
  deal: "Deal",
  plan: "Plan",
  license: "License",
  feature_flag: "Feature Flag",
  job: "Job",
  settings: "Settings",
};

const ACTION_VARIANT: Record<
  string,
  "success" | "warning" | "danger" | "default"
> = {
  create: "success",
  update: "warning",
  delete: "danger",
  read: "default",
  login: "success",
  logout: "default",
  export: "default",
  import: "success",
  assign: "warning",
  revoke: "danger",
};

interface AuditFilters {
  dateFrom?: string;
  dateTo?: string;
  actionType?: string;
  resource?: string;
  search?: string;
  page: number;
  pageSize: number;
}

export default function AdminAuditPage() {
  const { toast } = useToast();
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<AuditFilters>({
    dateFrom: undefined,
    dateTo: undefined,
    actionType: undefined,
    resource: undefined,
    search: undefined,
    page: 1,
    pageSize: 20,
  });

  const { data, isLoading, refetch } = useAdminAuditLogs({
    page: filters.page,
    page_size: filters.pageSize,
    date_from: filters.dateFrom,
    date_to: filters.dateTo,
    action_type: filters.actionType,
    resource: filters.resource,
    search: filters.search,
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / filters.pageSize));

  const handleFilterChange = useCallback((partial: Partial<AuditFilters>) => {
    setFilters((prev) => ({ ...prev, ...partial }));
  }, []);

  const handleClearFilters = useCallback(() => {
    setFilters({ page: 1, pageSize: 20 });
  }, []);

  const handleExport = useCallback(() => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.set("date_from", filters.dateFrom);
    if (filters.dateTo) params.set("date_to", filters.dateTo);
    if (filters.actionType) params.set("action_type", filters.actionType);
    if (filters.resource) params.set("resource", filters.resource);
    if (filters.search) params.set("search", filters.search);
    params.set("format", "csv");
    window.open(`/api/v1/audit/logs/export?${params.toString()}`, "_blank");
    toast({
      variant: "default",
      title: "Export started",
      description: "Your CSV export is downloading.",
    });
  }, [filters, toast]);

  const activeFilterCount = [
    filters.dateFrom,
    filters.dateTo,
    filters.actionType,
    filters.resource,
    filters.search,
  ].filter(Boolean).length;

  const formatDateTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-audit-page">
      <OwnerOpsPageHonesty surface="audit" />
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">
            Audit Log
          </h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Track all user actions, resource changes, and system events.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            leftIcon={<RefreshCw className="h-4 w-4" />}
          >
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            leftIcon={<Download className="h-4 w-4" />}
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Filter Toggle */}
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
          leftIcon={<Filter className="h-4 w-4" />}
        >
          Filters{" "}
          {activeFilterCount > 0 && (
            <Badge variant="default" className="ml-1">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            leftIcon={<X className="h-4 w-4" />}
          >
            Clear all
          </Button>
        )}
        <span className="text-sm text-[var(--text-muted)]">
          {total.toLocaleString()} entries
        </span>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <Card className="p-4 space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1 text-[var(--text-secondary)]">
                From Date
              </label>
              <Input
                type="date"
                value={filters.dateFrom || ""}
                onChange={(e) =>
                  handleFilterChange({
                    dateFrom: e.target.value || undefined,
                    page: 1,
                  })
                }
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1 text-[var(--text-secondary)]">
                To Date
              </label>
              <Input
                type="date"
                value={filters.dateTo || ""}
                onChange={(e) =>
                  handleFilterChange({
                    dateTo: e.target.value || undefined,
                    page: 1,
                  })
                }
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1 text-[var(--text-secondary)]">
                Action Type
              </label>
              <select
                value={filters.actionType || ""}
                onChange={(e) =>
                  handleFilterChange({
                    actionType: e.target.value || undefined,
                    page: 1,
                  })
                }
                className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
              >
                <option value="">All Actions</option>
                {Object.entries(ACTION_TYPE_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1 text-[var(--text-secondary)]">
                Resource Type
              </label>
              <select
                value={filters.resource || ""}
                onChange={(e) =>
                  handleFilterChange({
                    resource: e.target.value || undefined,
                    page: 1,
                  })
                }
                className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
              >
                <option value="">All Resources</option>
                {Object.entries(RESOURCE_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="relative max-w-sm">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-disabled)]" />
            <Input
              placeholder="Search audit logs..."
              value={filters.search || ""}
              onChange={(e) =>
                handleFilterChange({
                  search: e.target.value || undefined,
                  page: 1,
                })
              }
              className="pr-9"
            />
          </div>
        </Card>
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)]">
        {isLoading ? (
          <div className="py-20 text-center text-[var(--text-muted)]">
            <Spinner className="mx-auto h-6 w-6" />
            <p className="mt-2">Loading audit logs...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="py-20 text-center text-[var(--text-muted)]">
            <FileText className="mx-auto mb-2 h-10 w-10 opacity-40" />
            <p>No audit log entries found</p>
            <p className="mt-1 text-sm text-[var(--text-disabled)]">
              No events match your current filters.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Timestamp
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    User
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Action
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Resource
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    Details
                  </th>
                  <th className="p-3 font-medium text-[var(--text-muted)]">
                    IP
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((entry: AuditLogEntry) => (
                  <tr
                    key={entry.id}
                    className="border-b hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]/50 transition-colors"
                  >
                    <td className="p-3 text-xs text-[var(--text-muted)] font-mono whitespace-nowrap">
                      {formatDateTime(entry.created_at)}
                    </td>
                    <td className="p-3">
                      <div className="text-sm font-medium text-[var(--text-primary)]">
                        {entry.actor_name}
                      </div>
                      <div className="text-xs text-[var(--text-muted)]">
                        {entry.actor_email}
                      </div>
                    </td>
                    <td className="p-3">
                      <Badge
                        variant={ACTION_VARIANT[entry.action_type] || "default"}
                        className="font-mono text-[10px]"
                      >
                        {ACTION_TYPE_LABELS[entry.action_type] ||
                          entry.action_type}
                      </Badge>
                    </td>
                    <td className="p-3">
                      <div className="text-sm">
                        <span className="font-medium text-[var(--text-secondary)]">
                          {RESOURCE_LABELS[entry.resource_type] ||
                            entry.resource_type}
                        </span>
                        <span className="text-[var(--text-muted)] ml-1 text-xs">
                          {entry.resource}
                        </span>
                      </div>
                    </td>
                    <td className="p-3 text-xs text-[var(--text-secondary)] max-w-[200px] truncate">
                      {entry.details
                        ? JSON.stringify(entry.details).slice(0, 80)
                        : "-"}
                    </td>
                    <td className="p-3 text-xs text-[var(--text-muted)] font-mono">
                      {entry.ip_address || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-[var(--text-muted)]">
            Showing {(filters.page - 1) * filters.pageSize + 1}-
            {Math.min(filters.page * filters.pageSize, total)} of{" "}
            {total.toLocaleString()}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleFilterChange({ page: filters.page - 1 })}
              disabled={filters.page <= 1}
              leftIcon={<ChevronRight className="h-4 w-4" />}
            >
              Previous
            </Button>
            <span className="text-sm font-medium text-[var(--text-secondary)]">
              Page {filters.page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleFilterChange({ page: filters.page + 1 })}
              disabled={filters.page >= totalPages}
              leftIcon={<ChevronLeft className="h-4 w-4" />}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
