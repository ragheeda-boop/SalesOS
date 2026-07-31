from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import safe_error_detail
from app.common.rate_limit import check_rate_limit_by_key
from app.dependencies import get_db_session

from .schemas import validate_password_strength
from .signup_service import SignupService

router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    company_name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = Field(None, pattern=r"^\+?[0-9\s\-()]{7,20}$")

    @model_validator(mode="after")
    def validate_password(self) -> "SignupRequest":
        validate_password_strength(self.password)
        return self


class ResendVerificationRequest(BaseModel):
    email: EmailStr


def get_service(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> SignupService:
    return SignupService(
        db=db,
        event_bus=getattr(request.app.state, "event_bus", None),
        logger=getattr(request.app.state, "logger", None),
    )


@router.post("/auth/signup", status_code=201)
async def signup(
    body: SignupRequest,
    request: Request,
    service: SignupService = Depends(get_service),
):
    await check_rate_limit_by_key(f"signup:{body.email.lower().strip()}", limit=3, window=900)
    try:
        result = await service.signup(
            email=body.email,
            password=body.password,
            company_name=body.company_name,
            phone=body.phone,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Invalid request")) from e
    return {
        "message": "Account created. Please verify your email.",
        "user_id": result["user_id"],
        "tenant_id": result["tenant_id"],
        "email": result["email"],
    }


@router.get("/auth/verify-email/{token}")
async def verify_email(
    token: str,
    request: Request,
    service: SignupService = Depends(get_service),
):
    await check_rate_limit_by_key(f"verify-email:{request.client.host}", limit=10, window=900)
    try:
        result = await service.verify_email(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Invalid request")) from e
    return result


@router.post("/auth/resend-verification")
async def resend_verification(
    body: ResendVerificationRequest,
    service: SignupService = Depends(get_service),
):
    await check_rate_limit_by_key(
        f"resend-verify:{body.email.lower().strip()}", limit=3, window=900
    )
    return await service.resend_verification(body.email)
