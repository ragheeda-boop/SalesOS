from typing import Any

import strawberry
from fastapi import HTTPException, Request
from strawberry.extensions import QueryDepthLimiter, MaxTokensLimiter
from strawberry.fastapi import GraphQLRouter

from app.config import settings
from app.graphql.query import Query
from app.graphql.mutation import Mutation
from app.modules.identity.service import decode_access_token


async def get_context(request: Request) -> dict[str, Any]:
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = decode_access_token(auth.replace("Bearer ", ""))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    tenant_id = request.headers.get("x-tenant-id", "")
    token_tenant = payload.get("tenant_id")
    if token_tenant and str(token_tenant) != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    return {
        "request": request,
        "tenant_id": tenant_id,
        "user_id": payload.get("sub", ""),
        "user_role": payload.get("role", "user"),
    }


extensions = [
    lambda: QueryDepthLimiter(max_depth=8),
    lambda: MaxTokensLimiter(max_token_count=500),
]

schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=extensions)

graphql_ide_setting = None if settings.env == "production" else "graphiql"

graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphql_ide=graphql_ide_setting,
)
