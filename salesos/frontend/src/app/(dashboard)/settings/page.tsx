"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Settings, User, Shield, Bell, Database, Key, ChevronLeft, Save, Loader2, Copy, Trash2 } from "lucide-react";
import { Tabs, TabsList, Tab, TabsPanel, Input, Button, Badge, Card, cn, useToast } from "@salesos/ui";
import api, { getCurrentUser, changePassword } from "@/lib/api";
import { useTenant } from "@/lib/hooks/useTenant";

const TABS = [
  { id: "profile", label: "الملف الشخصي", icon: User },
  { id: "security", label: "الأمان", icon: Shield },
  { id: "notifications", label: "الإشعارات", icon: Bell },
  { id: "api", label: "API Keys", icon: Key },
  { id: "data", label: "إعدادات البيانات", icon: Database },
];

interface ApiKey {
  id: string;
  name: string;
  key_preview: string;
  created_at: string;
}

function loadApiKeys(): ApiKey[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem("api_keys") || "[]");
  } catch {
    return [];
  }
}

function saveApiKeys(keys: ApiKey[]) {
  localStorage.setItem("api_keys", JSON.stringify(keys));
}

function generateKey(): string {
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
  let key = "sk-";
  for (let i = 0; i < 32; i++) {
    key += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return key;
}

function loadNotifications(): Record<string, boolean> {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(localStorage.getItem("notification_prefs") || "null") || {};
  } catch {
    return {};
  }
}

const ROLE_LABELS: Record<string, string> = {
  admin: "مدير",
  manager: "مدير فريق",
  user: "مستخدم",
};

export default function SettingsPage() {
  const { toast } = useToast();
  const { tenantId } = useTenant();
  const [activeTab, setActiveTab] = useState("profile");

  // ─── Profile ─────────────────────────────────────────────
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ["profile", "me"],
    queryFn: getCurrentUser,
  });

  const [profileForm, setProfileForm] = useState({
    full_name: "",
    full_name_ar: "",
    email: "",
  });

  useEffect(() => {
    if (profile) {
      setProfileForm({
        full_name: profile.full_name,
        full_name_ar: profile.full_name_ar || "",
        email: profile.email,
      });
    }
  }, [profile]);

  const profileMutation = useMutation({
    mutationFn: async (data: { full_name: string; full_name_ar: string }) => {
      await api.patch("/api/v1/identity/users/me", data);
    },
    onSuccess: () => {
      toast({ variant: "success", title: "تم حفظ التغييرات" });
    },
    onError: () => {
      toast({ variant: "error", title: "فشل الحفظ", description: "حدث خطأ أثناء حفظ التغييرات" });
    },
  });

  // ─── Password ────────────────────────────────────────────
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [passwordError, setPasswordError] = useState("");

  const passwordMutation = useMutation({
    mutationFn: ({ current_password, new_password }: { current_password: string; new_password: string }) =>
      changePassword(current_password, new_password),
    onSuccess: () => {
      toast({ variant: "success", title: "تم تحديث كلمة المرور" });
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
      setPasswordError("");
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      const msg = err.response?.data?.detail || "فشل تحديث كلمة المرور";
      setPasswordError(msg);
      toast({ variant: "error", title: "فشل التحديث", description: msg });
    },
  });

  // ─── Notifications ───────────────────────────────────────
  const [notifPrefs, setNotifPrefs] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setNotifPrefs(loadNotifications());
  }, []);

  const toggleNotif = (key: string) => {
    const updated = { ...notifPrefs, [key]: !notifPrefs[key] };
    setNotifPrefs(updated);
    localStorage.setItem("notification_prefs", JSON.stringify(updated));
    toast({ variant: "success", title: "تم تحديث الإعدادات" });
  };

  // ─── API Keys ────────────────────────────────────────────
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [showNewKey, setShowNewKey] = useState<string | null>(null);

  useEffect(() => {
    setApiKeys(loadApiKeys());
  }, []);

  const addApiKey = () => {
    if (!newKeyName.trim()) return;
    const key = generateKey();
    const newKey: ApiKey = {
      id: crypto.randomUUID(),
      name: newKeyName.trim(),
      key_preview: key.slice(0, 7) + "••••••••" + key.slice(-4),
      created_at: new Date().toISOString(),
    };
    const updated = [...apiKeys, newKey];
    setApiKeys(updated);
    saveApiKeys(updated);
    setShowNewKey(key);
    setNewKeyName("");
    toast({ variant: "success", title: "تم إنشاء المفتاح" });
  };

  const revokeApiKey = (id: string) => {
    const updated = apiKeys.filter((k) => k.id !== id);
    setApiKeys(updated);
    saveApiKeys(updated);
    toast({ variant: "success", title: "تم حذف المفتاح" });
  };

  const copyKey = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ variant: "default", title: "تم النسخ" });
  };

  if (profileLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--muhide-orange)]" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">الإعدادات</h1>
        <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">إعدادات الحساب والنظام</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex gap-6">
          {/* Sidebar */}
          <TabsList className="hidden w-56 shrink-0 sm:flex sm:flex-col items-stretch !border-0 !border-b-0 !gap-0">
            {TABS.map((tab) => (
              <Tab
                key={tab.id}
                value={tab.id}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors !border-b-0 !border-transparent data-[state=active]:!border-b-0 data-[state=active]:!border-transparent data-[state=active]:bg-[var(--muhide-orange)]/10 data-[state=active]:text-[var(--muhide-orange)] dark:data-[state=active]:bg-[var(--muhide-orange)]/20 dark:data-[state=active]:text-orange-300 text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-200"
              >
                <tab.icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </Tab>
            ))}
          </TabsList>

          {/* Content */}
          <div className="min-w-0 flex-1 space-y-6">
            {/* ─── Profile Tab ──────────────────────────── */}
            <TabsPanel value="profile">
              <Card className="p-6">
                <h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">الملف الشخصي</h2>
                {profile && (
                  <div className="mb-4 flex items-center gap-3 rounded-lg bg-neutral-50 p-3 dark:bg-neutral-700/50">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]">
                      <User className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{profile.full_name}</p>
                      <p className="text-xs text-neutral-500 dark:text-neutral-400">{ROLE_LABELS[profile.role] || profile.role}</p>
                    </div>
                    <Badge className="mr-auto">{profile.is_active ? "نشط" : "غير نشط"}</Badge>
                  </div>
                )}
                <div className="space-y-4">
                  <Input
                    label="الاسم بالإنجليزية"
                    value={profileForm.full_name}
                    onChange={(e) => setProfileForm((p) => ({ ...p, full_name: e.target.value }))}
                  />
                  <Input
                    label="الاسم بالعربية"
                    value={profileForm.full_name_ar}
                    onChange={(e) => setProfileForm((p) => ({ ...p, full_name_ar: e.target.value }))}
                    dir="rtl"
                  />
                  <Input
                    label="البريد الإلكتروني"
                    type="email"
                    value={profileForm.email}
                    disabled
                  />
                  <div className="flex items-center gap-3 text-xs text-neutral-500 dark:text-neutral-400">
                    <span>الدور: {ROLE_LABELS[profile?.role || ""] || profile?.role}</span>
                    <span>|</span>
                    <span>عضو منذ: {profile?.created_at ? new Date(profile.created_at).toLocaleDateString("ar-SA") : "—"}</span>
                  </div>
                  <Button
                    onClick={() => profileMutation.mutate(profileForm)}
                    disabled={profileMutation.isPending}
                  >
                    {profileMutation.isPending ? (
                      <Loader2 className="ml-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="ml-2 h-4 w-4" />
                    )}
                    حفظ التغييرات
                  </Button>
                </div>
              </Card>
            </TabsPanel>

            {/* ─── Security Tab ─────────────────────────── */}
            <TabsPanel value="security">
              <Card className="p-6">
                <h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">الأمان</h2>
                <div className="space-y-4">
                  <Input
                    label="كلمة المرور الحالية"
                    type="password"
                    value={passwordForm.current_password}
                    onChange={(e) => setPasswordForm((p) => ({ ...p, current_password: e.target.value }))}
                  />
                  <Input
                    label="كلمة المرور الجديدة"
                    type="password"
                    value={passwordForm.new_password}
                    onChange={(e) => setPasswordForm((p) => ({ ...p, new_password: e.target.value }))}
                    error={passwordForm.new_password && passwordForm.new_password.length < 12 ? "12 حرفًا كحد أدنى" : undefined}
                  />
                  <Input
                    label="تأكيد كلمة المرور"
                    type="password"
                    value={passwordForm.confirm_password}
                    onChange={(e) => setPasswordForm((p) => ({ ...p, confirm_password: e.target.value }))}
                    error={
                      passwordForm.confirm_password && passwordForm.new_password !== passwordForm.confirm_password
                        ? "كلمتا المرور غير متطابقتين"
                        : undefined
                    }
                  />
                  {passwordError && (
                    <p className="text-sm text-danger-600">{passwordError}</p>
                  )}
                  <Button
                    onClick={() => {
                      setPasswordError("");
                      if (passwordForm.new_password !== passwordForm.confirm_password) {
                        setPasswordError("كلمتا المرور غير متطابقتين");
                        return;
                      }
                      if (passwordForm.new_password.length < 12) {
                        setPasswordError("كلمة المرور يجب أن تكون 12 حرفًا على الأقل");
                        return;
                      }
                      passwordMutation.mutate({
                        current_password: passwordForm.current_password,
                        new_password: passwordForm.new_password,
                      });
                    }}
                    disabled={passwordMutation.isPending || !passwordForm.current_password || !passwordForm.new_password}
                  >
                    {passwordMutation.isPending ? (
                      <Loader2 className="ml-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Shield className="ml-2 h-4 w-4" />
                    )}
                    تحديث كلمة المرور
                  </Button>
                </div>
              </Card>
            </TabsPanel>

            {/* ─── Notifications Tab ────────────────────── */}
            <TabsPanel value="notifications">
              <Card className="p-6">
                <h2 className="mb-4 text-lg font-semibold text-neutral-900 dark:text-neutral-100">الإشعارات</h2>
                <div className="space-y-3">
                  {[
                    { key: "email_notifications", label: "إشعارات البريد الإلكتروني" },
                    { key: "app_notifications", label: "إشعارات التطبيق" },
                    { key: "opportunity_alerts", label: "تنبيهات الفرص" },
                    { key: "company_updates", label: "تحديثات الشركات" },
                    { key: "weekly_summary", label: "ملخص أسبوعي" },
                  ].map((item) => (
                    <label
                      key={item.key}
                      className="flex items-center justify-between rounded-lg border border-neutral-100 p-3 dark:border-neutral-700"
                    >
                      <span className="text-sm text-neutral-700 dark:text-neutral-300">{item.label}</span>
                      <button
                        type="button"
                        onClick={() => toggleNotif(item.key)}
                        className={cn(
                          "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors",
                          notifPrefs[item.key] ? "bg-[var(--muhide-orange)]" : "bg-neutral-200 dark:bg-neutral-600"
                        )}
                        role="switch"
                        aria-checked={notifPrefs[item.key] ?? true}
                      >
                        <span
                          className={cn(
                            "pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transition-transform",
                            (notifPrefs[item.key] ?? true) ? "translate-x-5" : "translate-x-0"
                          )}
                        />
                      </button>
                    </label>
                  ))}
                </div>
              </Card>
            </TabsPanel>

            {/* ─── API Keys Tab ─────────────────────────── */}
            <TabsPanel value="api">
              <Card className="p-6">
                <h2 className="mb-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">API Keys</h2>
                <p className="mb-4 text-sm text-neutral-500 dark:text-neutral-400">
                  مفاتيح API للتكامل مع الأنظمة الخارجية
                </p>

                {showNewKey && (
                  <div className="mb-4 rounded-lg border border-success-200 bg-success-50 p-4 dark:border-success-800 dark:bg-success-900/20">
                    <p className="mb-2 text-sm font-medium text-success-800 dark:text-success-300">
                      المفتاح الجديد (احفظه الآن — لن يظهر مرة أخرى):
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 rounded bg-white px-2 py-1 text-xs text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200">
                        {showNewKey}
                      </code>
                      <Button size="sm" variant="outline" onClick={() => copyKey(showNewKey)}>
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                    <button
                      onClick={() => setShowNewKey(null)}
                      className="mt-2 text-xs text-success-700 underline dark:text-success-400"
                    >
                      تم النسخ، أغلق
                    </button>
                  </div>
                )}

                <div className="space-y-3">
                  {apiKeys.map((k) => (
                    <div
                      key={k.id}
                      className="flex items-center justify-between rounded-lg border border-neutral-100 p-3 dark:border-neutral-700"
                    >
                      <div>
                        <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{k.name}</p>
                        <code className="text-xs text-neutral-500 dark:text-neutral-400">{k.key_preview}</code>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => copyKey(k.key_preview)}
                          className="text-xs text-[var(--muhide-orange)] hover:text-orange-700 dark:text-orange-400"
                        >
                          نسخ
                        </button>
                        <button
                          onClick={() => revokeApiKey(k.id)}
                          className="text-xs text-danger-500 hover:text-danger-700"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-4 flex gap-2">
                  <Input
                    placeholder="اسم المفتاح"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    className="flex-1"
                  />
                  <Button onClick={addApiKey} disabled={!newKeyName.trim()}>
                    <Key className="ml-2 h-4 w-4" />
                    إضافة مفتاح
                  </Button>
                </div>
              </Card>
            </TabsPanel>

            {/* ─── Data Tab ─────────────────────────────── */}
            {activeTab === "data" && (
              <Card className="p-6">
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
                        <div
                          key={src.name}
                          className="flex items-center justify-between rounded-lg border border-neutral-100 p-2 dark:border-neutral-700"
                        >
                          <span className="text-sm text-neutral-700 dark:text-neutral-300">{src.name}</span>
                          <Badge variant="success">مفعل</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="border-t border-neutral-100 pt-4 dark:border-neutral-700">
                    <Button variant="outline" onClick={() => window.print()}>
                      <Database className="ml-2 h-4 w-4" />
                      تصدير البيانات
                    </Button>
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>
      </Tabs>
    </div>
  );
}
