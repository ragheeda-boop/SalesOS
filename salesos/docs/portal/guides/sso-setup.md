# Tutorial: Configuring SSO

> **إعداد الدخول الموحد — Azure AD، Google Workspace، Okta**

---

## Supported Providers

| Provider | Protocol | Setup Time |
|----------|----------|------------|
| Azure AD | OIDC | 15 min |
| Google Workspace | OIDC | 10 min |
| Okta | OIDC | 15 min |
| Custom | OIDC / SAML | 30 min |

---

## Step 1: Configure Your Identity Provider

### Azure AD

1. Go to Azure Portal → App Registrations → New Registration
2. Set redirect URI: `https://api.salesos.sa/api/v1/auth/sso/azure/callback`
3. Note: Client ID and Client Secret
4. Under "Certificates & Secrets" → New Client Secret

### Google Workspace

1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID
3. Set authorized redirect URI: `https://api.salesos.sa/api/v1/auth/sso/google/callback`
4. Note: Client ID and Client Secret

---

## Step 2: Configure SalesOS

```bash
# In your .env file
SSO_PROVIDER=azure
SSO_CLIENT_ID=your-client-id
SSO_CLIENT_SECRET=your-client-secret
SSO_TENANT=your-tenant-id  # For Azure AD
```

Or via Admin API:

```bash
curl -X PUT "https://api.salesos.sa/api/v1/admin/tenant" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sso": {
      "provider": "azure",
      "client_id": "your-client-id",
      "client_secret": "your-client-secret",
      "tenant": "your-azure-tenant-id"
    }
  }'
```

---

## Step 3: Test SSO Login

Navigate to: `https://app.salesos.sa/login`

Click "Sign in with [Provider]" → redirected to provider's login page → redirected back.

---

## User Provisioning

| Method | Description |
|--------|-------------|
| **Just-in-Time** | First SSO login creates user automatically |
| **SCIM** | Automatic provisioning from IdP (Azure AD only) |
| **Manual** | Admin invites users via Admin API |

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Redirect URI mismatch | Callback URL in IdP doesn't match | Verify exact URL in both places |
| `invalid_client` | Wrong client secret | Regenerate secret in IdP |
| User not created | Email domain not allowed | Add domain to allowed list |
| Role not assigned | Default role missing | Set `SSO_DEFAULT_ROLE=user` |

---

## Related

| Resource | Link |
|----------|------|
| SSO API Reference | [API](../api/sso.md) |
| Security Architecture | [Security](../architecture/security.md) |
