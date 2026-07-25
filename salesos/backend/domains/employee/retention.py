"""GDPR and Data Retention Policy for Employee Domain.

Defines:
  - Data classification levels per field
  - Retention periods for employee data
  - Purge strategy for soft-deleted records
  - Right-to-erasure workflow

PII Classification (per field on users table):
  - full_name:           PII (personal)         — retained until account deletion
  - full_name_ar:        PII (personal)         — retained until account deletion
  - email:               PII (contact)          — retained until account deletion
  - phone:               PII (sensitive)        — masked in API responses
  - avatar_url:          PII (biometric-adjacent)— retained until account deletion
  - password_hash:       PII (sensitive)        — never exposed via API
  - department:          Non-PII                — retained indefinitely (aggregate)
  - role:                Non-PII                — retained indefinitely (aggregate)
  - preferences:         PII (behavioral)       — retained until account deletion
  - last_login_at:       PII (behavioral)       — retained 90 days post-deletion

Retention Periods:
  - Active employee data:          Indefinite (while is_active=True)
  - Inactive employee data:        90 days from is_active=False (if deleted_at is NULL)
  - Soft-deleted data (deleted_at): 30 days from deleted_at, then purge
  - Signals data:                 30 days from employee deletion
  - Scores data:                  30 days from employee deletion
  - Audit logs:                   1 year minimum (compliance), 3 years recommended

Right-to-Erasure Workflow:
  1. Admin initiates bulk delete → sets is_active=False + deleted_at=now()
  2. After 30-day grace period, scheduled job hard-deletes:
     a. User record (sets full_name='[deleted]', email='[deleted]', phone=null, avatar_url=null)
     b. Associated signals (DELETE FROM employee_signals WHERE employee_id IN (...))
     c. Associated scores (DELETE FROM employee_scores WHERE employee_id IN (...))
     d. Audit logs preserved (immutable, for compliance)
"""

from datetime import datetime, timedelta, timezone
from typing import Any


RETENTION_DAYS_SOFT_DELETED = 30
RETENTION_DAYS_INACTIVE = 90
RETENTION_DAYS_SIGNALS_AFTER_DELETION = 30


PII_FIELDS = {
    "full_name": "personal",
    "full_name_ar": "personal",
    "email": "contact",
    "phone": "sensitive",
    "avatar_url": "biometric_adjacent",
    "password_hash": "sensitive_never_exposed",
    "preferences": "behavioral",
    "last_login_at": "behavioral",
}

NON_PII_FIELDS = {
    "id", "tenant_id", "role", "department", "is_active", "is_verified",
    "failed_attempts", "locked_until", "deleted_at", "created_at", "updated_at",
}


def is_eligible_for_purge(deleted_at: datetime | None, reference_date: datetime | None = None) -> bool:
    """Check if a soft-deleted record has exceeded the retention grace period."""
    if deleted_at is None:
        return False
    now = reference_date or datetime.now(timezone.utc)
    return (now - deleted_at).days >= RETENTION_DAYS_SOFT_DELETED


def mask_pii_field(field_name: str, value: Any) -> Any:
    """Mask PII fields for public-facing API responses."""
    if field_name in ("phone",):
        if value and isinstance(value, str) and len(value) > 4:
            return "****" + value[-4:]
        return "****"
    if field_name == "email":
        if value and isinstance(value, str) and "@" in value:
            local, domain = value.split("@", 1)
            return local[:2] + "****@" + domain
        return "****@****"
    return value
