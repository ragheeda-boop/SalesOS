# Progress — Communication Hub + Activity Intelligence honesty pass (2026-07-28)

**Classification:** light validated (static + unit tenant test added; full suite not run this pass)  
**Production:** still **NO-GO**

## Closed this pass (engineering)

1. **Tenant `get()`** — already required `tenant_id`; regression test `tests/test_postgres_readers_tenant.py`
2. **f-string SQL** — readers use whitelisted fragments only; router uses static optional `AND employee_id = :eid`
3. **Honest metrics** — thread-based `reply_rate`, real `avg_response_hours`, real `upcoming`, company names via join, followup counters split (need/overdue/waiting_*), engagement `total_companies` vs `total_employees`
4. **Pagination** — employee email/calendar `limit`+`offset`+true `total` count
5. **Encryption** — `GOOGLE_ENCRYPTION_KEY` required (no `SECRET_KEY` fallback); env examples updated
6. **Dockerfile** — dep-first Poetry install + `tini` ENTRYPOINT on used `Dockerfile`
7. **Auth mounts** — notifications + MCP include `dependencies=_auth`
8. **Gmail pagination** — `nextPageToken` loop in `fetch_emails`
9. **database_url** — skip double `+asyncpg` if already present

## Still OPEN (ops / GA)

- Staging cloud / soak / signatures / primary WAL / prod migrate
- OAuth state still in-memory
- Staging SSRF pentest not executed

**Verdict:** Activity vertical remains **pilot-ready with conditions**; SalesOS GA **production no-go**.
