import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError, UnauthorizedError
from app.modules.identity.service import IdentityService, hash_password, verify_password


@pytest.mark.asyncio
async def test_hash_and_verify_password():
    password = "SecureP@ss123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


@pytest.mark.asyncio
async def test_create_tenant(db_session: AsyncSession):
    service = IdentityService(db_session)
    tenant = await service.create_tenant(
        name="Test Company",
        slug="test-company",
    )
    assert tenant.name == "Test Company"
    assert tenant.slug == "test-company"
    assert tenant.plan == "free"


@pytest.mark.asyncio
async def test_create_duplicate_tenant(db_session: AsyncSession):
    service = IdentityService(db_session)
    await service.create_tenant(name="Test", slug="test-slug")
    with pytest.raises(DuplicateError):
        await service.create_tenant(name="Test Again", slug="test-slug")


@pytest.mark.asyncio
async def test_get_tenant_not_found(db_session: AsyncSession):
    service = IdentityService(db_session)
    with pytest.raises(NotFoundError):
        await service.get_tenant("00000000-0000-0000-0000-000000000000")


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    service = IdentityService(db_session)
    tenant = await service.create_tenant(name="Test", slug="test-company-2")

    user = await service.create_user(
        email="test@example.com",
        password="TestP@ss123",
        full_name="Test User",
        tenant_id=str(tenant.id),
    )
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.role == "user"


@pytest.mark.asyncio
async def test_create_duplicate_user(db_session: AsyncSession):
    service = IdentityService(db_session)
    tenant = await service.create_tenant(name="Test", slug="test-company-3")
    await service.create_user(
        email="dupe@example.com",
        password="TestP@ss123",
        full_name="User 1",
        tenant_id=str(tenant.id),
    )
    with pytest.raises(DuplicateError):
        await service.create_user(
            email="dupe@example.com",
            password="TestP@ss456",
            full_name="User 2",
            tenant_id=str(tenant.id),
        )


@pytest.mark.asyncio
async def test_authenticate_success(db_session: AsyncSession):
    service = IdentityService(db_session)
    tenant = await service.create_tenant(name="Test", slug="test-company-4")
    await service.create_user(
        email="auth@example.com",
        password="AuthP@ss123",
        full_name="Auth User",
        tenant_id=str(tenant.id),
    )
    user = await service.authenticate(email="auth@example.com", password="AuthP@ss123")
    assert user.email == "auth@example.com"


@pytest.mark.asyncio
async def test_authenticate_failure(db_session: AsyncSession):
    service = IdentityService(db_session)
    with pytest.raises(UnauthorizedError):
        await service.authenticate(email="nonexistent@example.com", password="password")
