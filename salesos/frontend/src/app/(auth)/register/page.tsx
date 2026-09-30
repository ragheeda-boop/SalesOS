"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useRegister, useRequestOrgRegistration } from "@/lib/hooks/mutationHooks";
import { useTranslation } from "@/lib/i18n";

function errorText(err: unknown, fallback: string): string {
  if (err && typeof err === "object" && "response" in err) {
    const axiosErr = err as {
      response?: { data?: { detail?: string | { msg?: string }[] } };
      message?: string;
    };
    const detail = axiosErr.response?.data?.detail;
    if (typeof detail === "string" && detail) return detail;
    if (Array.isArray(detail) && detail[0]?.msg) {
      return detail.map((d) => d.msg).filter(Boolean).join("; ") || fallback;
    }
    if (!axiosErr.response) {
      return `Cannot reach API (${axiosErr.message || "network error"}). Check NEXT_PUBLIC_API_URL.`;
    }
  }
  return fallback;
}

export default function RegisterPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [organizationName, setOrganizationName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [requestNote, setRequestNote] = useState("");
  const [error, setError] = useState("");
  const requestMutation = useRequestOrgRegistration();
  const registerMutation = useRegister();

  const handleRequest = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setRequestNote("");
    if (!organizationName || !name || !email) {
      setError(t("register.fill_all_fields"));
      return;
    }
    requestMutation.mutate(
      { organizationName, email, fullName: name },
      {
        onSuccess: () => setRequestNote(t("register.request_sent")),
        onError: (err: unknown) => setError(errorText(err, t("register.failed"))),
      }
    );
  };

  const handleComplete = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email || !password || !name) {
      setError(t("register.fill_all_fields"));
      return;
    }
    if (password !== confirmPassword) {
      setError(t("register.passwords_dont_match"));
      return;
    }
    if (password.length < 12) {
      setError(t("register.password_min_length"));
      return;
    }
    registerMutation.mutate(
      { email, password, fullName: name, organizationName },
      {
        onSuccess: () => router.push("/v3"),
        onError: (err: unknown) => setError(errorText(err, t("register.failed"))),
      }
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
      <div className="w-full max-w-md p-8 bg-[var(--card)] rounded-xl shadow-muhide-1 border border-[var(--border)]">
        <h1 className="text-2xl font-bold mb-6 text-center">{t("register.title")}</h1>
        <form onSubmit={handleRequest} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">{t("register.org_name")}</label>
            <input
              type="text"
              value={organizationName}
              onChange={(e) => setOrganizationName(e.target.value)}
              className="w-full px-4 py-2 border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t("labels.full_name")}</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t("labels.email")}</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
              required
            />
          </div>
          <button
            type="submit"
            disabled={requestMutation.isPending}
            className="w-full py-3 bg-[var(--muhide-orange)] text-white rounded-lg hover:brightness-90 transition disabled:opacity-50 font-medium"
          >
            {requestMutation.isPending ? t("register.request_sending") : t("register.request_submit")}
          </button>
        </form>
        {requestNote && <p className="mt-4 text-sm text-[var(--foreground)]">{requestNote}</p>}

        <h2 className="text-lg font-semibold mt-8 mb-2">{t("register.complete_title")}</h2>
        <p className="text-sm text-[var(--muted-foreground)] mb-4">{t("register.complete_hint")}</p>
        <form onSubmit={handleComplete} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">{t("labels.password")}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t("labels.confirm_password")}</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-2 border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
              required
            />
          </div>
          {error && <p className="text-danger-500 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={registerMutation.isPending}
            className="w-full py-3 border border-[var(--muhide-orange)] text-[var(--muhide-orange)] rounded-lg hover:brightness-90 transition disabled:opacity-50 font-medium"
          >
            {registerMutation.isPending ? t("register.creating") : t("auth.register")}
          </button>
        </form>
        <p className="mt-4 text-sm text-center text-[var(--muted-foreground)]">
          {t("register.has_account")}
          {""}
          <Link href="/login" className="text-[var(--muhide-orange)] hover:underline">
            {t("auth.login")}
          </Link>
        </p>
      </div>
    </div>
  );
}
