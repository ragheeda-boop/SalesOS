"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { CustomerSuccessView } from "./CustomerSuccessView";
import { useTranslation } from "@/lib/i18n";

interface CustomerSuccessData {
  health_score: number;
  dau: number;
  wau: number;
  mau: number;
  adoption: {
    feature: string;
    label: string;
    user_count: number;
    total_users: number;
    adoption_pct: number;
  }[];
  nba_views: number;
  nba_accepts: number;
  nba_rejects: number;
  acceptance_rate: number;
  total_searches: number;
  searches_with_action: number;
  success_rate: number;
  tenants: {
    tenant_id: string;
    tenant_name: string;
    score: number;
    status: string;
    color: string;
    components: Record<
      string,
      { weight: number; value: number; contribution: number }
    >;
    user_count: number;
    last_active: string | null;
    renewal_risk: boolean;
    days_in_low_health: number;
  }[];
}

export function CustomerSuccessContainer() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useQuery<CustomerSuccessData>({
    queryKey: ["customer-success", "overview"],
    queryFn: () =>
      api
        .get("/customer-success/overview")
        .then((r: { data: CustomerSuccessData }) => r.data),
  });

  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="grid grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-xl bg-[var(--bg-secondary)]" />
          ))}
        </div>
        <div className="h-40 rounded-xl bg-[var(--bg-secondary)]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-xs text-[var(--color-danger-600)] p-3 bg-[var(--color-danger-50)] rounded-lg">
        {t("cs.loading_error")}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-xs text-[var(--text-muted)] p-3 text-center">
        {t("cs.no_data")}
      </div>
    );
  }

  return <CustomerSuccessView data={data} />;
}
