# Knowledge Packs API

> **حزم المعرفة — إدارة حزم المعرفة المجالية**
> Base path: `/api/v1/knowledge-packs`

---

## Authentication

All endpoints require `Authorization: Bearer <token>` and `X-Tenant-Id` headers.

---

## List Knowledge Packs

```
GET /api/v1/knowledge-packs
```

**Permissions:** `knowledge_packs:read`

```bash
curl -X GET "https://api.salesos.sa/api/v1/knowledge-packs" \
  -H "Authorization: Bearer <token>"
```

Response:

```json
{
  "packs": [
    {
      "id": "kp-arabic-business",
      "name": "Arabic Business Terms",
      "version": "1.2.0",
      "description": "Standard Arabic-English business terminology for the Saudi market",
      "category": "language",
      "size_kb": 245,
      "installed": true,
      "auto_install": true,
      "dependencies": []
    },
    {
      "id": "kp-saudi-market",
      "name": "Saudi Market Intelligence",
      "version": "2.0.0",
      "description": "Market structure, key players, regulations, and business practices in Saudi Arabia",
      "category": "market-intelligence",
      "size_kb": 890,
      "installed": true,
      "auto_install": false,
      "dependencies": ["kp-arabic-business"]
    }
  ],
  "total": 8
}
```

**Categories:** `language`, `market-intelligence`, `industry`, `regulatory`, `enrichment`

---

## Get Pack Details

```
GET /api/v1/knowledge-packs/{pack_id}
```

---

## Install Pack

```
POST /api/v1/knowledge-packs/{pack_id}/install
```

**Permissions:** `knowledge_packs:write`

Installs the pack for the current tenant. Dependencies are auto-resolved.

---

## Uninstall Pack

```
POST /api/v1/knowledge-packs/{pack_id}/uninstall
```

---

## List Installed Packs

```
GET /api/v1/knowledge-packs/installed
```

Returns packs installed on the current tenant with activation status.

---

## Upload Pack (Admin)

```
POST /api/v1/admin/knowledge-packs
```

**Permissions:** `admin:knowledge_packs`

Upload a new knowledge pack (ZIP format with manifest.json):

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Pack identifier |
| `version` | Yes | Semantic version |
| `category` | Yes | Pack category |
| `description` | Yes | Human-readable description |
| `dependencies` | No | Array of pack IDs |
| `auto_install` | No | Auto-install on new tenants |

---

## Pack Manifest Structure

```json
{
  "name": "kp-healthcare",
  "version": "1.0.0",
  "category": "industry",
  "description": "KSA healthcare sector knowledge",
  "dependencies": ["kp-arabic-business"],
  "auto_install": true,
  "contents": {
    "entities": ["hospitals", "clinics", "pharmacies", "insurance"],
    "terms": 1500,
    "relationships": 320
  }
}
```

---

## Related

| Resource | Link |
|----------|------|
| Knowledge Packs Guide | [Knowledge Packs README](../../knowledge-packs/README.md) |
| API Portal | [README.md](README.md) |
