"use client"

import { useState } from "react"
import Link from "next/link"
import { useCompanySearch } from "@/lib/hooks/companyQueries"
import { useDebounce } from "@salesos/hooks"
import { Input, Badge, Button, Spinner } from "@salesos/ui"
import { Search, Plus, Building2, ArrowLeft } from "lucide-react"

export default function CompaniesPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const debouncedQuery = useDebounce(searchQuery, 400)

  const { data, isLoading, isError } = useCompanySearch(
    debouncedQuery ? { q: debouncedQuery, page_size: 50 } : { page_size: 50 }
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">الشركات</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            إدارة ومراقبة الشركات المسجلة في المنصة
          </p>
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />}>إضافة شركة</Button>
      </div>

      <Input
        placeholder="البحث باسم الشركة أو رقم السجل التجاري..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        leftIcon={<Search className="h-4 w-4" />}
      />

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50">
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300">اسم الشركة</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300">رقم السجل</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300">الحالة</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300">المدينة</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
                  <div className="flex items-center justify-center gap-2">
                    <Spinner className="h-5 w-5" />
                    <span>جاري التحميل...</span>
                  </div>
                </td>
              </tr>
            ) : isError ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-red-500">فشل تحميل البيانات</td>
              </tr>
            ) : !data || data.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
                  {searchQuery ? "لا توجد نتائج للبحث" : "لا توجد شركات. قم باستيراد أول شركة للبدء."}
                </td>
              </tr>
            ) : (
              data.items.map((company) => (
                <tr key={company.id} className="border-b border-gray-100 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800/50">
                  <td className="px-4 py-3">
                    <Link href={`/companies/${company.id}`} className="flex items-center gap-2 font-medium text-blue-600 hover:underline dark:text-blue-400">
                      <Building2 className="h-4 w-4" />
                      {company.name_ar || company.name_en}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{company.cr_number}</td>
                  <td className="px-4 py-3">
                    <Badge variant="primary">{company.status}</Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{company.city || "-"}</td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/companies/${company.id}`}
                      className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline dark:text-blue-400"
                    >
                      عرض التفاصيل
                      <ArrowLeft className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {data && data.total > 0 && (
        <p className="text-sm text-gray-500 dark:text-gray-400">إجمالي {data.total} شركة</p>
      )}
    </div>
  )
}
