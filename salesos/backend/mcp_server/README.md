# SalesOS MCP Server

Model Context Protocol (MCP) server that enables AI agents (Claude Desktop, Cursor, etc.) to interact with SalesOS data through tools and resources.

## Architecture

```
AI Agent (Claude Desktop / Cursor)  ←→  MCP (stdio)  ←→  SalesOS API  ←→  PostgreSQL + Neo4j
                           ↕
                      FastAPI SSE
```

## Quick Start

### 1. Install dependencies

```bash
cd backend
pip install mcp httpx
```

### 2. Set environment variables

```bash
export MCP_API_KEY="your-mcp-api-key"
# Also set standard SalesOS env vars:
export POSTGRES_PASSWORD="..."
export JWT_SECRET_KEY="..."
export NEO4J_PASSWORD="..."
export DATABASE_URL="postgresql+asyncpg://..."
```

### 3. Run the server

**Stdio transport (for AI agents):**

```bash
python -m mcp_server.server stdio
```

**SSE transport (for web):**

```bash
python -m mcp_server.server sse
```

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "salesos": {
      "command": "python",
      "args": ["-m", "mcp_server.server", "stdio"],
      "env": {
        "MCP_API_KEY": "your-mcp-api-key",
        "POSTGRES_PASSWORD": "...",
        "JWT_SECRET_KEY": "...",
        "NEO4J_PASSWORD": "..."
      }
    }
  }
}
```

## Available Tools

### Company Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `search_companies` | Search companies by name/industry | `api_key`, `query`, `limit` (default 10) |
| `get_company` | Get company details + health score | `api_key`, `company_id` |
| `get_company_pipeline` | Get pipeline for a company | `api_key`, `company_id` |

### Pipeline Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_pipeline_summary` | Pipeline overview (value, stages, win rate) | `api_key` |
| `get_opportunity` | Get opportunity details | `api_key`, `opportunity_id` |

### Decision Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `evaluate_decision` | Evaluate next-best-action (NBA) | `api_key`, `company_id`, `context` |
| `get_decision_history` | Recent decisions | `api_key`, `company_id`, `limit` (default 10) |

### Search Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `search` | Full-text + semantic hybrid search | `api_key`, `query`, `domain` (default "all") |
| `search_employees` | Employee intelligence search | `api_key`, `query`, `company_id` (optional) |

### Analytics Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_revenue_analytics` | Revenue KPIs | `api_key`, `timeframe` (default "monthly") |
| `get_market_intelligence` | Market trends by industry | `api_key`, `industry` (optional) |

### Workflow Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `list_workflows` | List automation workflows | `api_key`, `status` (optional) |
| `execute_workflow` | Execute a workflow | `api_key`, `workflow_id`, `context` (dict) |

## Available Resources

| URI | Description |
|-----|-------------|
| `salesos://pipeline/summary` | Current pipeline overview |
| `salesos://metrics/kpi` | Current KPI metrics |
| `salesos://search/recent` | Recent search activity |
| `salesos://metrics/revenue` | Revenue metrics |
| `salesos://workflows/active` | Active automation workflows |

## Example Queries (for AI agents)

- "Search for companies named 'اللطيف'"
- "What's the current pipeline summary?"
- "Evaluate next best action for company X"
- "Get revenue analytics for this quarter"
- "Search for employees working at company Y"
- "Execute workflow Z with context {'company_id': '...'}"

## Development

### Running tests

```bash
cd backend
$env:POSTGRES_PASSWORD="testpass"; $env:JWT_SECRET="test-jwt-secret-for-testing-only-32chars!!"; $env:NEO4J_PASSWORD="test"; $env:REDIS_URL="redis://localhost:6379"; $env:DATABASE_URL="sqlite:///./test.db"
python -m pytest tests/unit/test_mcp_server.py -q --tb=short
```
