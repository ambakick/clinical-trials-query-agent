from __future__ import annotations

from app.config import Settings
from app.models.analysis_plan import AnalysisPlan, ComparisonSelection
from app.models.enums import ComparisonDimension
from app.models.request import QueryRequest
from app.services.cache import CacheBackend, build_cache_key
from app.services.llm.base import LLMProvider


class QueryPlanner:
    def __init__(self, provider: LLMProvider, cache: CacheBackend, settings: Settings) -> None:
        self._provider = provider
        self._cache = cache
        self._settings = settings

    async def create_plan(self, request: QueryRequest) -> AnalysisPlan:
        semantic_payload = {
            "query": request.query,
            "drug_name": request.drug_name,
            "condition": request.condition,
            "trial_phase": request.trial_phase,
            "sponsor": request.sponsor,
            "country": request.country,
            "start_year": request.start_year,
            "end_year": request.end_year,
            "status": request.status,
        }
        cache_key = build_cache_key(
            "analysis_plan",
            f"{self._settings.cache_namespace_version}:{self._settings.planner_prompt_version}",
            semantic_payload,
        )
        cached = await self._cache.get(cache_key)
        if cached is not None:
            plan = AnalysisPlan.model_validate(cached)
        else:
            plan = await self._provider.create_analysis_plan(request)
            await self._cache.set(
                cache_key,
                plan.model_dump(mode="json"),
                self._settings.cache_ttl_plan_seconds,
            )
        if plan.citation_mode != request.citation_mode:
            plan = plan.model_copy(update={"citation_mode": request.citation_mode})
        return self._apply_structured_hints(plan, request)

    def _apply_structured_hints(self, plan: AnalysisPlan, request: QueryRequest) -> AnalysisPlan:
        updated = plan.model_copy(deep=True)
        if request.drug_name:
            if updated.entities.comparison and updated.entities.comparison.dimension == ComparisonDimension.DRUG_NAME:
                if not updated.entities.comparison.left:
                    updated.entities.comparison = ComparisonSelection(
                        dimension=ComparisonDimension.DRUG_NAME,
                        left=request.drug_name,
                        right=updated.entities.comparison.right,
                    )
            else:
                updated.entities.drug_name = request.drug_name
        if request.condition:
            updated.entities.condition = request.condition
        if request.sponsor:
            updated.entities.sponsor = request.sponsor
            updated.filters.sponsor = request.sponsor
        if request.country:
            updated.entities.country = request.country
            updated.filters.country = request.country
        if request.trial_phase:
            updated.filters.trial_phase = request.trial_phase
        if request.start_year is not None:
            updated.filters.start_year = request.start_year
        if request.end_year is not None:
            updated.filters.end_year = request.end_year
        if request.status:
            updated.filters.status = request.status
        return updated
