"""Phase 4D — signal_catalog seeding tests.

Covers: parsing a synthetic pack via KNOWLEDGE_PACKS_PATH override (unit),
idempotent re-seed (no duplicates), and the real shipped packs mounted at
/app/knowledge-packs (>=3 packs, >0 signals). The catalog is GLOBAL_PLATFORM:
no tenant GUC involved; rows are platform content, cleaned after synthetic
pack cases only.
"""

import json
import shutil
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.database import async_session
from app.modules.signal_marketplace.seeding import seed_signal_catalog_from_packs


async def _count() -> int:
    async with async_session() as db:
        return (await db.execute(text("SELECT COUNT(*) FROM signal_catalog"))).scalar()


async def _count_pack(pack_id: str) -> int:
    async with async_session() as db:
        return (
            await db.execute(
                text("SELECT COUNT(*) FROM signal_catalog WHERE pack_id=:p"),
                {"p": pack_id},
            )
        ).scalar()


async def _delete_ids(prefix: str) -> None:
    async with async_session() as db:
        await db.execute(
            text("DELETE FROM signal_catalog WHERE id LIKE :p"), {"p": f"{prefix}%"}
        )
        await db.commit()


def _make_pack(root: Path, pack_name: str, sig_id: str) -> None:
    d = root / pack_name / "signals"
    d.mkdir(parents=True)
    (d / "signal-definitions.json").write_text(
        json.dumps(
            {
                "pack_id": pack_name,
                "signals": [
                    {
                        "id": sig_id,
                        "name": "Test Signal",
                        "ar_name": "إشارة اختبار",
                        "description": "synthetic unit fixture",
                        "type": "test",
                        "category": "growth",
                        "priority": "high",
                        "source": "unit",
                        "weight": 0.7,
                        "decay_days": 30,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine():
    yield
    # each test owns an asyncio loop; drop pooled connections bound to it
    from app.database import engine

    await engine.dispose()


@pytest_asyncio.fixture
async def tmp_packs(monkeypatch, tmp_path):
    _make_pack(tmp_path, "unit-pack-a", "unit-sig-0001")
    _make_pack(tmp_path, "unit-pack-b", "unit-sig-0002")
    monkeypatch.setenv("KNOWLEDGE_PACKS_PATH", str(tmp_path))
    yield tmp_path
    await _delete_ids("unit-sig-")


@pytest.mark.asyncio
async def test_seeds_synthetic_pack_into_postgres(tmp_packs):
    info = await seed_signal_catalog_from_packs()
    assert info["ok"] is True and info["seeded"] == 2
    assert await _count_pack("unit-pack-a") == 1


@pytest.mark.asyncio
async def test_reseed_is_idempotent(tmp_packs):
    await seed_signal_catalog_from_packs()
    n1 = await _count()
    assert await _count_pack("unit-pack-a") == 1
    assert await _count_pack("unit-pack-b") == 1
    await seed_signal_catalog_from_packs()
    assert await _count() == n1  # zero duplicates on re-seed


@pytest.mark.asyncio
async def test_missing_packs_root_degrades_cleanly(monkeypatch, tmp_path):
    monkeypatch.setenv("KNOWLEDGE_PACKS_PATH", str(tmp_path / "does-not-exist"))
    info = await seed_signal_catalog_from_packs()
    assert info["ok"] is True and info["seeded"] == 0


@pytest.mark.asyncio
async def test_real_shipped_packs_load():
    """The mounted repo knowledge-packs must yield the shipped catalog."""
    base = Path("/app/knowledge-packs")
    if not base.exists():  # host-run fallback
        pytest.skip("knowledge-packs volume not mounted")
    info = await seed_signal_catalog_from_packs()
    assert info["ok"] is True
    assert info["seeded"] >= 3  # construction, financial-services, healthcare
    for pid in ("kp-construction", "kp-healthcare", "kp-financial-services"):
        assert await _count_pack(pid) >= 1


@pytest.mark.asyncio
async def test_startup_hook_present_in_boot():
    import inspect

    from app.boot import startup as boot

    src = inspect.getsource(boot.init_startup_services)
    assert "seed_signal_catalog_from_packs" in src
