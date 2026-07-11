"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useLogin } from "@/lib/hooks/mutationHooks";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const loginMutation = useLogin();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("يرجى إدخال البريد الإلكتروني وكلمة المرور");
      return;
    }

    loginMutation.mutate(
      { email, password },
      {
        onSuccess: () => router.push("/dashboard"),
        onError: (err: unknown) => {
          if (err && typeof err === "object" && "response" in err) {
            const axiosErr = err as { response?: { data?: { detail?: string } } };
            setError(axiosErr.response?.data?.detail || "فشل تسجيل الدخول");
          } else {
            setError("حدث خطأ غير متوقع");
          }
        },
      }
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
      <div className="w-full max-w-md p-8 bg-[var(--card)] rounded-xl shadow-muhide-1 border border-[var(--border)]">
        <h1 className="text-2xl font-bold mb-6 text-center">تسجيل الدخول إلى سيلز أو إس</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">البريد الإلكتروني</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">كلمة المرور</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-[var(--border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
              required
            />
          </div>
          {error && <p className="text-danger-500 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loginMutation.isPending}
            className="w-full py-3 bg-[var(--muhide-orange)] text-white rounded-lg hover:bg-orange-700 transition disabled:opacity-50 font-medium"
          >
            {loginMutation.isPending ? "جاري تسجيل الدخول..." : "تسجيل الدخول"}
          </button>
        </form>
        <p className="mt-4 text-sm text-center text-[var(--muted-foreground)]">
          ليس لديك حساب؟{" "}
          <Link href="/register" className="text-[var(--muhide-orange)] hover:underline">
            إنشاء حساب
          </Link>
        </p>
      </div>
    </div>
  );
}
