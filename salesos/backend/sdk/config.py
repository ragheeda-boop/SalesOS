"""SDK-level configuration loaded from environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class SdkSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-large"
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str  # Must be set via NEO4J_PASSWORD
    redis_url: str = "redis://redis:6379/0"
    default_cache_ttl: int = 300
    service_version: str = "1.0.0"
    environment: str = "development"
    otlp_endpoint: str = "http://otel-collector:4318/v1/traces"

    # Neo4j
    neo4j_database: str = "neo4j"
    neo4j_max_transaction_retry_time: int = 10

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_group_id: str = "salesos-group"
    kafka_auto_offset_reset: str = "earliest"

    # LLM
    openai_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024
    llm_research_max_tokens: int = 2048


sdk_settings = SdkSettings()
