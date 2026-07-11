"""Action Engine REST API."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import verify_token

router = APIRouter(prefix="/api/v1/actions", tags=["Action Engine"], dependencies=[Depends(verify_token)])


class ExecuteRequest(BaseModel):
    action_id: str
    user_id: str = ""
    tenant_id: str = ""
    input: dict = {}


@router.get("")
async def list_actions(category: str = ""):
    """List all registered actions."""
    from runtime.action_engine import ActionRegistry
    from app.main import app
    registry = app.state.action_registry
    actions = registry.all(category or None)
    return [a.to_dict() for a in actions]


@router.get("/{action_id}")
async def get_action(action_id: str):
    """Get an action definition."""
    from runtime.action_engine import ActionRegistry
    from app.main import app
    action = app.state.action_registry.get(action_id)
    if not action:
        raise HTTPException(404, f"Action '{action_id}' not found")
    return action.to_dict()


@router.post("/execute")
async def execute_action(req: ExecuteRequest):
    """Execute an action (sync)."""
    from app.main import app
    try:
        execution = await app.state.action_registry.execute(
            req.action_id, req.user_id, req.tenant_id, req.input
        )
        return execution.to_dict()
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Get an action execution result."""
    from app.main import app
    execution = app.state.action_registry.get_execution(execution_id)
    if not execution:
        raise HTTPException(404, "Execution not found")
    return execution.to_dict()
