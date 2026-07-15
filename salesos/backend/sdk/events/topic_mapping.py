"""Topic mapping: domain event types → Kafka topics.

Each domain gets its own topic. Event types are mapped to their
domain topic for routing. This keeps the topic count manageable
while allowing consumers to subscribe at the domain level.
"""

TOPIC_PREFIX = "salesos"

DOMAIN_PREFIXES: dict[str, str] = {
    # identity
    "tenant": "identity",
    "user": "identity",
    # company
    "company": "company",
    "branch": "company",
    "license": "company",
    "contact": "company",
    # entity_resolution
    "entity_resolution": "entity_resolution",
    "golden_record": "entity_resolution",
    # timeline
    "activity": "timeline",
    "timeline": "timeline",
    # crm
    "opportunity": "crm",
    "pipeline": "crm",
    "meeting": "crm",
    "email": "crm",
    "nba": "crm",
    # scoring
    "lead": "scoring",
    "recommendation": "scoring",
    "embedding": "scoring",
    # ai
    "agent": "ai",
    # workflow
    "workflow": "workflow",
    # integration
    "integration": "integration",
    "data_import": "integration",
    "data_export": "integration",
    # billing
    "subscription": "billing",
    "usage": "billing",
}

# Explicit event type → domain overrides for edge cases
# where prefix alone is ambiguous (e.g. 'company.scored' → 'scoring')
EVENT_TYPE_OVERRIDES: dict[str, str] = {
    "company.scored": "scoring",
    "company.enriched": "company",
}

# Reverse mapping: domain → list of event prefixes
DOMAIN_EVENT_PREFIXES: dict[str, list[str]] = {}
for prefix, domain in DOMAIN_PREFIXES.items():
    DOMAIN_EVENT_PREFIXES.setdefault(domain, []).append(prefix)

ALL_TOPICS: list[str] = sorted({f"{TOPIC_PREFIX}.{d}" for d in DOMAIN_EVENT_PREFIXES})


def event_type_to_topic(event_type: str) -> str:
    """Map an event type string to its Kafka topic.

    Uses explicit event_type overrides first, then falls back to
    prefix-based domain mapping (e.g. 'company.created'
    → prefix 'company' → topic 'salesos.company').

    Falls back to 'salesos.system' for unknown event types.
    """
    domain = EVENT_TYPE_OVERRIDES.get(event_type)
    if domain is not None:
        return f"{TOPIC_PREFIX}.{domain}"

    prefix = event_type.split(".")[0] if "." in event_type else event_type
    domain = DOMAIN_PREFIXES.get(prefix)
    if domain is None:
        domain = "system"
    return f"{TOPIC_PREFIX}.{domain}"


def topic_to_domain(topic: str) -> str:
    """Extract domain name from a fully-qualified topic name.

    'salesos.company' → 'company'
    """
    if topic.startswith(f"{TOPIC_PREFIX}."):
        return topic[len(TOPIC_PREFIX) + 1:]
    return topic


def topics_for_event_types(event_types: list[str]) -> list[str]:
    """Return the unique topics needed for a list of event types."""
    return sorted({event_type_to_topic(et) for et in event_types})
