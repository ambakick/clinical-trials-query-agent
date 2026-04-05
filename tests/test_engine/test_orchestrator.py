from __future__ import annotations

import pytest

from app.analytics.registry import ProcessorRegistry
from app.citations.engine import CitationEngine
from app.engine.compiler import PlanCompiler
from app.engine.orchestrator import QueryOrchestrator
from app.engine.planner import QueryPlanner
from app.models.request import QueryRequest
from app.normalize.studies import normalize_fetch_result
from app.services.cache import InMemoryCacheBackend
from app.services.llm.openai_provider import MockProvider
from app.visualization.builder import VisualizationBuilder


class FakeCtgovClient:
    def __init__(self, fetch_result):
        self.fetch_result = fetch_result
        self.execute_calls = 0

    async def startup(self):
        return None

    async def aclose(self):
        return None

    async def get_version(self):
        return self.fetch_result.version_info

    async def execute(self, fetch_plan):
        self.execute_calls += 1
        return self.fetch_result


@pytest.mark.asyncio
async def test_orchestrator_uses_l5_cache(settings, sample_plan, sample_fetch_result) -> None:
    cache = InMemoryCacheBackend()
    planner = QueryPlanner(MockProvider(sample_plan), cache=cache, settings=settings)
    ctgov = FakeCtgovClient(sample_fetch_result)
    orchestrator = QueryOrchestrator(
        settings=settings,
        planner=planner,
        compiler=PlanCompiler(settings),
        ctgov_client=ctgov,
        processor_registry=ProcessorRegistry(CitationEngine(settings.max_citations_per_bucket), settings),
        visualization_builder=VisualizationBuilder(),
        cache=cache,
    )
    request = QueryRequest(query="How are lung cancer trials distributed across phases?", condition="Lung cancer")
    first = await orchestrator.handle_query(request)
    second = await orchestrator.handle_query(request)
    assert first.model_dump() == second.model_dump()
    assert ctgov.execute_calls == 1

