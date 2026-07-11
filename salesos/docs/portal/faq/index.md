# Frequently Asked Questions

> **الأسئلة الشائعة — إجابات سريعة للأسئلة المتكررة**

---

## Getting Started

### What is SalesOS?

SalesOS is a sales intelligence platform for the Middle East market. It organizes company data from government and commercial sources, provides AI-powered recommendations, and automates sales workflows.

### How do I get an API key?

Log in to your tenant → Settings → API Keys → Generate New Key. Keys start with `sos_`.

### Do I need a credit card to start?

No. All plans include a 14-day free trial with full access.

### What languages does the platform support?

English and Arabic. The UI, API responses, and explainability all support both languages.

---

## Technical

### What is the NBA Engine?

The Next Best Action Engine is SalesOS's decision intelligence system. It analyzes opportunity context (stage, signals, engagement) and recommends the single best action to move the deal forward. Every recommendation includes evidence and confidence.

### What data sources does SalesOS use?

Government sources: Balady, Taqeem, Waseel, ZATCA, MCI. Commercial sources: news, social media, web crawling. User-provided: emails, meetings, notes, documents.

### How is tenant isolation enforced?

Every database query includes a `tenant_id` filter. The `X-Tenant-Id` header must match the JWT token's tenant. Cross-tenant access returns HTTP 403.

### Can I run SalesOS on-premise?

Yes. The platform ships with Docker Compose for self-hosted deployment. See the [Installation Guide](getting-started/installation.md).

### What happens if the AI service is unavailable?

The system degrades gracefully. NBA falls back to rule-only mode. RAG returns keyword search results without LLM generation. No critical functionality is lost.

---

## Data & Privacy

### Where is my data stored?

All data is stored in Saudi Arabia (KSA data centers). We comply with KSA PDPL regulations.

### How long is data retained?

Active data: as long as your account is active. Audit logs: 7 years. Cache: configurable TTL (default 5 minutes to 24 hours).

### Can I delete my data?

Yes. Use the Admin API to request data deletion. We process deletion requests within 30 days per PDPL requirements.

### Is my data used to train AI models?

No. Your data is never used to train or fine-tune LLMs. AI responses are generated from your documents only.

---

## Billing

### What plans are available?

| Plan | Price | Features |
|------|-------|----------|
| Starter | Free | 100 companies, basic search |
| Professional | SAR 999/mo | 10K companies, NBA, pipeline |
| Enterprise | Custom | Unlimited, SSO, workflows, RAG, dedicated support |

### How is billing calculated?

Monthly subscription based on plan. Additional API usage above plan limits is billed at $0.001 per API call.

### Can I change my plan?

Yes. Upgrade or downgrade at any time. Changes take effect next billing cycle.

---

## SDK & Development

### What SDKs are available?

TypeScript SDKs: `@salesos/workspace` (widgets), `@salesos/search`, `@salesos/decision-platform`, `@salesos/platform`. Python: FastAPI backend with Pydantic models.

### Can I build custom widgets?

Yes. Use the Widget SDK (`@salesos/workspace`) with the Container/View pattern. See the [Creating a Widget Guide](guides/creating-a-widget.md).

### How do I test my widget?

Every widget requires `describeWidgetContract()` tests covering loading, ready, degraded, and error states.

### Can I integrate with my CRM?

Yes. SalesOS has REST APIs for all functionality. Custom integrations can use webhooks (via Workflow Engine) or direct API calls.

---

## Support

### How do I get help?

- Documentation: [docs.salesos.sa](https://docs.salesos.sa)
- Email: `support@salesos.sa`
- Support hours: Sat–Thu, 9:00–18:00 AST
- Enterprise: Dedicated Slack channel

### What is the SLA?

| Plan | Uptime | Response Time |
|------|--------|---------------|
| Starter | 99.5% | 24 hours |
| Professional | 99.9% | 4 hours |
| Enterprise | 99.99% | 1 hour |

### How do I report a bug?

From the app: Help → Report Bug. API: `POST /api/v1/support/bugs`. Critical security issues: `security@salesos.sa`.
