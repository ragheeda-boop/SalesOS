-- SalesOS v0.2 — Ensure opportunities & tasks tables exist (idempotent)

CREATE TABLE IF NOT EXISTS opportunities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  company_id UUID REFERENCES companies(id),
  title VARCHAR(500) NOT NULL,
  stage VARCHAR(20) NOT NULL DEFAULT 'identified' CHECK (stage IN ('identified','qualifying','developing','proposing','negotiating','closing','won','lost')),
  estimated_value DECIMAL(15,2),
  confidence DECIMAL(3,2),
  win_probability DECIMAL(3,2),
  source VARCHAR(20) DEFAULT 'manual',
  source_action_id VARCHAR(100),
  buying_intent DECIMAL(3,2),
  relationship_strength DECIMAL(3,2),
  risk_level VARCHAR(10) CHECK (risk_level IN ('low','medium','high')),
  assignee_id UUID REFERENCES users(id),
  expected_close_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  stage_changed_at TIMESTAMPTZ,
  last_activity_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_opp_tenant ON opportunities(tenant_id);
CREATE INDEX IF NOT EXISTS idx_opp_company ON opportunities(company_id);
CREATE INDEX IF NOT EXISTS idx_opp_stage ON opportunities(stage);

CREATE TABLE IF NOT EXISTS opportunity_notes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  author_id UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  company_id UUID REFERENCES companies(id),
  title VARCHAR(500) NOT NULL,
  description TEXT,
  priority VARCHAR(10) CHECK (priority IN ('critical','high','medium','low')),
  source VARCHAR(20) NOT NULL DEFAULT 'manual',
  source_entity_id VARCHAR(100),
  assignee_id UUID REFERENCES users(id),
  due_date DATE,
  completed BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_tenant ON tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority) WHERE NOT completed;
