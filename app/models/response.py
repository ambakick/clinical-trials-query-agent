from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import MatchMode
from app.models.visualization import VisualizationSpec


class ResponseMetadata(BaseModel):
    query_interpretation: str
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    match_mode: MatchMode
    total_studies_matched: int | None = None
    studies_analyzed: int
    data_source: str = "clinicaltrials.gov"
    api_version: str
    data_timestamp: str
    warnings: list[str] = Field(default_factory=list)
    processing_time_ms: int | None = None


class QueryResponse(BaseModel):
    visualization: VisualizationSpec
    meta: ResponseMetadata


class ClarificationResponse(BaseModel):
    status: Literal["needs_clarification"] = "needs_clarification"
    reason: str
    question: str
    suggested_interpretation: str | None = None

