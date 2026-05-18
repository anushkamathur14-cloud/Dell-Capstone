"""Environment-aware settings loader."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(alias="DATABASE_URL")
    enable_pgvector: bool = Field(default=False, alias="ENABLE_PGVECTOR")
    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str | None = Field(default=None, alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="dell-capstone-validation", alias="LANGCHAIN_PROJECT")
    benchmark_data_dir: str = Field(
        default="synthetic_env/benchmarks/generated_sanity_calibrated",
        alias="BENCHMARK_DATA_DIR",
    )
    enable_validation_llm: bool = Field(default=False, alias="ENABLE_VALIDATION_LLM")
    validation_llm_model: str = Field(default="gpt-4o-mini", alias="VALIDATION_LLM_MODEL")
    enable_recommendation_llm: bool = Field(default=False, alias="ENABLE_RECOMMENDATION_LLM")
    recommendation_llm_model: str = Field(default="gpt-4o-mini", alias="RECOMMENDATION_LLM_MODEL")
    recommendation_variance_lambda: float = Field(default=0.2, alias="RECOMMENDATION_VARIANCE_LAMBDA")
    recommendation_uncertainty_weight: float = Field(default=0.2, alias="RECOMMENDATION_UNCERTAINTY_WEIGHT")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def get_settings() -> Settings:
    return Settings()
