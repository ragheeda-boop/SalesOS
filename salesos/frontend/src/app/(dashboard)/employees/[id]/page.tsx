"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { Employee360Page } from "@/components/employee-360-page";
import { ArrowRight } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

export default function EmployeePage() {
  const params = useParams();
  const id = params.id as string;
  const { t } = useTranslation();

  return (
    <div>
      <Link
        href="/employees"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] dark:hover:text-[var(--text-primary)] transition-colors"
      >
        <ArrowRight className="h-4 w-4" />
        {t("common.back")}
      </Link>
      <Employee360Page employeeId={id} />
    </div>
  );
}
