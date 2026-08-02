# Phase 1 Stream A — pagination + reprovision

> **Stream:** Backend · after FE wired sort/activate @ `78e4c26`  
> **Honesty:** Not Production GO. DEC-085 untouched. BE-only.

## Landed

| Item | Detail |
|------|--------|
| Pagination | GET `/admin/tenants?page=&page_size=` (omit `page` = full list); `X-Total-Count` header; CORS `expose_headers` |
| Reprovision | `POST /admin/tenants/{id}/reprovision` — retries failed/pending; suspended requires `force_active=true` |
| STORY-04 status | Schema + provision skeleton **LANDED** (pilot conditions; no Production GO) |

## Non-goals

- FE wire of page/page_size or Reprovision CTA (Stream B)  
- Production GO / GA GO
