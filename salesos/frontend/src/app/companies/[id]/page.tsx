"use client"

import { useParams } from "next/navigation"
import Link from "next/link"
import { CompanyWorkspace } from "@/components/company-workspace"

export default function CompanyPage() {
  const params = useParams()
  const id = params.id as string

  return (
    <div>
      <Link
        href="/companies"
        className="mb-4 inline-flex items-center text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
      >
        العودة إلى الشركات
      </Link>
      <CompanyWorkspace companyId={id} />
    </div>
  )
}
