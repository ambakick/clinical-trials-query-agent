from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.request import QueryRequest


def test_query_request_validates_year_order() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(query="hello world", start_year=2025, end_year=2024)

