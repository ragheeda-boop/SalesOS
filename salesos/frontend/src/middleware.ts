import { NextResponse, type NextRequest } from "next/server";
import {
  buildLoginRedirectUrl,
  readAccessTokenFromRequest,
  shouldRedirectOwnerConsoleToOwnerLogin,
  shouldRedirectToLogin,
} from "@/lib/auth/middleware-auth";

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const token = readAccessTokenFromRequest(request);

  if (shouldRedirectToLogin(pathname, token)) {
    const loginUrl = buildLoginRedirectUrl(request.nextUrl.origin, pathname, search);
    return NextResponse.redirect(loginUrl);
  }

  if (shouldRedirectOwnerConsoleToOwnerLogin(pathname, token)) {
    const loginUrl = buildLoginRedirectUrl(request.nextUrl.origin, pathname, search);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Run on app routes only — skip static assets and image optimizer output.
     */
    "/((?!_next/static|_next/image|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
