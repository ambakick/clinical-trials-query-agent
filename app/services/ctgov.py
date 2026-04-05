from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from app.config import Settings
from app.models.fetch_plan import CompiledRequest, FetchExecutionResult, FetchedStudyBatch, FetchPlan, VersionInfo
from app.services.cache import CacheBackend, build_cache_key
from app.utils.rate_limiter import AsyncSlidingWindowRateLimiter


class ClinicalTrialsClientError(RuntimeError):
    """Raised when the CT.gov client fails."""


class ClinicalTrialsClient:
    def __init__(self, settings: Settings, cache: CacheBackend) -> None:
        self._settings = settings
        self._cache = cache
        self._http = httpx.AsyncClient(
            base_url=settings.ctgov_base_url,
            timeout=settings.ctgov_timeout_seconds,
        )
        self._rate_limiter = AsyncSlidingWindowRateLimiter(settings.ctgov_rate_limit_per_minute, 60.0)
        self._version_info: VersionInfo | None = None
        self._version_expires_at = 0.0
        self._version_lock = asyncio.Lock()
        self._version_refresh_task: asyncio.Task[None] | None = None

    async def aclose(self) -> None:
        await self._http.aclose()

    async def startup(self) -> None:
        await self._refresh_version(blocking=True)

    async def get_version(self) -> VersionInfo:
        now = time.monotonic()
        if self._version_info is None:
            await self._refresh_version(blocking=True)
        elif now >= self._version_expires_at and self._version_refresh_task is None:
            self._version_refresh_task = asyncio.create_task(self._refresh_version(blocking=False))
        return self._version_info or VersionInfo(api_version="unknown", data_timestamp="unknown")

    async def _refresh_version(self, blocking: bool) -> None:
        async with self._version_lock:
            try:
                version_payload = await self._request("GET", "/version", params=None)
                self._version_info = VersionInfo(
                    api_version=version_payload["apiVersion"],
                    data_timestamp=version_payload["dataTimestamp"],
                )
                self._version_expires_at = time.monotonic() + self._settings.ctgov_version_ttl_seconds
            finally:
                if not blocking:
                    self._version_refresh_task = None

    async def execute(self, fetch_plan: FetchPlan) -> FetchExecutionResult:
        version_info = await self.get_version()
        warnings: list[str] = []

        async def _fetch_one(request: CompiledRequest) -> FetchedStudyBatch:
            studies, total_count, truncated = await self.search_studies(
                request=request,
                max_results=fetch_plan.max_results,
                version_info=version_info,
            )
            return FetchedStudyBatch(
                label=request.label,
                purpose=request.purpose,
                studies=studies,
                total_count=total_count,
                truncated=truncated,
            )

        batches = list(await asyncio.gather(*[_fetch_one(request) for request in fetch_plan.requests]))
        for batch in batches:
            if batch.truncated:
                warnings.append(f"Results truncated for request: {batch.purpose}")
        return FetchExecutionResult(batches=batches, version_info=version_info, warnings=warnings)

    async def search_studies(
        self,
        request: CompiledRequest,
        max_results: int,
        version_info: VersionInfo,
    ) -> tuple[list[dict[str, Any]], int | None, bool]:
        studies: list[dict[str, Any]] = []
        next_page_token: str | None = None
        total_count: int | None = None
        truncated = False

        while True:
            params = dict(request.params)
            params["pageSize"] = request.page_size
            params["countTotal"] = "true"
            params["fields"] = ",".join(request.fields)
            if next_page_token:
                params["pageToken"] = next_page_token
            cache_key = build_cache_key(
                "ctgov_raw",
                self._settings.cache_namespace_version,
                {
                    "params": params,
                    "fields": request.fields,
                    "page_token": next_page_token,
                    "data_timestamp": version_info.data_timestamp,
                },
            )
            page = await self._cache.get(cache_key)
            if page is None:
                page = await self._request("GET", request.endpoint, params=params)
                await self._cache.set(cache_key, page, self._settings.cache_ttl_ctgov_raw_seconds)

            page_studies = page.get("studies", [])
            studies.extend(page_studies)
            total_count = page.get("totalCount", total_count)
            next_page_token = page.get("nextPageToken")

            if len(studies) >= max_results:
                studies = studies[:max_results]
                truncated = bool(next_page_token or (total_count and total_count > max_results))
                break
            if not next_page_token:
                break

        return studies, total_count, truncated

    async def _request(self, method: str, url: str, params: dict[str, Any] | None) -> dict[str, Any]:
        last_error: Exception | None = None
        delays = [0.0, 1.0, 2.0, 4.0]
        for attempt, delay in enumerate(delays):
            if delay:
                await asyncio.sleep(delay)
            await self._rate_limiter.acquire()
            try:
                response = await self._http.request(method, url, params=params)
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                status_code = getattr(getattr(exc, "response", None), "status_code", None)
                retryable_status = status_code in {429, 500, 502, 503, 504}
                if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)) or retryable_status:
                    last_error = exc
                    if attempt < len(delays) - 1:
                        continue
                raise ClinicalTrialsClientError("ClinicalTrials.gov request failed") from exc
        raise ClinicalTrialsClientError("ClinicalTrials.gov unavailable after retries") from last_error
