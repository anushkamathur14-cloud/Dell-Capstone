"""Environment-aware settings loader."""

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
    langchain_api_key: str | None = Field(default=None, alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="dell-capstone-validation", alias="LANGCHAIN_PROJECT")
    benchmark_data_dir: str = Field(
        default="synthetic_env/benchmarks/generated_sanity_calibrated",
        alias="BENCHMARK_DATA_DIR",
    )
    # Azure OpenAI (Microsoft Foundry) — deployment names, not model marketing names
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field(
        default="2024-12-01-preview",
        alias="AZURE_OPENAI_API_VERSION",
    )
    azure_openai_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    enable_validation_llm: bool = Field(default=False, alias="ENABLE_VALIDATION_LLM")
    validation_llm_model: str = Field(default="capstone-mini", alias="VALIDATION_LLM_MODEL")
    generation_llm_model: str = Field(default="capstone-standard", alias="GENERATION_LLM_MODEL")
    stat_llm_model: str = Field(default="capstone-code", alias="STAT_LLM_MODEL")
    enable_causal_agent_loop: bool = Field(default=False, alias="ENABLE_CAUSAL_AGENT_LOOP")
    enable_generation_agent: bool = Field(default=False, alias="ENABLE_GENERATION_AGENT")
    prompt_disclosure_level: str = Field(default="standard", alias="PROMPT_DISCLOSURE_LEVEL")
    causal_agent_max_iterations: int = Field(default=6, alias="CAUSAL_AGENT_MAX_ITERATIONS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def get_settings() -> Settings:
    return Settings()
