from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.models.response import QueryResponse, ResponseMetadata
from app.models.visualization import FieldEncoding, VisualizationSpec
from app.models.enums import ChartType, DataType, MatchMode


class DummyCtgov:
    async def startup(self):
        return None

    async def aclose(self):
        return None

    async def get_version(self):
        class Version:
            api_version = "2.0.5"
            data_timestamp = "2026-04-03T09:00:05"

        return Version()


class DummyOrchestrator:
    def __init__(self):
        self._ctgov_client = DummyCtgov()

    async def handle_query(self, request):
        return QueryResponse(
            visualization=VisualizationSpec(
                type=ChartType.BAR_CHART,
                title="Example",
                encoding={
                    "x": FieldEncoding(field="category", type=DataType.NOMINAL),
                    "y": FieldEncoding(field="trial_count", type=DataType.QUANTITATIVE),
                },
                data=[{"category": "Phase 1", "trial_count": 1}],
            ),
            meta=ResponseMetadata(
                query_interpretation="Example",
                filters_applied={},
                match_mode=MatchMode.BROAD,
                studies_analyzed=1,
                api_version="2.0.5",
                data_timestamp="2026-04-03T09:00:05",
            ),
        )


def test_app_query_endpoint(settings) -> None:
    app = create_app(settings=settings, orchestrator=DummyOrchestrator())
    client = TestClient(app)
    response = client.post("/api/v1/query", json={"query": "Show trials by phase"})
    assert response.status_code == 200
    assert response.json()["visualization"]["type"] == "bar_chart"


def test_schema_endpoint(settings) -> None:
    app = create_app(settings=settings, orchestrator=DummyOrchestrator())
    client = TestClient(app)
    response = client.get("/api/v1/schema/input")
    assert response.status_code == 200
    assert "properties" in response.json()


def test_cors_headers(settings) -> None:
    app = create_app(settings=settings, orchestrator=DummyOrchestrator())
    client = TestClient(app)
    response = client.options(
        "/api/v1/query",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
