"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { User, Shield, Bell, Database, Key, Save, Copy, Trash2 } from "lucide-react";
import {
  Tabs,
  TabsList,
  Tab,
  TabsPanel,
  Input,
  Button,
  Badge,
  Card,
  cn,
  useToast,
  Spinner,
} from "@salesos/ui";
import api, {
  getCurrentUser,
  changePassword,
  getNotificationPreferences,
  updateNotificationPreferences,
  getApiKeys,
  createApiKey,
  deleteApiKey,
  type NotificationPreferences,
} from "@/lib/api";
import { useTenant } from "@/lib/hooks/useTenant";
import { useTranslation } from "@/lib/i18n";
import { settingsKeys } from "@/lib/queryKeys";

const TAB_KEYS: Record<string, string> = {
  profile: "settings.profile",
  security: "settings.security",
  notifications: "settings.notifications",
  api: "settings.api_keys",
  data: "settings.data",
};

const TAB_ICONS: Record<string, typeof User> = {
  profile: User,
  security: Shield,
  notifications: Bell,
  api: Key,
  data: Database,
};

const ROLE_KEYS: Record<string, string> = {
  admin: "settings.role.admin",
  manager: "settings.role.manager",
  user: "settings.role.user",
};

export default function SettingsPage() {
  const { toast } = useToast();
  const { tenantId } = useTenant();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
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
      toast({ variant: "success", title: t("settings.saved") });
    },
    onError: () => {
      toast({
        variant: "error",
        title: t("settings.save_failed"),
        description: t("settings.save_error"),
      });
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
    mutationFn: ({
      current_password,
      new_password,
    }: {
      current_password: string;
      new_password: string;
    }) => changePassword(current_password, new_password),
    onSuccess: () => {
      toast({ variant: "success", title: t("settings.password_updated") });
      setPasswordForm({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
      setPasswordError("");
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      const msg = err.response?.data?.detail || t("settings.password_update_failed");
      setPasswordError(msg);
      toast({
        variant: "error",
        title: t("settings.password_update_failed"),
        description: msg,
      });
    },
  });

  // ─── Notifications ───────────────────────────────────────
  const { data: notifPrefsData, isLoading: notifLoading } = useQuery({
    queryKey: settingsKeys.notifications(),
    queryFn: () => getNotificationPreferences(tenantId),
    enabled: !!tenantId,
  });

  const [notifPrefs, setNotifPrefs] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (notifPrefsData) {
      setNotifPrefs(notifPrefsData as unknown as Record<string, boolean>);
    }
  }, [notifPrefsData]);

  const notifMutation = useMutation({
    mutationFn: (prefs: Record<string, boolean>) =>
      updateNotificationPreferences(prefs as unknown as NotificationPreferences, tenantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.notifications() });
      toast({ variant: "success", title: t("settings.settings_updated") });
    },
    onError: () => {
      toast({ variant: "error", title: t("settings.save_failed") });
    },
  });

  const toggleNotif = (key: string) => {
    const updated = { ...notifPrefs, [key]: !notifPrefs[key] };
    setNotifPrefs(updated);
    notifMutation.mutate(updated);
  };

  // ─── API Keys ────────────────────────────────────────────
  const { data: apiKeysData, isLoading: apiKeysLoading } = useQuery({
    queryKey: settingsKeys.apiKeys(),
    queryFn: () => getApiKeys(tenantId),
    enabled: !!tenantId,
  });

  const [newKeyName, setNewKeyName] = useState("");
  const [showNewKey, setShowNewKey] = useState<string | null>(null);

  const createKeyMutation = useMutation({
    mutationFn: (name: string) => createApiKey(name, tenantId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.apiKeys() });
      setShowNewKey(data.key);
      setNewKeyName("");
      toast({ variant: "success", title: t("settings.api_key_created") });
    },
    onError: () => {
      toast({ variant: "error", title: t("settings.save_failed") });
    },
  });

  const revokeKeyMutation = useMutation({
    mutationFn: (id: string) => deleteApiKey(id, tenantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.apiKeys() });
      toast({ variant: "success", title: t("settings.api_key_deleted") });
    },
    onError: () => {
      toast({ variant: "error", title: t("settings.save_failed") });
    },
  });

  const copyKey = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ variant: "default", title: t("settings.api_copied") });
  };

  if (profileLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Spinner className="h-8 w-8 text-[var(--muhide-orange)]" />
      </div>
    );
  }

  const TABS = Object.keys(TAB_KEYS);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t("settings.title")}</h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">{t("settings.subtitle")}</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex gap-6">
          {/* Sidebar */}
          <TabsList className="hidden w-56 shrink-0 sm:flex sm:flex-col items-stretch !border-0 !border-b-0 !gap-0">
            {TABS.map((tabId) => {
              const Icon = TAB_ICONS[tabId];
              return (
                <Tab
                  key={tabId}
                  value={tabId}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors !border-b-0 !border-transparent data-[state=active]:!border-b-0 data-[state=active]:!border-transparent data-[state=active]:bg-[var(--muhide-orange)]/10 data-[state=active]:text-[var(--muhide-orange)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] dark:hover:bg-[var(--bg-secondary)] dark:hover:text-[var(--text-disabled)]"
                >
                  {Icon && <Icon className="h-4 w-4" />}
                  <span>{t(TAB_KEYS[tabId])}</span>
                </Tab>
              );
            })}
          </TabsList>

          {/* Content */}
          <div className="min-w-0 flex-1 space-y-6">
            {/* ─── Profile Tab ──────────────────────────── */}
            <TabsPanel value="profile">
              <Card className="p-6">
                <h2 className="mb-4 text-lg font-semibold text-[var(--text-primary)]">
                  {t("settings.profile_title")}
                </h2>
                {profile && (
                  <div className="mb-4 flex items-center gap-3 rounded-lg bg-[var(--bg-secondary)] p-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]">
                      <User className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">
                        {profile.full_name}
                      </p>
                      <p className="text-xs text-[var(--text-muted)]">
                        {t(ROLE_KEYS[profile.role] || "") || profile.role}
                      </p>
                    </div>
                    <Badge className="mr-auto">
                      {profile.is_active ? t("settings.active") : t("settings.inactive")}
                    </Badge>
                  </div>
                )}
                <div className="space-y-4">
                  <Input
                    label={t("settings.name_en")}
                    value={profileForm.full_name}
                    onChange={(e) =>
                      setProfileForm((p) => ({
                        ...p,
                        full_name: e.target.value,
                      }))
                    }
                  />
                  <Input
                    label={t("settings.name_ar")}
                    value={profileForm.full_name_ar}
                    onChange={(e) =>
                      setProfileForm((p) => ({
                        ...p,
                        full_name_ar: e.target.value,
                      }))
                    }
                    dir="rtl"
                  />
                  <Input
                    label={t("settings.email")}
                    type="email"
                    value={profileForm.email}
                    disabled
                  />
                  <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
                    <span>
                      {t("settings.role")}:{" "}
                      {t(ROLE_KEYS[profile?.role || ""] || "") || profile?.role}
                    </span>
                    <span>|</span>
                    <span>
                      {t("settings.member_since")}:{" "}
                      {profile?.created_at
                        ? new Date(profile.created_at).toLocaleDateString("ar-SA")
                        : "\u2014"}
                    </span>
                  </div>
                  <Button
                    onClick={() => profileMutation.mutate(profileForm)}
                    disabled={profileMutation.isPending}
                  >
                    {profileMutation.isPending ? (
                      <Spinner className="ml-2 h-4 w-4" />
                    ) : (
                      <Save className="ml-2 h-4 w-4" />
                    )}
                    {t("settings.save_changes")}
                  </Button>
                </div>
              </Card>
            </TabsPanel>

            {/* ─── Security Tab ─────────────────────────── */}
            <TabsPanel value="security">
              <Card className="p-6">
                <h2 className="mb-4 text-lg font-semibold text-[var(--text-primary)]">
                  {t("settings.security_title")}
                </h2>
                <div className="space-y-4">
                  <Input
                    label={t("settings.current_password")}
                    type="password"
                    value={passwordForm.current_password}
                    onChange={(e) =>
                      setPasswordForm((p) => ({
                        ...p,
                        current_password: e.target.value,
                      }))
                    }
                  />
                  <Input
                    label={t("settings.new_password")}
                    type="password"
                    value={passwordForm.new_password}
                    onChange={(e) =>
                      setPasswordForm((p) => ({
                        ...p,
                        new_password: e.target.value,
                      }))
                    }
                    error={
                      passwordForm.new_password && passwordForm.new_password.length < 12
                        ? t("settings.password_min_length")
                        : undefined
                    }
                  />
                  <Input
                    label={t("settings.confirm_password")}
                    type="password"
                    value={passwordForm.confirm_password}
                    onChange={(e) =>
                      setPasswordForm((p) => ({
                        ...p,
                        confirm_password: e.target.value,
                      }))
                    }
                    error={
                      passwordForm.confirm_password &&
                      passwordForm.new_password !== passwordForm.confirm_password
                        ? t("settings.password_mismatch")
                        : undefined
                    }
                  />
                  {passwordError && <p className="text-sm text-danger-600">{passwordError}</p>}
                  <Button
                    onClick={() => {
                      setPasswordError("");
                      if (passwordForm.new_password !== passwordForm.confirm_password) {
                        setPasswordError(t("settings.password_mismatch"));
                        return;
                      }
                      if (passwordForm.new_password.length < 12) {
                        setPasswordError(t("settings.password_min_length"));
                        return;
                      }
                      passwordMutation.mutate({
                        current_password: passwordForm.current_password,
                        new_password: passwordForm.new_password,
                      });
                    }}
                    disabled={
                      passwordMutation.isPending ||
                      !passwordForm.current_password ||
                      !passwordForm.new_password
                    }
                  >
                    {passwordMutation.isPending ? (
                      <Spinner className="ml-2 h-4 w-4" />
                    ) : (
                      <Shield className="ml-2 h-4 w-4" />
                    )}
                    {t("settings.update_password")}
                  </Button>
                </div>
              </Card>
            </TabsPanel>

            {/* ─── Notifications Tab ────────────────────── */}
            <TabsPanel value="notifications">
              <Card className="p-6">
                <h2 className="mb-4 text-lg font-semibold text-[var(--text-primary)]">
                  {t("settings.notifications_title")}
                </h2>
                {notifLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Spinner className="h-6 w-6 text-[var(--muhide-orange)]" />
                  </div>
                ) : (
                  <div className="space-y-3">
                    {[
                      {
                        key: "email_notifications",
                        labelKey: "settings.notif.email_notifications",
                      },
                      {
                        key: "app_notifications",
                        labelKey: "settings.notif.app_notifications",
                      },
                      {
                        key: "opportunity_alerts",
                        labelKey: "settings.notif.opportunity_alerts",
                      },
                      {
                        key: "company_updates",
                        labelKey: "settings.notif.company_updates",
                      },
                      {
                        key: "weekly_summary",
                        labelKey: "settings.notif.weekly_summary",
                      },
                    ].map((item) => (
                      <label
                        key={item.key}
                        className="flex items-center justify-between rounded-lg border border-[var(--border-subtle)] p-3"
                      >
                        <span className="text-sm text-[var(--text-secondary)]">
                          {t(item.labelKey)}
                        </span>
                        <button
                          type="button"
                          onClick={() => toggleNotif(item.key)}
                          className={cn(
                            "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors",
                            notifPrefs[item.key]
                              ? "bg-[var(--muhide-orange)]"
                              : "bg-[var(--bg-tertiary)]"
                          )}
                          role="switch"
                          aria-checked={notifPrefs[item.key] ?? true}
                        >
                          <span
                            className={cn(
                              "pointer-events-none inline-block h-5 w-5 rounded-full bg-[var(--bg-primary)] shadow transition-transform",
                              (notifPrefs[item.key] ?? true) ? "translate-x-5" : "translate-x-0"
                            )}
                          />
                        </button>
                      </label>
                    ))}
                  </div>
                )}
              </Card>
            </TabsPanel>

            {/* ─── API Keys Tab ─────────────────────────── */}
            <TabsPanel value="api">
              <Card className="p-6">
                <h2 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">
                  {t("settings.api_title")}
                </h2>
                <p className="mb-4 text-sm text-[var(--text-muted)]">
                  {t("settings.api_subtitle")}
                </p>

                {showNewKey && (
                  <div className="mb-4 rounded-lg border border-success-200 bg-success-50 p-4 dark:border-success-800 dark:bg-success-900/20">
                    <p className="mb-2 text-sm font-medium text-success-800 dark:text-success-300">
                      {t("settings.api_new_key")}
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 rounded bg-[var(--bg-primary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
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
                      {t("settings.api_copied_close")}
                    </button>
                  </div>
                )}

                <div className="space-y-3">
                  {apiKeysLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Spinner className="h-6 w-6 text-[var(--muhide-orange)]" />
                    </div>
                  ) : (
                    (apiKeysData || []).map((k) => (
                      <div
                        key={k.id}
                        className="flex items-center justify-between rounded-lg border border-[var(--border-subtle)] p-3"
                      >
                        <div>
                          <p className="text-sm font-medium text-[var(--text-primary)]">{k.name}</p>
                          <code className="text-xs text-[var(--text-muted)]">{k.key_preview}</code>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => copyKey(k.key_preview)}
                            className="text-xs text-[var(--muhide-orange)]"
                          >
                            {t("common.copy")}
                          </button>
                          <button
                            onClick={() => revokeKeyMutation.mutate(k.id)}
                            className="text-xs text-danger-500 hover:text-danger-700"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                  {(!apiKeysData || apiKeysData.length === 0) && !apiKeysLoading && (
                    <p className="py-4 text-center text-sm text-[var(--text-muted)]">
                      {t("settings.no_api_keys")}
                    </p>
                  )}
                </div>

                <div className="mt-4 flex gap-2">
                  <Input
                    placeholder={t("settings.api_key_name")}
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    className="flex-1"
                  />
                  <Button
                    onClick={() => createKeyMutation.mutate(newKeyName.trim())}
                    disabled={!newKeyName.trim() || createKeyMutation.isPending}
                  >
                    {createKeyMutation.isPending ? (
                      <Spinner className="ml-2 h-4 w-4" />
                    ) : (
                      <Key className="ml-2 h-4 w-4" />
                    )}
                    {t("settings.api_add_key")}
                  </Button>
                </div>
              </Card>
            </TabsPanel>

            {/* ─── Data Tab ─────────────────────────────── */}
            {activeTab === "data" && (
              <Card className="p-6">
                <h2 className="mb-4 text-lg font-semibold text-[var(--text-primary)]">
                  {t("settings.data_title")}
                </h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)]">
                      {t("settings.data_sources")}
                    </label>
                    <div className="mt-2 space-y-2">
                      {[
                        { name: "\u0628\u0644\u062F\u064A", status: "active" },
                        {
                          name: "\u062A\u0642\u064A\u064A\u0645",
                          status: "active",
                        },
                        {
                          name: "\u0625\u0639\u0644\u0627\u0646\u0627\u062A",
                          status: "active",
                        },
                        { name: "\u0646\u0627\u062C\u0632", status: "active" },
                        {
                          name: "\u0627\u0644\u0647\u064A\u0626\u0629 \u0627\u0644\u0639\u0627\u0645\u0629 \u0644\u0644\u0639\u0642\u0627\u0631",
                          status: "active",
                        },
                      ].map((src) => (
                        <div
                          key={src.name}
                          className="flex items-center justify-between rounded-lg border border-[var(--border-subtle)] p-2"
                        >
                          <span className="text-sm text-[var(--text-secondary)]">{src.name}</span>
                          <Badge variant="success">{t("settings.enabled")}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="border-t border-[var(--border-subtle)] pt-4">
                    <Button variant="outline" onClick={() => window.print()}>
                      <Database className="ml-2 h-4 w-4" />
                      {t("settings.export_data")}
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
