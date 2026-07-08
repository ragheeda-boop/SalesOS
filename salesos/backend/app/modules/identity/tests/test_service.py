import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError, UnauthorizedError
from app.modules.identity.models import RefreshTokenFamily
from app.modules.identity.service import IdentityService, hash_password, verify_password, create_access_token, decode_access_token, decode_refresh_token


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


# ── Security Regression Tests (S6 Refresh Token Architecture) ───────────


@pytest.mark.asyncio
async def test_create_token_family(db_session: AsyncSession):
    service = IdentityService(db_session)
    tenant = await service.create_tenant(name="Test", slug="sec-test-1")
    user = await service.create_user(
        email="sec@test.com", password="Test1234!", full_name="Sec User",
        tenant_id=str(tenant.id),
    )
    uid = str(user.id)
    tid = str(tenant.id)
    refresh_token, family_id, family_pk, jti = await service.create_token_family(uid, tid)
    assert refresh_token is not None
    assert len(refresh_token) > 20
    assert family_id is not None
    result = await db_session.execute(
        select(RefreshTokenFamily).where(RefreshTokenFamily.family_id == family_id)
    )
    family = result.scalar_one_or_none()
    assert family is not None
    assert str(family.user_id) == uid


@pytest.mark.asyncio
async def test_refresh_token_rotation(db_session: AsyncSession):
    service = IdentityService(db_session)
    tenant = await service.create_tenant(name="Test", slug="sec-test-2")
    user = await service.create_user(
        email="rot@test.com", password="Test1234!", full_name="Rot User",
        tenant_id=str(tenant.id),
    )
    uid = str(user.id)
    tid = str(tenant.id)
    _, family_id, _, jti = await service.create_token_family(uid, tid)
    new_access, new_refresh = await service.rotate_refresh_token(jti, uid, tid)
    assert new_access is not None
    assert new_refresh is not None
    payload = decode_refresh_token(new_refresh)
    assert payload["sub"] == uid
    assert payload["tenant_id"] == tid


@pytest.mark.asyncio
async def test_refresh_token_reuse_detection(db_session: AsyncSession):
    service = IdentityService(db_session)
    tenant = await service.create_tenant(name="Test", slug="sec-test-3")
    user = await service.create_user(
        email="reuse@test.com", password="Test1234!", full_name="Reuse User",
        tenant_id=str(tenant.id),
    )
    uid = str(user.id)
    tid = str(tenant.id)
    _, family_id, _, jti = await service.create_token_family(uid, tid)
    await service.rotate_refresh_token(jti, uid, tid)
    with pytest.raises(UnauthorizedError) as exc:
        await service.rotate_refresh_token(jti, uid, tid)
    assert "reuse" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_device_session_creation_and_revocation(db_session: AsyncSession):
    service = IdentityService(db_session)
    tenant = await service.create_tenant(name="Test", slug="sec-test-4")
    user = await service.create_user(
        email="sess@test.com", password="Test1234!", full_name="Sess User",
        tenant_id=str(tenant.id),
    )
    uid = str(user.id)
    tid = str(tenant.id)
    _, _, family_pk, _ = await service.create_token_family(uid, tid)
    session = await service.create_device_session(
        user_id=uid, tenant_id=tid, refresh_family_id=family_pk,
        device_name="Test Browser", device_type="desktop", ip_address="127.0.0.1",
    )
    assert session is not None
    assert session.device_name == "Test Browser"
    assert session.is_revoked is False
    result = await service.get_user_sessions(uid)
    assert len(result) == 1
    revoked = await service.revoke_session(session.id, uid)
    assert revoked == 1
    result2 = await service.get_user_sessions(uid)
    assert len(result2) == 0


@pytest.mark.asyncio
async def test_revoke_all_user_sessions(db_session: AsyncSession):
    service = IdentityService(db_session)
    tenant = await service.create_tenant(name="Test", slug="sec-test-5")
    user = await service.create_user(
        email="all@test.com", password="Test1234!", full_name="All User",
        tenant_id=str(tenant.id),
    )
    uid = str(user.id)
    tid = str(tenant.id)
    _, _, fp1, _ = await service.create_token_family(uid, tid)
    _, _, fp2, _ = await service.create_token_family(uid, tid)
    await service.create_device_session(
        user_id=uid, tenant_id=tid, refresh_family_id=fp1,
        device_name="Device 1", device_type="desktop", ip_address="1.1.1.1",
    )
    await service.create_device_session(
        user_id=uid, tenant_id=tid, refresh_family_id=fp2,
        device_name="Device 2", device_type="mobile", ip_address="2.2.2.2",
    )
    total = await service.revoke_all_user_sessions(uid)
    assert total == 2


@pytest.mark.asyncio
async def test_token_blacklist(db_session: AsyncSession):
    from datetime import datetime, timedelta, timezone
    service = IdentityService(db_session)
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    await service.blacklist_token("test-jti-123", "refresh", future)
    assert await service.is_token_blacklisted("test-jti-123") is True
    assert await service.is_token_blacklisted("nonexistent-jti") is False


@pytest.mark.asyncio
async def test_create_access_token_and_decode():
    token = create_access_token("user-123", "tenant-456")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["tenant_id"] == "tenant-456"
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_decode_expired_token():
    from jose import jwt
    from datetime import datetime, timedelta, timezone
    token = jwt.encode(
        {"sub": "u1", "tenant_id": "t1", "exp": datetime.now(timezone.utc) - timedelta(hours=1),
         "type": "access", "jti": "test", "iat": datetime.now(timezone.utc) - timedelta(hours=2),
         "iss": "salesos", "aud": "salesos-api"},
        "test-key", algorithm="HS256",
    )
    with pytest.raises(Exception):
        decode_access_token(token)
