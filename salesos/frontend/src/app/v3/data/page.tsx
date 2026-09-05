"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Building2, Users, FileText, GitBranch, AlertTriangle } from "lucide-react";
import { PageHeader } from "../_components/page-header";
import { LoadingState } from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

const features = [
  {
    label: "Global Companies",
    description: "296,746 canonical company records",
    href: "/v3/data/companies",
    icon: Building2,
    color: "text-blue-600",
  },
  {
    label: "Global People",
    description: "1,124 canonical person records",
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

  const { data: companiesData, isLoading: companiesLoading } = useQuery({
    queryKey: ["masterData", "companies", "count"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/master-data/global-companies", {
        params: { page: 1, page_size: 1 },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as { total: number };
    },
    enabled: ready && hasToken,
  });

  const { data: peopleData, isLoading: peopleLoading } = useQuery({
    queryKey: ["masterData", "people", "count"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/master-data/global-people", {
        params: { page: 1, page_size: 1 },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return res.data as { total: number };
    },
    enabled: ready && hasToken,
  });

  if (!ready || companiesLoading || peopleLoading) return <LoadingState />;

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
          <div className="text-2xl font-bold text-[var(--text-link)]">6</div>
          <div className="text-sm text-[var(--text-muted)]">Source Files</div>
        </div>
        <div className="rounded-lg border border-[var(--border-default)] p-4">
          <div className="text-2xl font-bold text-[var(--text-muted)]">296,746</div>
          <div className="text-sm text-[var(--text-muted)]">Total Records</div>
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
            <p className="text-sm text-[var(--text-muted)]">{f.description}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
