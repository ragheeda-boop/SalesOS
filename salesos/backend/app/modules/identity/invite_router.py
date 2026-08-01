from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import safe_error_detail
from app.common.rate_limit import check_rate_limit_by_key
from app.dependencies import (
    get_current_tenant_id,
    get_current_user_id,
    get_db_session,
    require_role_dep,
)

from .invite_service import InviteService
from .schemas import validate_password_strength

router = APIRouter()


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="user", pattern=r"^(admin|manager|user)$")


class AcceptInviteRequest(BaseModel):
    password: str = Field(..., min_length=12, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_password(self) -> "AcceptInviteRequest":
        validate_password_strength(self.password)
        return self


def get_service(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> InviteService:
    return InviteService(
        db=db,
        event_bus=getattr(request.app.state, "event_bus", None),
        logger=getattr(request.app.state, "logger", None),
    )


@router.post("/auth/invite", status_code=201)
async def invite_user(
    body: InviteRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    service: InviteService = Depends(get_service),
    _: bool = Depends(require_role_dep("admin")),
):
    try:
        result = await service.create_invite(
            email=body.email,
            role=body.role,
            invited_by=user_id,
            tenant_id=tenant_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=safe_error_detail(e, "Invalid invitation")
        ) from e  # noqa: E501
    return {
        "message": f"Invitation sent to {body.email}",
        "email": result["email"],
        "role": result["role"],
        "expires_at": result["expires_at"].isoformat(),
    }


@router.get("/auth/accept-invite/{token}")
async def validate_invite(
    token: str,
    service: InviteService = Depends(get_service),
):
    try:
        result = await service.validate_invite(token)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=safe_error_detail(e, "Invalid invitation")
        ) from e  # noqa: E501
    return result


@router.post("/auth/accept-invite/{token}")
async def accept_invite(
    token: str,
    body: AcceptInviteRequest,
    request: Request,
    service: InviteService = Depends(get_service),
):
    client_host = request.client.host if request.client else "unknown"
    await check_rate_limit_by_key(f"accept-invite:{client_host}", limit=5, window=900)
    try:
        result = await service.accept_invite(
            token=token,
            password=body.password,
            full_name=body.full_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=safe_error_detail(e, "Invalid invitation")
        ) from e  # noqa: E501
    return {
        "message": "Invitation accepted successfully",
        "user_id": result["user_id"],
        "tenant_id": result["tenant_id"],
        "email": result["email"],
        "role": result["role"],
    }
