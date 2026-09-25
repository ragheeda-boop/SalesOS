"""Recorded customer-survey responses for the v3 Customer Success surface."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from app.modules.customer_success.service import (
    SurveyCompanyNotFound,
    list_survey_responses,
    record_survey_response,
    survey_summary,
)
from sdk.permissions import PermissionAction

router = APIRouter(prefix="/customer-success", tags=["Customer Success"])


class SurveyResponseCreate(BaseModel):
    company_id: str = Field(min_length=1, max_length=36)
    survey_type: Literal["nps", "csat"]
    score: float
    comment: str | None = Field(default=None, max_length=5000)
    source: Literal["manual", "import"] = "manual"
    recorded_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_scale(self) -> "SurveyResponseCreate":
        if self.survey_type == "nps" and not 0 <= self.score <= 10:
            raise ValueError("NPS score must be between 0 and 10")
        if self.survey_type == "csat" and not 1 <= self.score <= 5:
            raise ValueError("CSAT score must be between 1 and 5")
        return self


class SurveyResponseItem(BaseModel):
    id: str
    tenant_id: str
    company_id: str
    survey_type: Literal["nps", "csat"]
    score: float
    comment: str | None
    source: str
    recorded_at: datetime
    created_at: datetime


class SurveyResponseList(BaseModel):
    items: list[SurveyResponseItem]
    total: int


class SurveySummary(BaseModel):
    company_id: str | None
    nps: float | None
    nps_responses: int
    promoters: int
    detractors: int
    csat_average: float | None
    csat_responses: int
    response_rate: float | None
    response_rate_reason: str


@router.post("/surveys", response_model=SurveyResponseItem, status_code=201)
async def create_survey_response(
    body: SurveyResponseCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("company", PermissionAction.CREATE)),
):
    try:
        return await record_survey_response(db, tenant_id=tenant_id, **body.model_dump())
    except SurveyCompanyNotFound as exc:
        raise HTTPException(status_code=404, detail="Company not found") from exc


@router.get("/surveys", response_model=SurveyResponseList)
async def get_survey_responses(
    company_id: str | None = Query(default=None, max_length=36),
    survey_type: Literal["nps", "csat"] | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("company", PermissionAction.READ)),
):
    items, total = await list_survey_responses(
        db,
        tenant_id=tenant_id,
        company_id=company_id,
        survey_type=survey_type,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total}


@router.get("/surveys/summary", response_model=SurveySummary)
async def get_survey_summary(
    company_id: str | None = Query(default=None, max_length=36),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep("company", PermissionAction.READ)),
):
    return await survey_summary(db, tenant_id=tenant_id, company_id=company_id)
