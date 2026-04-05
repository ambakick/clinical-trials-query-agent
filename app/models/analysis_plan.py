from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    CitationMode,
    ComparisonDimension,
    GroupByField,
    MatchMode,
    MeasureKind,
    QueryClass,
    RelationshipKind,
    TimeBucket,
    TrialPhase,
    TrialStatus,
    ChartType,
)


class ComparisonSelection(BaseModel):
    dimension: ComparisonDimension
    left: str
    right: str


class EntitySelection(BaseModel):
    drug_name: str | None = None
    condition: str | None = None
    sponsor: str | None = None
    country: str | None = None
    comparison: ComparisonSelection | None = None
    relationship_kind: RelationshipKind | None = None


class FilterSelection(BaseModel):
    trial_phase: list[TrialPhase] | None = None
    sponsor: str | None = None
    country: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    status: list[TrialStatus] | None = None
    top_n: int | None = Field(default=10, ge=1, le=50)

    @model_validator(mode="after")
    def validate_years(self) -> "FilterSelection":
        if self.start_year is not None and self.end_year is not None and self.start_year > self.end_year:
            raise ValueError("filter start_year must be <= end_year")
        return self


class MeasureSpec(BaseModel):
    kind: MeasureKind


class AnalysisPlan(BaseModel):
    query_class: QueryClass
    intent: str = Field(..., min_length=5)
    match_mode: MatchMode
    entities: EntitySelection = Field(default_factory=EntitySelection)
    filters: FilterSelection = Field(default_factory=FilterSelection)
    measure: MeasureSpec
    group_by: list[GroupByField] = Field(default_factory=list, max_length=2)
    time_bucket: TimeBucket | None = None
    chart_type: ChartType
    citation_mode: CitationMode = CitationMode.DEEP
    confidence: float = Field(..., ge=0.0, le=1.0)
    needs_clarification: bool = False
    clarification_reason: str | None = None

