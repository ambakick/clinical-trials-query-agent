from __future__ import annotations

from typing import Protocol

from app.models.analysis_plan import AnalysisPlan
from app.models.request import QueryRequest


class LLMProvider(Protocol):
    async def create_analysis_plan(self, request: QueryRequest) -> AnalysisPlan:
        ...

