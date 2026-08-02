"""Integration Hub framework (STORY-08-01..08-06).

SourceConnector + connections + mappings + ACL + SyncRun + ConflictResolutionPolicy.
HTTP under /api/v1/integrations. Not Production GO.
"""

from app.modules.integration_hub.anti_corruption import (
    AclValidationError,
    CanonicalRecord,
    OdooTranslator,
)
from app.modules.integration_hub.certify import certify_source_connector
from app.modules.integration_hub.conflict_policy import (
    ConflictResolutionPolicy,
    FeedbackLoopExclusionError,
    assert_no_feedback_loop_pull,
    filter_mappings_for_pull,
)
from app.modules.integration_hub.conflict_policy_service import (
    ConflictResolutionPolicyService,
)
from app.modules.integration_hub.connection_service import ExternalSystemConnectionService
from app.modules.integration_hub.drift_job import DriftJobResult, run_field_drift_job
from app.modules.integration_hub.fake_adapter import FakeSourceConnector
from app.modules.integration_hub.field_mapping_service import FieldMappingConfigService
from app.modules.integration_hub.models import (
    ConflictResolutionPolicyModel,
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

__all__ = [
    "AclValidationError",
    "CanonicalRecord",
    "ConflictResolutionPolicy",
    "ConflictResolutionPolicyModel",
    "ConflictResolutionPolicyService",
    "DriftJobResult",
    "ExternalSystemConnectionModel",
    "ExternalSystemConnectionService",
    "FakeSourceConnector",
    "FeedbackLoopExclusionError",
    "FieldMappingConfigModel",
    "FieldMappingConfigService",
    "KIND_INTEGRATION_HUB_SYNC",
    "OdooTranslator",
    "SourceConnector",
    "SyncRunModel",
    "SyncRunService",
    "assert_no_feedback_loop_pull",
    "certify_source_connector",
    "filter_mappings_for_pull",
    "run_field_drift_job",
    "schedule_connection_sync",
    "tick_with_sync_logging",
]
