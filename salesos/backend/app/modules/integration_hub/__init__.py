"""Integration Hub framework (STORY-08-01..08-05).

SourceConnector + ExternalSystemConnection + FieldMappingConfig/drift + ACL + SyncRun.
No Odoo/vendor leakage in this package. Not Production GO.
"""

from app.modules.integration_hub.anti_corruption import (
    AclValidationError,
    CanonicalRecord,
    OdooTranslator,
)
from app.modules.integration_hub.certify import certify_source_connector
from app.modules.integration_hub.connection_service import ExternalSystemConnectionService
from app.modules.integration_hub.drift_job import DriftJobResult, run_field_drift_job
from app.modules.integration_hub.fake_adapter import FakeSourceConnector
from app.modules.integration_hub.field_mapping_service import FieldMappingConfigService
from app.modules.integration_hub.models import (
    ExternalSystemConnectionModel,
    FieldMappingConfigModel,
    SyncRunModel,
)
from app.modules.integration_hub.source_connector import SourceConnector
from app.modules.integration_hub.sync_run_service import SyncRunService
from app.modules.integration_hub.sync_schedule import (
    KIND_INTEGRATION_HUB_SYNC,
    schedule_connection_sync,
    tick_with_sync_logging,
)
from app.modules.integration_hub.types import (
    ConnectionTestResult,
    IncrementalCursor,
    PullIncrementalResult,
    PullRecord,
    WriteBackRequest,
    WriteBackResult,
)

__all__ = [
    "AclValidationError",
    "CanonicalRecord",
    "ConnectionTestResult",
    "DriftJobResult",
    "ExternalSystemConnectionModel",
    "ExternalSystemConnectionService",
    "FakeSourceConnector",
    "FieldMappingConfigModel",
    "FieldMappingConfigService",
    "IncrementalCursor",
    "KIND_INTEGRATION_HUB_SYNC",
    "OdooTranslator",
    "PullIncrementalResult",
    "PullRecord",
    "SourceConnector",
    "SyncRunModel",
    "SyncRunService",
    "WriteBackRequest",
    "WriteBackResult",
    "certify_source_connector",
    "run_field_drift_job",
    "schedule_connection_sync",
    "tick_with_sync_logging",
]
