"use client";

import { useState } from "react";
import { Settings, User, Shield, Bell, Database, Key, ChevronLeft, Save } from "lucide-react";
import { cn } from "@salesos/ui";

const TABS = [
  { id: "profile", label: "الملف الشخصي", icon: User },
  { id: "security", label: "الأمان", icon: Shield },
  { id: "notifications", label: "الإشعارات", icon: Bell },
  { id: "api", label: "API Keys", icon: Key },
  { id: "data", label: "إعدادات البيانات", icon: Database },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");
  const [saved, setSaved] = useState(false);

  const showSaved = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">الإعدادات</h1>
        <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">إعدادات الحساب والنظام</p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="hidden w-56 shrink-0 space-y-1 sm:block">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                activeTab === tab.id
                  ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] dark:bg-[var(--muhide-orange)]/20 dark:text-orange-300"
                  : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-200"
              )}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1 space-y-6">
          {activeTab === "profile" && (
            <div className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-700 dark:bg-neutral-800">
              <h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">الملف الشخصي</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">الاسم الكامل</label>
                  <input
                    type="text"
                    defaultValue="المستخدم"
                    className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-700 dark:text-neutral-200"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">البريد الإلكتروني</label>
                  <input
                    type="email"
                    defaultValue="user@salesos.com"
                    className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-700 dark:text-neutral-200"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">رقم الجوال</label>
                  <input
                    type="tel"
                    defaultValue="+966 5X XXX XXXX"
                    className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-700 dark:text-neutral-200"
                  />
                </div>
                <button
                  onClick={showSaved}
                  className="flex items-center gap-2 rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm font-medium text-white hover:bg-orange-700"
                >
                  <Save className="h-4 w-4" />
                  حفظ التغييرات
                </button>
                {saved && <p className="text-sm text-success-600 dark:text-success-400">✓ تم الحفظ</p>}
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-700 dark:bg-neutral-800">
              <h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">الأمان</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">كلمة المرور الحالية</label>
                  <input type="password" className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-700 dark:text-neutral-200" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">كلمة المرور الجديدة</label>
                  <input type="password" className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-700 dark:text-neutral-200" />
                </div>
                <button
                  onClick={showSaved}
                  className="rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm font-medium text-white hover:bg-orange-700"
                >
                  تحديث كلمة المرور
                </button>
                {saved && <p className="text-sm text-success-600 dark:text-success-400">✓ تم التحديث</p>}
              </div>
            </div>
          )}

          {activeTab === "notifications" && (
            <div className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-700 dark:bg-neutral-800">
              <h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">الإشعارات</h2>
              <div className="space-y-3">
                {["إشعارات البريد الإلكتروني", "إشعارات التطبيق", "تنبيهات الفرص", "تحديثات الشركات"].map((item) => (
                  <label key={item} className="flex items-center justify-between rounded-lg border border-neutral-100 p-3 dark:border-neutral-700">
                    <span className="text-sm text-neutral-700 dark:text-neutral-300">{item}</span>
                    <input type="checkbox" defaultChecked className="rounded border-neutral-300 text-[var(--muhide-orange)]" />
                  </label>
                ))}
              </div>
            </div>
          )}

          {activeTab === "api" && (
            <div className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-700 dark:bg-neutral-800">
              <h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">API Keys</h2>
              <p className="mb-4 text-sm text-neutral-500 dark:text-neutral-400">مفاتيح API للتكامل مع الأنظمة الخارجية</p>
              <div className="space-y-3">
                {[
                  { name: "Production", key: "sk-••••••••••••a1b2" },
                  { name: "Development", key: "sk-••••••••••••c3d4" },
                ].map((k) => (
                  <div key={k.name} className="flex items-center justify-between rounded-lg border border-neutral-100 p-3 dark:border-neutral-700">
                    <div>
                      <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{k.name}</p>
                      <code className="text-xs text-neutral-500 dark:text-neutral-400">{k.key}</code>
                    </div>
                    <button className="text-xs text-[var(--muhide-orange)] hover:text-orange-700 dark:text-orange-400">نسخ</button>
                  </div>
                ))}
                <button className="mt-2 rounded-lg border border-dashed border-neutral-300 px-4 py-2 text-sm text-neutral-600 hover:border-orange-400 hover:text-[var(--muhide-orange)] dark:border-neutral-600 dark:text-neutral-400">
                  + إضافة مفتاح جديد
                </button>
              </div>
            </div>
          )}

          {activeTab === "data" && (
            <div className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-700 dark:bg-neutral-800">
              <h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">إعدادات البيانات</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">مصادر البيانات</label>
                  <div className="mt-2 space-y-2">
                    {[
                      { name: "بلدي", status: "active" },
                      { name: "تقييم", status: "active" },
                      { name: "إعلانات", status: "active" },
                      { name: "ناجز", status: "active" },
                      { name: "الهيئة العامة للعقار", status: "active" },
                    ].map((src) => (
                      <div key={src.name} className="flex items-center justify-between rounded-lg border border-neutral-100 p-2 dark:border-neutral-700">
                        <span className="text-sm text-neutral-700 dark:text-neutral-300">{src.name}</span>
                        <span className="rounded-full bg-success-100 px-2 py-0.5 text-xs font-medium text-success-700 dark:bg-success-900/30 dark:text-success-400">
                          {src.status === "active" ? "مفعل" : "غير مفعل"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
