"""Tests for HybridSearchEngine — RRF fusion, full-text, semantic, filtering."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.search.engine.hybrid_search import (
    RRF_K,
    HybridSearchEngine,
    HybridSearchResult,
)

# ── Fixtures ──────────────────────────────────────────────────────


def _make_result(
    id: str,
    name_ar: str = "",
    score: float = 0.0,
    match_type: str = "fulltext",
    **kwargs,
) -> HybridSearchResult:
    return HybridSearchResult(
        id=id, name_ar=name_ar, score=score, match_type=match_type, **kwargs
    )


# ── RRF Fusion Tests ─────────────────────────────────────────────


class TestRRFFusion:
    """Test the Reciprocal Rank Fusion algorithm in isolation."""

    def _engine(self) -> HybridSearchEngine:
        return HybridSearchEngine(
            session_factory=MagicMock(),
            embedding_service=None,
        )

    def test_rrf_single_list(self):
        """Full-text only — no semantic results."""
        engine = self._engine()
        ft = [_make_result("1", "A"), _make_result("2", "B"), _make_result("3", "C")]
        result = engine._rrf_fusion(ft, [])

        assert len(result) == 3
        assert result[0].id == "1"
        assert result[1].id == "2"
        assert result[2].id == "3"
        # Score for position 0: 1/(60+0) ≈ 0.01667
        assert abs(result[0].score - 1 / RRF_K) < 1e-6

    def test_rrf_semantic_only(self):
        """Semantic only — no full-text results."""
        engine = self._engine()
        sem = [
            _make_result("1", "A", match_type="semantic"),
            _make_result("2", "B", match_type="semantic"),
        ]
        result = engine._rrf_fusion([], sem)

        assert len(result) == 2
        assert result[0].id == "1"

    def test_rrf_overlap_fusion(self):
        """Document appearing in both lists gets boosted."""
        engine = self._engine()
        ft = [_make_result("1", "A"), _make_result("2", "B")]
        sem = [
            _make_result("1", "A", match_type="semantic"),
            _make_result("3", "C", match_type="semantic"),
        ]

        result = engine._rrf_fusion(ft, sem)

        assert len(result) == 3

        # Doc "1" appears in both lists → higher score
        doc1 = next(r for r in result if r.id == "1")
        doc2 = next(r for r in result if r.id == "2")
        doc3 = next(r for r in result if r.id == "3")

        # Doc 1: 1/(60+0) from ft + 1/(60+0) from sem = 2/60
        assert abs(doc1.score - 2 / RRF_K) < 1e-6
        assert doc1.match_type == "hybrid"

        # Doc 2: only in ft at rank 1 → 1/(60+1)
        assert abs(doc2.score - 1 / (RRF_K + 1)) < 1e-6
        assert doc2.match_type == "fulltext"

        # Doc 3: only in sem at rank 1 → 1/(60+1)
        assert abs(doc3.score - 1 / (RRF_K + 1)) < 1e-6
        assert doc3.match_type == "semantic"

    def test_rrf_disjoint_lists(self):
        """No overlap — all results are from a single source."""
        engine = self._engine()
        ft = [_make_result("1", "A"), _make_result("2", "B")]
        sem = [
            _make_result("3", "C", match_type="semantic"),
            _make_result("4", "D", match_type="semantic"),
        ]

        result = engine._rrf_fusion(ft, sem)

        assert len(result) == 4
        # All should be in order: ft rank 0, ft rank 1, sem rank 0, sem rank 1
        # (or sem rank 0 before ft rank 1 — scores are equal at ranks 0 and 1)
        ids = [r.id for r in result]
        assert "1" in ids
        assert "4" in ids

    def test_rrf_empty_lists(self):
        """Both lists empty — should return empty."""
        engine = self._engine()
        result = engine._rrf_fusion([], [])
        assert result == []

    def test_rrf_large_list_ordering(self):
        """Verify ordering is correct for larger result sets."""
        engine = self._engine()
        ft = [_make_result(str(i), f"Company {i}") for i in range(10)]
        sem = [_make_result(str(i), f"Company {i}", match_type="semantic") for i in range(5, 15)]

        result = engine._rrf_fusion(ft, sem)

        # Documents 5-9 appear in both lists, should be at the top
        top_ids = [r.id for r in result[:5]]
        for i in range(5, 10):
            assert str(i) in top_ids

    def test_rrf_match_type_hybrid(self):
        """Documents in both lists should be marked as 'hybrid'."""
        engine = self._engine()
        ft = [_make_result("1", "A")]
        sem = [_make_result("1", "A", match_type="semantic")]

        result = engine._rrf_fusion(ft, sem)
        assert result[0].match_type == "hybrid"
        assert "fulltext_rank" in result[0].explanation
        assert "semantic_rank" in result[0].explanation

    def test_rrf_explanation_fields(self):
        """Verify explanation strings are populated."""
        engine = self._engine()
        ft = [_make_result("1", "A")]
        sem = [_make_result("2", "B", match_type="semantic")]

        result = engine._rrf_fusion(ft, sem)
        doc1 = next(r for r in result if r.id == "1")
        doc2 = next(r for r in result if r.id == "2")

        assert "fulltext_only" in doc1.explanation
        assert "semantic_only" in doc2.explanation


# ── Filter Tests ──────────────────────────────────────────────────


class TestFiltering:
    """Test structured field filtering on semantic results."""

    def _engine(self) -> HybridSearchEngine:
        return HybridSearchEngine(
            session_factory=MagicMock(),
            embedding_service=None,
        )

    def test_apply_filters_city(self):
        engine = self._engine()
        results = [
            _make_result("1", "A", city="الرياض"),
            _make_result("2", "B", city="جدة"),
            _make_result("3", "C", city="الرياض"),
        ]
        filtered = engine._apply_filters(results, {"city": "الرياض"})
        assert len(filtered) == 2
        assert all(r.city == "الرياض" for r in filtered)

    def test_apply_filters_no_match(self):
        engine = self._engine()
        results = [_make_result("1", "A", city="جدة")]
        filtered = engine._apply_filters(results, {"city": "الرياض"})
        assert len(filtered) == 0

    def test_apply_filters_empty(self):
        engine = self._engine()
        results = [_make_result("1", "A")]
        filtered = engine._apply_filters(results, {})
        assert len(filtered) == 1

    def test_apply_filters_multiple_fields(self):
        engine = self._engine()
        results = [
            _make_result("1", "A", city="الرياض", industry="تقنية"),
            _make_result("2", "B", city="الرياض", industry="تجارة"),
            _make_result("3", "C", city="جدة", industry="تقنية"),
        ]
        filtered = engine._apply_filters(results, {"city": "الرياض", "industry": "تقنية"})
        assert len(filtered) == 1
        assert filtered[0].id == "1"


# ── Embedding Service Adapter Tests ──────────────────────────────


class TestSearchEmbeddingService:
    """Test the embedding service adapter with mocking."""

    @pytest.mark.asyncio
    async def test_get_embedding_cache_hit(self):
        from domains.search.engine.embedding_service import SearchEmbeddingService

        service = SearchEmbeddingService(openai_api_key="test-key")
        # Pre-populate cache
        key = service._cache_key("hello")
        service._cache[key] = [0.1, 0.2, 0.3]

        result = await service.get_embedding("hello")
        assert result == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_get_embedding_empty_text(self):
        from domains.search.engine.embedding_service import SearchEmbeddingService

        service = SearchEmbeddingService(openai_api_key="test-key")
        assert await service.get_embedding("") is None
        assert await service.get_embedding("   ") is None

    @pytest.mark.asyncio
    async def test_get_embedding_no_api_key(self):
        from domains.search.engine.embedding_service import SearchEmbeddingService

        service = SearchEmbeddingService(openai_api_key="")
        result = await service.get_embedding("hello")
        assert result is None  # graceful fallback

    @pytest.mark.asyncio
    async def test_get_embedding_api_failure(self):
        from domains.search.engine.embedding_service import SearchEmbeddingService

        service = SearchEmbeddingService(openai_api_key="invalid-key")
        # Mock the API call to raise
        service._call_api = AsyncMock(side_effect=RuntimeError("API down"))
        result = await service.get_embedding("hello")
        assert result is None  # graceful fallback

    @pytest.mark.asyncio
    async def test_get_embeddings_batch(self):
        from domains.search.engine.embedding_service import SearchEmbeddingService

        service = SearchEmbeddingService(openai_api_key="test-key")
        # Pre-populate cache for one text
        key = service._cache_key("cached")
        service._cache[key] = [0.5, 0.6]

        # Mock API for uncached texts
        service._call_api_batch = AsyncMock(
            return_value=[[0.1, 0.2], [0.3, 0.4]]
        )

        results = await service.get_embeddings_batch(["cached", "text1", "text2"])
        assert results[0] == [0.5, 0.6]  # from cache
        assert results[1] == [0.1, 0.2]  # from API
        assert results[2] == [0.3, 0.4]  # from API

    @pytest.mark.asyncio
    async def test_get_embeddings_batch_empty(self):
        from domains.search.engine.embedding_service import SearchEmbeddingService

        service = SearchEmbeddingService(openai_api_key="test-key")
        results = await service.get_embeddings_batch([])
        assert results == []

    def test_dimensions(self):
        from domains.search.engine.embedding_service import SearchEmbeddingService

        assert SearchEmbeddingService(model="text-embedding-3-large").dimensions == 3072
        assert SearchEmbeddingService(model="text-embedding-3-small").dimensions == 1536
        assert SearchEmbeddingService(model="all-MiniLM-L6-v2").dimensions == 384

    def test_cache_eviction(self):
        from domains.search.engine.embedding_service import SearchEmbeddingService

        service = SearchEmbeddingService(openai_api_key="test-key", max_cache_entries=4)
        for i in range(4):
            service._cache[f"key{i}"] = [float(i)]

        # Adding a 5th should trigger eviction of ~25% (1 item)
        service._cache["key4"] = [4.0]
        service._evict_if_needed()
        # 5 items, evict floor(5/4)=1 → 4 remain
        assert len(service._cache) == 4
        # The oldest key ("key0") should be evicted
        assert "key0" not in service._cache


# ── HybridSearchResult Tests ──────────────────────────────────────


class TestHybridSearchResult:
    """Test the result dataclass and serialization."""

    def test_to_dict(self):
        r = HybridSearchResult(
            id="123",
            name_ar="شركةテスト",
            score=0.05,
            fulltext_score=0.03,
            semantic_score=0.02,
            match_type="hybrid",
        )
        d = r.to_dict()
        assert d["id"] == "123"
        assert d["name_ar"] == "شركةテスト"
        assert d["score"] == 0.05
        assert d["match_type"] == "hybrid"
        assert "explanation" in d

    def test_default_values(self):
        r = HybridSearchResult(id="1")
        assert r.match_type == "fulltext"
        assert r.score == 0.0
        assert r.name_ar == ""


# ── Integration-style Tests (with mocked DB) ─────────────────────


class TestHybridSearchEngineIntegration:
    """Integration tests using mocked database sessions."""

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        engine = HybridSearchEngine(
            session_factory=MagicMock(),
            embedding_service=None,
        )
        result = await engine.search("", tenant_id="t1")
        assert result.items == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_search_whitespace_query(self):
        engine = HybridSearchEngine(
            session_factory=MagicMock(),
            embedding_service=None,
        )
        result = await engine.search("   ", tenant_id="t1")
        assert result.items == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_search_fulltext_only(self):
        """Search without embedding service falls back to fulltext only."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        # Mock the SQL result
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {
                "id": "1",
                "name_ar": "شركة الأمل",
                "name_en": "Al Amal Co",
                "cr_number": "1010123456",
                "city": "الرياض",
                "region": "الرياض",
                "industry": "تقنية",
                "status": "active",
                "activity_description": "خدمات تقنية",
                "rank": 0.8,
            }
        ]
        mock_session.execute.return_value = mock_result

        factory = MagicMock(return_value=mock_session)
        engine = HybridSearchEngine(
            session_factory=factory,
            embedding_service=None,
        )

        response = await engine.search("الأمل", tenant_id="t1")

        assert response.total == 1
        assert response.items[0].name_ar == "شركة الأمل"
        assert response.items[0].match_type == "fulltext"
        assert response.strategy == "hybrid"

    @pytest.mark.asyncio
    async def test_search_hybrid_with_mocked_semantic(self):
        """Full hybrid search with mocked embedding service and DB."""
        # Mock embedding service
        mock_embed = AsyncMock()
        mock_embed.get_embedding = AsyncMock(return_value=[0.1] * 3072)

        # Mock session
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        # Full-text result
        ft_result = MagicMock()
        ft_result.mappings.return_value.all.return_value = [
            {
                "id": "1",
                "name_ar": "شركة الأمل",
                "name_en": "Al Amal",
                "cr_number": "100",
                "city": "الرياض",
                "region": "الرياض",
                "industry": "تقنية",
                "status": "active",
                "activity_description": "",
                "rank": 0.5,
            },
            {
                "id": "2",
                "name_ar": "مؤسسة النور",
                "name_en": "Al Noor",
                "cr_number": "200",
                "city": "جدة",
                "region": "جدة",
                "industry": "تجارة",
                "status": "active",
                "activity_description": "",
                "rank": 0.3,
            },
        ]

        # Semantic result
        sem_result = MagicMock()
        sem_result.mappings.return_value.all.return_value = [
            {
                "id": "1",
                "name_ar": "شركة الأمل",
                "name_en": "Al Amal",
                "cr_number": "100",
                "city": "الرياض",
                "region": "الرياض",
                "industry": "تقنية",
                "status": "active",
                "activity_description": "",
                "similarity": 0.85,
            },
            {
                "id": "3",
                "name_ar": "شركة البشائر",
                "name_en": "Bashayer",
                "cr_number": "300",
                "city": "الرياض",
                "region": "الرياض",
                "industry": "تقنية",
                "status": "active",
                "activity_description": "",
                "similarity": 0.72,
            },
        ]

        # Each search method calls SET LOCAL then SELECT (2 calls each),
        # so we need 4 execute calls total for fulltext + semantic
        mock_session.execute.side_effect = [
            MagicMock(),  # SET LOCAL (fulltext)
            ft_result,     # SELECT (fulltext)
            MagicMock(),  # SET LOCAL (semantic)
            sem_result,    # SELECT (semantic)
        ]

        factory = MagicMock(return_value=mock_session)
        engine = HybridSearchEngine(
            session_factory=factory,
            embedding_service=mock_embed,
        )

        response = await engine.search("الأمل", tenant_id="t1")

        assert response.total == 3  # 2 ft + 1 unique semantic
        # Doc 1 appears in both → hybrid, should be ranked first
        assert response.items[0].id == "1"
        assert response.items[0].match_type == "hybrid"
        # Doc 2 only in fulltext
        assert response.items[1].match_type in ("fulltext", "semantic")
        # Response metadata
        assert response.fulltext_count == 2
        assert response.semantic_count == 2
        assert response.took_ms >= 0

    @pytest.mark.asyncio
    async def test_search_semantic_failure_graceful_fallback(self):
        """When semantic search fails, fulltext results are still returned."""
        mock_embed = AsyncMock()
        mock_embed.get_embedding = AsyncMock(side_effect=RuntimeError("API down"))

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ft_result = MagicMock()
        ft_result.mappings.return_value.all.return_value = [
            {
                "id": "1",
                "name_ar": "شركة",
                "name_en": "",
                "cr_number": "100",
                "city": "",
                "region": "",
                "industry": "",
                "status": "active",
                "activity_description": "",
                "rank": 0.5,
            }
        ]
        mock_session.execute.return_value = ft_result

        factory = MagicMock(return_value=mock_session)
        engine = HybridSearchEngine(
            session_factory=factory,
            embedding_service=mock_embed,
        )

        response = await engine.search("test", tenant_id="t1")
        assert response.total == 1
        assert response.items[0].match_type == "fulltext"

    @pytest.mark.asyncio
    async def test_search_pagination(self):
        """Verify offset/limit pagination works correctly."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        ft_result = MagicMock()
        ft_result.mappings.return_value.all.return_value = [
            {
                "id": str(i),
                "name_ar": f"Company {i}",
                "name_en": "",
                "cr_number": str(100 + i),
                "city": "",
                "region": "",
                "industry": "",
                "status": "active",
                "activity_description": "",
                "rank": 1.0 - i * 0.1,
            }
            for i in range(10)
        ]
        mock_session.execute.return_value = ft_result

        factory = MagicMock(return_value=mock_session)
        engine = HybridSearchEngine(
            session_factory=factory,
            embedding_service=None,
        )

        # Page 1
        r1 = await engine.search("test", tenant_id="t1", limit=3, offset=0)
        assert len(r1.items) == 3
        assert r1.items[0].id == "0"

        # Page 2
        r2 = await engine.search("test", tenant_id="t1", limit=3, offset=3)
        assert len(r2.items) == 3
        assert r2.items[0].id == "3"
