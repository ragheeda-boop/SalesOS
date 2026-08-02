"""Integration Hub framework (STORY-08-01..08-03).

SourceConnector + ExternalSystemConnection + FieldMappingConfig/drift.
No Odoo/vendor leakage in this package. Not Production GO.
"""

from app.modules.integration_hub.certify import certify_source_connector
from app.modules.integration_hub.connection_service import ExternalSystemConnectionService
from app.modules.integration_hub.drift_job import DriftJobResult, run_field_drift_job
from app.modules.integration_hub.fake_adapter import FakeSourceConnector
from app.modules.integration_hub.field_mapping_service import FieldMappingConfigService
from app.modules.integration_hub.models import (
    ExternalSystemConnectionModel,
    FieldMappingConfigModel,
)
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
    "DriftJobResult",
    "ExternalSystemConnectionModel",
    "ExternalSystemConnectionService",
    "FakeSourceConnector",
    "FieldMappingConfigModel",
    "FieldMappingConfigService",
    "IncrementalCursor",
    "PullIncrementalResult",
    "PullRecord",
    "SourceConnector",
    "WriteBackRequest",
    "WriteBackResult",
    "certify_source_connector",
    "run_field_drift_job",
]
