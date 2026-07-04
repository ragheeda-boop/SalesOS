"""Feature Store REST endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query

from app.dependencies import get_current_tenant_id

router = APIRouter()


@router.get("/features/{company_id}")
async def get_company_features(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    feature_names: Optional[str] = Query(None, description="Comma-separated feature names"),
):
    store = getattr(request.app.state, "feature_store", None)
    if not store:
        raise HTTPException(status_code=503, detail="Feature Store not initialized")

    names = [n.strip() for n in feature_names.split(",")] if feature_names else None
    results = await store.get_features(company_id=company_id, tenant_id=tenant_id, feature_names=names)
    if not results:
        raise HTTPException(status_code=404, detail="No features found for company")
    return {
        "company_id": company_id,
        "features": {
            name: {
                "score": r.score,
                "version": r.version,
                "computed_at": r.computed_at.isoformat(),
                "confidence": r.confidence,
                "contributing_signals": r.contributing_signals,
                "explanation": r.explanation,
            }
            for name, r in results.items()
        },
    }


@router.get("/features/{company_id}/{feature_name}")
async def get_single_feature(
    company_id: str,
    feature_name: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    store = getattr(request.app.state, "feature_store", None)
    if not store:
        raise HTTPException(status_code=503, detail="Feature Store not initialized")

    result = await store.get_feature(company_id=company_id, tenant_id=tenant_id, feature_name=feature_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Feature '{feature_name}' not found")
    return {
        "company_id": company_id,
        "feature_name": feature_name,
        "score": result.score,
        "version": result.version,
        "computed_at": result.computed_at.isoformat(),
        "confidence": result.confidence,
        "contributing_signals": result.contributing_signals,
        "explanation": result.explanation,
    }


@router.post("/features/{company_id}/recompute")
async def recompute_features(
    company_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    store = getattr(request.app.state, "feature_store", None)
    if not store:
        raise HTTPException(status_code=503, detail="Feature Store not initialized")

    results = await store.recompute(company_id=company_id, tenant_id=tenant_id)
    return {
        "company_id": company_id,
        "features": {
            name: {
                "score": r.score,
                "version": r.version,
                "computed_at": r.computed_at.isoformat(),
                "confidence": r.confidence,
                "explanation": r.explanation,
            }
            for name, r in results.items()
        },
    }
