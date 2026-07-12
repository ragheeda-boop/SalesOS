"use client";

import { useMy360 } from "@/lib/hooks/employeeQueries";
import { Employee360View } from "@/components/employee-360-view";
import { ErrorFallback } from "@/components/foundation/error-boundary";
import { Spinner } from "@salesos/ui";

export default function MyEmployeePage() {
  const { data, isLoading, isError, error, refetch } = useMy360();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="h-6 w-6" />
        <span className="mr-2 text-neutral-500">جاري التحميل...</span>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <ErrorFallback
        title="فشل تحميل بيانات الموظف"
        message={(error as Error)?.message || "تعذر تحميل بيانات الموظف. تأكد من اتصال الخادم."}
        onRetry={() => refetch()}
        showDetails={process.env.NODE_ENV === "development"}
        errorDetails={String(error)}
      />
    );
  }

  return <Employee360View employeeId={data.profile.id} />;
}
