"""DB-05 Slice 3 (DEC-122): index names match ORM after rename migration."""

from __future__ import annotations

from app.modules.revenue_execution.models import Opportunity, Task
from app.modules.webhooks.repository import WebhookDeliveryModel, WebhookSubscriptionModel
from domains.notifications.db_models import NotificationModel
from domains.workflow.db_models import ScheduledJobModel


def _index_names(model) -> set[str]:
    return {ix.name for ix in model.__table__.indexes if ix.name}


def test_opportunity_indexes_no_rev_prefix_no_status_dup() -> None:
    names = _index_names(Opportunity)
    assert "ix_opportunities_tenant_stage" in names
    assert "ix_opportunities_company" in names
    assert "ix_opportunities_tenant_status" not in names
    assert not any(n.startswith("ix_rev_") for n in names)
    # company_id must not also auto-index as company_id (duplicate)
    assert "ix_opportunities_company_id" not in names


def test_task_indexes_no_rev_prefix() -> None:
    names = _index_names(Task)
    assert "ix_tasks_tenant_priority" in names
    assert "ix_tasks_assignee_completed" in names
    assert not any(n.startswith("ix_rev_") for n in names)


def test_webhook_orm_index_true_names() -> None:
    # index=True → SQLAlchemy default ix_<table>_<col>
    sub_cols = WebhookSubscriptionModel.__table__.c
    del_cols = WebhookDeliveryModel.__table__.c
    assert sub_cols.tenant_id.index is True
    assert del_cols.subscription_id.index is True


def test_notification_composite_index_names() -> None:
    names = _index_names(NotificationModel)
    assert "ix_notifications_user_read" in names
    assert "ix_notifications_tenant_type" in names


def test_scheduled_job_next_run_index_true() -> None:
    assert ScheduledJobModel.__table__.c.next_run_at.index is True
