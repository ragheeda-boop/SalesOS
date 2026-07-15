"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { Employee360View } from "@/components/employee-360-view";
import { ArrowRight } from "lucide-react";

export default function EmployeePage() {
  const params = useParams();
  const id = params.id as string;

  return (
    <div>
      <Link
        href="/companies"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 transition-colors"
      >
        <ArrowRight className="h-4 w-4" />
        العودة
      </Link>
      <Employee360View employeeId={id} />
    </div>
  );
}
