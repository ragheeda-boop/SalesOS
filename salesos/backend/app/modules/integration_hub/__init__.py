"""Integration Hub framework (STORY-08-01..09-09).

SourceConnector + Hub HTTP + ConflictResolutionPolicy + OdooAdapter
(res.partner + crm.lead + mail.message + helpdesk.ticket + project.task
+ account.move CustomerInvoice) + write_date incremental + feature_odoo_integration
+ unlinked cr_number badge list API + SyncRun cursor HTTP.
Not Production GO.
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
from app.modules.integration_hub.cr_number_join import CrJoinResult, join_partner_by_cr_number
from app.modules.integration_hub.customer_invoice_sync import (
    CustomerInvoice,
    sync_customer_invoices,
)
from app.modules.integration_hub.drift_job import DriftJobResult, run_field_drift_job
from app.modules.integration_hub.fake_adapter import FakeSourceConnector
from app.modules.integration_hub.field_mapping_service import FieldMappingConfigService
from app.modules.integration_hub.models import (
    ConflictResolutionPolicyModel,
    ExternalSystemConnectionModel,
    FieldMappingConfigModel,
    SyncRunModel,
)
from app.modules.integration_hub.note_sync import sync_interaction_notes
from app.modules.integration_hub.odoo_adapter import OdooAdapter
from app.modules.integration_hub.odoo_incremental_sync import (
    FLAG_ODOO_INTEGRATION,
    pull_odoo_incremental_for_sync,
)
from app.modules.integration_hub.opportunity_sync import sync_opportunity_records
from app.modules.integration_hub.partner_sync import sync_partner_records
from app.modules.integration_hub.source_connector import SourceConnector
from app.modules.integration_hub.sync_run_service import SyncRunService
from app.modules.integration_hub.sync_schedule import (
    KIND_INTEGRATION_HUB_SYNC,
    schedule_connection_sync,
    tick_with_sync_logging,
)
from app.modules.integration_hub.task_case_extension import TaskCaseExtension
from app.modules.integration_hub.task_sync import sync_project_tasks
from app.modules.integration_hub.ticket_sync import sync_support_tickets
from app.modules.integration_hub.unlinked_badge import (
    KIND_UNLINKED_BADGE,
    badge_items_from_partner_batch,
    collect_unlinked_badges_from_error_logs,
)

__all__ = [
    "AclValidationError",
    "CanonicalRecord",
    "ConflictResolutionPolicy",
    "ConflictResolutionPolicyModel",
    "ConflictResolutionPolicyService",
    "CrJoinResult",
    "CustomerInvoice",
    "DriftJobResult",
    "ExternalSystemConnectionModel",
    "ExternalSystemConnectionService",
    "FLAG_ODOO_INTEGRATION",
    "FakeSourceConnector",
    "FeedbackLoopExclusionError",
    "FieldMappingConfigModel",
    "FieldMappingConfigService",
    "KIND_INTEGRATION_HUB_SYNC",
    "KIND_UNLINKED_BADGE",
    "OdooAdapter",
    "OdooTranslator",
    "SourceConnector",
    "SyncRunModel",
    "SyncRunService",
    "TaskCaseExtension",
    "assert_no_feedback_loop_pull",
    "badge_items_from_partner_batch",
    "certify_source_connector",
    "collect_unlinked_badges_from_error_logs",
    "filter_mappings_for_pull",
    "join_partner_by_cr_number",
    "pull_odoo_incremental_for_sync",
    "run_field_drift_job",
    "schedule_connection_sync",
    "sync_customer_invoices",
    "sync_interaction_notes",
    "sync_opportunity_records",
    "sync_partner_records",
    "sync_project_tasks",
    "sync_support_tickets",
    "tick_with_sync_logging",
]
