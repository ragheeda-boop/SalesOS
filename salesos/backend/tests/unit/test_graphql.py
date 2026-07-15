"""Tests for the GraphQL API layer — schema validation, endpoint health, query/mutation structure."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.modules.identity.service import create_access_token


@pytest.fixture
def graphql_client():
    transport = ASGITransport(app=app)
    token = create_access_token("test-user", "test-tenant")
    return AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={
            "Authorization": f"Bearer {token}",
            "x-tenant-id": "test-tenant",
        },
    )


@pytest.mark.asyncio
async def test_graphql_schema_introspection(graphql_client: AsyncClient):
    """Verify the GraphQL endpoint responds with a valid schema on introspection."""
    query = """
    query IntrospectionQuery {
        __schema {
            queryType { name }
            mutationType { name }
            types { name kind }
        }
    }
    """
    response = await graphql_client.post(
        "/graphql",
        json={"query": query},
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["__schema"]["queryType"]["name"] == "Query"
    assert data["data"]["__schema"]["mutationType"]["name"] == "Mutation"


@pytest.mark.asyncio
async def test_graphql_company_query_exists(graphql_client: AsyncClient):
    """Verify the company query is defined in the schema."""
    query = """
    query {
        __type(name: "Query") {
            fields {
                name
                description
            }
        }
    }
    """
    response = await graphql_client.post(
        "/graphql",
        json={"query": query},
    )
    assert response.status_code == 200
    data = response.json()
    fields = {f["name"]: f for f in data["data"]["__type"]["fields"]}
    assert "company" in fields
    assert "search" in fields
    assert "opportunities" in fields
    assert "pipeline" in fields


@pytest.mark.asyncio
async def test_graphql_mutation_types_exist(graphql_client: AsyncClient):
    """Verify mutations are defined in the schema."""
    query = """
    query {
        __type(name: "Mutation") {
            fields {
                name
                description
            }
        }
    }
    """
    response = await graphql_client.post(
        "/graphql",
        json={"query": query},
    )
    assert response.status_code == 200
    data = response.json()
    fields = {f["name"]: f for f in data["data"]["__type"]["fields"]}
    assert "createOpportunity" in fields
    assert "updateCompany" in fields
    assert "enrichCompany" in fields


@pytest.mark.asyncio
async def test_graphql_type_definitions(graphql_client: AsyncClient):
    """Verify key GraphQL types are defined in the schema."""
    query = """
    query {
        __type(name: "CompanyType") {
            name
            fields { name type { name kind } }
        }
    }
    """
    response = await graphql_client.post(
        "/graphql",
        json={"query": query},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["__type"]["name"] == "CompanyType"
    field_names = {f["name"] for f in data["data"]["__type"]["fields"]}
    assert "id" in field_names
    assert "nameAr" in field_names
    assert "crNumber" in field_names


@pytest.mark.asyncio
async def test_graphql_company_query_not_found(graphql_client: AsyncClient):
    """Query for a non-existent company returns null (no error)."""
    query = """
    query GetCompany($id: String!) {
        company(companyId: $id) {
            id
            nameAr
            crNumber
        }
    }
    """
    response = await graphql_client.post(
        "/graphql",
        json={"query": query, "variables": {"id": "00000000-0000-0000-0000-000000000000"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["company"] is None


@pytest.mark.asyncio
async def test_graphql_opportunities_query(graphql_client: AsyncClient):
    """Query opportunities returns data or errors gracefully (no crash)."""
    query = """
    query ListOpportunities {
        opportunities {
            id
            name
            stage
            value
        }
    }
    """
    response = await graphql_client.post(
        "/graphql",
        json={"query": query},
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    # May return empty list or error — either is fine as long as no crash


@pytest.mark.asyncio
async def test_graphql_schema_sdl(graphql_client: AsyncClient):
    """Full SDL output is valid and contains expected types."""
    query = """
    query {
        __schema {
            types {
                name
                kind
            }
        }
    }
    """
    response = await graphql_client.post(
        "/graphql",
        json={"query": query},
    )
    assert response.status_code == 200
    data = response.json()
    type_names = {t["name"] for t in data["data"]["__schema"]["types"]}
    assert "CompanyType" in type_names
    assert "OpportunityType" in type_names
    assert "SearchResultType" in type_names
    assert "PipelineSummaryType" in type_names
    assert "CreateOpportunityInput" in type_names
    assert "CompanyUpdateInput" in type_names
    assert "EnrichmentResultType" in type_names
