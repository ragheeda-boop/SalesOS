# Contacts API

> **Base Path:** `/api/v1/contacts`

Contact entity lifecycle — CRUD, search, and bulk upsert. Contacts are linked to companies and appear across opportunity timelines and company 360 views.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/contacts` | Create a new contact |
| `GET` | `/contacts/{id}` | Get contact by ID |
| `PUT` | `/contacts/{id}` | Update contact |
| `DELETE` | `/contacts/{id}` | Delete contact |
| `POST` | `/contacts/search` | Search contacts |
| `POST` | `/contacts/bulk` | Bulk upsert contacts |

---

## Create Contact

```bash
curl -X POST https://api.salesos.sa/api/v1/contacts \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sara Ahmed",
    "email": "sara@acme.com",
    "phone": "+966501234567",
    "title": "VP Sales",
    "company_id": "comp_abc123",
    "linkedin_url": "https://linkedin.com/in/saraahmed",
    "location": "Riyadh, SA"
  }'
```

**Response:** `201 Created`

```json
{
  "id": "cont_xyz",
  "name": "Sara Ahmed",
  "email": "sara@acme.com",
  "phone": "+966501234567",
  "title": "VP Sales",
  "company_id": "comp_abc123",
  "linkedin_url": "https://linkedin.com/in/saraahmed",
  "location": "Riyadh, SA",
  "created_at": "2026-07-12T14:30:00.000Z"
}
```

---

## Get Contact

```bash
curl -X GET https://api.salesos.sa/api/v1/contacts/cont_xyz \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "id": "cont_xyz",
  "name": "Sara Ahmed",
  "email": "sara@acme.com",
  "phone": "+966501234567",
  "title": "VP Sales",
  "company_id": "comp_abc123",
  "company_name": "Acme Corp",
  "linkedin_url": "https://linkedin.com/in/saraahmed",
  "location": "Riyadh, SA",
  "created_at": "2026-07-12T14:30:00.000Z",
  "updated_at": "2026-07-12T14:30:00.000Z"
}
```

---

## Update Contact

```bash
curl -X PUT https://api.salesos.sa/api/v1/contacts/cont_xyz \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Chief Revenue Officer",
    "phone": "+966509876543"
  }'
```

**Response:** `200 OK`

```json
{
  "id": "cont_xyz",
  "name": "Sara Ahmed",
  "title": "Chief Revenue Officer",
  "phone": "+966509876543",
  "updated_at": "2026-07-12T15:00:00.000Z"
}
```

---

## Delete Contact

```bash
curl -X DELETE https://api.salesos.sa/api/v1/contacts/cont_xyz \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz"
```

**Response:** `200 OK`

```json
{
  "message": "Contact deleted successfully"
}
```

---

## Search Contacts

```bash
curl -X POST https://api.salesos.sa/api/v1/contacts/search \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "VP sales Riyadh",
    "filters": {
      "company_id": "comp_abc123",
      "title": ["VP", "Director"]
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
      "id": "cont_xyz",
      "name": "Sara Ahmed",
      "title": "VP Sales",
      "company_name": "Acme Corp",
      "email": "sara@acme.com",
      "score": 0.88
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 12,
    "total_pages": 1
  }
}
```

---

## Bulk Upsert

```bash
curl -X POST https://api.salesos.sa/api/v1/contacts/bulk \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Tenant-Id: tenant_xyz" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "Ali Hassan",
      "email": "ali@companya.com",
      "title": "CTO",
      "company_id": "comp_111"
    },
    {
      "name": "Nora Khalid",
      "email": "nora@companyb.com",
      "title": "CFO",
      "company_id": "comp_222"
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
| `CONTACT_NOT_FOUND` | 404 | Contact with given ID doesn't exist |
| `VALIDATION_ERROR` | 422 | Missing required fields (name, email) |
| `DUPLICATE_EMAIL` | 409 | Contact with this email already exists |
| `COMPANY_NOT_FOUND` | 404 | Referenced company doesn't exist |
| `TENANT_MISMATCH` | 403 | Contact belongs to different tenant |
