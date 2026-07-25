"""PostgreSQL Feature Store repository — re-exports from postgres_repo for compatibility."""
from __future__ import annotations

from .postgres_repo import (  # noqa: F401
    FeatureDefinitionModel,
    FeatureValueModel,
    PostgresFeatureStoreRepository,
)
