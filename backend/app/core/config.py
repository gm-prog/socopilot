"""Application configuration via environment variables."""

from functools import lru_cache
import os
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_ENV_FILES = tuple(
    str(candidate)
    for parent in Path(__file__).resolve().parents
    for candidate in [parent / ".env"]
    if candidate.exists()
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="SOCoPilot", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    build_version: str = Field(default="0.2.0", alias="BUILD_VERSION")

    secret_key: str = Field(alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    algorithm: Literal["HS256"] = "HS256"

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="socopilot", alias="POSTGRES_USER")
    postgres_password: str = Field(default="socopilot_dev", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="socopilot", alias="POSTGRES_DB")

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    celery_broker_url: str | None = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: str | None = Field(default=None, alias="CELERY_RESULT_BACKEND")

    ollama_host: str = Field(default="http://localhost:11434", alias="OLLAMA_HOST")
    ollama_llm_model: str = Field(default="mistral:7b-instruct", alias="OLLAMA_LLM_MODEL")
    ollama_embed_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBED_MODEL")

    elasticsearch_enabled: bool = Field(default=False, alias="ELASTICSEARCH_ENABLED")
    elasticsearch_url: str = Field(default="http://localhost:9200", alias="ELASTICSEARCH_URL")
    opensearch_enabled: bool = Field(default=False, alias="OPENSEARCH_ENABLED")
    opensearch_url: str = Field(default="http://opensearch:9200", alias="OPENSEARCH_URL")
    opensearch_index_alerts: str = Field(default="socopilot-alerts", alias="OPENSEARCH_INDEX_ALERTS")
    opensearch_index_iocs: str = Field(default="socopilot-iocs", alias="OPENSEARCH_INDEX_IOCS")

    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")

    abuseipdb_api_key: str = Field(default="", alias="ABUSEIPDB_API_KEY")
    virustotal_api_key: str = Field(default="", alias="VIRUSTOTAL_API_KEY")
    greynoise_api_key: str = Field(default="", alias="GREYNOISE_API_KEY")
    shodan_api_key: str = Field(default="", alias="SHODAN_API_KEY")

    dedup_time_bucket_minutes: int = Field(default=15, alias="DEDUP_TIME_BUCKET_MINUTES")
    ingest_default_source: str = Field(default="webhook", alias="INGEST_DEFAULT_SOURCE")

    enrichment_timeout_seconds: int = Field(default=15, alias="ENRICHMENT_TIMEOUT_SECONDS")
    enrichment_max_retries: int = Field(default=3, alias="ENRICHMENT_MAX_RETRIES")

    _INSECURE_SECRET_KEYS = frozenset({
        "change-me-in-production-use-openssl-rand-hex-32",
        "changeme",
        "secret",
    })

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("SECRET_KEY must not be empty")
        if len(normalized) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters")
        return normalized

    @model_validator(mode="after")
    def reject_insecure_secret_key_in_production(self) -> "Settings":
        if self.app_env not in ("development", "test") and self.secret_key in self._INSECURE_SECRET_KEYS:
            raise ValueError(
                "SECRET_KEY is set to a well-known insecure value. "
                "Generate a strong key: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return self

    @computed_field
    @property
    def search_enabled(self) -> bool:
        return self.opensearch_enabled or self.elasticsearch_enabled

    @computed_field
    @property
    def search_url(self) -> str:
        return self.opensearch_url if self.opensearch_enabled else self.elasticsearch_url

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field
    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @computed_field
    @property
    def result_backend_url(self) -> str:
        return self.celery_result_backend or f"redis://{self.redis_host}:{self.redis_port}/1"

    @computed_field
    @property
    def secret_key_source(self) -> str:
        if "SECRET_KEY" in os.environ:
            return "environment"

        for env_file in _ENV_FILES:
            try:
                for line in Path(env_file).read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("SECRET_KEY="):
                        return "env_file"
            except OSError:
                continue

        return "unknown"


@lru_cache
def get_settings() -> Settings:
    return Settings()
