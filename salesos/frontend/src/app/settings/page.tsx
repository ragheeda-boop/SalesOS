"use client"

import { Settings } from "lucide-react"

export default function SettingsPage() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-500 dark:text-gray-400">
      <Settings className="mb-4 h-16 w-16" />
      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">الإعدادات</h2>
      <p className="mt-2 text-sm">قريبًا — هذه الصفحة قيد التطوير.</p>
    </div>
  )
}
