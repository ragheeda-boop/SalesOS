# GraphQL API

> **واجهة GraphQL — استعلامات مرنة وفعالة**
> Endpoint: `https://api.salesos.sa/graphql`

---

## Overview

SalesOS provides a GraphQL endpoint for flexible data queries. The schema is designed with Apollo Federation in mind, allowing future microservice decomposition.

**Authentication:** Standard JWT via `Authorization: Bearer <token>` header.

---

## Schema

### Core Types

```graphql
type Company {
  id: ID!
  name: String!
  domain: String
  industry: String
  size: String
  stage: String
  pipeline: Pipeline
  opportunities: [Opportunity!]
  createdAt: String
  updatedAt: String
}

type Opportunity {
  id: ID!
  name: String!
  value: Float
  stage: String
  probability: Int
  owner: User
  company: Company
  expectedCloseDate: String
  createdAt: String
}

type Pipeline {
  totalValue: Float
  weightedValue: Float
  dealCount: Int
  winRate: Float
  stages: [PipelineStage!]
}

type PipelineStage {
  name: String!
  value: Float
  count: Int
}

type Analytics {
  revenue: Float
  pipelineValue: Float
  conversionRate: Float
  forecastAccuracy: Float
  revenueTrend: [DataPoint!]
  pipelineStages: [DataPoint!]
}

type DataPoint {
  label: String!
  value: Float
}

type User {
  id: ID!
  name: String
  email: String
  role: String
}

type Activity {
  id: ID!
  type: String
  description: String
  timestamp: String
  userId: String
}
```

### Queries

```graphql
type Query {
  companies(limit: Int, offset: Int, filter: CompanyFilter): [Company!]
  company(id: ID!): Company
  opportunities(limit: Int, offset: Int, stage: String): [Opportunity!]
  opportunity(id: ID!): Opportunity
  pipelineHealth: Pipeline
  analytics: Analytics
  search(query: String!, limit: Int): SearchResult
}

input CompanyFilter {
  industry: String
  stage: String
  search: String
}

type SearchResult {
  companies: [Company!]
  opportunities: [Opportunity!]
  total: Int
}
```

### Mutations

```graphql
type Mutation {
  createCompany(input: CompanyInput!): Company
  updateCompany(id: ID!, input: CompanyInput!): Company
  createOpportunity(input: OpportunityInput!): Opportunity
  updateOpportunity(id: ID!, input: OpportunityInput!): Opportunity
}

input CompanyInput {
  name: String!
  domain: String
  industry: String
  size: String
}

input OpportunityInput {
  name: String!
  value: Float
  stage: String
  probability: Int
  companyId: ID!
  expectedCloseDate: String
}
```

---

## Example Queries

### Get dashboard analytics

```graphql
query GetAnalytics {
  analytics {
    revenue
    pipelineValue
    conversionRate
    forecastAccuracy
    revenueTrend { label value }
    pipelineStages { label value }
  }
}
```

### Get company with opportunities

```graphql
query GetCompanyWithDeals($id: ID!) {
  company(id: $id) {
    name
    industry
    pipeline { totalValue dealCount }
    opportunities {
      name
      value
      stage
      probability
    }
  }
}
```

---

## Rate Limiting

- Standard: 30 requests/min
- Enterprise: 60 requests/min

---

## Related

| Resource | Link |
|----------|------|
| REST API Overview | [overview.md](overview.md) |
| API Portal | [README.md](README.md) |
