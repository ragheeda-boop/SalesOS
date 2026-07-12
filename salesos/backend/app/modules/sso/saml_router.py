from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session, require_role_dep

from .saml_service import SAMLService, register_saml_config

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db_session)) -> SAMLService:
    return SAMLService(db=db)


@router.get("/sso/saml/metadata")
async def saml_metadata(
    tenant_id: str = Query(..., description="Tenant ID to identify SP config"),
    service: SAMLService = Depends(get_service),
):
    metadata = service.get_saml_metadata(tenant_id)
    from fastapi.responses import Response
    return Response(content=metadata, media_type="application/xml")


@router.post("/sso/saml/login")
async def saml_login(
    tenant_id: str = Form(...),
    service: SAMLService = Depends(get_service),
):
    try:
        redirect_url = service.initiate_saml_login(tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"redirect_url": redirect_url}


@router.post("/sso/saml/callback")
async def saml_callback(
    request: Request,
    SAMLResponse: str = Form(...),
    RelayState: str = Form(""),
    service: SAMLService = Depends(get_service),
):
    import base64
    import zlib
    try:
        decoded = base64.b64decode(SAMLResponse)
        try:
            xml_data = zlib.decompress(decoded, -15)
        except zlib.error:
            xml_data = decoded.decode("utf-8")
        if isinstance(xml_data, bytes):
            xml_data = xml_data.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode SAMLResponse: {e}")

    try:
        access_token, user_id = await service.handle_saml_callback(xml_data, RelayState or None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"SAML authentication failed: {str(e)}")

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
    import base64
    import zlib
    try:
        decoded = base64.b64decode(SAMLResponse)
        try:
            xml_data = zlib.decompress(decoded, -15)
        except zlib.error:
            xml_data = decoded.decode("utf-8")
        if isinstance(xml_data, bytes):
            xml_data = xml_data.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode SAMLResponse: {e}")

    try:
        access_token, user_id = await service.handle_idp_initiated(xml_data, RelayState or None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"SAML authentication failed: {str(e)}")

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
