"""Search Caching — in-memory cache for search results with TTL and hit tracking."""

from .cache import SearchCache, SearchCacheStats

__all__ = ["SearchCache", "SearchCacheStats"]
