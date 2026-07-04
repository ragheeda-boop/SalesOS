"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { Employee360View } from "@/components/employee-360-view";

export default function EmployeePage() {
  const params = useParams();
  const id = params.id as string;

  return (
    <div>
      <Link
        href="/dashboard"
        className="mb-4 inline-flex items-center text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
      >
        العودة إلى لوحة المعلومات
      </Link>
      <Employee360View employeeId={id} />
    </div>
  );
}
