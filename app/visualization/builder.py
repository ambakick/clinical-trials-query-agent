from __future__ import annotations

import time

from app.analytics.base import ProcessedVisualizationData
from app.models.analysis_plan import AnalysisPlan
from app.models.enums import ChartType, MatchMode
from app.models.fetch_plan import FetchExecutionResult
from app.models.response import QueryResponse, ResponseMetadata
from app.models.visualization import VisualizationSpec


class VisualizationBuilder:
    def build(
        self,
        processed: ProcessedVisualizationData,
        plan: AnalysisPlan,
        fetch_result: FetchExecutionResult,
        processing_started_at: float,
    ) -> QueryResponse:
        warnings = list(fetch_result.warnings) + list(processed.warnings)
        chart_type = processed.chart_type
        if chart_type == ChartType.PIE_CHART and not isinstance(processed.data, list):
            chart_type = ChartType.BAR_CHART
            warnings.append("Pie chart downgraded because the response shape was not categorical.")

        unique_studies = {
            study["protocolSection"]["identificationModule"]["nctId"]
            for batch in fetch_result.batches
            for study in batch.studies
            if study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
        }
        total_count = None
        if all(batch.total_count is not None for batch in fetch_result.batches):
            total_count = sum(batch.total_count or 0 for batch in fetch_result.batches)

        visualization = VisualizationSpec(
            type=chart_type,
            title=processed.title,
            description=processed.description,
            encoding=processed.encoding,
            data=processed.data,
            render_hints=processed.render_hints,
        )
        metadata = ResponseMetadata(
            query_interpretation=plan.intent,
            filters_applied=processed.filters_applied,
            match_mode=MatchMode(plan.match_mode),
            total_studies_matched=total_count,
            studies_analyzed=processed.studies_used if processed.studies_used is not None else len(unique_studies),
            api_version=fetch_result.version_info.api_version,
            data_timestamp=fetch_result.version_info.data_timestamp,
            warnings=warnings,
            processing_time_ms=int((time.perf_counter() - processing_started_at) * 1000),
        )
        return QueryResponse(visualization=visualization, meta=metadata)
