-- SalesOS AI Foundation — Episodic Memory & Cost Tracking
-- Migration 007: Part of Wave C (WO-003)

-- Episodic Memory Store
CREATE TABLE IF NOT EXISTS episodic_memory (
    id              VARCHAR(64) PRIMARY KEY,
    agent_id        VARCHAR(255) NOT NULL,
    scope           VARCHAR(50) NOT NULL,
    type            VARCHAR(50) NOT NULL DEFAULT 'message',
    content         TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ttl_seconds     INTEGER,
    session_id      VARCHAR(255),
    conversation_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS ix_episodic_memory_agent ON episodic_memory(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_episodic_memory_scope ON episodic_memory(scope, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_episodic_memory_session ON episodic_memory(session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_episodic_memory_conversation ON episodic_memory(conversation_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_episodic_memory_ttl_expires_at ON episodic_memory((timestamp + make_interval(secs => ttl_seconds))) WHERE ttl_seconds IS NOT NULL;

-- LLM Cost Tracking
CREATE TABLE IF NOT EXISTS llm_cost_tracking (
    id                VARCHAR(64) PRIMARY KEY,
    provider          VARCHAR(50) NOT NULL,
    model             VARCHAR(100) NOT NULL,
    prompt_tokens     INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens      INTEGER NOT NULL DEFAULT 0,
    cost              NUMERIC(12, 8) NOT NULL DEFAULT 0,
    latency_ms        NUMERIC(10, 2) NOT NULL DEFAULT 0,
    operation         VARCHAR(50) NOT NULL DEFAULT 'completion',
    tenant_id         VARCHAR(64),
    user_id           VARCHAR(64),
    success           BOOLEAN NOT NULL DEFAULT TRUE,
    error             TEXT,
    retry_count       INTEGER NOT NULL DEFAULT 0,
    timestamp         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_llm_cost_tenant ON llm_cost_tracking(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_llm_cost_model ON llm_cost_tracking(model, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_llm_cost_provider ON llm_cost_tracking(provider, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_llm_cost_timestamp ON llm_cost_tracking(timestamp DESC);
