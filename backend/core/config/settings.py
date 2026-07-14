from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = Field("Enterprise AI OS", alias="APP_NAME")
    app_env: str = Field("development", alias="APP_ENV")
    app_debug: bool = Field(False, alias="APP_DEBUG")
    app_secret_key: str = Field(..., alias="APP_SECRET_KEY")
    app_host: str = Field("0.0.0.0", alias="APP_HOST")
    app_port: int = Field(8060, alias="APP_PORT")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    database_pool_size: int = Field(20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(0, alias="DATABASE_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # JWT
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    # AI Providers
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", alias="OPENAI_MODEL")

    azure_openai_api_key: str = Field("", alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field("", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: str = Field("", alias="AZURE_OPENAI_DEPLOYMENT")

    gemini_api_key: str = Field("", alias="GEMINI_API_KEY")
    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")

    ollama_base_url: str = Field("http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field("llama3", alias="OLLAMA_MODEL")

    ai_provider: str = Field("openai", alias="AI_PROVIDER")

    # Embeddings
    embedding_provider: str = Field("openai", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field("text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(1536, alias="EMBEDDING_DIMENSION")

    # Vector Store
    vector_store: str = Field("pgvector", alias="VECTOR_STORE")
    qdrant_url: str = Field("http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str = Field("", alias="QDRANT_API_KEY")

    # Elasticsearch
    elasticsearch_url: str = Field("http://localhost:9200", alias="ELASTICSEARCH_URL")
    elasticsearch_index_prefix: str = Field("enterprise_ai", alias="ELASTICSEARCH_INDEX_PREFIX")

    # Messaging
    messaging_backend: str = Field("kafka", alias="MESSAGING_BACKEND")
    kafka_bootstrap_servers: str = Field("localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    rabbitmq_url: str = Field("amqp://guest:guest@localhost:5672/", alias="RABBITMQ_URL")

    # Storage
    storage_backend: str = Field("s3", alias="STORAGE_BACKEND")
    aws_access_key_id: str = Field("", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field("", alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", alias="AWS_REGION")
    aws_s3_bucket: str = Field("enterprise-ai-documents", alias="AWS_S3_BUCKET")
    # GCS (used when STORAGE_BACKEND=gcs)
    gcs_project_id: str = Field("", alias="GCS_PROJECT_ID")
    gcs_bucket: str = Field("enterprise-ai-documents", alias="GCS_BUCKET")
    # Leave empty on Cloud Run — ADC is injected automatically.
    # Set to a JSON service-account key string only for local dev.
    gcs_credentials_json: str = Field("", alias="GCS_CREDENTIALS_JSON")

    # Observability
    otel_exporter_otlp_endpoint: str = Field("", alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_service_name: str = Field("enterprise-ai-os", alias="OTEL_SERVICE_NAME")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_format: str = Field("json", alias="LOG_FORMAT")

    # Multi-tenancy
    default_tenant_id: str = Field("default", alias="DEFAULT_TENANT_ID")
    tenant_isolation_strategy: str = Field("shared_schema", alias="TENANT_ISOLATION_STRATEGY")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"], alias="CORS_ORIGINS"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value

    # Email
    smtp_host: str = Field("smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT")
    smtp_user: str = Field("", alias="SMTP_USER")
    smtp_password: str = Field("", alias="SMTP_PASSWORD")
    email_from: str = Field("noreply@enterprise-ai.com", alias="EMAIL_FROM")


settings = Settings()
