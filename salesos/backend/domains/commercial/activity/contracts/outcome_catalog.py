"""OutcomeCatalog — predefined outcomes per activity type.

Each outcome may trigger a business action via the Rule Engine.
"""

from __future__ import annotations

from .models import ActivityType, OutcomeDefinition


class OutcomeCatalog:

    _outcomes: dict[str, OutcomeDefinition] = {}
    _by_type: dict[ActivityType, list[OutcomeDefinition]] = {}

    @classmethod
    def load_defaults(cls) -> None:
        cls._outcomes.clear()
        cls._by_type.clear()
        for od in OutcomeDefinition._default_catalog():
            cls._outcomes[od.id] = od
            if od.activity_type not in cls._by_type:
                cls._by_type[od.activity_type] = []
            cls._by_type[od.activity_type].append(od)

    @classmethod
    def get(cls, outcome_id: str) -> OutcomeDefinition | None:
        if not cls._outcomes:
            cls.load_defaults()
        return cls._outcomes.get(outcome_id)

    @classmethod
    def for_type(cls, activity_type: ActivityType) -> list[OutcomeDefinition]:
        if not cls._outcomes:
            cls.load_defaults()
        return cls._by_type.get(activity_type, [])

    @classmethod
    def all_actions(cls) -> list[str]:
        if not cls._outcomes:
            cls.load_defaults()
        return list(set(
            od.business_action for od in cls._outcomes.values()
            if od.business_action != "none"
        ))
