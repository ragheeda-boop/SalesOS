"use client";

import { useMy360 } from "@/lib/hooks/employeeQueries";
import { Employee360Page } from "@/components/employee-360-page";
import { ErrorFallback } from "@/components/foundation/error-boundary";
import { Spinner } from "@salesos/ui";
import { useTranslation } from "@/lib/i18n";

export default function MyEmployeePage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, error, refetch } = useMy360();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="h-6 w-6" />
        <span className="mr-2 text-[var(--text-muted)]">
          {t("common.loading")}
        </span>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <ErrorFallback
        title={t("employee.load_error")}
        message={(error as Error)?.message || t("employee.load_error_hint")}
        onRetry={() => refetch()}
        showDetails={process.env.NODE_ENV === "development"}
        errorDetails={String(error)}
      />
    );
  }

  return <Employee360Page employeeId={data.profile.id} />;
}
