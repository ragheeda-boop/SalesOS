/**
 * FE-SEC-02 — tip-live bake probe for NEXT_PUBLIC httpOnly access flag.
 * Public (no auth). Default false. Not a session oracle. No Production GO.
 */
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const nextPublicRaw =
    process.env.NEXT_PUBLIC_FEATURE_HTTPONLY_ACCESS_COOKIE ?? null;
  const nextPublicBaked = nextPublicRaw === "true";
  const serverFeature =
    process.env.FEATURE_HTTPONLY_ACCESS_COOKIE === "true";

  return NextResponse.json({
    feature: "FE-SEC-02",
    /** Client bundle bake — required for #5 (skip document.cookie mirror). */
    next_public_httponly_access_cookie_baked: nextPublicBaked,
    next_public_raw: nextPublicRaw,
    /** Runtime server-only env — insufficient alone for browser persist path. */
    server_feature_httponly_access_cookie: serverFeature,
    honesty:
      "#5 PASS needs next_public_httponly_access_cookie_baked=true after FE rebuild " +
      "plus browser proof that document.cookie has no access_token= after login. " +
      "Finding stays Open until field evidence. Flags default OFF. No Production GO.",
  });
}
