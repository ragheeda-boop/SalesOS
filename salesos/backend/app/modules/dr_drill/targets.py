"""STORY-14-03 — DR drill SLO targets (PRODUCTION_READINESS_CHECKLIST).

CI/non-prod harness only. Not Production GO. No live primary kill.
"""

from __future__ import annotations

# RTO ≤4 hours, RPO ≤1 hour (seconds).
RTO_TARGET_SECONDS = 4 * 60 * 60
RPO_TARGET_SECONDS = 1 * 60 * 60

DRILL_KINDS = frozenset({"full_backup_restore", "point_in_time_recovery"})
