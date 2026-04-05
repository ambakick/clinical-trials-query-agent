from __future__ import annotations

import time
from typing import Any

from app.analytics.registry import ProcessorRegistry
from app.config import Settings
from app.engine.compiler import PlanCompiler
from app.engine.errors import CompilerValidationError, PlannerExecutionError
from app.engine.planner import QueryPlanner
from app.models.fetch_plan import FetchExecutionResult, VersionInfo
from app.models.request import QueryRequest
from app.models.response import ClarificationResponse, QueryResponse
from app.normalize.studies import normalize_fetch_result
from app.services.cache import CacheBackend, build_cache_key
from app.services.ctgov import ClinicalTrialsClient, ClinicalTrialsClientError
from app.services.llm.openai_provider import OpenAIPlannerError
from app.visualization.builder import VisualizationBuilder


class QueryOrchestrator:
    def __init__(
        self,
        settings: Settings,
        planner: QueryPlanner,
        compiler: PlanCompiler,
        ctgov_client: ClinicalTrialsClient,
        processor_registry: ProcessorRegistry,
        visualization_builder: VisualizationBuilder,
        cache: CacheBackend,
    ) -> None:
        self._settings = settings
        self._planner = planner
        self._compiler = compiler
        self._ctgov_client = ctgov_client
        self._processor_registry = processor_registry
        self._visualization_builder = visualization_builder
        self._cache = cache

    async def handle_query(self, request: QueryRequest) -> QueryResponse | ClarificationResponse:
        started_at = time.perf_counter()
        version_info = await self._ctgov_client.get_version()
        response_cache_key = self._build_response_cache_key(request, version_info)
        cached_response = await self._cache.get(response_cache_key)
        if cached_response is not None:
            return QueryResponse.model_validate(cached_response)

        try:
            plan = await self._planner.create_plan(request)
        except OpenAIPlannerError as exc:
            raise PlannerExecutionError("planner unavailable") from exc

        if plan.needs_clarification:
            return ClarificationResponse(
                reason=plan.clarification_reason or "The query needs more detail before it can be answered reliably.",
                question=plan.clarification_reason or "Can you clarify the comparison or filter you want to apply?",
                suggested_interpretation=plan.intent,
            )

        fetch_plan = self._compiler.compile(plan, request)
        fetch_result = await self._ctgov_client.execute(fetch_plan)
        facts = normalize_fetch_result(fetch_result)
        processor = self._processor_registry.get(plan.query_class)
        processed = processor.process(facts, plan, fetch_plan)
        response = self._visualization_builder.build(processed, plan, fetch_result, started_at)
        if self._is_empty_response(response):
            response.meta.warnings.append("No matching studies were found for this query.")
        await self._cache.set(
            response_cache_key,
            response.model_dump(mode="json"),
            self._settings.cache_ttl_response_seconds,
        )
        return response

    def _build_response_cache_key(self, request: QueryRequest, version_info: VersionInfo) -> str:
        payload: dict[str, Any] = request.model_dump(mode="json")
        payload["response_schema_version"] = self._settings.response_schema_version
        payload["data_timestamp"] = version_info.data_timestamp
        return build_cache_key(
            "query_response",
            self._settings.cache_namespace_version,
            payload,
        )

    @staticmethod
    def _is_empty_response(response: QueryResponse) -> bool:
        data = response.visualization.data
        if isinstance(data, list):
            return len(data) == 0
        return len(data.nodes) == 0 and len(data.edges) == 0

