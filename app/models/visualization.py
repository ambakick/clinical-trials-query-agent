from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ChartType, DataType


class Citation(BaseModel):
    nct_id: str
    title: str | None = None
    field_path: str | None = None
    field_value: str | int | float | bool | None = None
    excerpt: str


class FieldEncoding(BaseModel):
    field: str
    type: DataType
    title: str | None = None
    sort: str | None = None
    format: str | None = None


class NetworkNode(BaseModel):
    id: str
    label: str
    type: str
    size: int | float
    metadata: dict[str, Any] | None = None


class NetworkEdge(BaseModel):
    source: str
    target: str
    weight: int | float
    citations: list[Citation] | None = None


class NetworkData(BaseModel):
    nodes: list[NetworkNode] = Field(default_factory=list)
    edges: list[NetworkEdge] = Field(default_factory=list)


class VisualizationSpec(BaseModel):
    type: ChartType
    title: str
    description: str | None = None
    encoding: dict[str, FieldEncoding]
    data: list[dict[str, Any]] | NetworkData
    render_hints: dict[str, Any] | None = None

