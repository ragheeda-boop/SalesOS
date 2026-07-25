"use client";

import { useState } from"react";
import { useRouter } from"next/navigation";
import Link from"next/link";
import { useLogin } from"@/lib/hooks/mutationHooks";
import { useTranslation } from"@/lib/i18n";
import { Card, CardContent, Input, Button, cn } from"@salesos/ui";

export default function LoginPage() {
 const router = useRouter();
 const { t } = useTranslation();
 const [email, setEmail] = useState("");
 const [password, setPassword] = useState("");
 const [error, setError] = useState("");
 const loginMutation = useLogin();

 const handleSubmit = async (e: React.FormEvent) => {
 e.preventDefault();
 setError("");

 if (!email || !password) {
 setError(t("auth.login_fill_all"));
 return;
 }

 loginMutation.mutate(
 { email, password },
 {
 onSuccess: () => router.push("/dashboard"),
 onError: (err: unknown) => {
 if (err && typeof err ==="object" &&"response" in err) {
 const axiosErr = err as {
 response?: { status?: number; data?: { detail?: string | { msg?: string }[] } };
 message?: string;
 };
 const detail = axiosErr.response?.data?.detail;
 if (typeof detail ==="string" && detail) {
 setError(detail);
 } else if (Array.isArray(detail) && detail[0]?.msg) {
 setError(detail.map((d) => d.msg).filter(Boolean).join(";") || t("auth.login_failed"));
 } else if (!axiosErr.response) {
 setError(
 `Cannot reach API (${axiosErr.message ||"network error"}). Check NEXT_PUBLIC_API_URL.`
 );
 } else {
 setError(t("auth.login_failed"));
 }
 } else {
 setError(t("error.unexpected"));
 }
 },
 }
 );
 };

 return (
 <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-secondary)' }}>
 <Card className="w-full max-w-md p-8">
 <CardContent>
 <h1 className="text-2xl font-bold mb-6 text-center" style={{ color: 'var(--text-primary)' }}>{t("auth.login_title")}</h1>
 <form onSubmit={handleSubmit} className="space-y-4">
 <Input
 label={t("labels.email")}
 type="email"
 value={email}
 onChange={(e) => setEmail(e.target.value)}
 error={error && !email ? error : undefined}
 required
 />
 <Input
 label={t("labels.password")}
 type="password"
 value={password}
 onChange={(e) => setPassword(e.target.value)}
 required
 />
 {error && <p className="text-sm" role="alert" style={{ color: 'var(--danger-600, #EF4444)' }}>{error}</p>}
 <Button
 type="submit"
 variant="primary"
 className="w-full"
 loading={loginMutation.isPending}
 disabled={loginMutation.isPending}
 >
 {loginMutation.isPending ? t("auth.logging_in") : t("auth.login")}
 </Button>
 </form>
 <p className="mt-4 text-sm text-center" style={{ color: 'var(--text-muted)' }}>
 {t("auth.no_account")}{""}
 <Link href="/register" style={{ color: 'var(--muhide-orange)' }} className="hover:underline">
 {t("auth.register")}
 </Link>
 </p>
 </CardContent>
 </Card>
 </div>
 );
}
