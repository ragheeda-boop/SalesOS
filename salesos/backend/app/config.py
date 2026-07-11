from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    env: str = "development"
    debug: bool = True
    secret_key: str  # Must be set via SECRET_KEY environment variable
    allowed_hosts: str = "http://localhost:3000,http://127.0.0.1:3000"

    postgres_user: str = "salesos"
    postgres_password: str  # Must be set via POSTGRES_PASSWORD
    postgres_db: str = "salesos"
    postgres_host: str = "postgres"
    postgres_port: int = 6432

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str  # Must be set via NEO4J_PASSWORD

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_group_id: str = "salesos-group"
    kafka_auto_offset_reset: str = "earliest"

    redis_url: str = "redis://redis:6379/0"

    jwt_secret_key: str  # Must be set via JWT_SECRET_KEY environment variable
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    openai_api_key: str = ""
    notion_token: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-large"

    next_public_api_url: str = "http://localhost:8000"

    feature_search_fuzzy_v2: bool = False
    feature_ai_copilot: bool = False
    feature_crm_kanban: bool = False

    log_level: str = "DEBUG"
    sentry_dsn: str = ""
    service_version: str = "0.1.0"
    sentry_traces_sample_rate: float = 0.1

    # Neo4j connection details
    neo4j_database: str = "neo4j"
    neo4j_max_connection_pool_size: int = 50
    neo4j_connection_acquisition_timeout: int = 30
    neo4j_max_transaction_retry_time: int = 10

    # Rate limiting
    rate_limit_default: int = 60
    rate_limit_window: int = 60
    rate_limit_health: int = 120
    rate_limit_identity: int = 10
    rate_limit_authenticated: int = 60
    rate_limit_anonymous: int = 20

    # CORS
    cors_allow_methods: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    cors_allow_headers: str = "Authorization,Content-Type,X-Tenant-Id,X-Request-ID,X-CSRF-Token"

    # Redis timeouts
    redis_socket_connect_timeout: int = 2
    redis_socket_timeout: int = 2
    redis_health_socket_connect_timeout: int = 1
    redis_health_socket_timeout: int = 1

    # Meilisearch
    meili_url: str = "http://meilisearch:7700"
    meili_master_key: str = ""

    # Celery
    celery_task_time_limit: int = 600
    celery_task_soft_time_limit: int = 300
    celery_worker_max_tasks_per_child: int = 1000
    celery_result_expires: int = 86400
    celery_worker_prefetch_multiplier: int = 1
    celery_max_retries: int = 3
    celery_default_retry_delay: int = 60
    celery_process_entity_delay: int = 30
    celery_index_delay: int = 30
    celery_enrich_delay: int = 120
    celery_sync_notion_delay: int = 300

    # Rate limiter cleanup
    rate_limit_cleanup_interval: int = 300

    # Notion
    notion_request_timeout: int = 60

    # LLM defaults
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024
    llm_research_max_tokens: int = 2048


settings = Settings()
