import axios from "axios";
import { clearAuthTokens, ACCESS_TOKEN_KEY } from "@/lib/auth/session";
import {
  ENTITLEMENT_DENIED_EVENT,
  formatEntitlementDeniedMessage,
  isEntitlementDeniedPayload,
} from "@/lib/api/entitlementErrors";
import {
  QUOTA_EXCEEDED_EVENT,
  formatQuotaExceededMessage,
  isQuotaExceededPayload,
} from "@/lib/api/quotaErrors";
import {
  OWNER_AUTH_DENIED_EVENT,
  formatOwnerAuthDeniedMessage,
  shouldSurfaceOwnerAudienceDenial,
} from "@/lib/auth/ownerAudience";

// Browser: same-origin so Next.js rewrites proxy to Railway (avoids CORS Network Error).
// Server: absolute backend URL for SSR / Route Handlers.
const api = axios.create({
  baseURL:
    typeof window !== "undefined"
      ? ""
      : process.env.NEXT_PUBLIC_API_URL ||
        process.env.API_URL ||
        "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Always attach tenant when available so endpoints requiring X-Tenant-Id
    // do not 422 when callers omit the header.
    if (!config.headers["X-Tenant-Id"] && !config.headers["x-tenant-id"]) {
      const stored = localStorage.getItem("tenant_id");
      if (stored) {
        config.headers["X-Tenant-Id"] = stored;
      } else if (token) {
        try {
          const payload = JSON.parse(
            atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")),
          );
          if (payload?.tenant_id) {
            config.headers["X-Tenant-Id"] = String(payload.tenant_id);
          }
        } catch {
          /* ignore malformed token; auth interceptor handles 401/422 */
        }
      }
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (typeof window === "undefined") return Promise.reject(error);

    const status = error.response?.status;

    if (status === 401) {
      const requestUrl =
        typeof error.config?.url === "string" ? error.config.url : "";
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem(ACCESS_TOKEN_KEY)
          : null;
      if (
        shouldSurfaceOwnerAudienceDenial({
          status,
          url: requestUrl,
          token,
        })
      ) {
        const message = formatOwnerAuthDeniedMessage("tenant");
        console.warn("[API] 401 owner audience required:", message);
        window.dispatchEvent(
          new CustomEvent(OWNER_AUTH_DENIED_EVENT, {
            detail: { message, status, url: requestUrl },
          }),
        );
        return Promise.reject(error);
      }
      clearAuthTokens();
      window.location.href = "/login";
      return Promise.reject(error);
    }

    if (status === 422) {
      const detail = error.response?.data?.detail;
      if (Array.isArray(detail)) {
        const hasAuthError = detail.some(
          (d: { loc?: string[] }) =>
            d.loc?.includes("header") && d.loc?.includes("authorization"),
        );
        if (hasAuthError) {
          clearAuthTokens();
          window.location.href = "/login";
          return Promise.reject(error);
        }
      }
    }

    if (status === 403 || status === 429) {
      const data = error.response?.data;
      if (isQuotaExceededPayload(data)) {
        const message = formatQuotaExceededMessage(data);
        console.warn(`[API] ${status} quota exceeded:`, message, data);
        window.dispatchEvent(
          new CustomEvent(QUOTA_EXCEEDED_EVENT, {
            detail: { ...data, message, status },
          }),
        );
      } else if (status === 403 && isEntitlementDeniedPayload(data)) {
        const message = formatEntitlementDeniedMessage(data);
        console.warn("[API] 403 entitlement denied:", message, data);
        window.dispatchEvent(
          new CustomEvent(ENTITLEMENT_DENIED_EVENT, {
            detail: { ...data, message },
          }),
        );
      } else if (status === 403) {
        console.warn("[API] 403 Forbidden:", data);
      } else {
        console.warn("[API] 429 Too Many Requests:", data);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
