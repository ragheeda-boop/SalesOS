/** SalesOS frontend configuration — centralized constants. */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
export const DEFAULT_PAGE_SIZE = 20
export const SEARCH_DEBOUNCE_MS = 400
export const STALE_TIME_MS = 10_000
export const RETRY_COUNT = 1

export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  DASHBOARD: "/dashboard",
  COMPANIES: "/companies",
  CONTACTS: "/contacts",
  OPPORTUNITIES: "/opportunities",
  SETTINGS: "/settings",
} as const
