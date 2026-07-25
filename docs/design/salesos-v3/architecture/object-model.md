# Object Model

> Every screen binds to objects below. Schema: Attributes · Lifecycle · Relationships · Commands · Permissions · Events · Widgets.

## Shared conventions

- **IDs:** UUID. **Tenant:** required on all tenant-scoped objects.
- **Timestamps:** `created_at`, `updated_at`. **Soft delete** where audit requires.
- **Permissions:** `object.action` (e.g. `company.read`).
- **Legacy map:** routes from PAGE_MAP noted as `legacy:`.

---

### Company
- **Attributes:** name, legal_name, domain, cr_number, country, industry, size, health_score, owner_id, tags
- **Lifecycle:** prospect → customer → churned · archived
- **Relationships:** People, Deals, Activities, Contracts, Documents, Signals, Graph edges
- **Commands:** create, merge, assign_owner, add_tag, open_360, ask_ai_summary
- **Permissions:** company.read/write/delete/merge
- **Events:** company.created/updated/merged/health_changed
- **Widgets:** Health, AI Summary, Open Deals, Timeline, Graph
- **legacy:** `/companies`, `/companies/[id]`, `/companies/[id]/360`

### People (Contact)
- **Attributes:** name, email, phone, title, company_id, seniority, influence_score
- **Lifecycle:** active · inactive · do_not_contact
- **Relationships:** Company, Deals, Activities, Meetings
- **Commands:** create, enrich, log_activity, sequence_enroll
- **Permissions:** contact.*
- **Events:** contact.created/updated
- **Widgets:** Influence, Communication History
- **legacy:** `/contacts`

### Employee
- **Attributes:** user_id, title, team, manager_id, skills[], performance_score
- **Lifecycle:** active · leave · terminated
- **Relationships:** User, Team, Activities, Meetings, Signals
- **Commands:** open_360, coach_actions (Preview)
- **Permissions:** employee.read / employee.admin
- **Events:** employee.score_updated
- **Widgets:** Performance, Timeline, AI Coach (Preview)
- **legacy:** `/employees`, `/employees/me`, `/employees/[id]`

### Lead
- **Attributes:** source, status, score, company_id, owner_id
- **Lifecycle:** new → working → qualified → converted · disqualified
- **Relationships:** Company, People, Activities
- **Commands:** qualify, convert, assign, disqualify
- **Permissions:** lead.*
- **Events:** lead.converted
- **Widgets:** Lead Score, Source Mix

### Deal / Opportunity
- **Attributes:** name, amount, currency, stage, close_date, probability, company_id, owner_id
- **Lifecycle:** stages (configurable) → won/lost
- **Relationships:** Company, People, Activities, Quotes, Contracts
- **Commands:** move_stage, mark_won/lost, forecast_include, nba (Preview)
- **Permissions:** opportunity.*
- **Events:** stage_changed, amount_changed
- **Widgets:** Stage, NBA, Risk
- **legacy:** `/opportunities`, `/opportunities/[id]`, `/pipeline`

### Activity
- **Attributes:** type (call/email/meeting/note), subject, body, occurred_at, related_ids
- **Lifecycle:** planned → done · canceled
- **Commands:** log, complete, reschedule
- **Permissions:** activity.*
- **Events:** activity.logged
- **legacy:** `/activities`

### Task
- **Attributes:** title, due_at, priority, status, assignee_id, related_ids
- **Lifecycle:** open → in_progress → done · canceled
- **Commands:** create, complete, reassign
- **Permissions:** task.*
- **Events:** task.due_soon, task.completed

### Meeting
- **Attributes:** starts_at, ends_at, attendees[], location, notes
- **Lifecycle:** scheduled → completed · canceled
- **Commands:** schedule, summarize (Preview AI)
- **Permissions:** meeting.*
- **legacy:** `/meetings`

### Contract
- **Attributes:** title, value, status, company_id, starts_on, ends_on, version
- **Lifecycle:** draft → in_review → approved → active → expired · terminated
- **Relationships:** Company, Documents, Approvals
- **Commands:** submit, approve, reject, ai_review (Preview)
- **Permissions:** contract.*
- **Widgets:** Risk, Version History

### Invoice / Order / Quote
- **Attributes:** number, amount, status, company_id, deal_id, line_items[]
- **Lifecycle:** draft → sent → accepted/paid/fulfilled · void
- **Commands:** send, accept, void
- **Permissions:** finance.* (module gated)

### Supplier / Buyer
- **Attributes:** org profile, matching_score, categories[]
- **Lifecycle:** listed → matched → transacting · suspended
- **Commands:** match, recommend
- **Permissions:** marketplace.*
- **legacy overlap:** `/marketplace` (plugins today — Network is net-new IA)

### Workspace / Organization / Tenant
- See [multi-workspace.md](./multi-workspace.md).

### User / Role / Permission
- **Attributes:** email, role_ids, status, mfa
- **Lifecycle:** invited → active → suspended
- **Commands:** invite, assign_role, impersonate (audited)
- **Permissions:** admin.users, rbac.manage
- **legacy:** `/admin`, `/admin/tenants`, settings

### AI Agent
- **Attributes:** name, tools[], status, evaluation_score
- **Lifecycle:** draft → preview → enabled · disabled
- **Commands:** run, approve_action, disable
- **Permissions:** ai.agent.manage
- **Honesty:** Preview until evaluation pass

### Knowledge / Document
- **Attributes:** title, mime, versions[], acl, ocr_status
- **Lifecycle:** uploaded → indexed → archived
- **Commands:** upload, search, approve
- **Permissions:** document.*, knowledge.*
- **legacy:** `/rag`, `/knowledge`, `/knowledge/connectors`

### Signal / Workflow / Widget / DashboardView
- **Signal:** type, severity, entity_ref, status (open/acked) — legacy `/signals`, rules net-new
- **Workflow:** definition, runs — legacy `/automation`
- **Widget:** manifest_id, config — Widget SDK
- **DashboardView:** layout JSON, scope (personal/role/shared) — Dashboard Engine

## Coverage checklist

All program objects listed above have Attributes/Lifecycle/Relationships/Commands/Permissions/Events/Widgets (or pointer to multi-workspace).
