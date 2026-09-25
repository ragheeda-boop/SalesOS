"""Master Data REST endpoints — Phase 1.

Global entities (md_global_companies, md_global_people) — NO tenant scoping.
Tenant entities (md_source_files, md_source_rows) — tenant-scoped via RLS.
Legacy mappings (md_legacy_id_mappings) — cross-tenant lookup.
"""

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

from .schemas import (
    GlobalCompanyCreate,
    GlobalCompanyResponse,
    GlobalCompanyUpdate,
    GlobalPersonCreate,
    GlobalPersonResponse,
    GlobalPersonUpdate,
    LegacyIDMappingCreate,
    LegacyIDMappingResponse,
    PaginatedResponse,
    SourceFileCreate,
    SourceFileResponse,
    SourceRowCreate,
    SourceRowResponse,
)
from .service import MasterDataService

router = APIRouter(tags=["Master Data"])


def get_service(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant_id),
) -> MasterDataService:
    return MasterDataService(session=db, tenant_id=tenant_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Global Company
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/global-companies",
    response_model=GlobalCompanyResponse,
    status_code=201,
    summary="Create a global company",
    description="Create a new global company entity with canonical name, CR number, VAT number, and other identifiers.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.CREATE))],
)
async def create_global_company(
    body: GlobalCompanyCreate,
    service: MasterDataService = Depends(get_service),
):
    return await service.create_global_company(
        canonical_name=body.canonical_name,
        canonical_name_ar=body.canonical_name_ar,
        cr_number=body.cr_number,
        vat_number=body.vat_number,
        unified_national_number=body.unified_national_number,
        status=body.status,
    )


@router.get(
    "/global-companies",
    response_model=PaginatedResponse,
    summary="List global companies",
    description="List global company entities with pagination.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def list_global_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MasterDataService = Depends(get_service),
):
    items, total = await service.list_global_companies(page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[GlobalCompanyResponse(**i) for i in items],
        has_next=(page * page_size) < total,
    )


@router.get(
    "/global-companies/{company_id}",
    response_model=GlobalCompanyResponse,
    summary="Get a global company",
    description="Get a single global company entity by ID.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def get_global_company(
    company_id: str = Path(...),
    service: MasterDataService = Depends(get_service),
):
    result = await service.get_global_company(company_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Global company not found")
    return result


@router.patch(
    "/global-companies/{company_id}",
    response_model=GlobalCompanyResponse,
    summary="Update a global company",
    description="Partially update a global company entity. Only provided fields are updated.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.UPDATE))],
)
async def update_global_company(
    company_id: str = Path(...),
    body: GlobalCompanyUpdate = ...,
    service: MasterDataService = Depends(get_service),
):
    result = await service.update_global_company(
        company_id, body.model_dump(exclude_unset=True)
    )
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Global company not found")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Global Person
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/global-people",
    response_model=GlobalPersonResponse,
    status_code=201,
    summary="Create a global person",
    description="Create a new global person entity with name, email, phone, and optional company association.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.CREATE))],
)
async def create_global_person(
    body: GlobalPersonCreate,
    service: MasterDataService = Depends(get_service),
):
    return await service.create_global_person(
        canonical_name=body.canonical_name,
        email=body.email,
        phone=body.phone,
        company_global_id=body.company_global_id,
        job_title=body.job_title,
        status=body.status,
    )


@router.get(
    "/global-people",
    response_model=PaginatedResponse,
    summary="List global people",
    description="List global person entities with pagination.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def list_global_people(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MasterDataService = Depends(get_service),
):
    items, total = await service.list_global_people(page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[GlobalPersonResponse(**i) for i in items],
        has_next=(page * page_size) < total,
    )


@router.get(
    "/global-people/{person_id}",
    response_model=GlobalPersonResponse,
    summary="Get a global person",
    description="Get a single global person entity by ID.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def get_global_person(
    person_id: str = Path(...),
    service: MasterDataService = Depends(get_service),
):
    result = await service.get_global_person(person_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Global person not found")
    return result


@router.patch(
    "/global-people/{person_id}",
    response_model=GlobalPersonResponse,
    summary="Update a global person",
    description="Partially update a global person entity. Only provided fields are updated.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.UPDATE))],
)
async def update_global_person(
    person_id: str = Path(...),
    body: GlobalPersonUpdate = ...,
    service: MasterDataService = Depends(get_service),
):
    result = await service.update_global_person(
        person_id, body.model_dump(exclude_unset=True)
    )
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Global person not found")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Legacy ID Mapping
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/legacy-id-mappings",
    response_model=LegacyIDMappingResponse,
    status_code=201,
    summary="Register a legacy ID mapping",
    description="Register a mapping from a legacy ID (e.g. MA-001234) to a global entity. Fails if mapping already exists.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.CREATE))],
)
async def register_legacy_id(
    body: LegacyIDMappingCreate,
    service: MasterDataService = Depends(get_service),
):
    result = await service.register_legacy_id(
        legacy_id_type=body.legacy_id_type,
        legacy_id=body.legacy_id,
        global_entity_type=body.global_entity_type,
        global_entity_id=body.global_entity_id,
        confidence=body.confidence,
    )
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Legacy ID mapping already exists")
    return result


@router.get(
    "/legacy-id-mappings/by-legacy/{legacy_id_type}/{legacy_id}",
    response_model=LegacyIDMappingResponse,
    summary="Get legacy mapping by legacy ID",
    description="Look up a legacy ID mapping by legacy ID type and value.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def get_legacy_mapping(
    legacy_id_type: str = Path(...),
    legacy_id: str = Path(...),
    service: MasterDataService = Depends(get_service),
):
    result = await service.get_legacy_mapping(legacy_id_type, legacy_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Legacy ID mapping not found")
    return result


@router.get(
    "/legacy-id-mappings/by-entity/{global_entity_id}",
    response_model=list[LegacyIDMappingResponse],
    summary="List legacy mappings for entity",
    description="List all legacy ID mappings associated with a global entity.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def list_legacy_mappings_for_entity(
    global_entity_id: str = Path(...),
    service: MasterDataService = Depends(get_service),
):
    return await service.list_legacy_mappings_for_entity(global_entity_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Source File
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/source-files",
    response_model=SourceFileResponse,
    status_code=201,
    summary="Register a source file",
    description="Register a new source file metadata record with hash, size, and schema mapping.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.CREATE))],
)
async def register_source_file(
    body: SourceFileCreate,
    service: MasterDataService = Depends(get_service),
):
    return await service.register_source_file(
        filename=body.filename,
        file_hash_sha256=body.file_hash_sha256,
        file_size_bytes=body.file_size_bytes,
        source_system=body.source_system,
        mime_type=body.mime_type,
        storage_path=body.storage_path,
        uploaded_by=body.uploaded_by,
        sheet_count=body.sheet_count,
        total_rows=body.total_rows,
        schema_mapping=body.schema_mapping,
    )


@router.get(
    "/source-files",
    response_model=PaginatedResponse,
    summary="List source files",
    description="List registered source file metadata records with pagination.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def list_source_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MasterDataService = Depends(get_service),
):
    items, total = await service.list_source_files(page=page, page_size=page_size)
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[SourceFileResponse(**i) for i in items],
        has_next=(page * page_size) < total,
    )


@router.get(
    "/source-files/{file_id}",
    response_model=SourceFileResponse,
    summary="Get a source file",
    description="Get a single source file metadata record by ID.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def get_source_file(
    file_id: str = Path(...),
    service: MasterDataService = Depends(get_service),
):
    result = await service.get_source_file(file_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Source file not found")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Source Row
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/source-rows",
    response_model=SourceRowResponse,
    status_code=201,
    summary="Insert a source row",
    description="Insert a raw source row linked to a source file, with row number and raw payload.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.CREATE))],
)
async def insert_source_row(
    body: SourceRowCreate,
    service: MasterDataService = Depends(get_service),
):
    return await service.insert_source_row(
        source_file_id=body.source_file_id,
        source_id=body.source_id,
        source_record_id=body.source_record_id,
        row_number=body.row_number,
        raw_payload=body.raw_payload,
        sheet_name=body.sheet_name,
        entity_type=body.entity_type,
    )


@router.get(
    "/source-rows/{row_id}",
    response_model=SourceRowResponse,
    summary="Get a source row",
    description="Get a single source row by ID.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def get_source_row(
    row_id: str = Path(...),
    service: MasterDataService = Depends(get_service),
):
    result = await service.get_source_row(row_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Source row not found")
    return result


@router.get(
    "/source-files/{file_id}/rows",
    response_model=PaginatedResponse,
    summary="List source rows for a file",
    description="List source rows belonging to a source file with pagination.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def list_source_rows(
    file_id: str = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    service: MasterDataService = Depends(get_service),
):
    items, total = await service.list_source_rows(
        source_file_id=file_id, page=page, page_size=page_size
    )
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[SourceRowResponse(**i) for i in items],
        has_next=(page * page_size) < total,
    )
