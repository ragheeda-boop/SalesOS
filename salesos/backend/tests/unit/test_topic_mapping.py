"""Tests for domain event → Kafka topic mapping."""

from sdk.events.topic_mapping import (
    ALL_TOPICS,
    DOMAIN_PREFIXES,
    TOPIC_PREFIX,
    event_type_to_topic,
    topic_to_domain,
    topics_for_event_types,
)


def test_event_type_to_topic_identity() -> None:
    assert event_type_to_topic("tenant.created") == "salesos.identity"
    assert event_type_to_topic("user.registered") == "salesos.identity"


def test_event_type_to_topic_company() -> None:
    assert event_type_to_topic("company.created") == "salesos.company"
    assert event_type_to_topic("company.merged") == "salesos.company"
    assert event_type_to_topic("branch.created") == "salesos.company"


def test_event_type_to_topic_crm() -> None:
    assert event_type_to_topic("opportunity.created") == "salesos.crm"
    assert event_type_to_topic("opportunity.stage_changed") == "salesos.crm"
    assert event_type_to_topic("meeting.completed") == "salesos.crm"
    assert event_type_to_topic("email.analyzed") == "salesos.crm"
    assert event_type_to_topic("nba.generated") == "salesos.crm"


def test_event_type_to_topic_scoring() -> None:
    assert event_type_to_topic("company.scored") == "salesos.scoring"
    assert event_type_to_topic("lead.scored") == "salesos.scoring"
    assert event_type_to_topic("recommendation.generated") == "salesos.scoring"


def test_event_type_to_topic_ai() -> None:
    assert event_type_to_topic("agent.task_created") == "salesos.ai"
    assert event_type_to_topic("agent.task_completed") == "salesos.ai"


def test_event_type_to_topic_timeline() -> None:
    assert event_type_to_topic("activity.logged") == "salesos.timeline"
    assert event_type_to_topic("timeline.updated") == "salesos.timeline"


def test_event_type_to_topic_workflow() -> None:
    assert event_type_to_topic("workflow.triggered") == "salesos.workflow"


def test_event_type_to_topic_entity_resolution() -> None:
    assert event_type_to_topic("entity_resolution.completed") == "salesos.entity_resolution"
    assert event_type_to_topic("golden_record.created") == "salesos.entity_resolution"


def test_event_type_to_topic_integration() -> None:
    assert event_type_to_topic("integration.connected") == "salesos.integration"
    assert event_type_to_topic("data_import.completed") == "salesos.integration"


def test_event_type_to_topic_billing() -> None:
    assert event_type_to_topic("subscription.created") == "salesos.billing"
    assert event_type_to_topic("usage.recorded") == "salesos.billing"


def test_event_type_to_topic_unknown_falls_back_to_system() -> None:
    assert event_type_to_topic("unknown.event") == "salesos.system"


def test_topic_to_domain() -> None:
    assert topic_to_domain("salesos.company") == "company"
    assert topic_to_domain("salesos.crm") == "crm"
    assert topic_to_domain("salesos.identity") == "identity"


def test_topics_for_event_types_deduplicates() -> None:
    types = ["company.created", "company.updated", "opportunity.created"]
    topics = topics_for_event_types(types)
    assert topics == ["salesos.company", "salesos.crm"]


def test_topics_for_event_types_single() -> None:
    assert topics_for_event_types(["user.registered"]) == ["salesos.identity"]


def test_all_topics_contains_all_domains() -> None:
    expected_domains = {
        "identity",
        "company",
        "entity_resolution",
        "timeline",
        "crm",
        "scoring",
        "ai",
        "workflow",
        "integration",
        "billing",
    }
    for domain in expected_domains:
        assert f"{TOPIC_PREFIX}.{domain}" in ALL_TOPICS


def test_every_domain_has_at_least_one_prefix() -> None:
    for domain_prefix in DOMAIN_PREFIXES.values():
        assert domain_prefix  # non-empty
