from __future__ import annotations

import asyncio
import time

import pytest

from app.models.fetch_plan import CompiledRequest, FetchPlan, VersionInfo
from app.services.cache import InMemoryCacheBackend
from app.services.ctgov import ClinicalTrialsClient
from app.services.llm.prompts import SYSTEM_PROMPT
from app.utils.rate_limiter import AsyncSlidingWindowRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_delays_second_acquire() -> None:
    limiter = AsyncSlidingWindowRateLimiter(max_requests=1, period_seconds=0.05)
    start = time.monotonic()
    await limiter.acquire()
    await limiter.acquire()
    assert time.monotonic() - start >= 0.045


@pytest.mark.asyncio
async def test_version_refresh_uses_last_known_value(settings) -> None:
    client = ClinicalTrialsClient(settings=settings.model_copy(update={"ctgov_version_ttl_seconds": 0}), cache=InMemoryCacheBackend())
    calls = 0

    async def fake_request(method, url, params):
        nonlocal calls
        calls += 1
        if calls == 1:
            return {"apiVersion": "2.0.5", "dataTimestamp": "ts-1"}
        raise RuntimeError("boom")

    client._request = fake_request  # type: ignore[method-assign]
    await client.startup()
    version = await client.get_version()
    await asyncio.sleep(0)
    assert version.data_timestamp == "ts-1"


@pytest.mark.asyncio
async def test_execute_fetches_independent_requests_concurrently(settings) -> None:
    client = ClinicalTrialsClient(settings=settings, cache=InMemoryCacheBackend())
    client._version_info = VersionInfo(api_version="2.0.5", data_timestamp="ts-1")
    client._version_expires_at = time.monotonic() + 60

    async def fake_search_studies(request, max_results, version_info):
        await asyncio.sleep(0.05)
        return [{"request": request.purpose}], 1, False

    client.search_studies = fake_search_studies  # type: ignore[method-assign]
    fetch_plan = FetchPlan(
        requests=[
            CompiledRequest(purpose="left", fields=["NCTId"]),
            CompiledRequest(purpose="right", fields=["NCTId"]),
        ],
        max_results=10,
    )

    started = time.monotonic()
    result = await client.execute(fetch_plan)
    elapsed = time.monotonic() - started

    assert len(result.batches) == 2
    assert elapsed < 0.09


def test_system_prompt_contains_field_guidance_and_examples() -> None:
    assert "Valid group_by values" in SYSTEM_PROMPT
    assert "sponsor_class" in SYSTEM_PROMPT
    assert "Valid relationship_kind values" in SYSTEM_PROMPT
    assert "Valid comparison.dimension values" in SYSTEM_PROMPT
    assert "scatter" in SYSTEM_PROMPT
    assert "scatter_plot" in SYSTEM_PROMPT
    assert "Example 1" in SYSTEM_PROMPT
    assert "Example 2" in SYSTEM_PROMPT
    assert "Example 3" in SYSTEM_PROMPT
    assert "Example 4" in SYSTEM_PROMPT
