"""Shared query-building utilities for graph repository implementations."""

from __future__ import annotations

import re
from typing import Optional

_CYPHER_IDENT_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _validate_cypher_identifier(name: str, kind: str = "identifier") -> str:
    """Validate a string is safe to use as a Cypher identifier."""
    if not _CYPHER_IDENT_RE.match(name):
        raise ValueError(f"Invalid Cypher {kind}: {name!r}")
    return name


def build_tenant_filter(tenant_id: str) -> str:
    """Return a Cypher tenant-filter string for use in MATCH clauses.

    Returns a string like "{tenant_id: $tenant_id}" when tenant_id is
    non-empty, otherwise returns an empty string (no filter).
    """
    if tenant_id:
        return "{tenant_id: $tenant_id}"
    return ""


def build_tenant_params(tenant_id: str, base_params: Optional[dict] = None) -> dict:
    """Merge tenant_id into a parameter dict for tenant-filtered queries.

    Returns a copy of base_params with ``tenant_id`` added. If base_params
    is None, returns a new dict containing only ``tenant_id``.
    """
    params = dict(base_params or {})
    if tenant_id:
        params["tenant_id"] = tenant_id
    return params
