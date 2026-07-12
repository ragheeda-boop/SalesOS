from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session

from .signup_service import SignupService

router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    company_name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = Field(None, pattern=r"^\+?[0-9\s\-()]{7,20}$")


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
    service: SignupService = Depends(get_service),
):
    try:
        result = await service.signup(
            email=body.email,
            password=body.password,
            company_name=body.company_name,
            phone=body.phone,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "message": "Account created. Please verify your email.",
        "user_id": result["user_id"],
        "tenant_id": result["tenant_id"],
        "email": result["email"],
    }


@router.get("/auth/verify-email/{token}")
async def verify_email(
    token: str,
    service: SignupService = Depends(get_service),
):
    try:
        result = await service.verify_email(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/auth/resend-verification")
async def resend_verification(
    body: ResendVerificationRequest,
    service: SignupService = Depends(get_service),
):
    return await service.resend_verification(body.email)
