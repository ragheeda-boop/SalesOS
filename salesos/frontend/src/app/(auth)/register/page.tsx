"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useRegister } from "@/lib/hooks/mutationHooks";
import { useTranslation } from "@/lib/i18n";

export default function RegisterPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const registerMutation = useRegister();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!name || !email || !password) {
      setError(t("register.fill_all_fields"));
      return;
    }

    if (password !== confirmPassword) {
      setError(t("register.passwords_dont_match"));
      return;
    }

    if (password.length < 8) {
      setError(t("register.password_min_length"));
      return;
    }

    registerMutation.mutate(
      { email, password, fullName: name },
      {
        onSuccess: () => router.push("/dashboard"),
        onError: (err: unknown) => {
          if (err && typeof err === "object" && "response" in err) {
            const axiosErr = err as {
              response?: {
                status?: number;
                data?: { detail?: string | { msg?: string }[] };
              };
              message?: string;
            };
            const detail = axiosErr.response?.data?.detail;
            if (typeof detail === "string" && detail) {
              setError(detail);
            } else if (Array.isArray(detail) && detail[0]?.msg) {
              setError(
                detail
                  .map((d) => d.msg)
                  .filter(Boolean)
                  .join(";") || t("register.failed")
              );
            } else if (!axiosErr.response) {
              setError(
                `Cannot reach API (${axiosErr.message || "network error"}). Check NEXT_PUBLIC_API_URL.`
              );
            } else {
              setError(t("register.failed"));
            }
          } else {
            setError(t("error.unexpected"));
          }
        },
      }
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
      <div className="w-full max-w-md p-8 bg-[var(--card)] rounded-xl shadow-muhide-1 border border-[var(--border)]">
        <h1 className="text-2xl font-bold mb-6 text-center">{t("register.title")}</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
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
            className="w-full py-3 bg-[var(--muhide-orange)] text-white rounded-lg hover:brightness-90 transition disabled:opacity-50 font-medium"
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
