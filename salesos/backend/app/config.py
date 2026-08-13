from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Optional comma-separated extra CORS origins to merge into allowed_hosts.
    # Set EXTRA_CORS_ORIGINS in Railway to add Vercel preview/prod URLs without
    # overwriting the full ALLOWED_HOSTS list.
    extra_cors_origins: str = ""

    @model_validator(mode="after")
    def _merge_cors_origins(self) -> "Settings":
        extras = [o.strip() for o in self.extra_cors_origins.split(",") if o.strip()]
        if extras:
            existing = [o.strip() for o in self.allowed_hosts.split(",") if o.strip()]
            merged = list(dict.fromkeys(existing + extras))
            self.allowed_hosts = ",".join(merged)
        return self

    env: str = "development"
    debug: bool = False
    secret_key: str  # Must be set via SECRET_KEY environment variable

    @field_validator("secret_key")
    @classmethod
    def _validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                'Generate with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        return v

    @field_validator("jwt_secret_key")
    @classmethod
    def _validate_jwt_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters. "
                'Generate with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        return v

    allowed_hosts: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Support DATABASE_URL (Railway, Render, etc.) or individual POSTGRES_* vars
    database_url: str = ""

    postgres_user: str = "salesos"
    postgres_password: str = ""
    postgres_db: str = "salesos"
    postgres_host: str = "postgres"
    postgres_port: int = 6432

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            # DATABASE_URL takes precedence (12-factor / Railway / Render)
            url = self.database_url
            # Already asyncpg — do not double-prefix
            if "+asyncpg://" in url or url.startswith("postgresql+asyncpg://"):
                return url
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # STORY-02-01 / R-14 remediation (docs/program/RISK_REGISTER.md,
    # docs/program/DECISION_LOG.md DEC-013): `postgres_user` above
    # (`salesos`) is a Postgres superuser with BYPASSRLS — RLS policies,
    # however correctly written, provide zero protection under that role.
    # This is the RUNTIME application's connection only; Alembic
    # (app/alembic/env.py) and app/database.py's own DDL calls in init_db()
    # keep using `resolved_database_url` (the owner role) unchanged, since
    # migrations must create/alter tables, which a restricted role cannot do.
    app_postgres_user: str = "salesos_app"
    app_postgres_password: str = ""
    app_database_url_override: str = ""

    @property
    def app_database_url(self) -> str:
        if self.app_database_url_override:
            url = self.app_database_url_override
            if "+asyncpg://" in url or url.startswith("postgresql+asyncpg://"):
                return url
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        if not self.app_postgres_password:
            # EAB-001-P0-SEC-02 / R-14: empty password previously fell back to
            # the owner role (BYPASSRLS) — silent tenant-isolation fail-open.
            # Refuse in non-dev; keep local/dev/test fallback so boots still work
            # before salesos_app is provisioned (OPERATIONS_MANUAL §14).
            env = (self.env or "").strip().lower()
            if env in ("production", "prod", "staging", "stage"):
                raise RuntimeError(
                    "APP_POSTGRES_PASSWORD is required when ENV is "
                    f"{env!r}. Empty password would fall back to the owner "
                    "role (BYPASSRLS). Provision salesos_app and set "
                    "APP_POSTGRES_USER/APP_POSTGRES_PASSWORD (R-14 / DEC-013)."
                )
            return self.resolved_database_url
        return f"postgresql+asyncpg://{self.app_postgres_user}:{self.app_postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    event_bus_type: str = "in_memory"
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_group_id: str = "salesos-group"
    kafka_auto_offset_reset: str = "earliest"

    redis_url: str = "redis://redis:6379/0"

    jwt_secret_key: str  # Must be set via JWT_SECRET_KEY environment variable
    # ADR-102: JWTs are always RS256 (RSA-4096 asymmetric via JWKS).
    # The jwt_algorithm setting is informational; actual signing is hardcoded
    # in sdk/auth/jwks.py. Setting this to anything other than RS256 has no effect.
    jwt_algorithm: str = "RS256"

    @field_validator("jwt_algorithm")
    @classmethod
    def _validate_jwt_algorithm(cls, v: str) -> str:
        if v != "RS256":
            raise ValueError("JWT_ALGORITHM must be RS256. HS256 is not supported.")
        return v
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    jwt_issuer: str = "salesos"
    jwt_audience: str = "salesos-api"  # Tenant API (existing endpoints)
    jwt_owner_audience: str = "salesos-owner-platform"  # Owner Platform (EPIC-04+)

    openai_api_key: str = ""
    notion_token: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-large"
    # Optional OpenAI-compatible endpoint (dev/staging shim). Empty = SDK default
    # (api.openai.com). Env: OPENAI_BASE_URL. Example: http://freellmapi:3001/v1
    # Does not enable copilot. Do not point this at live providers in production.
    openai_base_url: str = ""

    next_public_api_url: str = "http://localhost:8000"
    salesos_api_url: str = "http://localhost:8000"

    feature_search_fuzzy_v2: bool = False
    # GA honesty (Wave 6): keep False until AI runtime is evidence-validated.
    # Do not market copilot as production-ready while this remains False.
    # See docs/audit/ga-engineering-audit/AI_HONESTY.md
    feature_ai_copilot: bool = False
    # C.1: Postgres signal marketplace after alembic f7a1b82c3d09. Default False =
    # InMemory (current behavior). Flip only after non-prod upgrade.
    feature_signal_marketplace_postgres: bool = False
    feature_crm_kanban: bool = False
    # FE-SEC-02 vertical slice — optional httpOnly access JWT cookie (salesos_access).
    # Default False: body TokenResponse + Bearer unchanged; no half-break.
    # When True: also Set-Cookie salesos_access (httponly) on login/register/refresh.
    feature_httponly_access_cookie: bool = False

    # STORY-04-04 — soft-delete retention before hard-delete (days). Not Production GO.
    tenant_deletion_retention_days: int = 30

    # STORY-05-02 — Stripe sandbox/live credentials from env only. Never invent defaults.
    # Empty = fail-closed (webhook 503, checkout 503). Not Production GO.
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    # STORY-05-04 — dunning grace before auto-suspend (days). Policy, not a secret.
    dunning_grace_days: int = 7

    # STORY-06-02 — enforce Plan.entitlements on gated tenant paths. Policy, not a secret.
    entitlement_enforcement_enabled: bool = True

    # STORY-06-02/06-04 — entitlement resolve cache TTL (seconds). Clamped to 1..60.
    entitlement_cache_ttl_seconds: int = 60

    # STORY-06-03 — enforce UsageMeter quotas on gated paths. Policy, not a secret.
    quota_enforcement_enabled: bool = True

    # STORY-08-02 — optional Fernet key for connector credentials; empty → secret_key.
    # Policy/env only — never invent or commit real key material.
    integration_hub_encryption_key: str = ""

    log_level: str = "INFO"
    sentry_dsn: str = ""
    service_version: str = "5.1.0-rc1"
    sentry_traces_sample_rate: float = 0.1

    # Build provenance — set at deploy time (Railway: RAILWAY_GIT_COMMIT_SHA /
    # SOURCE_COMMIT; Vercel: VERCEL_GIT_COMMIT_SHA). Used by GET /version so the
    # FE /system page and CI can prove backend==frontend commit parity (GA gate).
    build_commit: str = ""
    build_date: str = ""
    build_id: str = ""

    # Neo4j connection details
    neo4j_database: str = "neo4j"
    neo4j_max_connection_pool_size: int = 50
    neo4j_connection_acquisition_timeout: int = 30
    neo4j_max_transaction_retry_time: int = 10

    # Body size limit (bytes, default 10 MB)
    max_body_size: int = 10 * 1024 * 1024

    # Rate limiting (requests per window)
    rate_limit_default: int = 60
    rate_limit_window: int = 60
    rate_limit_health: int = 120
    rate_limit_identity: int = 10
    rate_limit_authenticated: int = 100
    rate_limit_anonymous: int = 20
    rate_limit_search: int = 30

    # CORS
    cors_allow_methods: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    # Include Accept* so browser preflights from axios/fetch pass CORS checks.
    cors_allow_headers: str = (
        "Authorization,Content-Type,Accept,Accept-Language,X-Tenant-Id,X-Request-ID,X-CSRF-Token"
    )

    # Redis timeouts
    redis_socket_connect_timeout: int = 2
    redis_socket_timeout: int = 2
    redis_health_socket_connect_timeout: int = 1
    redis_health_socket_timeout: int = 1

    # Feature cache TTL (seconds, default 5 min)
    feature_cache_ttl: int = 300

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

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@salesos.io"

    # SSO / OAuth
    sso_google_client_id: str = ""
    sso_google_client_secret: str = ""
    sso_microsoft_client_id: str = ""
    sso_microsoft_client_secret: str = ""
    sso_github_client_id: str = ""
    sso_github_client_secret: str = ""

    # Odoo Integration (Track E1/E2)
    odoo_url: str = ""
    odoo_database: str = ""
    odoo_username: str = ""
    odoo_api_key: str = ""

    # Google Workspace integration
    google_redirect_uri: str = ""
    google_encryption_key: str = ""
    # Comma-separated previous keys for decrypt during rotation (optional).
    google_encryption_key_previous: str = ""
    # Post-OAuth browser return target (settings integrations panel)
    frontend_url: str = "http://localhost:3000"

    # Audit
    audit_retention_days: int = 90
    audit_excluded_paths: list[str] = [
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/ping",
        "/openapi.json",
    ]

    # API Keys
    api_key_expiry_days: int = 365

    # Demo Mode
    demo_mode: bool = False

    # Knowledge graph SQL fallback (disabled in production unless explicitly enabled)
    kg_allow_sql_fallback: bool | None = None

    def is_kg_sql_fallback_allowed(self) -> bool:
        if self.kg_allow_sql_fallback is not None:
            return self.kg_allow_sql_fallback
        return self.env.lower() not in ("production", "prod")


settings = Settings()  # type: ignore[call-arg]
