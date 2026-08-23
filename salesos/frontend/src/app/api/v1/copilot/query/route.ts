import { NextRequest, NextResponse } from "next/server";

/**
 * Long-request passthrough for POST /api/v1/copilot/query.
 *
 * The Next standalone rewrite proxy aborts upstream requests around the
 * 30s mark (returns 500 to the browser while the backend keeps processing).
 * Local AI providers can legitimately take 60-120s per query, so this route
 * handler shadows the rewrite for this path only and awaits the upstream
 * response without an artificial timeout.
 *
 * Headers are whitelisted (never forward hop-by-hop/host headers).
 */

function apiBase(): string {
  const raw =
    process.env.API_REWRITE_URL ||
    process.env.INTERNAL_API_URL ||
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";
  return raw.replace(/\/$/, "");
}

const FORWARDED_HEADERS = [
  "authorization",
  "x-tenant-id",
  "x-csrf-token",
  "x-request-id",
  "content-type",
  "accept",
  "cookie",
  "user-agent",
] as const;

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const base = apiBase();
  const headers: Record<string, string> = {};
  for (const name of FORWARDED_HEADERS) {
    const value = req.headers.get(name);
    if (value !== null) headers[name] = value;
  }

  const body = await req.text();

  let upstream: Response;
  try {
    upstream = await fetch(`${base}/api/v1/copilot/query`, {
      method: "POST",
      headers,
      body,
      cache: "no-store",
    });
  } catch (err) {
    console.error("[copilot-query-proxy] upstream fetch failed:", err);
    return NextResponse.json(
      { detail: "Copilot upstream unavailable" },
      { status: 502 }
    );
  }

  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") || "application/json",
      "cache-control": "no-store",
    },
  });
}
