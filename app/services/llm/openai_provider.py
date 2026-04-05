from __future__ import annotations

import asyncio
import json

try:
    from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, InternalServerError, RateLimitError
except ImportError:  # pragma: no cover - optional at test time
    APIConnectionError = APITimeoutError = InternalServerError = RateLimitError = Exception
    AsyncOpenAI = None

from app.config import Settings
from app.models.analysis_plan import AnalysisPlan
from app.models.request import QueryRequest
from app.services.llm.prompts import SYSTEM_PROMPT, build_user_prompt


class OpenAIPlannerError(RuntimeError):
    """Raised when the planner fails after retries."""


class UnavailableProvider:
    async def create_analysis_plan(self, request: QueryRequest) -> AnalysisPlan:
        raise OpenAIPlannerError("planner is not configured")


class OpenAIProvider:
    def __init__(self, settings: Settings) -> None:
        if AsyncOpenAI is None:
            raise ValueError("openai package is not installed")
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI provider")
        self._settings = settings
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def create_analysis_plan(self, request: QueryRequest) -> AnalysisPlan:
        last_error: Exception | None = None
        delays = [0.0, 1.0, 3.0]
        payload = request.model_dump(mode="json")
        for attempt, delay in enumerate(delays):
            if delay:
                await asyncio.sleep(delay)
            try:
                response = await self._client.chat.completions.create(
                    model=self._settings.openai_model,
                    temperature=self._settings.llm_temperature,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_user_prompt(payload)},
                    ],
                )
                content = response.choices[0].message.content or "{}"
                return AnalysisPlan.model_validate(json.loads(content))
            except (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError) as exc:
                last_error = exc
                continue
            except Exception as exc:  # noqa: BLE001
                status_code = getattr(exc, "status_code", None)
                if status_code in {429, 500, 503} and attempt < len(delays) - 1:
                    last_error = exc
                    continue
                raise OpenAIPlannerError("planner returned an invalid response") from exc
        raise OpenAIPlannerError("planner unavailable after retries") from last_error


class MockProvider:
    def __init__(self, plan: AnalysisPlan) -> None:
        self._plan = plan

    async def create_analysis_plan(self, request: QueryRequest) -> AnalysisPlan:
        return self._plan.model_copy(deep=True)
