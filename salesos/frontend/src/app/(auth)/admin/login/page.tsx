"use client";
/* eslint-disable custom-rules/no-hardcoded-colors */

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useOwnerLogin } from "@/lib/hooks/mutationHooks";
import { OWNER_JWT_AUDIENCE } from "@/lib/auth/ownerAudience";
import { Card, CardContent, Input, Button } from "@salesos/ui";

/**
 * DEC-093 follow-up — Owner Platform login mint UX.
 * Posts to POST /api/v1/identity/owner/login (admin role → salesos-owner-platform).
 * Not Production GO. Separate from tenant /login.
 */
function OwnerLoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const ownerLoginMutation = useOwnerLogin();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Email and password are required.");
      return;
    }

    ownerLoginMutation.mutate(
      { email, password },
      {
        onSuccess: () => {
          const callback = searchParams.get("callbackUrl");
          const safe =
            callback &&
            callback.startsWith("/admin") &&
            !callback.startsWith("//") &&
            callback !== "/admin/login"
              ? callback
              : "/admin";
          router.push(safe);
        },
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
                  .join(";") || "Owner login failed."
              );
            } else if (!axiosErr.response) {
              setError(
                `Cannot reach API (${axiosErr.message || "network error"}). Check NEXT_PUBLIC_API_URL.`
              );
            } else {
              setError("Owner login failed.");
            }

          } else {
            setError("Unexpected error.");
          }
        },
      }
    );
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: "var(--bg-secondary)" }}
      data-testid="owner-login-page"
    >
      <Card className="w-full max-w-md p-8">
        <CardContent>
          <p className="text-xs uppercase tracking-wide text-center mb-2" style={{ color: "var(--text-muted)" }}>
            Owner Platform
          </p>
          <h1
            className="text-2xl font-bold mb-2 text-center"
            style={{ color: "var(--text-primary)" }}
          >
            Owner login
          </h1>
          <p className="text-xs text-center mb-6" style={{ color: "var(--text-muted)" }}>
            Mints audience <code>{OWNER_JWT_AUDIENCE}</code> for{" "}
            <code>/api/v1/admin/*</code>. Admin role required. Not Production GO.
          </p>
          <form onSubmit={handleSubmit} className="space-y-4" data-testid="owner-login-form">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              data-testid="owner-login-email"
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              data-testid="owner-login-password"
            />
            {error && (
              <p
                className="text-sm"
                role="alert"
                data-testid="owner-login-error"
                style={{ color: "var(--danger-600, #EF4444)" }}
              >
                {error}
              </p>
            )}
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              loading={ownerLoginMutation.isPending}
              disabled={ownerLoginMutation.isPending}
              data-testid="owner-login-submit"
            >
              {ownerLoginMutation.isPending ? "Signing in…" : "Sign in to Owner Console"}
            </Button>
          </form>
          <p className="mt-4 text-sm text-center" style={{ color: "var(--text-muted)" }}>
            Tenant app login?{" "}
            <Link href="/login" style={{ color: "var(--muhide-orange)" }} className="hover:underline">
              /login
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export default function OwnerLoginPage() {
  return (
    <Suspense>
      <OwnerLoginPageContent />
    </Suspense>
  );
}
