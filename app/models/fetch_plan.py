from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import TruncationMode


class TruncationPolicy(BaseModel):
    mode: TruncationMode = TruncationMode.TRUNCATE
    max_results: int = Field(default=3000, ge=1)


class CompiledRequest(BaseModel):
    purpose: str
    endpoint: Literal["/studies"] = "/studies"
    params: dict[str, Any] = Field(default_factory=dict)
    fields: list[str] = Field(default_factory=list)
    page_size: int = Field(default=1000, ge=1, le=1000)
    label: str | None = None


class FetchPlan(BaseModel):
    requests: list[CompiledRequest]
    required_fields: list[str] = Field(default_factory=list)
    max_results: int = Field(default=3000, ge=1)
    truncation_policy: TruncationPolicy = Field(default_factory=TruncationPolicy)


class VersionInfo(BaseModel):
    api_version: str
    data_timestamp: str


class FetchedStudyBatch(BaseModel):
    label: str | None = None
    purpose: str
    studies: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int | None = None
    truncated: bool = False


class FetchExecutionResult(BaseModel):
    batches: list[FetchedStudyBatch]
    version_info: VersionInfo
    warnings: list[str] = Field(default_factory=list)

