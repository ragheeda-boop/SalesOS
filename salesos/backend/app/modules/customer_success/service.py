"""Tenant-safe persistence for recorded NPS and CSAT responses."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SurveyCompanyNotFound(ValueError):
    """The requested company is absent or belongs to another tenant."""


async def record_survey_response(
    db: AsyncSession,
    *,
    tenant_id: str,
    company_id: str,
    survey_type: str,
    score: float,
    comment: str | None,
    source: str,
    recorded_at: datetime | None,
    idempotency_key: str | None,
) -> dict:
    company = await db.execute(
        text(
            "SELECT id FROM companies "
            "WHERE id::text = :company_id AND tenant_id::text = :tenant_id"
        ),
        {"company_id": company_id, "tenant_id": tenant_id},
    )
    if company.scalar_one_or_none() is None:
        raise SurveyCompanyNotFound(company_id)

    response_id = str(uuid4())
    observed_at = recorded_at or datetime.now(UTC)
    inserted = await db.execute(
        text(
            """
            INSERT INTO customer_survey_responses
                (id, tenant_id, company_id, survey_type, score, comment, source,
                 recorded_at, idempotency_key)
            VALUES
                (:id, :tenant_id, :company_id, :survey_type, :score, :comment, :source,
                 :recorded_at, :idempotency_key)
            ON CONFLICT (tenant_id, company_id, idempotency_key) DO NOTHING
            RETURNING id, tenant_id, company_id, survey_type, score, comment, source,
                      recorded_at, created_at
            """
        ),
        {
            "id": response_id,
            "tenant_id": tenant_id,
            "company_id": company_id,
            "survey_type": survey_type,
            "score": score,
            "comment": comment,
            "source": source,
            "recorded_at": observed_at,
            "idempotency_key": idempotency_key,
        },
    )
    row = inserted.mappings().one_or_none()
    if row is None:
        existing = await db.execute(
            text(
                """
                SELECT id, tenant_id, company_id, survey_type, score, comment, source,
                       recorded_at, created_at
                FROM customer_survey_responses
                WHERE tenant_id = :tenant_id AND company_id = :company_id
                  AND idempotency_key = :idempotency_key
                """
            ),
            {
                "tenant_id": tenant_id,
                "company_id": company_id,
                "idempotency_key": idempotency_key,
            },
        )
        row = existing.mappings().one_or_none()
    if row is None:
        raise RuntimeError("Survey response was not persisted")
    await db.commit()
    return dict(row)


async def list_survey_responses(
    db: AsyncSession,
    *,
    tenant_id: str,
    company_id: str | None,
    survey_type: str | None,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:
    conditions = ["tenant_id = :tenant_id"]
    params: dict[str, object] = {"tenant_id": tenant_id}
    if company_id:
        conditions.append("company_id = :company_id")
        params["company_id"] = company_id
    if survey_type:
        conditions.append("survey_type = :survey_type")
        params["survey_type"] = survey_type
    where = " AND ".join(conditions)
    total = (
        await db.execute(
            text(f"SELECT count(*) FROM customer_survey_responses WHERE {where}"), params
        )
    ).scalar_one()
    records = await db.execute(
        text(
            f"""
            SELECT id, tenant_id, company_id, survey_type, score, comment, source,
                   recorded_at, created_at
            FROM customer_survey_responses
            WHERE {where}
            ORDER BY recorded_at DESC, created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {**params, "limit": limit, "offset": offset},
    )
    return [dict(row) for row in records.mappings().all()], int(total)


async def survey_summary(
    db: AsyncSession, *, tenant_id: str, company_id: str | None
) -> dict:
    conditions = ["tenant_id = :tenant_id"]
    params: dict[str, object] = {"tenant_id": tenant_id}
    if company_id:
        conditions.append("company_id = :company_id")
        params["company_id"] = company_id
    where = " AND ".join(conditions)
    row = (
        await db.execute(
            text(
                f"""
                SELECT
                    count(*) FILTER (WHERE survey_type = 'nps') AS nps_responses,
                    count(*) FILTER (WHERE survey_type = 'nps' AND score >= 9) AS promoters,
                    count(*) FILTER (WHERE survey_type = 'nps' AND score <= 6) AS detractors,
                    count(*) FILTER (WHERE survey_type = 'csat') AS csat_responses,
                    avg(score) FILTER (WHERE survey_type = 'csat') AS csat_average
                FROM customer_survey_responses
                WHERE {where}
                """
            ),
            params,
        )
    ).mappings().one()
    nps_responses = int(row["nps_responses"] or 0)
    promoters = int(row["promoters"] or 0)
    detractors = int(row["detractors"] or 0)
    nps = None
    if nps_responses:
        nps = round(((promoters - detractors) / nps_responses) * 100, 1)
    return {
        "company_id": company_id,
        "nps": nps,
        "nps_responses": nps_responses,
        "promoters": promoters,
        "detractors": detractors,
        "csat_average": float(row["csat_average"]) if row["csat_average"] is not None else None,
        "csat_responses": int(row["csat_responses"] or 0),
        "response_rate": None,
        "response_rate_reason": "Survey invitations are not yet recorded.",
    }
