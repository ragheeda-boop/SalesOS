"use client";

import { useMy360 } from "@/lib/hooks/employeeQueries";
import { Employee360View } from "@/components/employee-360-view";

export default function MyEmployeePage() {
  const { data, isLoading } = useMy360();

  if (isLoading) {
    return <div className="py-20 text-center text-gray-500">جاري التحميل...</div>;
  }

  if (!data) {
    return <div className="py-20 text-center text-gray-500">فشل تحميل البيانات</div>;
  }

  return <Employee360View employeeId={data.profile.id} />;
}
