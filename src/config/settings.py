"""Environment-aware settings loader."""

from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/adaptive_experiments",
        alias="DATABASE_URL",
    )
    enable_pgvector: bool = Field(default=False, alias="ENABLE_PGVECTOR")
    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(default=None, alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="dell-capstone-validation", alias="LANGCHAIN_PROJECT")
    benchmark_data_dir: str = Field(
        default="synthetic_env/benchmarks/generated_sanity_calibrated",
        alias="BENCHMARK_DATA_DIR",
    )
    llm_provider: str = Field(default="auto", alias="LLM_PROVIDER")
    azure_openai_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(
        default="2024-08-01-preview", alias="AZURE_OPENAI_API_VERSION"
    )
    enable_validation_llm: bool = Field(default=False, alias="ENABLE_VALIDATION_LLM")
    validation_llm_model: str = Field(default="gpt-4o-mini", alias="VALIDATION_LLM_MODEL")
    enable_recommendation_llm: bool = Field(default=False, alias="ENABLE_RECOMMENDATION_LLM")
    recommendation_llm_model: str = Field(default="gpt-4o-mini", alias="RECOMMENDATION_LLM_MODEL")
    generation_llm_model: str = Field(default="gpt-4o", alias="GENERATION_LLM_MODEL")
    stat_causal_llm_model: str = Field(default="gpt-4.1", alias="STAT_CAUSAL_LLM_MODEL")
    orchestration_llm_model: str = Field(default="gpt-4o", alias="ORCHESTRATION_LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    recommendation_variance_lambda: float = Field(default=0.2, alias="RECOMMENDATION_VARIANCE_LAMBDA")
    recommendation_uncertainty_weight: float = Field(default=0.2, alias="RECOMMENDATION_UNCERTAINTY_WEIGHT")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def get_settings() -> Settings:
    return Settings()
