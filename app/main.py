from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    import structlog
except ImportError:  # pragma: no cover - optional at test time
    import logging

    structlog = None

from app.analytics.registry import ProcessorRegistry
from app.citations.engine import CitationEngine
from app.config import Settings, get_settings
from app.engine.compiler import PlanCompiler
from app.engine.errors import CompilerValidationError, PlannerExecutionError
from app.engine.orchestrator import QueryOrchestrator
from app.engine.planner import QueryPlanner
from app.models.analysis_plan import AnalysisPlan
from app.models.request import QueryRequest
from app.models.response import ClarificationResponse, QueryResponse
from app.services.cache import InMemoryCacheBackend
from app.services.ctgov import ClinicalTrialsClient, ClinicalTrialsClientError
from app.services.llm.openai_provider import OpenAIProvider, UnavailableProvider
from app.visualization.builder import VisualizationBuilder

if structlog is not None:
    logger = structlog.get_logger(__name__)
else:  # pragma: no cover - fallback for minimal environments
    import logging

    logger = logging.getLogger(__name__)


def build_orchestrator(settings: Settings) -> QueryOrchestrator:
    cache = InMemoryCacheBackend()
    provider = OpenAIProvider(settings) if settings.openai_api_key else UnavailableProvider()
    planner = QueryPlanner(provider=provider, cache=cache, settings=settings)
    compiler = PlanCompiler(settings)
    ctgov_client = ClinicalTrialsClient(settings=settings, cache=cache)
    citation_engine = CitationEngine(settings.max_citations_per_bucket)
    processor_registry = ProcessorRegistry(citation_engine=citation_engine, settings=settings)
    visualization_builder = VisualizationBuilder()
    return QueryOrchestrator(
        settings=settings,
        planner=planner,
        compiler=compiler,
        ctgov_client=ctgov_client,
        processor_registry=processor_registry,
        visualization_builder=visualization_builder,
        cache=cache,
    )


def create_app(settings: Settings | None = None, orchestrator: QueryOrchestrator | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    app_orchestrator = orchestrator or build_orchestrator(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await app.state.orchestrator._ctgov_client.startup()
        try:
            yield
        finally:
            await app.state.orchestrator._ctgov_client.aclose()

    app = FastAPI(title="ClinicalTrials.gov Query Backend", lifespan=lifespan)
    app.state.settings = app_settings
    app.state.orchestrator = app_orchestrator

    if app_settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=app_settings.cors_allow_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.post("/api/v1/query", response_model=QueryResponse | ClarificationResponse)
    async def query_endpoint(request: QueryRequest) -> QueryResponse | ClarificationResponse:
        try:
            return await app.state.orchestrator.handle_query(request)
        except CompilerValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except PlannerExecutionError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except ClinicalTrialsClientError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/v1/health")
    async def health_endpoint() -> dict[str, Any]:
        try:
            version = await app.state.orchestrator._ctgov_client.get_version()
            return {
                "status": "ok",
                "planner_provider": app_settings.llm_provider,
                "planner_configured": bool(app_settings.openai_api_key),
                "ctgov": {
                    "reachable": True,
                    "api_version": version.api_version,
                    "data_timestamp": version.data_timestamp,
                },
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("health_check_failed", error=str(exc))
            return {
                "status": "degraded",
                "planner_provider": app_settings.llm_provider,
                "planner_configured": bool(app_settings.openai_api_key),
                "ctgov": {
                    "reachable": False,
                },
            }

    @app.get("/api/v1/schema/input")
    async def input_schema_endpoint() -> dict[str, Any]:
        return QueryRequest.model_json_schema()

    @app.get("/api/v1/schema/output")
    async def output_schema_endpoint() -> dict[str, Any]:
        return QueryResponse.model_json_schema()

    return app


app = create_app()
