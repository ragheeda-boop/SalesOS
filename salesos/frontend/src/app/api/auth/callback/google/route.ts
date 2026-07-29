import { NextRequest, NextResponse } from "next/server";

/**
 * Google OAuth redirect bridge.
 *
 * Google Cloud OAuth client is registered with this Vercel URI.
 * We forward code+state to the Railway Communication Hub callback,
 * which exchanges the token (using the same redirect_uri) and then
 * redirects back into /v3/settings.
 */
function apiBase(): string {
  const raw =
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.API_URL ||
    "https://salesos-production-96c0.up.railway.app";
  return raw.replace(/\/$/, "");
}

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const error = searchParams.get("error");
  const code = searchParams.get("code");
  const state = searchParams.get("state");

  const settings = new URL("/v3/settings", req.nextUrl.origin);
  settings.searchParams.set("tab", "integrations");

  if (error) {
    settings.searchParams.set("google", "error");
    settings.searchParams.set("reason", error);
    return NextResponse.redirect(settings);
  }

  if (!code || !state) {
    settings.searchParams.set("google", "error");
    settings.searchParams.set("reason", "missing_params");
    return NextResponse.redirect(settings);
  }

  const backend = new URL(`${apiBase()}/api/v1/integrations/google/callback`);
  backend.searchParams.set("code", code);
  backend.searchParams.set("state", state);
  return NextResponse.redirect(backend.toString());
}
