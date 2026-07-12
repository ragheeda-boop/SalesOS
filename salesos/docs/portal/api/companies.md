# Companies API

> **Base Path:** `/api/v1/companies`

Company entity lifecycle — CRUD, search, 360 view, relationship queries, branch management, bulk ingestion, and import integrations (Notion, Excel).

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/companies` | Create a new company |
| `GET` | `/companies/{id}` | Get company by ID |
| `PUT` | `/companies/{id}` | Update company |
| `DELETE` | `/companies/{id}` | Delete company |
| `GET` | `/companies/{id}/360` | Full 360-degree view |
| `POST` | `/companies/search` | Search companies |
| `GET` | `/companies/{id}/branches` | List branches |
| `POST` | `/companies/{id}/branches` | Add a branch |
| `GET` | `/companies/{id}/contacts` | List contacts at company |
| `GET` | `/companies/{id}/licenses` | List company licenses |
| `POST` | `/companies/bulk` | Bulk upsert companies |

---

## Create Company

```bash
curl -X POST https://api.salesos.sa/api/v1/companies \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "domain": "acme.com",
    "industry": "Technology",
    "size": "201-500",
    "country": "SA",
    "city": "Riyadh",
    "website": "https://acme.com",
    "linkedin_url": "https://linkedin.com/company/acme",
    "description": "Leading technology solutions provider"
  }'
```

**Response:** `201 Created`

```json
{
  "id": "comp_abc123",
  "name": "Acme Corp",
  "domain": "acme.com",
  "industry": "Technology",
  "size": "201-500",
  "country": "SA",
  "city": "Riyadh",
  "website": "https://acme.com",
  "created_at": "2026-07-12T14:30:00.000Z",
  "updated_at": "2026-07-12T14:30:00.000Z"
}
```

---

## Get Company

```bash
curl -X GET https://api.salesos.sa/api/v1/companies/comp_abc123 \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "id": "comp_abc123",
  "name": "Acme Corp",
  "domain": "acme.com",
  "industry": "Technology",
  "size": "201-500",
  "country": "SA",
  "city": "Riyadh",
  "website": "https://acme.com",
  "linkedin_url": "https://linkedin.com/company/acme",
  "description": "Leading technology solutions provider",
  "created_at": "2026-07-12T14:30:00.000Z",
  "updated_at": "2026-07-12T14:30:00.000Z"
}
```

---

## Update Company

```bash
curl -X PUT https://api.salesos.sa/api/v1/companies/comp_abc123 \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "FinTech",
    "size": "501-1000"
  }'
```

**Response:** `200 OK`

```json
{
  "id": "comp_abc123",
  "name": "Acme Corp",
  "industry": "FinTech",
  "size": "501-1000",
  "updated_at": "2026-07-12T15:00:00.000Z"
}
```

---

## Delete Company

```bash
curl -X DELETE https://api.salesos.sa/api/v1/companies/comp_abc123 \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "message": "Company deleted successfully"
}
```

---

## Company 360 View

Returns full company context: company details, contacts, opportunities, activities, timeline, graph edges, and enrichment data.

```bash
curl -X GET https://api.salesos.sa/api/v1/companies/comp_abc123/360 \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "company": {
    "id": "comp_abc123",
    "name": "Acme Corp",
    "domain": "acme.com",
    "industry": "Technology"
  },
  "contacts": [
    {
      "id": "cont_xyz",
      "name": "Sara Ahmed",
      "title": "VP Sales",
      "email": "sara@acme.com"
    }
  ],
  "opportunities": [
    {
      "id": "opp_123",
      "name": "Acme Enterprise Deal",
      "value": 250000,
      "stage": "proposal"
    }
  ],
  "activities": {
    "total": 145,
    "emails": 42,
    "meetings": 12,
    "calls": 35,
    "linkedin": 56
  },
  "graph": {
    "relationships": [
      {
        "target_id": "comp_def456",
        "target_name": "Globex Corp",
        "relationship_type": "subsidiary",
        "confidence": 0.85
      }
    ],
    "connections_count": 3
  },
  "enrichment": {
    "revenue": "$50M-100M",
    "employees": "500-1000",
    "founded": 2015
  }
}
```

---

## Search Companies

```bash
curl -X POST https://api.salesos.sa/api/v1/companies/search \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "technology companies Riyadh",
    "filters": {
      "industry": ["Technology", "FinTech"],
      "size": ["201-500", "501-1000"],
      "country": "SA"
    },
    "page": 1,
    "limit": 20
  }'
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "comp_abc123",
      "name": "Acme Corp",
      "domain": "acme.com",
      "industry": "Technology",
      "score": 0.92,
      "highlight": "Acme <em>Corp</em> — leading <em>technology</em> solutions"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

---

## List Branches

```bash
curl -X GET https://api.salesos.sa/api/v1/companies/comp_abc123/branches \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "branch_1",
      "name": "Riyadh HQ",
      "address": "King Fahd Road, Riyadh",
      "country": "SA",
      "city": "Riyadh",
      "is_primary": true
    },
    {
      "id": "branch_2",
      "name": "Dubai Office",
      "address": "DIFC, Dubai",
      "country": "AE",
      "city": "Dubai",
      "is_primary": false
    }
  ]
}
```

---

## Add Branch

```bash
curl -X POST https://api.salesos.sa/api/v1/companies/comp_abc123/branches \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jeddah Office",
    "address": "Corniche Road, Jeddah",
    "country": "SA",
    "city": "Jeddah",
    "is_primary": false
  }'
```

**Response:** `201 Created`

```json
{
  "id": "branch_3",
  "name": "Jeddah Office",
  "country": "SA",
  "city": "Jeddah",
  "is_primary": false,
  "created_at": "2026-07-12T14:30:00.000Z"
}
```

---

## List Company Contacts

```bash
curl -X GET https://api.salesos.sa/api/v1/companies/comp_abc123/contacts \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "cont_xyz",
      "name": "Sara Ahmed",
      "title": "VP Sales",
      "email": "sara@acme.com",
      "phone": "+966501234567",
      "is_primary": true
    }
  ],
  "total": 8
}
```

---

## List Company Licenses

```bash
curl -X GET https://api.salesos.sa/api/v1/companies/comp_abc123/licenses \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "lic_1",
      "license_number": "CR-1010123456",
      "license_type": "Commercial Registration",
      "issue_date": "2024-01-15",
      "expiry_date": "2025-01-14",
      "status": "active"
    }
  ],
  "total": 3
}
```

---

## Bulk Upsert

```bash
curl -X POST https://api.salesos.sa/api/v1/companies/bulk \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "Company A",
      "domain": "companya.com",
      "industry": "Healthcare"
    },
    {
      "name": "Company B",
      "domain": "companyb.com",
      "industry": "Retail"
    }
  ]'
```

**Response:** `200 OK`

```json
{
  "message": "Bulk upsert completed",
  "data": {
    "created": 2,
    "updated": 0,
    "errors": []
  }
}
```

---

## Error Codes

| Error | HTTP | Description |
|-------|------|-------------|
| `COMPANY_NOT_FOUND` | 404 | Company with given ID doesn't exist |
| `VALIDATION_ERROR` | 422 | Missing required fields (name, domain) |
| `DUPLICATE_DOMAIN` | 409 | Company with this domain already exists |
| `TENANT_MISMATCH` | 403 | Company belongs to different tenant |
| `BULK_PARTIAL_FAILURE` | 207 | Some items in bulk failed |
