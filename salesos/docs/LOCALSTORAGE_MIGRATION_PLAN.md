# localStorage Migration Plan

> **Purpose**: Migrate all client-side localStorage data to server-backed storage.
> **Status**: PLANNED — requires feature flag rollout per key
> **Last updated**: 2026-07-13

---

## Table of Contents

1. [Current localStorage Keys](#1-current-localstorage-keys)
2. [Migration Strategy](#2-migration-strategy)
3. [Feature Flag Configuration](#3-feature-flag-configuration)
4. [Rollback Plan](#4-rollback-plan)

---

## 1. Current localStorage Keys

| # | Key | Type | Source File | Data Stored | Sensitivity |
|---|-----|------|-------------|-------------|-------------|
| 1 | `access_token` | Auth | `src/lib/api.ts`, `src/lib/api/client.ts`, `src/lib/hooks/mutationHooks.ts` | JWT access token (Bearer auth) | **HIGH** — JWT token |
| 2 | `refresh_token` | Auth | `src/lib/api.ts`, `src/lib/hooks/mutationHooks.ts` | JWT refresh token | **HIGH** — refresh token |
| 3 | `tenant_id` | Auth | `src/lib/hooks/useTenant.ts`, `src/lib/hooks/mutationHooks.ts` | Current tenant UUID | **MEDIUM** — tenant context |
| 4 | `salesos_theme` | UI | `packages/hooks/src/use-theme.ts` | Theme preference (`light` / `dark`) | LOW |
| 5 | `salesos-locale` | UI | `src/lib/i18n/index.tsx`, `src/app/layout.tsx` | Locale/language (`en` / `ar`) | LOW |
| 6 | `salesos-copilot-messages` | State | `src/components/copilot-panel.tsx` | Copilot chat history (JSON array of messages) | LOW |
| 7 | `salesos_session` | Auth | `packages/runtime/src/session-runtime.ts` | Full session object: `{user, token, expiresAt, authenticated}` | **HIGH** — contains token + user PII |
| 8 | `salesos_offline_queue` | State | `packages/runtime/src/offline-runtime.ts` | Offline action queue (CRUD operations pending sync) | **MEDIUM** — pending mutations |
| 9 | `salesos_saved_searches` | State | `packages/search/src/saved-searches.ts` | Saved search queries (JSON array of `{name, query, timestamps}`) | LOW |
| 10 | `salesos_search_history` | State | `packages/search/src/search-history.ts` | Recent search queries (max 50 entries, `{text, timestamp}`) | LOW |
| 11 | `salesos:onboarding-progress` | State | `src/components/guidance/onboarding/OnboardingProvider.tsx` | Completed onboarding steps (JSON array of step keys) | LOW |
| 12 | `salesos:completed-tours` | State | `src/components/guidance/tour/TourProvider.tsx` | Completed guided tour IDs (JSON array of tour keys) | LOW |

---

## 2. Migration Strategy

### Phase 1: Auth Tokens → HttpOnly Cookies (P0 — Security)

**Current state**: `access_token`, `refresh_token`, and `salesos_session` are stored in localStorage, accessible to any JS on the page (XSS vector).

**Target state**: Tokens moved to HttpOnly + Secure + SameSite cookies, managed server-side.

| Key | API Endpoint | Migration Notes |
|-----|-------------|-----------------|
| `access_token` | `POST /api/v1/identity/login` | Backend sets `Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Lax; Path=/` |
| `refresh_token` | `POST /api/v1/identity/login` | Backend sets `Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/identity/refresh` |
| `salesos_session` | `GET /api/v1/identity/session` | New endpoint returns session from cookie; frontend SessionRuntime reads from API, not localStorage |

**Implementation:**

```typescript
// src/lib/api.ts — remove localStorage.getItem("access_token")
// Cookies are sent automatically by browser with every request.
// Remove the Authorization header interceptor entirely.
api.interceptors.request.use((config) => {
  // Cookies are sent automatically — no manual header needed
  return config;
});
```

**Backend changes:**

```python
# identity/router.py — login response sets cookies
@router.post("/login")
async def login(...):
    ...
    response.set_cookie("access_token", token, httponly=True, secure=True, samesite="lax", max_age=3600)
    response.set_cookie("refresh_token", refresh, httponly=True, secure=True, samesite="strict", max_age=604800, path="/api/v1/identity/refresh")
    return response
```

### Phase 2: Tenant Context → Server Session (P1)

| Key | API Endpoint | Migration Notes |
|-----|-------------|-----------------|
| `tenant_id` | `GET /api/v1/identity/me` | Returns tenant from JWT/session; no localStorage needed |

### Phase 3: UI Preferences → User Profile (P2)

| Key | API Endpoint | Migration Notes |
|-----|-------------|-----------------|
| `salesos_theme` | `PATCH /api/v1/users/me/preferences` | Store in `users.preferences.theme` JSONB field |
| `salesos-locale` | `PATCH /api/v1/users/me/preferences` | Store in `users.preferences.locale` JSONB field |

**New endpoint:**

```python
@router.patch("/users/me/preferences")
async def update_preferences(prefs: dict, ...):
    user.preferences = {**user.preferences, **prefs}
    await repo.update(user)
    return {"status": "ok"}
```

### Phase 4: Search State → Backend API (P3)

| Key | API Endpoint | Migration Notes |
|-----|-------------|-----------------|
| `salesos_saved_searches` | `GET/POST/DELETE /api/v1/search/saved` | New REST resource for saved searches |
| `salesos_search_history` | `GET/POST/DELETE /api/v1/search/history` | New REST resource for search history |

**New endpoints:**

```
GET    /api/v1/search/saved          → list saved searches
POST   /api/v1/search/saved          → save a search
DELETE /api/v1/search/saved/{id}     → delete a saved search
GET    /api/v1/search/history        → list recent searches (max 50)
POST   /api/v1/search/history        → add to history
DELETE /api/v1/search/history        → clear history
```

### Phase 5: Guidance State → Backend API (P3)

| Key | API Endpoint | Migration Notes |
|-----|-------------|-----------------|
| `salesos:onboarding-progress` | `GET/PATCH /api/v1/users/me/onboarding` | Store completed steps in user preferences |
| `salesos:completed-tours` | `GET/PATCH /api/v1/users/me/tours` | Store completed tour IDs in user preferences |

### Phase 6: Copilot Messages → Backend API (P4)

| Key | API Endpoint | Migration Notes |
|-----|-------------|-----------------|
| `salesos-copilot-messages` | `GET/POST/DELETE /api/v1/copilot/messages` | New REST resource for chat history |

### Phase 7: Offline Queue → IndexedDB (P4)

| Key | API Endpoint | Migration Notes |
|-----|-------------|-----------------|
| `salesos_offline_queue` | No server endpoint | Move to IndexedDB (larger storage, non-blocking). IndexedDB is already the correct browser API for offline queues. No server-side migration needed. |

---

## 3. Feature Flag Configuration

Each migration phase is gated by a feature flag for gradual rollout and instant rollback.

| Flag Key | Phase | Default | Description |
|----------|-------|---------|-------------|
| `auth_cookies_enabled` | 1 | `false` | Use HttpOnly cookies for auth tokens instead of localStorage |
| `tenant_server_session` | 2 | `false` | Read tenant_id from server session instead of localStorage |
| `prefs_server_sync` | 3 | `false` | Sync UI preferences (theme, locale) to server |
| `search_saved_server` | 4 | `false` | Use server API for saved searches |
| `search_history_server` | 4 | `false` | Use server API for search history |
| `guidance_server_sync` | 5 | `false` | Sync onboarding/tour progress to server |
| `copilot_server_history` | 6 | `false` | Store copilot messages in server API |
| `offline_indexeddb` | 7 | `false` | Use IndexedDB for offline queue |

**Rollout order:**

```
Phase 1 (auth) → 1 week soak → Phase 2 (tenant) → Phase 3 (prefs)
→ Phase 4 (search) → Phase 5 (guidance) → Phase 6 (copilot) → Phase 7 (offline)
```

**Gradual rollout per phase:**

1. **Internal testing** (flag ON for internal tenants only)
2. **Pilot tenants** (flag ON for 3 pilot tenants)
3. **10% rollout** (flag ON for 10% of tenants via A/B)
4. **100% rollout** (flag ON globally)
5. **Cleanup** (remove localStorage fallback code after 30 days at 100%)

---

## 4. Rollback Plan

### Per-Phase Rollback

Each phase has an independent rollback path:

| Phase | Rollback Action | Data Loss Risk |
|-------|----------------|----------------|
| 1 (Auth) | Set `auth_cookies_enabled` to `false`. Frontend falls back to localStorage. | **NONE** — cookies and localStorage coexist during migration |
| 2 (Tenant) | Set `tenant_server_session` to `false`. Frontend reads from localStorage. | **NONE** |
| 3 (Prefs) | Set `prefs_server_sync` to `false`. Frontend reads from localStorage. | **NONE** — server prefs ignored, localStorage prefs intact |
| 4 (Search) | Set `search_saved_server` and `search_history_server` to `false`. | **NONE** |
| 5 (Guidance) | Set `guidance_server_sync` to `false`. | **NONE** |
| 6 (Copilot) | Set `copilot_server_history` to `false`. | **NONE** |
| 7 (Offline) | Set `offline_indexeddb` to `false`. | **NONE** — data already synced to IndexedDB |

### Cross-Phase Rollback

If multiple phases are live and a regression is found:

1. **Disable all flags** → system falls back to localStorage for all data
2. **No data is lost** → localStorage still has the pre-migration data
3. **Investigate** → check logs, trace the issue
4. **Re-enable one phase at a time** → isolate which phase caused the issue

### Data Integrity During Migration

During the dual-write period (both localStorage and server):

1. **Read from server first** → if server has data, use it
2. **Write to both** → server and localStorage receive every write
3. **Fallback** → if server request fails, read from localStorage
4. **Cleanup** → after 30 days at 100% rollout, remove localStorage fallback reads

```typescript
// Example: dual-read pattern
async function getTheme(): Promise<string> {
  try {
    if (await featureFlag('prefs_server_sync')) {
      const resp = await api.get('/api/v1/users/me/preferences');
      return resp.data.theme || 'light';
    }
  } catch { /* server unavailable, fall through */ }
  return localStorage.getItem('salesos_theme') || 'light';
}
```

### Emergency Kill Switch

If a critical issue is found in production:

```bash
# Disable all migration flags via admin API
curl -X PUT https://api.salesos.com/api/v1/admin/feature-flags/auth_cookies_enabled \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"enabled": false}'

# Or via database directly
psql -U salesos -d salesos -c "
  UPDATE feature_flags SET enabled = false
  WHERE key IN (
    'auth_cookies_enabled', 'tenant_server_session', 'prefs_server_sync',
    'search_saved_server', 'search_history_server', 'guidance_server_sync',
    'copilot_server_history', 'offline_indexeddb'
  );
"
```

---

## 5. Implementation Checklist

- [ ] Phase 1: Auth tokens → HttpOnly cookies
  - [ ] Backend: Add Set-Cookie to login/register/refresh responses
  - [ ] Backend: Add cookie-based auth middleware
  - [ ] Frontend: Remove localStorage token reads
  - [ ] Frontend: Remove Authorization header interceptor
  - [ ] Tests: Update all auth-related tests
  - [ ] Feature flag: `auth_cookies_enabled`
- [ ] Phase 2: Tenant context → server session
- [ ] Phase 3: UI preferences → user profile API
- [ ] Phase 4: Search state → backend API
- [ ] Phase 5: Guidance state → backend API
- [ ] Phase 6: Copilot messages → backend API
- [ ] Phase 7: Offline queue → IndexedDB
- [ ] Cleanup: Remove all localStorage fallback code
- [ ] Audit: Verify no remaining localStorage usage in production code

---

*Created: 2026-07-13*
*Owner: Backend Engineering*
*Review: Security Review Board + Architecture Review Board*
