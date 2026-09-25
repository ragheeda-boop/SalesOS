"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Building2, Users, FileText, GitBranch, AlertTriangle } from "lucide-react";
import { PageHeader } from "../_components/page-header";
import { ErrorState, LoadingState, PermissionState } from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

const features = [
  {
    label: "Global Companies",
    description: "Canonical company records",
    href: "/v3/data/companies",
    icon: Building2,
    color: "text-blue-600",
  },
  {
    label: "Global People",
    description: "Canonical person records",
    href: "/v3/data/people",
    icon: Users,
    color: "text-green-600",
  },
  {
    label: "Source Files & Imports",
    description: "Manage ingested data files",
    href: "/v3/data/imports",
    icon: FileText,
    color: "text-purple-600",
  },
  {
    label: "Entity Resolution",
    description: "Golden records, conflicts, quality scores",
    href: "/v3/data/er",
    icon: GitBranch,
    color: "text-orange-600",
  },
  {
    label: "Review Queue",
    description: "P3 fuzzy pairs, suspicious CRs, triage",
    href: "/v3/review-queue",
    icon: AlertTriangle,
    color: "text-red-600",
  },
];

export default function V3DataPage() {
  const { ready, hasToken } = useAccessToken();
  const tenantHeaders = { "X-Tenant-Id": getTenantId() };

  const {
    data: companiesData,
    isLoading: companiesLoading,
    isError: companiesError,
    error: companiesErr,
  } = useQuery({
    queryKey: ["masterData", "companies", "count"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/master-data/global-companies", {
        params: { page: 1, page_size: 1 },
        headers: tenantHeaders,
      });
      return res.data as { total: number };
    },
    enabled: ready && hasToken,
  });

  const {
    data: peopleData,
    isLoading: peopleLoading,
    isError: peopleError,
    error: peopleErr,
  } = useQuery({
    queryKey: ["masterData", "people", "count"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/master-data/global-people", {
        params: { page: 1, page_size: 1 },
        headers: tenantHeaders,
      });
      return res.data as { total: number };
    },
    enabled: ready && hasToken,
  });

  const {
    data: sourceFilesData,
    isLoading: sourceFilesLoading,
    isError: sourceFilesError,
    error: sourceFilesErr,
  } = useQuery({
    queryKey: ["masterData", "sourceFiles", "count"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/master-data/source-files", {
        params: { page: 1, page_size: 1 },
        headers: tenantHeaders,
      });
      return res.data as { total: number };
    },
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState label="Checking session…" />;
  if (!hasToken) return <PermissionState nextPath="/v3/data" />;
  if (companiesLoading || peopleLoading || sourceFilesLoading)
    return <LoadingState label="Loading data overview…" />;
  if (companiesError || peopleError || sourceFilesError)
    return (
      <>
        <PageHeader
          title="Data"
          description="Master data management — companies, people, imports, entity resolution"
        />
        <ErrorState
          title="Could not load data counts"
          description={
            companiesErr instanceof Error
              ? companiesErr.message
              : peopleErr instanceof Error
                ? peopleErr.message
                : sourceFilesErr instanceof Error
                  ? sourceFilesErr.message
                  : "Request failed"
          }
        />
      </>
    );

  return (
    <>
      <PageHeader
        title="Data"
        description="Master data management — companies, people, imports, entity resolution"
      />

      {/* Metric Cards */}
      <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-lg border border-[var(--border-default)] p-4">
          <div className="text-2xl font-bold text-[var(--text-link)]">
            {companiesData?.total?.toLocaleString() ?? "-"}
          </div>
          <div className="text-sm text-[var(--text-muted)]">Global Companies</div>
        </div>
        <div className="rounded-lg border border-[var(--border-default)] p-4">
          <div className="text-2xl font-bold text-[var(--text-success)]">
            {peopleData?.total?.toLocaleString() ?? "-"}
          </div>
          <div className="text-sm text-[var(--text-muted)]">Global People</div>
        </div>
        <div className="rounded-lg border border-[var(--border-default)] p-4">
          <div className="text-2xl font-bold text-[var(--text-link)]">
            {sourceFilesData?.total?.toLocaleString() ?? "-"}
          </div>
          <div className="text-sm text-[var(--text-muted)]">Source Files</div>
        </div>
        <div className="rounded-lg border border-[var(--border-default)] p-4">
          <div className="text-2xl font-bold text-[var(--text-muted)]">
            {((companiesData?.total ?? 0) + (peopleData?.total ?? 0)).toLocaleString()}
          </div>
          <div className="text-sm text-[var(--text-muted)]">Canonical Entities</div>
        </div>
      </div>

      {/* Feature Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f) => (
          <Link
            key={f.href}
            href={f.href}
            className="group rounded-lg border border-[var(--border-default)] p-6 transition-colors hover:border-[var(--border-hover)] hover:bg-[var(--bg-hover)]"
          >
            <f.icon className={`mb-3 h-8 w-8 ${f.color}`} />
            <h3 className="mb-1 text-sm font-medium text-[var(--text-primary)] group-hover:text-[var(--text-link)]">
              {f.label}
            </h3>
            <p className="text-sm text-[var(--text-muted)]">
              {f.label === "Global Companies"
                ? `${(companiesData?.total ?? 0).toLocaleString()} canonical records`
                : f.label === "Global People"
                  ? `${(peopleData?.total ?? 0).toLocaleString()} canonical records`
                  : f.label === "Source Files & Imports"
                    ? `${(sourceFilesData?.total ?? 0).toLocaleString()} source files`
                    : f.description}
            </p>
          </Link>
        ))}
      </div>
    </>
  );
}
