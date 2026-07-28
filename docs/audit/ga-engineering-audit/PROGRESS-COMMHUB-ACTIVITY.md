# Progress — Communication Hub + Activity Intelligence (2026-07-28)

**Classification:** light validated (local Docker + FE build)  
**Production:** still **NO-GO** (staging cloud / soak / signatures / DR residuals)

## Commits this session

| Hash | Summary |
|------|---------|
| `fbea9aa` | Harden Google OAuth callback, calendar syncToken, company domain linking, Activity Intelligence FE metrics |
| `64858dd` | Fix OAuth unit test for URL-encoded redirect_uri |
| `0ef2ff1` | Unique tenant+provider IDs on synced email/calendar events (Alembic **0049**) |
| `cb7e914` | Wire Company/Employee 360 engagement to Postgres event readers |

## Fixes applied

1. **OAuth callback auth** — Hub mounted without router-level Bearer; protected routes use `Depends(verify_token)`; callback remains public (state-bound).
2. **Post-OAuth UX** — callback redirects to `FRONTEND_URL/v3/settings?google=connected|error`.
3. **OAuth URL encoding** — `urllib.parse.urlencode` for auth URL params.
4. **Token refresh skew** — refresh 60s before expiry; status `token_valid` true if refresh token present.
5. **Calendar incremental sync** — persist `calendar_sync_token` (migration **0048**); 410 → clear token + full resync.
6. **Company domain linking** — `company_linker.py` sets `related_company_ids` on email/calendar upsert.
7. **JSON binding** — lists dumped via `json.dumps` + `CAST(... AS jsonb)`.
8. **Direction vocabulary** — employee email KPIs accept `inbound`/`outbound` and legacy `sent`/`received`.
9. **Activity API DTO alignment** — dashboard/followups/engagement/email/calendar additive FE fields.
10. **FE** — Activities page wires `useActivityIntelligence`; Google panel allows sync when connected; OAuth return messaging.
11. **CalendarProvider ABC** — returns `(events, next_sync_token)`; worker unpacks tuple.
12. **Conference fields** — RawCalendarEvent + provider + hub insert.

## Validation evidence

| Check | Result |
|-------|--------|
| Alembic (local Docker) | **0048** applied earlier; **0049** added on disk (apply on next upgrade) |
| `pytest` Comm Hub + Activity API | **80 passed** (Docker, after pytest install) |
| FE `lint` / `tsc` / `build` | **exit 0** (warnings only) |
| Backend health | healthy after recreate |

## Remaining blockers (honest)

1. Cloud staging credentials / Environments / deploy workflow still **BLOCKED** (workflow now also triggers on `master` — still needs secrets)
2. 48–72h soak claim still **false** — [PROGRESS-WAVE11-SOAK-CLAIM.md](./PROGRESS-WAVE11-SOAK-CLAIM.md)
3. Prod Alembic migrate **needs human approval**
4. CTO/TL signatures **UNSIGNED**
5. OAuth state still **in-memory** (multi-replica gap; same pattern as SSO)
6. ActivityRuntime ingest still **not** wired from Hub sync (APIs read `employee_*_events` directly — intentional)
7. Google OAuth client credentials required for live connect smoke (**external credential**)
8. Primary WAL/PITR + offsite backup **OPEN** (MinIO profile added — drill not run)
9. Activity honesty engineering pass: [PROGRESS-COMMHUB-ACTIVITY-HONESTY.md](./PROGRESS-COMMHUB-ACTIVITY-HONESTY.md)

**Verdict:** production **no-go**. Comm Hub / Activity Intelligence vertical slice is **pilot-ready with conditions** locally.
