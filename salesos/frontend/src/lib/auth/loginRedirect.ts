const DEFAULT_POST_LOGIN_PATH = "/v3";

/** Resolve the local destination requested before login without allowing open redirects. */
export function resolvePostLoginPath(
  searchParams: Pick<URLSearchParams, "get">,
  origin: string
): string {
  const candidate = searchParams.get("callbackUrl") ?? searchParams.get("next");
  if (!candidate || !candidate.startsWith("/")) return DEFAULT_POST_LOGIN_PATH;

  try {
    const destination = new URL(candidate, origin);
    if (destination.origin !== origin) return DEFAULT_POST_LOGIN_PATH;
    return `${destination.pathname}${destination.search}${destination.hash}`;
  } catch {
    return DEFAULT_POST_LOGIN_PATH;
  }
}
