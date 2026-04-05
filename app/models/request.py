from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.models.enums import CitationMode, TrialPhase, TrialStatus


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=1000)
    drug_name: str | None = None
    condition: str | None = None
    trial_phase: list[TrialPhase] | None = None
    sponsor: str | None = None
    country: str | None = None
    start_year: int | None = Field(None, ge=1990, le=2035)
    end_year: int | None = Field(None, ge=1990, le=2035)
    status: list[TrialStatus] | None = None
    citation_mode: CitationMode = CitationMode.DEEP
    max_results: int = Field(3000, ge=1, le=10000)

    @model_validator(mode="after")
    def validate_years(self) -> "QueryRequest":
        if self.start_year is not None and self.end_year is not None and self.start_year > self.end_year:
            raise ValueError("start_year must be <= end_year")
        return self

