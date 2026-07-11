# Quickstart — 5 Minutes to Your First API Call

> **دليل البدء السريع — استخدم SalesOS في 5 دقائق**

This guide gets you from zero to your first API call in under 5 minutes.

---

## Prerequisites

- A SalesOS tenant account (sign up at [app.salesos.sa](https://app.salesos.sa))
- An API key from the Settings > API Keys page
- `curl` or any HTTP client

---

## Step 1: Get Your API Key

1. Log in to your SalesOS tenant
2. Navigate to **Settings > API Keys**
3. Click **Generate New Key**
4. Copy the key — it starts with `sos_`

---

## Step 2: Verify Authentication

```bash
curl -X GET "https://api.salesos.sa/api/v1/auth/me" \
  -H "Authorization: Bearer sos_your_api_key_here" \
  -H "X-Tenant-Id: your-tenant-id"
```

**Response:**

```json
{
  "id": "user_abc123",
  "email": "ahmed@example.com",
  "role": "admin",
  "tenant_id": "tenant_xyz789"
}
```

---

## Step 3: Search for a Company

Search for a company by name or CR number:

```bash
curl -X GET "https://api.salesos.sa/api/v1/search?q=الشركة+السعودية&type=company&limit=5" \
  -H "Authorization: Bearer sos_your_api_key_here" \
  -H "X-Tenant-Id: your-tenant-id"
```

**Response:**

```json
{
  "results": [
    {
      "id": "comp_4d5e6f7g",
      "name_ar": "الشركة السعودية للاستثمار",
      "name_en": "Saudi Investment Company",
      "cr_number": "1234567890",
      "city": "الرياض",
      "status": "active"
    }
  ],
  "total": 1
}
```

---

## Step 4: Get Company Details

```bash
curl -X GET "https://api.salesos.sa/api/v1/companies/comp_4d5e6f7g" \
  -H "Authorization: Bearer sos_your_api_key_here" \
  -H "X-Tenant-Id: your-tenant-id"
```

This returns full company data: branches, licenses, contacts, scores, and DNA profile.

---

## Step 5: Create an Opportunity

```bash
curl -X POST "https://api.salesos.sa/api/v1/revenue/opportunities" \
  -H "Authorization: Bearer sos_your_api_key_here" \
  -H "X-Tenant-Id: your-tenant-id" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "comp_4d5e6f7g",
    "name": "Enterprise License — Saudi Investment Co",
    "value": 500000,
    "currency": "SAR"
  }'
```

---

## What's Next

| Guide | Description |
|-------|-------------|
| [First API Call Tutorial](first-api-call.md) | Deep dive into API usage |
| [Configuration Guide](configuration.md) | Environment variables explained |
| [Installation Guide](installation.md) | Docker deployment for self-hosted |
| [API Overview](../api/overview.md) | Complete API reference |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `401 Unauthorized` | Check your API key and tenant ID |
| `403 Forbidden` | Your role lacks permission for this resource |
| `429 Too Many Requests` | Slow down — rate limit is 100 req/min |
| Company not found | Try Arabic name, English name, or CR number |
