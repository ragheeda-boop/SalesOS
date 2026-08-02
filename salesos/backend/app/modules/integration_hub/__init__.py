"""STORY-08-01 — Integration Hub framework (SourceConnector contract).

Generic connector surface only — no Odoo/vendor leakage here.
STORY-08-02+ owns persistence/credentials. Not Production GO.
"""

from app.modules.integration_hub.certify import certify_source_connector
from app.modules.integration_hub.fake_adapter import FakeSourceConnector
from app.modules.integration_hub.source_connector import SourceConnector
from app.modules.integration_hub.types import (
    ConnectionTestResult,
    IncrementalCursor,
    PullIncrementalResult,
    PullRecord,
    WriteBackRequest,
    WriteBackResult,
)

__all__ = [
    "ConnectionTestResult",
    "FakeSourceConnector",
    "IncrementalCursor",
    "PullIncrementalResult",
    "PullRecord",
    "SourceConnector",
    "WriteBackRequest",
    "WriteBackResult",
    "certify_source_connector",
]
