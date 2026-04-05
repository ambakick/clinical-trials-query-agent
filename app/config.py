from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, Field


def _get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def _get_env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)


def _get_env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1")
    llm_temperature: float = _get_env_float("LLM_TEMPERATURE", 0.0)
    llm_max_tokens: int = _get_env_int("LLM_MAX_TOKENS", 2000)

    ctgov_base_url: str = os.getenv("CTGOV_BASE_URL", "https://clinicaltrials.gov/api/v2")
    ctgov_timeout_seconds: int = _get_env_int("CTGOV_TIMEOUT_SECONDS", 30)
    ctgov_max_retries: int = _get_env_int("CTGOV_MAX_RETRIES", 3)
    ctgov_page_size: int = _get_env_int("CTGOV_PAGE_SIZE", 1000)
    ctgov_rate_limit_per_minute: int = _get_env_int("CTGOV_RATE_LIMIT_PER_MINUTE", 40)
    ctgov_version_ttl_seconds: int = _get_env_int("CTGOV_VERSION_TTL_SECONDS", 900)

    cache_backend: str = os.getenv("CACHE_BACKEND", "memory")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache_namespace_version: str = os.getenv("CACHE_NAMESPACE_VERSION", "v1")
    cache_ttl_plan_seconds: int = _get_env_int("CACHE_TTL_PLAN_SECONDS", 1800)
    cache_ttl_ctgov_raw_seconds: int = _get_env_int("CACHE_TTL_CTGOV_RAW_SECONDS", 3600)
    cache_ttl_response_seconds: int = _get_env_int("CACHE_TTL_RESPONSE_SECONDS", 900)

    max_studies_per_query: int = _get_env_int("MAX_STUDIES_PER_QUERY", 3000)
    max_citations_per_bucket: int = _get_env_int("MAX_CITATIONS_PER_BUCKET", 5)
    network_max_nodes: int = _get_env_int("NETWORK_MAX_NODES", 50)

    planner_prompt_version: str = os.getenv("PLANNER_PROMPT_VERSION", "v1")
    response_schema_version: str = os.getenv("RESPONSE_SCHEMA_VERSION", "v1")

    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = _get_env_int("PORT", 8000)
    log_level: str = os.getenv("LOG_LEVEL", "info")
    cors_allow_origins: list[str] = _get_env_list("CORS_ALLOW_ORIGINS", ["http://localhost:5173"])

    request_query_min_length: int = Field(default=5, ge=1)
    request_query_max_length: int = Field(default=1000, ge=32)


@lru_cache
def get_settings() -> Settings:
    return Settings()
