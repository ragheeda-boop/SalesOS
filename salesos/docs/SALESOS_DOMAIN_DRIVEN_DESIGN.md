# SalesOS Domain Driven Design (DDD)

> **المرجع النهائي لحدود المجالات، الكيانات، الأحداث، والسياسات — قبل أن يصبح المشروع كبيرًا**

| Document | Status |
|----------|--------|
| **Version** | v1.0 |
| **Last Updated** | 2026-06-29 |
| **Owner** | Domain Architect / CTO |
| **Audience** | All Engineering Teams |

---

## Table of Contents

1. [Strategic Design](#1-strategic-design)
2. [Bounded Contexts](#2-bounded-contexts)
3. [Context Map](#3-context-map)
4. [Ubiquitous Language](#4-ubiquitous-language)
5. [Core Domain: Company Intelligence](#5-core-domain-company-intelligence)
6. [Subdomain: Identity & Access](#6-subdomain-identity--access)
7. [Subdomain: CRM](#7-subdomain-crm)
8. [Subdomain: Activity](#8-subdomain-activity)
9. [Subdomain: Scoring & DNA](#9-subdomain-scoring--dna)
10. [Subdomain: Knowledge Graph](#10-subdomain-knowledge-graph)
11. [Subdomain: AI](#11-subdomain-ai)
12. [Subdomain: Workflow](#12-subdomain-workflow)
13. [Subdomain: Marketplace](#13-subdomain-marketplace)
14. [Subdomain: Data Lake](#14-subdomain-data-lake)
15. [Subdomain: Billing](#15-subdomain-billing)
16. [Domain Events Catalog](#16-domain-events-catalog)
17. [Repository Contracts](#17-repository-contracts)
18. [Application Services](#18-application-services)
19. [Domain Policies](#19-domain-policies)
20. [Specifications](#20-specifications)
21. [Architecture Decision Records](#21-architecture-decision-records)

---

# 1. Strategic Design

## 1.1 Domain Classification

| Domain Type | Domain | Strategy |
|-------------|--------|----------|
| **Core** | Company Intelligence | Differentiator, competitive advantage. Build in-house, invest heavily. |
| **Supporting** | CRM, Scoring, DNA, Timeline | Important but not unique. Build with standard patterns. |
| **Generic** | Identity, Billing, Search, Workflow | Commodity. Use best practices, consider off-the-shelf. |

## 1.2 Domain Vision

> **SalesOS organizes and enriches the world's company data so sales, procurement, and risk teams can make better decisions faster.**

## 1.3 Strategic Goals

| # | Goal | Domain Impact |
|---|------|--------------|
| 1 | Golden record for every company | Core: Entity Resolution |
| 2 | 100M+ companies searchable in under 500ms | Core: Search |
| 3 | AI copilot answers any company question | Core: AI Platform |
| 4 | CRM pipeline driven by AI signals | Supporting: CRM |
| 5 | Marketplace of plugins and data | Generic: Marketplace |

---

# 2. Bounded Contexts

## 2.1 Context Map

```
┌─────────────────────────────────────────────────────────────────┐
│                     SalesOS Platform                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Identity   │  │   Company    │  │   Entity Resolution   │   │
│  │   & Access   │◄─┤ Intelligence │◄─┤                       │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘   │
│         │                 │                                      │
│         │    ┌────────────┼────────────┐                        │
│         │    │            │            │                        │
│         ▼    ▼            ▼            ▼                        │
│  ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐               │
│  │  CRM     │ │Activity│ │Scoring │ │   DNA    │               │
│  │          │ │ Engine │ │ Engine │ │ Profiles │               │
│  └──────────┘ └────────┘ └────────┘ └──────────┘               │
│         │         │         │         │                        │
│         └─────────┼─────────┼─────────┘                        │
│                   │         │                                  │
│                   ▼         ▼                                  │
│  ┌──────────┐ ┌──────────┐ ┌────────────────────┐             │
│  │  Knowl-  │ │    AI    │ │     Workflow        │             │
│  │ edge Gr. │ │ Platform │ │     Engine          │             │
│  └──────────┘ └──────────┘ └────────────────────┘             │
│         │         │               │                            │
│         └─────────┼───────────────┘                            │
│                   │                                            │
│                   ▼                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │Marketpl. │ │Data Lake │ │ Billing  │                       │
│  └──────────┘ └──────────┘ └──────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

## 2.2 Bounded Contexts Summary

| # | Context | Type | Primary Data | Key Aggregate |
|---|---------|------|-------------|---------------|
| BC-01 | Identity & Access | Generic | Users, Tenants, Roles | Tenant, User |
| BC-02 | Company Intelligence | Core | Companies, Branches, Licenses | Company |
| BC-03 | Entity Resolution | Core | Golden Records, Source Links | GoldenRecord |
| BC-04 | CRM | Supporting | Opportunities, Pipelines | Opportunity |
| BC-05 | Activity Engine | Supporting | Events, Activities | Activity |
| BC-06 | Scoring Engine | Supporting | Scores, Models | CompanyScore |
| BC-07 | Company DNA | Supporting | Signals, Feature Store | DnaProfile |
| BC-08 | Knowledge Graph | Core | Nodes, Edges, Relationships | GraphNode |
| BC-09 | AI Platform | Core | Queries, Embeddings, Agents | AiQuery |
| BC-10 | Workflow Engine | Generic | Workflows, Triggers, Actions | WorkflowDefinition |
| BC-11 | Marketplace | Generic | Plugins, Listings, Purchases | PluginListing |
| BC-12 | Data Lake | Supporting | Tables, Pipelines, Partitions | DataPipeline |
| BC-13 | Billing | Generic | Subscriptions, Invoices | Subscription |

---

## 2.3 Context Relationships

| Source Context | Target Context | Relationship | Description |
|---------------|---------------|--------------|-------------|
| Identity | Company | Conformist | Company consumes tenant_id from Identity |
| Company | Entity Resolution | Partnership | Entity Resolution enriches Company |
| Company | CRM | Conformist | CRM consumes Company as customer |
| Company | Activity | Conformist | Activity consumes Company as subject |
| Company | Scoring | Conformist | Scoring consumes Company as input |
| Company | Knowledge Graph | Partnership | KG extends Company with relationships |
| Activity | Scoring | Conformist | Scoring consumes Activity for engagement |
| Scoring | DNA | Partnership | DNA uses Scoring signals |
| AI | All | Open-Host | AI queries all contexts via published language |
| Workflow | All | Open-Host | Workflow triggers on events from all contexts |
| Marketplace | Billing | Conformist | Marketplace consumes Billing for payments |

---

# 3. Ubiquitous Language

## 3.1 Core Terms

| Term | Definition | Context |
|------|------------|---------|
| **Company** | A legal entity with a Commercial Registration (CR) number registered in a government system | Company Intelligence |
| **Golden Record** | The single, canonical, deduplicated representation of a real-world company | Entity Resolution |
| **Source Record** | A company record as it appears in a specific source (e.g., Balady, Taqeem) | Entity Resolution |
| **CR Number** | Commercial Registration number — the unique identifier for a Saudi company | Company Intelligence |
| **License** | A permit issued by a government authority allowing a company to operate | Company Intelligence |
| **Branch** | A physical location of a company, distinct from its headquarters | Company Intelligence |
| **Contact** | A person associated with a company, with a role and contact information | Company Intelligence |
| **Opportunity** | A potential sales deal tracked through a pipeline stage | CRM |
| **Pipeline** | A sequence of stages through which opportunities progress | CRM |
| **Activity** | An interaction with a company or contact (email, call, meeting, note) | Activity Engine |
| **Timeline Event** | A significant occurrence in a company's lifecycle (license change, status change) | Activity Engine |
| **Score** | A numerical value representing a company's fitness, risk, or engagement level | Scoring Engine |
| **DNA Profile** | A multi-dimensional view of a company extracted from 50+ signals | Company DNA |
| **Graph Node** | An entity (company, person, license) in the knowledge graph | Knowledge Graph |
| **Graph Edge** | A weighted, temporal relationship between two graph nodes | Knowledge Graph |
| **Agent** | An AI system that performs a specific business function autonomously | AI Platform |
| **Workflow** | An automated sequence of triggers and actions | Workflow Engine |
| **Plugin** | A third-party extension that adds functionality to the platform | Marketplace |
| **Tenant** | A customer organization with isolated data and configuration | Identity |

## 3.2 Action Verbs

| Verb | Meaning | Used In |
|------|---------|---------|
| `Register` | Create a new tenant or user account | Identity |
| `Ingest` | Import raw data from an external source | Company Intelligence |
| `Resolve` | Match and merge duplicate company records | Entity Resolution |
| `Enrich` | Augment company data with additional attributes | Company Intelligence |
| `Score` | Calculate a numeric score for a company | Scoring Engine |
| `Detect` | Identify a change or pattern in company data | Company DNA |
| `Trigger` | Start a workflow when a condition is met | Workflow Engine |

---

# 4. Core Domain: Company Intelligence (BC-02)

## 4.1 Strategic Importance

**Company Intelligence is the core domain.** It is what differentiates SalesOS from every CRM and data platform. The quality, coverage, and freshness of company data is the single most important competitive advantage.

## 4.2 Aggregate: Company

```
┌─────────────────────────────────────────────────────────────┐
│                        Company                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  identity: CompanyId                                     ││
│  │  tenantId: TenantId                                      ││
│  │  nameAr: string                                          ││
│  │  nameEn: string?                                         ││
│  │  crNumber: CrNumber (Value Object)                       ││
│  │  status: CompanyStatus (Value Object)                    ││
│  │  address: Address (Value Object)                         ││
│  │  activityInfo: ActivityInfo (Value Object)               ││
│  │  financials: FinancialInfo? (Value Object)               ││
│  │  verification: VerificationStatus (Value Object)         ││
│  │                                                          ││
│  │  branches: Branch[] (Entity, owned by Company)           ││
│  │  licenses: License[] (Entity, owned by Company)          ││
│  │  contacts: Contact[] (Entity, owned by Company)          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  Invariants:                                                 │
│  - CR number must be unique within a tenant                  │
│  - Company must have at least one name (Arabic or English)   │
│  - Company status transitions follow lifecycle rules         │
│  - A company can have at most one primary contact            │
│                                                              │
│  Domain Events:                                              │
│  - CompanyCreated                                            │
│  - CompanyUpdated                                            │
│  - CompanyStatusChanged                                      │
│  - CompanyMerged                                             │
│  - CompanyVerified                                           │
└─────────────────────────────────────────────────────────────┘
```

### Company Entity

```python
class Company:
    id: CompanyId
    tenant_id: TenantId
    name_ar: str
    name_en: Optional[str]
    cr_number: CrNumber
    cr_type: Optional[str]
    status: CompanyStatus
    city: Optional[str]
    region: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    postal_code: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    address: Optional[str]
    capital: Optional[Money]
    currency: str
    employees_count: Optional[int]
    activity_description: Optional[str]
    activity_code: Optional[str]
    isic_code: Optional[str]
    legal_form: Optional[str]
    incorporation_date: Optional[date]
    expiry_date: Optional[date]
    is_golden_record: bool
    confidence_score: float
    tags: Tag[]
    branches: Branch[]
    licenses: License[]
    contacts: Contact[]
    created_at: datetime
    updated_at: datetime

    def change_status(self, new_status: CompanyStatus) -> None:
        valid_transitions = CompanyStatus.valid_transitions(self.status)
        if new_status not in valid_transitions:
            raise InvalidStatusTransition(self.status, new_status)
        self.status = new_status
        self.register_event(CompanyStatusChanged(self.id, self.status, new_status))

    def merge_with(self, other: Company) -> None:
        # Merge logic: consolidate fields, keep golden record
        self.is_golden_record = True
        self.confidence_score = max(self.confidence_score, other.confidence_score)
        self.source_ids = list(set(self.source_ids + other.source_ids))
        self.register_event(CompanyMerged(self.id, other.id))
```

### Value Object: CrNumber

```python
@dataclass(frozen=True)
class CrNumber:
    value: str

    def __post_init__(self):
        if not re.match(r"^\d{7,10}$", self.value):
            raise InvalidCrNumberError(self.value)

    def formatted(self) -> str:
        return f"{self.value[:2]}-{self.value[2:]}"

    def is_valid(self) -> bool:
        return bool(re.match(r"^\d{7,10}$", self.value))
```

### Value Object: CompanyStatus

```python
class CompanyStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    LIQUIDATED = "liquidated"
    UNDER_RESTRUCTURING = "under_restructuring"

    @classmethod
    def valid_transitions(cls, current: "CompanyStatus") -> set["CompanyStatus"]:
        transitions = {
            CompanyStatus.ACTIVE: {CompanyStatus.INACTIVE, CompanyStatus.SUSPENDED, CompanyStatus.EXPIRED},
            CompanyStatus.INACTIVE: {CompanyStatus.ACTIVE, CompanyStatus.LIQUIDATED},
            CompanyStatus.SUSPENDED: {CompanyStatus.ACTIVE, CompanyStatus.LIQUIDATED},
            CompanyStatus.EXPIRED: {CompanyStatus.ACTIVE, CompanyStatus.LIQUIDATED},
            CompanyStatus.LIQUIDATED: set(),
            CompanyStatus.UNDER_RESTRUCTURING: {CompanyStatus.ACTIVE, CompanyStatus.LIQUIDATED},
        }
        return transitions.get(current, set())
```

### Value Object: Address

```python
@dataclass(frozen=True)
class Address:
    street: Optional[str]
    city: str
    region: Optional[str]
    postal_code: Optional[str]
    country: str = "Saudi Arabia"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def full_address(self) -> str:
        parts = [p for p in [self.street, self.city, self.region, self.country] if p]
        return ", ".join(parts)

    def is_geocoded(self) -> bool:
        return self.latitude is not None and self.longitude is not None
```

## 4.3 Aggregate: License

```python
class License:
    id: LicenseId
    company_id: CompanyId
    license_number: str
    license_type: str
    license_type_ar: Optional[str]
    status: LicenseStatus
    issuing_authority: Optional[str]
    issue_date: Optional[date]
    expiry_date: Optional[date]
    renewal_date: Optional[date]

    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()

    def days_until_expiry(self) -> int:
        if not self.expiry_date:
            return -1
        return (self.expiry_date - date.today()).days

    def renew(self, new_expiry_date: date) -> None:
        self.expiry_date = new_expiry_date
        self.renewal_date = date.today()
        self.status = LicenseStatus.ACTIVE
        self.register_event(LicenseRenewed(self.id, self.company_id, new_expiry_date))
```

## 4.4 Aggregate: Contact

```python
class Contact:
    id: ContactId
    company_id: CompanyId
    name: str
    name_ar: Optional[str]
    email: Optional[EmailAddress]
    phone: Optional[PhoneNumber]
    mobile: Optional[PhoneNumber]
    position: Optional[str]
    department: Optional[str]
    is_primary: bool

    def make_primary(self) -> None:
        self.is_primary = True
        self.register_event(PrimaryContactChanged(self.id, self.company_id))
```

---

# 5. Subdomain: Identity & Access (BC-01)

## 5.1 Aggregate: Tenant

```python
class Tenant:
    id: TenantId
    name: str
    slug: str
    domain: Optional[str]
    plan: PlanType
    is_active: bool
    settings: dict
    features: dict
    subscription_ends_at: Optional[datetime]

    def is_subscription_active(self) -> bool:
        if not self.subscription_ends_at:
            return True
        return self.subscription_ends_at > datetime.utcnow()

    def has_feature(self, feature_key: str) -> bool:
        return self.features.get(feature_key, False)

    def activate(self) -> None:
        self.is_active = True
        self.register_event(TenantActivated(self.id))

    def deactivate(self) -> None:
        self.is_active = False
        self.register_event(TenantDeactivated(self.id))
```

## 5.2 Aggregate: User

```python
class User:
    id: UserId
    tenant_id: TenantId
    email: EmailAddress
    password_hash: str
    full_name: str
    full_name_ar: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    permissions: list[Permission]

    def verify(self) -> None:
        self.is_verified = True
        self.register_event(UserVerified(self.id))

    def change_role(self, new_role: UserRole, changed_by: UserId) -> None:
        old_role = self.role
        self.role = new_role
        self.register_event(UserRoleChanged(self.id, old_role, new_role, changed_by))

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions
```

### Value Object: UserRole

```python
class UserRole(Enum):
    ADMIN = "admin"       # Full access to all tenant data and settings
    MANAGER = "manager"   # Can manage data and users (except billing)
    USER = "user"         # Can view and create data, no admin functions
    API = "api"           # API-only access with limited scope
    AUDITOR = "auditor"   # Read-only access for compliance

    def permissions(self) -> list[Permission]:
        role_permissions = {
            UserRole.ADMIN: Permission.all(),
            UserRole.MANAGER: [p for p in Permission if not p.is_billing],
            UserRole.USER: [p for p in Permission if p.is_read or p.is_create],
            UserRole.API: [Permission.API_READ, Permission.API_WRITE],
            UserRole.AUDITOR: [Permission.AUDIT_READ, Permission.COMPANY_READ],
        }
        return role_permissions.get(self, [])
```

---

# 6. Subdomain: CRM (BC-04)

## 6.1 Aggregate: Pipeline

```python
class Pipeline:
    id: PipelineId
    tenant_id: TenantId
    name: str
    stages: list[PipelineStage]
    is_default: bool

    def add_stage(self, name: str, order: int) -> PipelineStage:
        stage = PipelineStage(name=name, order=order)
        self.stages.append(stage)
        self.stages.sort(key=lambda s: s.order)
        return stage

    def move_opportunity(self, opportunity_id: OpportunityId, to_stage: PipelineStage) -> None:
        opportunity = self.get_opportunity(opportunity_id)
        opportunity.move_to_stage(to_stage)
```

## 6.2 Aggregate: Opportunity

```python
class Opportunity:
    id: OpportunityId
    tenant_id: TenantId
    pipeline_id: PipelineId
    company_id: CompanyId
    name: str
    value: Money
    currency: str
    stage: PipelineStage
    probability: float
    expected_close_date: Optional[date]
    assigned_to: UserId
    tags: list[Tag]
    notes: list[Note]
    created_at: datetime
    updated_at: datetime

    def move_to_stage(self, new_stage: PipelineStage) -> None:
        old_stage = self.stage
        self.stage = new_stage
        self.probability = new_stage.default_probability
        self.register_event(OpportunityStageChanged(self.id, old_stage.id, new_stage.id))

    def update_value(self, new_value: Money) -> None:
        old_value = self.value
        self.value = new_value
        self.register_event(OpportunityValueChanged(self.id, old_value, new_value))

    def close_as_won(self) -> None:
        self.stage = PipelineStage.CLOSED_WON
        self.register_event(OpportunityWon(self.id, self.value))

    def close_as_lost(self, reason: str) -> None:
        self.stage = PipelineStage.CLOSED_LOST
        self.register_event(OpportunityLost(self.id, reason))
```

---

# 7. Subdomain: Activity Engine (BC-05)

## 7.1 Aggregate: Activity

```python
class Activity:
    id: ActivityId
    tenant_id: TenantId
    company_id: Optional[CompanyId]
    contact_id: Optional[ContactId]
    activity_type: ActivityType
    subject: str
    description: Optional[str]
    performed_by: UserId
    performed_at: datetime
    metadata: dict
    is_auto_generated: bool

    def link_to_company(self, company_id: CompanyId) -> None:
        self.company_id = company_id
        self.register_event(ActivityLinkedToCompany(self.id, company_id))

    def link_to_opportunity(self, opportunity_id: OpportunityId) -> None:
        self.register_event(ActivityLinkedToOpportunity(self.id, opportunity_id))
```

## 7.2 Value Object: ActivityType

```python
class ActivityType(Enum):
    EMAIL_SENT = "email_sent"
    EMAIL_RECEIVED = "email_received"
    CALL_MADE = "call_made"
    CALL_RECEIVED = "call_received"
    MEETING_HELD = "meeting_held"
    NOTE_ADDED = "note_added"
    TASK_COMPLETED = "task_completed"
    STATUS_CHANGE = "status_change"       # Auto-generated from license changes
    SYSTEM_EVENT = "system_event"         # Auto-generated from system
```

---

# 8. Subdomain: Scoring Engine (BC-06)

## 8.1 Aggregate: CompanyScore

```python
class CompanyScore:
    id: CompanyScoreId
    company_id: CompanyId
    score_type: ScoreType
    score: float            # 0.0 to 1.0
    confidence: float       # 0.0 to 1.0
    factors: list[ScoreFactor]
    model_version: str
    computed_at: datetime
    expires_at: datetime

    def is_stale(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def breakdown(self) -> dict[str, float]:
        return {f.name: f.weight for f in self.factors}
```

## 8.2 Value Object: ScoreFactor

```python
@dataclass(frozen=True)
class ScoreFactor:
    name: str
    value: float
    weight: float
    description: str

    def contribution(self) -> float:
        return self.value * self.weight
```

---

# 9. Subdomain: Knowledge Graph (BC-08)

## 9.1 Aggregate: GraphNode

```python
class GraphNode:
    id: GraphNodeId
    node_type: NodeType
    external_id: str       # UUID of the entity in its source context
    label: str
    properties: dict
    created_at: datetime

    def add_edge(self, target: GraphNode, relationship: RelationshipType) -> GraphEdge:
        edge = GraphEdge(
            source=self.id,
            target=target.id,
            relationship=relationship,
            weight=1.0,
            valid_from=datetime.utcnow(),
        )
        self.register_event(GraphEdgeAdded(self.id, target.id, relationship))
        return edge
```

## 9.2 Aggregate: GraphEdge

```python
class GraphEdge:
    id: GraphEdgeId
    source_id: GraphNodeId
    target_id: GraphNodeId
    relationship: RelationshipType
    weight: float
    properties: dict
    valid_from: datetime
    valid_to: Optional[datetime]
    confidence: float

    def is_active(self) -> bool:
        return self.valid_to is None or self.valid_to > datetime.utcnow()

    def deactivate(self) -> None:
        self.valid_to = datetime.utcnow()
        self.register_event(GraphEdgeDeactivated(self.id))
```

## 9.3 Relationship Types

```python
class RelationshipType(Enum):
    OWNS = "owns"                       # Company owns another company
    SUBSIDIARY = "subsidiary"           # Company is a subsidiary
    EMPLOYS = "employs"                 # Company employs contact
    HAS_LICENSE = "has_license"         # Company has a license
    COMPETES_WITH = "competes_with"     # Competitive relationship
    SUPPLIES = "supplies"               # Supplier relationship
    PARTNERS_WITH = "partners_with"     # Partnership
    SAME_GROUP = "same_group"           # Same corporate group
    LOCATED_AT = "located_at"           # Company located at address
    SHARES_DIRECTOR = "shares_director" # Companies share board member
```

---

# 10. Subdomain: AI Platform (BC-09)

## 10.1 Aggregate: AiQuery

```python
class AiQuery:
    id: AiQueryId
    tenant_id: TenantId
    user_id: UserId
    query_text: str
    context: AiContext
    result: Optional[str]
    tokens_used: int
    model: str
    latency_ms: int
    feedback_score: Optional[int]   # 1-5 from user
    created_at: datetime

    def record_result(self, result: str, tokens: int, latency: int) -> None:
        self.result = result
        self.tokens_used = tokens
        self.latency_ms = latency
        self.register_event(AiQueryCompleted(self.id, tokens, latency))

    def rate(self, score: int) -> None:
        if not 1 <= score <= 5:
            raise InvalidScoreError(score)
        self.feedback_score = score
```

## 10.2 Aggregate: AiAgent

```python
class AiAgent:
    id: AiAgentId
    tenant_id: TenantId
    name: str
    agent_type: AgentType
    configuration: dict
    is_active: bool
    last_run_at: Optional[datetime]
    total_runs: int
    success_rate: float

    def execute(self, input_data: dict) -> AgentResult:
        # Agent execution logic delegated to infrastructure
        pass

    def deactivate(self) -> None:
        self.is_active = False
        self.register_event(AgentDeactivated(self.id))
```

---

# 11. Subdomain: Workflow Engine (BC-10)

## 11.1 Aggregate: WorkflowDefinition

```python
class WorkflowDefinition:
    id: WorkflowId
    name: str
    description: Optional[str]
    trigger: WorkflowTrigger
    actions: list[WorkflowAction]
    is_active: bool
    version: int

    def add_action(self, action: WorkflowAction) -> None:
        self.actions.append(action)

    def activate(self) -> None:
        self.is_active = True
        self.register_event(WorkflowActivated(self.id))

    def deactivate(self) -> None:
        self.is_active = False
        self.register_event(WorkflowDeactivated(self.id))
```

## 11.2 Value Object: WorkflowTrigger

```python
@dataclass(frozen=True)
class WorkflowTrigger:
    event_type: str        # Domain event name
    conditions: list[Condition]

    def matches(self, event: DomainEvent) -> bool:
        if event.event_type != self.event_type:
            return False
        return all(c.evaluate(event) for c in self.conditions)
```

## 11.3 Value Object: WorkflowAction

```python
@dataclass
class WorkflowAction:
    action_type: ActionType
    config: dict
    order: int

    class ActionType(Enum):
        SEND_NOTIFICATION = "send_notification"
        SEND_EMAIL = "send_email"
        CREATE_OPPORTUNITY = "create_opportunity"
        UPDATE_FIELD = "update_field"
        ASSIGN_USER = "assign_user"
        CALL_WEBHOOK = "call_webhook"
        TRIGGER_AGENT = "trigger_agent"
```

---

# 12. Domain Events Catalog

## 12.1 Event Schema

Every domain event follows this structure:

```json
{
  "event_id": "uuid",
  "event_type": "company.company_created",
  "event_version": 1,
  "aggregate_id": "uuid",
  "aggregate_type": "Company",
  "tenant_id": "uuid",
  "occurred_at": "2026-06-29T10:00:00Z",
  "data": {},
  "metadata": {
    "correlation_id": "uuid",
    "causation_id": "uuid",
    "user_id": "uuid"
  }
}
```

## 12.2 Event Catalog

### Core Domain Events

| Event | Version | Aggregates | Description |
|-------|---------|------------|-------------|
| `company.created` | 1 | Company | New company ingested or created |
| `company.updated` | 1 | Company | Company field(s) updated |
| `company.status_changed` | 1 | Company | Status transition (e.g., active to expired) |
| `company.merged` | 1 | Company, GoldenRecord | Two companies merged into golden record |
| `company.verified` | 1 | Company | Company data verified by authority |
| `company.scored` | 1 | Company, CompanyScore | New score computed for company |
| `company.dna_generated` | 1 | Company, DnaProfile | DNA profile generated or updated |
| `company.graph_synced` | 1 | Company, GraphNode | Company synced to knowledge graph |

### Identity Events

| Event | Version | Aggregates | Description |
|-------|---------|------------|-------------|
| `tenant.created` | 1 | Tenant | New tenant registered |
| `tenant.activated` | 1 | Tenant | Tenant activated |
| `tenant.deactivated` | 1 | Tenant | Tenant deactivated |
| `user.registered` | 1 | User | New user registered |
| `user.verified` | 1 | User | User email verified |
| `user.role_changed` | 1 | User | User role changed |
| `user.invited` | 1 | User | User invited to tenant |

### CRM Events

| Event | Version | Aggregates | Description |
|-------|---------|------------|-------------|
| `opportunity.created` | 1 | Opportunity | New opportunity created |
| `opportunity.stage_changed` | 1 | Opportunity | Opportunity moved to new stage |
| `opportunity.value_changed` | 1 | Opportunity | Opportunity value updated |
| `opportunity.won` | 1 | Opportunity | Opportunity closed as won |
| `opportunity.lost` | 1 | Opportunity | Opportunity closed as lost |

### Activity Events

| Event | Version | Aggregates | Description |
|-------|---------|------------|-------------|
| `activity.created` | 1 | Activity | New activity recorded |
| `activity.linked` | 1 | Activity | Activity linked to company/opportunity |

### License Events

| Event | Version | Aggregates | Description |
|-------|---------|------------|-------------|
| `license.added` | 1 | License | New license added to company |
| `license.expired` | 1 | License | License passed expiry date |
| `license.renewed` | 1 | License | License renewed |

### Workflow Events

| Event | Version | Aggregates | Description |
|-------|---------|------------|-------------|
| `workflow.triggered` | 1 | WorkflowDefinition | Workflow triggered by event |
| `workflow.completed` | 1 | WorkflowDefinition | Workflow executed successfully |
| `workflow.failed` | 1 | WorkflowDefinition | Workflow execution failed |

### Marketplace Events

| Event | Version | Aggregates | Description |
|-------|---------|------------|-------------|
| `plugin.installed` | 1 | PluginInstallation | Plugin installed in tenant |
| `plugin.uninstalled` | 1 | PluginInstallation | Plugin removed |
| `marketplace.purchase_completed` | 1 | PluginListing | Plugin or data purchased |

---

# 13. Repository Contracts

## 13.1 Repository Pattern

```python
class Repository[T, TId]:
    async def get(self, id: TId) -> T: ...
    async def save(self, aggregate: T) -> None: ...
    async def delete(self, id: TId) -> None: ...
    async def exists(self, id: TId) -> bool: ...
```

## 13.2 Company Repository

```python
class CompanyRepository(Repository[Company, CompanyId]):
    async def get(self, id: CompanyId) -> Company:
        """Returns Company or raises NotFoundError"""

    async def save(self, company: Company) -> None:
        """Persists aggregate and publishes collected domain events"""

    async def delete(self, id: CompanyId) -> None:
        """Soft-deletes company"""

    async def find_by_cr_number(self, tenant_id: TenantId, cr_number: CrNumber) -> Optional[Company]:
        """Returns company matching CR number within tenant"""

    async def find_by_name(self, tenant_id: TenantId, name: str, limit: int = 10) -> list[Company]:
        """Search companies by name (Arabic or English)"""

    async def find_by_city(self, tenant_id: TenantId, city: str, page: int, page_size: int) -> tuple[list[Company], int]:
        """Paginated companies by city"""

    async def find_expiring_licenses(self, tenant_id: TenantId, within_days: int) -> list[Company]:
        """Companies with licenses expiring within N days"""

    async def find_by_status(self, tenant_id: TenantId, status: CompanyStatus) -> list[Company]:
        """Companies with specific status"""
```

## 13.3 Opportunity Repository

```python
class OpportunityRepository(Repository[Opportunity, OpportunityId]):
    async def get(self, id: OpportunityId) -> Opportunity: ...

    async def save(self, opportunity: Opportunity) -> None: ...

    async def find_by_company(self, company_id: CompanyId) -> list[Opportunity]: ...

    async def find_by_pipeline(self, pipeline_id: PipelineId) -> list[Opportunity]: ...

    async def find_by_user(self, user_id: UserId) -> list[Opportunity]: ...

    async def aggregate_by_stage(self, tenant_id: TenantId) -> dict[str, AggregationResult]: ...
```

## 13.4 Activity Repository

```python
class ActivityRepository(Repository[Activity, ActivityId]):
    async def get(self, id: ActivityId) -> Activity: ...

    async def save(self, activity: Activity) -> None: ...

    async def find_by_company(self, company_id: CompanyId, page: int, page_size: int) -> tuple[list[Activity], int]:
        """Paginated activities for a company (timeline view)"""

    async def find_by_user(self, user_id: UserId, page: int, page_size: int) -> tuple[list[Activity], int]: ...

    async def count_by_type(self, tenant_id: TenantId, since: datetime) -> dict[str, int]: ...
```

## 13.5 Domain Event Store

```python
class DomainEventStore:
    async def append(self, event: DomainEvent) -> None:
        """Append event to event store (Kafka topic or DB table)"""

    async def read_stream(self, aggregate_type: str, aggregate_id: str) -> list[DomainEvent]:
        """Read all events for an aggregate (event sourcing)"""

    async def read_all(self, event_type: str, since: datetime, limit: int = 100) -> list[DomainEvent]:
        """Read events by type for rebuilding projections"""
```

---

# 14. Application Services

## 14.1 Application Service Pattern

```python
class ApplicationService:
    """Orchestrates domain logic, repositories, and infrastructure."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def __call__(self, command: Command) -> Result:
        async with self.uow:
            # 1. Load aggregate
            # 2. Execute domain logic
            # 3. Save aggregate (publishes domain events)
            # 4. Return result
            pass
```

## 14.2 Company Application Services

```python
class CompanyApplicationService:
    def __init__(self, repo: CompanyRepository, uow: UnitOfWork):
        self.repo = repo
        self.uow = uow

    async def create_company(self, command: CreateCompanyCommand) -> Company:
        async with self.uow:
            company = Company.create(
                tenant_id=command.tenant_id,
                name_ar=command.name_ar,
                cr_number=CrNumber(command.cr_number),
                city=command.city,
            )
            await self.repo.save(company)
            return company

    async def change_company_status(self, command: ChangeCompanyStatusCommand) -> Company:
        async with self.uow:
            company = await self.repo.get(command.company_id)
            company.change_status(CompanyStatus(command.new_status))
            await self.repo.save(company)
            return company

    async def ingest_companies(self, command: IngestCompaniesCommand) -> IngestResult:
        async with self.uow:
            created = 0
            updated = 0
            for record in command.records:
                existing = await self.repo.find_by_cr_number(command.tenant_id, CrNumber(record["cr_number"]))
                if existing:
                    existing.update_from_source(record, command.source)
                    await self.repo.save(existing)
                    updated += 1
                else:
                    company = Company.create_from_source(record, command.source, command.tenant_id)
                    await self.repo.save(company)
                    created += 1
            return IngestResult(created=created, updated=updated)

    async def merge_companies(self, command: MergeCompaniesCommand) -> Company:
        async with self.uow:
            primary = await self.repo.get(command.primary_id)
            secondary = await self.repo.get(command.secondary_id)
            primary.merge_with(secondary)
            await self.repo.save(primary)
            await self.repo.delete(secondary.id)
            return primary
```

## 14.3 CRM Application Services

```python
class CrmApplicationService:
    def __init__(self, opportunity_repo: OpportunityRepository, uow: UnitOfWork):
        self.opportunity_repo = opportunity_repo
        self.uow = uow

    async def create_opportunity(self, command: CreateOpportunityCommand) -> Opportunity:
        async with self.uow:
            opportunity = Opportunity.create(
                tenant_id=command.tenant_id,
                pipeline_id=command.pipeline_id,
                company_id=command.company_id,
                name=command.name,
                value=Money(command.value),
                assigned_to=command.assigned_to,
            )
            await self.opportunity_repo.save(opportunity)
            return opportunity

    async def move_opportunity(self, command: MoveOpportunityCommand) -> Opportunity:
        async with self.uow:
            opportunity = await self.opportunity_repo.get(command.opportunity_id)
            opportunity.move_to_stage(PipelineStage(command.to_stage_id))
            await self.opportunity_repo.save(opportunity)
            return opportunity
```

---

# 15. Domain Policies

## 15.1 Policy: License Expiry Notification

```yaml
Policy: LicenseExpiryNotificationPolicy
Trigger: Domain time event (daily cron)
Context: Company Intelligence
Description: When a company's license is expiring within 30 days,
  send notification to tenant users.

Rules:
  - For each tenant, find companies with licenses expiring in <=30 days
  - Group by tenant
  - For each tenant, create notification events
  - If expiry <= 7 days, also create workflow trigger
```

## 15.2 Policy: Golden Record Auto-Verification

```yaml
Policy: GoldenRecordAutoVerificationPolicy
Trigger: company.updated
Context: Entity Resolution
Description: When a company's data is confirmed by 3+ sources,
  automatically mark as verified golden record.

Rules:
  - If company.source_ids >= 3
  - AND company.status == CompanyStatus.ACTIVE
  - AND any source is from a government authority
  - THEN mark is_golden_record = True
  - AND set confidence_score = 0.95
```

## 15.3 Policy: New Company Opportunity

```yaml
Policy: NewCompanyOpportunityPolicy
Trigger: company.created
Context: CRM
Description: When a new company matching a saved search is created,
  auto-create an opportunity for assigned users.

Rules:
  - For each tenant, evaluate saved searches against new company
  - If company matches a saved search
  - AND the search has auto-create-opportunity enabled
  - THEN create Opportunity with stage=LEAD
  - AND assign to search owner
```

## 15.4 Policy: Activity Scoring

```yaml
Policy: ActivityScoringPolicy
Trigger: activity.created
Context: Scoring Engine
Description: When a new activity is recorded, recalculate engagement score.

Rules:
  - Recent email = +5 points
  - Recent meeting = +10 points
  - Recent call = +3 points
  - No activity in 30 days = engagement score halved
  - Recalculate every time a new activity is added
```

---

# 16. Specifications

## 16.1 Specification Pattern

```python
class Specification[T]:
    def is_satisfied_by(self, candidate: T) -> bool: ...

    def __and__(self, other: "Specification") -> "Specification":
        return AndSpecification(self, other)

    def __or__(self, other: "Specification") -> "Specification":
        return OrSpecification(self, other)

    def __not__(self) -> "Specification":
        return NotSpecification(self)
```

## 16.2 Key Specifications

```python
class CompanyInCity(Specification[Company]):
    def __init__(self, city: str):
        self.city = city

    def is_satisfied_by(self, company: Company) -> bool:
        return company.city == self.city


class CompanyWithActiveLicenses(Specification[Company]):
    def is_satisfied_by(self, company: Company) -> bool:
        return any(l.is_active() for l in company.licenses)


class CompanyWithExpiredLicenses(Specification[Company]):
    def is_satisfied_by(self, company: Company) -> bool:
        return any(l.is_expired() for l in company.licenses)


class CompanyInIndustry(Specification[Company]):
    def __init__(self, isic_code_prefix: str):
        self.isic_code_prefix = isic_code_prefix

    def is_satisfied_by(self, company: Company) -> bool:
        return company.isic_code and company.isic_code.startswith(self.isic_code_prefix)


class HighConfidenceCompany(Specification[Company]):
    def __init__(self, min_confidence: float = 0.8):
        self.min_confidence = min_confidence

    def is_satisfied_by(self, company: Company) -> bool:
        return company.confidence_score >= self.min_confidence


# Composite example:
# Riyadh companies with expired licenses, high confidence
spec = CompanyInCity("الرياض") & CompanyWithExpiredLicenses() & HighConfidenceCompany(0.9)
matching = [c for c in companies if spec.is_satisfied_by(c)]
```

---

# 17. Architecture Decision Records

## ADR-DDD-01: Aggregates are Consistency Boundaries

**Status:** Accepted

**Context:** Multiple entities need to be updated together (e.g., Company + Licenses).

**Decision:** Aggregates define transactional consistency boundaries. Changes to an aggregate are atomic. References between aggregates use IDs, not object references.

**Consequences:**
- Company aggregates include owned entities (Branches, Licenses, Contacts)
- Changes across aggregates use eventual consistency via domain events
- Aggregate size must be kept manageable

## ADR-DDD-02: Event Sourcing for Entity Resolution Only

**Status:** Accepted

**Context:** Entity resolution needs full audit trail of merge/split decisions.

**Decision:** Entity Resolution context uses event sourcing. All other contexts use standard ORM with audit logging.

**Consequences:**
- Entity Resolution rebuilds golden records from event stream
- All other contexts use PostgreSQL with `audit_log` table
- Simpler development for non-core contexts

## ADR-DDD-03: Domain Events via Kafka

**Status:** Accepted

**Context:** Multiple contexts need to react to changes in other contexts.

**Decision:** All domain events are published to Kafka topics. Each context has its own topic. Events are Avro-serialized with schema registry.

**Consequences:**
- Each context can consume events from other contexts
- Event schema evolution managed by Schema Registry
- At-least-once delivery guarantees

## ADR-DDD-04: Read Models Separated from Write Models

**Status:** Accepted

**Context:** Application queries (search, list) have different requirements than commands (create, update).

**Decision:** Use CQRS pattern. Write models are domain aggregates. Read models are optimized tables/views for queries.

**Consequences:**
- Write models optimized for consistency
- Read models optimized for performance
- Eventual consistency between write and read models acceptable (sub-second)

---

*End of SalesOS Domain Driven Design v1.0*
