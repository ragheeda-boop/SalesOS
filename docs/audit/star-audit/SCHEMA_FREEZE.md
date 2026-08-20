# Schema Freeze — Agent Runtime

**Status:** ACCEPTED
**Accepted:** 2026-08-09
**Review:** Cross-artifact consistency verified
**Phase:** P1

---

## Phase 1 Tables (MUST BUILD)

### agent_tasks

```sql
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Task identity
    kind VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,

    -- State machine
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','CLAIMED','RUNNING','REQUIRES_APPROVAL',
                          'COMPLETED','FAILED','EXHAUSTED')),
    completion_reason VARCHAR(30)
        CHECK (completion_reason IN ('SUCCESS','PARTIAL_BUDGET','PARTIAL_DATA',
                                      'NO_ACTION_REQUIRED')),

    -- Scheduling
    priority INTEGER DEFAULT 0,
    due_at TIMESTAMPTZ DEFAULT NOW(),

    -- Budget
    budget INTEGER DEFAULT 4,
    max_attempts INTEGER DEFAULT 3,
    attempts INTEGER DEFAULT 0,

    -- Lease + fencing
    lease_generation INTEGER DEFAULT 0,
    leased_until TIMESTAMPTZ,
    leased_by VARCHAR(100),

    -- Execution tracking
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    outcome TEXT,
    session_id VARCHAR(255),

    -- Input/output
    input_data JSONB DEFAULT '{}',

    -- Idempotency
    idempotency_key VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agent_tasks_dispatch
    ON agent_tasks (tenant_id, status, due_at)
    WHERE status = 'PENDING';

CREATE INDEX idx_agent_tasks_lease
    ON agent_tasks (tenant_id, status, leased_until)
    WHERE status IN ('CLAIMED', 'RUNNING');

CREATE INDEX idx_agent_tasks_entity
    ON agent_tasks (tenant_id, entity_type, entity_id, kind);

-- Constraints (applied in app layer, enforced by unique index)
CREATE UNIQUE INDEX uq_agent_tasks_idempotency
    ON agent_tasks (tenant_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- RLS
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tasks FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_agent_tasks ON agent_tasks
    FOR ALL
    USING (tenant_id::text = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));
```

### agent_runs

```sql
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES agent_tasks(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Agent identity
    agent_type VARCHAR(100) NOT NULL,

    -- Run state
    status VARCHAR(20) DEFAULT 'RUNNING'
        CHECK (status IN ('RUNNING','COMPLETED','FAILED','CANCELLED')),

    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Cost tracking (source of truth for budget)
    budget_spent INTEGER DEFAULT 0,
    input_tokens BIGINT DEFAULT 0,
    output_tokens BIGINT DEFAULT 0,
    cost_usd DECIMAL(12,6) DEFAULT 0,

    -- Results
    result_summary TEXT,
    result_data JSONB DEFAULT '{}',
    session_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_agent_runs_task ON agent_runs (task_id);
CREATE INDEX idx_agent_runs_tenant ON agent_runs (tenant_id);

CREATE UNIQUE INDEX uq_agent_runs_active
    ON agent_runs (task_id)
    WHERE status = 'RUNNING';

ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_agent_runs ON agent_runs
    FOR ALL
    USING (tenant_id::text = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));
```

### agent_actions

```sql
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES agent_runs(id),
    task_id UUID NOT NULL REFERENCES agent_tasks(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- Action classification
    action_type VARCHAR(20) NOT NULL
        CHECK (action_type IN ('READ','WRITE','CREATE','UPDATE','DELETE','SCHEDULE')),
    target_entity VARCHAR(100) NOT NULL,
    target_id UUID,
    payload JSONB DEFAULT '{}',

    -- Execution result
    status VARCHAR(20) DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','EXECUTED','FAILED','REJECTED')),

    -- Idempotency (READ=NULL, WRITE/CREATE/UPDATE/DELETE/SCHEDULE=REQUIRED)
    idempotency_key VARCHAR(255),

    -- Governance
    pdp_result VARCHAR(20),
    approval_id UUID,

    -- Timing
    executed_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX uq_agent_actions_idempotency
    ON agent_actions (tenant_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

ALTER TABLE agent_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_actions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_agent_actions ON agent_actions
    FOR ALL
    USING (tenant_id::text = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));
```

---

## Phase 2 Tables (SHOULD BUILD)

### evidence_records

```sql
CREATE TABLE evidence_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES agent_runs(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    evidence_kind VARCHAR(100) NOT NULL,
    detail TEXT NOT NULL,
    source_url TEXT,
    source_type VARCHAR(50),
    observed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE evidence_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_records FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_evidence ON evidence_records
    FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true));
```

### canonical_facts

```sql
CREATE TABLE canonical_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    field VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    band VARCHAR(20) NOT NULL CHECK (band IN ('VERIFIED','PROBABLE','POSSIBLE')),
    score DECIMAL(5,4) NOT NULL,
    status VARCHAR(20) DEFAULT 'PROPOSED'
        CHECK (status IN ('PROPOSED','APPLIED','DISMISSED','SUPERSEDED')),
    run_id UUID REFERENCES agent_runs(id),
    decided_by UUID REFERENCES users(id),
    decided_at TIMESTAMPTZ,
    superseded_by UUID REFERENCES canonical_facts(id),
    evidence_snapshot JSONB,  -- immutable audit copy, NOT source of truth
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_canonical_facts_entity
    ON canonical_facts (tenant_id, entity_type, entity_id, field);

CREATE UNIQUE INDEX uq_canonical_facts_active
    ON canonical_facts (tenant_id, entity_type, entity_id, field)
    WHERE status = 'APPLIED';

ALTER TABLE canonical_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE canonical_facts FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_facts ON canonical_facts
    FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true));
```

### fact_evidence

```sql
CREATE TABLE fact_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fact_id UUID NOT NULL REFERENCES canonical_facts(id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES evidence_records(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fact_id, evidence_id)
);
```

---

## Phase 3 Tables (SHOULD BUILD)

### approval_requests

```sql
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    field VARCHAR(100) NOT NULL,
    proposed_value TEXT NOT NULL,
    current_value TEXT,
    evidence_score DECIMAL(5,4) NOT NULL,
    band VARCHAR(20) NOT NULL,
    run_id UUID REFERENCES agent_runs(id),
    status VARCHAR(20) DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','APPROVED','DISMISSED')),
    decided_by UUID REFERENCES users(id),
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_approvals ON approval_requests
    FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true));
```

### agent_capabilities

```sql
CREATE TABLE agent_capabilities (
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    capability_name VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    PRIMARY KEY (tenant_id, capability_name)
);
```

---

## Execution Identity Model

| Entity | Purpose | Constancy |
|--------|---------|:---------:|
| `agent_tasks.id` | Logical task identity | Constant across retries and approval |
| `agent_runs.id` | Execution identity | NEW on retry; SAME on approval resume |
| `lease_generation` | Worker ownership identity | NEW on every claim |

---

## Constraint Summary

| Constraint | Table | Type |
|-----------|-------|------|
| `UNIQUE (tenant_id, idempotency_key) WHERE NOT NULL` | `agent_tasks` | Partial unique index |
| `UNIQUE (tenant_id, idempotency_key) WHERE NOT NULL` | `agent_actions` | Partial unique index |
| `UNIQUE (task_id) WHERE status = 'RUNNING'` | `agent_runs` | Partial unique index |
| `UNIQUE (tenant_id, entity_type, entity_id, field) WHERE status = 'APPLIED'` | `canonical_facts` | Partial unique index |
| `UNIQUE (fact_id, evidence_id)` | `fact_evidence` | Standard unique |
| `PRIMARY KEY (tenant_id, capability_name)` | `agent_capabilities` | Composite PK |
