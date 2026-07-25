"""SAML 2.0 endpoints — with rate limiting and secure decode."""

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import safe_error_detail
from app.dependencies import get_db_session, require_role_dep
from app.common.rate_limit import check_rate_limit_by_key

from .saml_service import SAMLService, decode_saml_response, register_saml_config

router = APIRouter()

_SAML_RATE_LIMIT = 5  # requests per window per IP for sensitive endpoints


def get_service(db: AsyncSession = Depends(get_db_session)) -> SAMLService:
    return SAMLService(db=db)


@router.get("/sso/saml/metadata")
async def saml_metadata(
    request: Request,
    tenant_id: str = Query(..., description="Tenant ID to identify SP config"),
    service: SAMLService = Depends(get_service),
):
    await check_rate_limit_by_key(f"saml-metadata:{request.client.host}", limit=30, window=60)
    metadata = service.get_saml_metadata(tenant_id)
    return Response(content=metadata, media_type="application/xml")


@router.post("/sso/saml/login")
async def saml_login(
    request: Request,
    tenant_id: str = Form(...),
    service: SAMLService = Depends(get_service),
):
    await check_rate_limit_by_key(f"saml-login:{request.client.host}", limit=_SAML_RATE_LIMIT, window=60)
    try:
        redirect_url = service.initiate_saml_login(tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Invalid SAML login request"))
    return {"redirect_url": redirect_url}


@router.post("/sso/saml/callback")
async def saml_callback(
    request: Request,
    SAMLResponse: str = Form(...),
    RelayState: str = Form(""),
    service: SAMLService = Depends(get_service),
):
    await check_rate_limit_by_key(f"saml-callback:{request.client.host}", limit=_SAML_RATE_LIMIT, window=60)

    try:
        xml_data = decode_saml_response(SAMLResponse)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Failed to decode SAMLResponse"))

    try:
        access_token, user_id = await service.handle_saml_callback(xml_data, RelayState or None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Invalid SAML login request"))
    except Exception as e:
        raise HTTPException(status_code=401, detail=safe_error_detail(e, "SAML authentication failed"))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
    }


@router.post("/sso/saml/idp-initiated")
async def saml_idp_initiated(
    request: Request,
    SAMLResponse: str = Form(...),
    RelayState: str = Form(""),
    service: SAMLService = Depends(get_service),
):
    await check_rate_limit_by_key(f"saml-idp-init:{request.client.host}", limit=_SAML_RATE_LIMIT, window=60)

    try:
        xml_data = decode_saml_response(SAMLResponse)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Failed to decode SAMLResponse"))

    try:
        access_token, user_id = await service.handle_idp_initiated(xml_data, RelayState or None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Invalid SAML login request"))
    except Exception as e:
        raise HTTPException(status_code=401, detail=safe_error_detail(e, "SAML authentication failed"))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
    }


@router.post("/sso/saml/config", dependencies=[Depends(require_role_dep("admin"))])
async def saml_configure(
    tenant_id: str = Form(...),
    idp_sso_url: str = Form(...),
    idp_entity_id: str = Form(...),
    idp_cert: str = Form(""),
):
    register_saml_config(tenant_id, {
        "idp_sso_url": idp_sso_url,
        "idp_entity_id": idp_entity_id,
        "idp_cert": idp_cert,
    })
    return {"message": f"SAML configured for tenant {tenant_id}"}
