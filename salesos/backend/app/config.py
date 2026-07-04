from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    allowed_hosts: str = "http://localhost:3000,http://127.0.0.1:3000"

    postgres_user: str = "salesos"
    postgres_password: str = "salesos_dev_password"
    postgres_db: str = "salesos"
    postgres_host: str = "postgres"
    postgres_port: int = 6432

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "salesos_neo4j_dev"

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


settings = Settings()
