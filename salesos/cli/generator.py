"""Module generator — `salesos create module <name>`.

Generates complete module scaffold: folder structure, models, APIs,
schemas, services, tests, migrations, permissions, and metadata.
"""

from __future__ import annotations

import os
from pathlib import Path
from string import Template


_MODEL_TEMPLATE = Template("""from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from sdk.database import Entity

if TYPE_CHECKING:
    pass


class ${Entity}Model(Entity):
    __tablename__ = "${table_name}"
    __table_args__ = {"schema": "${schema}"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )
""")


_SCHEMA_TEMPLATE = Template("""from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ${Entity}Base(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    is_active: bool = True


class ${Entity}Create(${Entity}Base):
    pass


class ${Entity}Update(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ${Entity}Response(${Entity}Base):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ${Entity}ListResponse(BaseModel):
    items: list[${Entity}Response]
    total: int
    page: int
    page_size: int
""")


_SERVICE_TEMPLATE = Template("""from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from sdk.database import SqlAlchemyRepository, UnitOfWork
from sdk.exceptions import ObjectNotFoundError

from .models import ${Entity}Model
from .schemas import ${Entity}Create, ${Entity}Update


class ${Entity}Repository(SqlAlchemyRepository[${Entity}Model]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ${Entity}Model)


class ${Entity}Service:
    def __init__(self, session: AsyncSession):
        self._repo = ${Entity}Repository(session)
        self._uow = UnitOfWork(session)

    async def create(self, data: ${Entity}Create, tenant_id: str) -> ${Entity}Model:
        entity = ${Entity}Model(**data.model_dump())
        async with self._uow:
            self._repo.add(entity)
        return entity

    async def get(self, entity_id: UUID, tenant_id: str) -> ${Entity}Model:
        entity = await self._repo.find_by_id(entity_id)
        if not entity:
            raise ObjectNotFoundError("${Entity}", str(entity_id))
        return entity

    async def update(self, entity_id: UUID, data: ${Entity}Update, tenant_id: str) -> ${Entity}Model:
        entity = await self.get(entity_id, tenant_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, field, value)
        async with self._uow:
            self._repo.add(entity)
        return entity

    async def delete(self, entity_id: UUID, tenant_id: str) -> None:
        entity = await self.get(entity_id, tenant_id)
        async with self._uow:
            await self._repo.delete(entity)

    async def list(
        self, tenant_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[${Entity}Model], int]:
        stmt = select(${Entity}Model).where(${Entity}Model.is_active == True)
        count_stmt = select(func.count()).select_from(${Entity}Model).where(${Entity}Model.is_active == True)

        result = await self._repo._session.execute(stmt.offset((page - 1) * page_size).limit(page_size))
        items = result.scalars().all()

        count_result = await self._repo._session.execute(count_stmt)
        total = count_result.scalar() or 0

        return items, total
""")


_API_TEMPLATE = Template("""from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from sdk.database import get_session
from sdk.exceptions import ObjectNotFoundError

from .schemas import ${Entity}Create, ${Entity}Response, ${Entity}Update, ${Entity}ListResponse
from .service import ${Entity}Service

router = APIRouter(prefix="/${module}", tags=["${Entity}"])


@router.post("", response_model=${Entity}Response, status_code=201)
async def create_${var_name}(
    data: ${Entity}Create,
    session=Depends(get_session),
    tenant_id: str = "",
):
    service = ${Entity}Service(session)
    entity = await service.create(data, tenant_id)
    return entity


@router.get("/{${var_name}_id}", response_model=${Entity}Response)
async def get_${var_name}(
    ${var_name}_id: UUID,
    session=Depends(get_session),
    tenant_id: str = "",
):
    service = ${Entity}Service(session)
    try:
        return await service.get(${var_name}_id, tenant_id)
    except ObjectNotFoundError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="${Entity} not found")


@router.put("/{${var_name}_id}", response_model=${Entity}Response)
async def update_${var_name}(
    ${var_name}_id: UUID,
    data: ${Entity}Update,
    session=Depends(get_session),
    tenant_id: str = "",
):
    service = ${Entity}Service(session)
    return await service.update(${var_name}_id, data, tenant_id)


@router.delete("/{${var_name}_id}", status_code=204)
async def delete_${var_name}(
    ${var_name}_id: UUID,
    session=Depends(get_session),
    tenant_id: str = "",
):
    service = ${Entity}Service(session)
    await service.delete(${var_name}_id, tenant_id)


@router.get("", response_model=${Entity}ListResponse)
async def list_${var_name}s(
    page: int = 1,
    page_size: int = 20,
    session=Depends(get_session),
    tenant_id: str = "",
):
    service = ${Entity}Service(session)
    items, total = await service.list(tenant_id, page, page_size)
    return ${Entity}ListResponse(
        items=[${Entity}Response.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
""")


_TEST_TEMPLATE = Template("""from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from backend.database import get_session


@pytest.fixture
def client(session: AsyncSession):
    async def _override():
        yield session
    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_create_${var_name}(client):
    payload = {"name": "Test ${Entity}"}
    response = await client.post("/api/v1/${module}", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test ${Entity}"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_${var_name}s(client):
    response = await client.get("/api/v1/${module}")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_${var_name}_not_found(client):
    response = await client.get("/api/v1/${module}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
""")


_METADATA_TEMPLATE = Template("""from sdk.metadata import EntityMetadata, FieldMetadata, FieldType, MetadataRegistry, UiWidget


def register_${module}_metadata() -> None:
    meta = EntityMetadata(
        module="${module}",
        entity="${entity}",
        label="${Entity}",
        label_ar="${Entity_ar}",
        label_plural="${Entity}s",
        label_plural_ar="${Entity_ar}s",
        description="${description}",
        description_ar="${description_ar}",
        fields={
            "name": FieldMetadata(
                name="name",
                label="Name",
                label_ar="الاسم",
                field_type=FieldType.STRING,
                required=True,
                searchable=True,
                sortable=True,
                filterable=True,
                widget=UiWidget.TEXT_INPUT,
            ),
            "description": FieldMetadata(
                name="description",
                label="Description",
                label_ar="الوصف",
                field_type=FieldType.TEXT,
                required=False,
                searchable=True,
                widget=UiWidget.TEXTAREA,
            ),
            "is_active": FieldMetadata(
                name="is_active",
                label="Active",
                label_ar="نشط",
                field_type=FieldType.BOOLEAN,
                default_value=True,
                widget=UiWidget.TOGGLE,
            ),
        },
        default_sort_field="created_at",
        search_enabled=True,
        audit_enabled=True,
    )
    MetadataRegistry.register(meta)
""")


_PERMISSIONS_TEMPLATE = Template("""from sdk.permissions import Permission, PermissionAction, PermissionRegistry, Role


def register_${module}_permissions() -> None:
    PermissionRegistry.register_module_permissions("${module}", [
        PermissionAction.CREATE,
        PermissionAction.READ,
        PermissionAction.UPDATE,
        PermissionAction.DELETE,
    ])
""")


_INIT_TEMPLATE = Template('''"""${Entity} module for SalesOS."""\n''')


class ModuleGenerator:
    """Generates a complete module scaffold."""

    def __init__(self, base_path: str | Path):
        self._base = Path(base_path)

    def generate(
        self,
        module: str,
        entity: str,
        schema: str = "public",
        label_ar: str | None = None,
        description: str = "",
        description_ar: str = "",
    ) -> Path:
        label_ar = label_ar or entity
        entity_upper = entity[0].upper() + entity[1:]
        entity_lower = entity[0].lower() + entity[1:]
        table_name = entity_lower + "s"

        module_path = self._base / "modules" / module
        module_path.mkdir(parents=True, exist_ok=True)

        context = {
            "module": module,
            "Entity": entity_upper,
            "entity": entity_lower,
            "var_name": entity_lower,
            "table_name": table_name,
            "schema": schema,
            "Entity_ar": label_ar,
            "description": description,
            "description_ar": description_ar,
        }

        files = {
            "__init__.py": _INIT_TEMPLATE,
            "models.py": _MODEL_TEMPLATE,
            "schemas.py": _SCHEMA_TEMPLATE,
            "service.py": _SERVICE_TEMPLATE,
            "api.py": _API_TEMPLATE,
            "metadata.py": _METADATA_TEMPLATE,
            "permissions.py": _PERMISSIONS_TEMPLATE,
            "tests/test_api.py": _TEST_TEMPLATE,
        }

        for rel_path, template in files.items():
            file_path = module_path / rel_path
            (module_path / os.path.dirname(rel_path)).mkdir(parents=True, exist_ok=True)
            content = template.safe_substitute(context)
            file_path.write_text(content)

        return module_path


def create_module(
    base_path: str,
    module: str,
    entity: str,
    schema: str = "public",
    label_ar: str | None = None,
    description: str = "",
    description_ar: str = "",
) -> Path:
    """CLI entry point for `salesos create module <name>`."""
    gen = ModuleGenerator(base_path)
    return gen.generate(module, entity, schema, label_ar, description, description_ar)
