from __future__ import annotations

import pytest

from app.engine.planner import QueryPlanner
from app.models.request import QueryRequest
from app.services.cache import InMemoryCacheBackend
from app.services.llm.openai_provider import MockProvider


@pytest.mark.asyncio
async def test_planner_applies_structured_hints(settings, sample_plan) -> None:
    planner = QueryPlanner(provider=MockProvider(sample_plan), cache=InMemoryCacheBackend(), settings=settings)
    request = QueryRequest(query="show distribution", condition="Melanoma", start_year=2015)
    plan = await planner.create_plan(request)
    assert plan.entities.condition == "Melanoma"
    assert plan.filters.start_year == 2015


@pytest.mark.asyncio
async def test_planner_uses_cache(settings, sample_plan) -> None:
    class CountingProvider(MockProvider):
        def __init__(self, plan):
            super().__init__(plan)
            self.calls = 0

        async def create_analysis_plan(self, request):
            self.calls += 1
            return await super().create_analysis_plan(request)

    provider = CountingProvider(sample_plan)
    planner = QueryPlanner(provider=provider, cache=InMemoryCacheBackend(), settings=settings)
    request = QueryRequest(query="show distribution", condition="Melanoma")
    await planner.create_plan(request)
    await planner.create_plan(request)
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_planner_applies_structured_hints_once_per_create_plan(settings, sample_plan) -> None:
    class TrackingPlanner(QueryPlanner):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.apply_calls = 0

        def _apply_structured_hints(self, plan, request):
            self.apply_calls += 1
            return super()._apply_structured_hints(plan, request)

    planner = TrackingPlanner(provider=MockProvider(sample_plan), cache=InMemoryCacheBackend(), settings=settings)
    request = QueryRequest(query="show distribution", condition="Melanoma")
    await planner.create_plan(request)
    await planner.create_plan(request)
    assert planner.apply_calls == 2
