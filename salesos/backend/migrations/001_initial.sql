-- SalesOS v1.0 — Initial Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Tenants (organizations)
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name_ar VARCHAR(255),
  name_en VARCHAR(255),
  role VARCHAR(20) NOT NULL DEFAULT 'sales', -- admin, sales, marketing, executive, legal
  active BOOLEAN DEFAULT true,
  last_login TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Companies
CREATE TABLE companies (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  name_ar VARCHAR(500),
  name_en VARCHAR(500),
  cr_number VARCHAR(20) UNIQUE,
  city VARCHAR(100),
  region VARCHAR(100),
  status VARCHAR(50) DEFAULT 'نشط',
  industry VARCHAR(100),
  business_model VARCHAR(20),
  employees INTEGER,
  founded_year INTEGER,
  website VARCHAR(500),
  phone VARCHAR(50),
  embedding vector(768),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_companies_tenant ON companies(tenant_id);
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_fts ON companies USING GIN(
  to_tsvector('arabic', coalesce(name_ar,'') || ' ' || coalesce(name_en,'') || ' ' || coalesce(industry,''))
);

-- Company Intelligence (cache)
CREATE TABLE company_intelligence (
  company_id UUID PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
  dna JSONB,
  ai_recommendation JSONB,
  buying_journey JSONB,
  golden_record JSONB,
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '5 minutes'
);

-- Decision Makers
CREATE TABLE decision_makers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name VARCHAR(255),
  role VARCHAR(255),
  department VARCHAR(255),
  influence VARCHAR(10) CHECK (influence IN ('low','medium','high')),
  connected BOOLEAN DEFAULT false,
  email VARCHAR(255),
  phone VARCHAR(50),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_dm_company ON decision_makers(company_id);

-- Signals
CREATE TABLE signals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  type VARCHAR(20) NOT NULL, -- hiring, expansion, partnership, contract, regulation, market, financial, news
  title VARCHAR(500) NOT NULL,
  description TEXT,
  source VARCHAR(255),
  severity VARCHAR(10) CHECK (severity IN ('low','medium','high','critical')),
  ai_confidence DECIMAL(3,2),
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_signals_company ON signals(company_id);
CREATE INDEX idx_signals_severity ON signals(severity);
CREATE INDEX idx_signals_time ON signals(timestamp DESC);

-- Timeline Events
CREATE TABLE timeline_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
  type VARCHAR(20) NOT NULL, -- signal, news, government, email, meeting, crm, document, license, hiring, funding, ai
  summary TEXT NOT NULL,
  detail TEXT,
  source VARCHAR(255),
  confidence DECIMAL(3,2),
  ai_highlighted BOOLEAN DEFAULT false,
  date TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_timeline_company ON timeline_events(company_id);
CREATE INDEX idx_timeline_date ON timeline_events(date DESC);

-- Government Records
CREATE TABLE government_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  type VARCHAR(20) NOT NULL, -- cr, municipality, zakat, misa, tender, license, violation
  title VARCHAR(500) NOT NULL,
  status VARCHAR(20) CHECK (status IN ('active','expired','pending','violation')),
  issue_date DATE,
  expiry_date DATE,
  confidence DECIMAL(3,2),
  source VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_gov_company ON government_records(company_id);
CREATE INDEX idx_gov_expiry ON government_records(expiry_date);

-- Documents
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  title VARCHAR(500) NOT NULL,
  type VARCHAR(20) NOT NULL, -- contract, pdf, government, report, legal
  file_url TEXT,
  ai_summary TEXT,
  confidence DECIMAL(3,2),
  date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_docs_company ON documents(company_id);

-- Opportunities
CREATE TABLE opportunities (
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
CREATE INDEX idx_opp_tenant ON opportunities(tenant_id);
CREATE INDEX idx_opp_company ON opportunities(company_id);
CREATE INDEX idx_opp_stage ON opportunities(stage);

CREATE TABLE opportunity_notes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  author_id UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
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
CREATE INDEX idx_tasks_tenant ON tasks(tenant_id);
CREATE INDEX idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX idx_tasks_priority ON tasks(priority) WHERE NOT completed;

-- Meetings
CREATE TABLE meetings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID REFERENCES companies(id),
  title VARCHAR(500) NOT NULL,
  date TIMESTAMPTZ NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Search History
CREATE TABLE search_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id),
  query_text TEXT NOT NULL,
  result_count INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_search_user ON search_history(user_id);
CREATE INDEX idx_search_time ON search_history(created_at DESC);
