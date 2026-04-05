from __future__ import annotations

from app.analytics.base import ProcessedVisualizationData, make_citation, study_matches_plan
from app.citations.engine import CitationEngine
from app.models.analysis_plan import AnalysisPlan
from app.models.enums import ChartType, DataType
from app.models.fetch_plan import FetchPlan
from app.models.visualization import FieldEncoding
from app.normalize.facts import CanonicalFacts
from app.utils.date_parser import duration_months


class ScatterProcessor:
    def __init__(self, citation_engine: CitationEngine) -> None:
        self._citation_engine = citation_engine

    def process(self, facts: CanonicalFacts, plan: AnalysisPlan, fetch_plan: FetchPlan) -> ProcessedVisualizationData:
        rows: list[dict[str, object]] = []
        studies_used: set[str] = set()

        for study in facts.studies:
            if not study_matches_plan(study, plan):
                continue
            if study.enrollment_count is None:
                continue
            study_duration_months = duration_months(study.start_date, study.completion_date)
            if study_duration_months is None:
                continue
            studies_used.add(study.nct_id)
            citations = self._citation_engine.sample(
                [
                    make_citation(
                        study.nct_id,
                        f"enrollmentInfo.count = {study.enrollment_count}",
                        title=study.brief_title,
                        field_path="protocolSection.designModule.enrollmentInfo.count",
                        field_value=study.enrollment_count,
                    ),
                    make_citation(
                        study.nct_id,
                        f"startDateStruct.date = {study.start_date.raw if study.start_date else None}",
                        title=study.brief_title,
                        field_path="protocolSection.statusModule.startDateStruct.date",
                        field_value=study.start_date.raw if study.start_date else None,
                    ),
                    make_citation(
                        study.nct_id,
                        f"completionDateStruct.date = {study.completion_date.raw if study.completion_date else None}",
                        title=study.brief_title,
                        field_path="protocolSection.statusModule.completionDateStruct.date",
                        field_value=study.completion_date.raw if study.completion_date else None,
                    ),
                ]
            )
            rows.append(
                {
                    "nct_id": study.nct_id,
                    "title": study.brief_title or study.nct_id,
                    "enrollment_count": study.enrollment_count,
                    "duration_months": study_duration_months,
                    "citations": citations,
                }
            )

        return ProcessedVisualizationData(
            chart_type=ChartType.SCATTER_PLOT,
            title="Enrollment vs Duration",
            encoding={
                "x": FieldEncoding(field="enrollment_count", type=DataType.QUANTITATIVE, title="Enrollment"),
                "y": FieldEncoding(field="duration_months", type=DataType.QUANTITATIVE, title="Duration (Months)"),
            },
            data=rows,
            filters_applied={k: v for k, v in plan.model_dump(mode="json")["filters"].items() if v not in (None, [], {})},
            studies_used=len(studies_used),
            description="Each point represents one study with enrollment count plotted against duration in months.",
        )
