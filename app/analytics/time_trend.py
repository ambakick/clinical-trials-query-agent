from __future__ import annotations

from collections import defaultdict

from app.analytics.base import ProcessedVisualizationData, make_citation, study_matches_plan
from app.citations.engine import CitationEngine
from app.models.analysis_plan import AnalysisPlan
from app.models.enums import ChartType, DataType
from app.models.fetch_plan import FetchPlan
from app.models.visualization import FieldEncoding
from app.normalize.facts import CanonicalFacts


class TimeTrendProcessor:
    def __init__(self, citation_engine: CitationEngine) -> None:
        self._citation_engine = citation_engine

    def process(self, facts: CanonicalFacts, plan: AnalysisPlan, fetch_plan: FetchPlan) -> ProcessedVisualizationData:
        buckets: defaultdict[int, set[str]] = defaultdict(set)
        citations_by_year: defaultdict[int, list] = defaultdict(list)
        studies_used: set[str] = set()
        for study in facts.studies:
            if not study_matches_plan(study, plan):
                continue
            if study.start_date is None or study.start_date.year is None:
                continue
            year = study.start_date.year
            studies_used.add(study.nct_id)
            buckets[year].add(study.nct_id)
            citations_by_year[year].append(
                make_citation(
                    study.nct_id,
                    f"startDateStruct.date = {study.start_date.raw}",
                    title=study.brief_title,
                    field_path="protocolSection.statusModule.startDateStruct.date",
                    field_value=study.start_date.raw,
                )
            )
        data = [
            {"year": year, "trial_count": len(sorted_ids), "citations": self._citation_engine.sample(citations_by_year[year])}
            for year, sorted_ids in sorted(buckets.items())
        ]
        return ProcessedVisualizationData(
            chart_type=ChartType.TIME_SERIES,
            title="Trials by Start Year",
            encoding={
                "x": FieldEncoding(field="year", type=DataType.TEMPORAL, title="Year"),
                "y": FieldEncoding(field="trial_count", type=DataType.QUANTITATIVE, title="Trials"),
            },
            data=data,
            filters_applied=_filters_applied(plan),
            studies_used=len(studies_used),
        )


def _filters_applied(plan: AnalysisPlan) -> dict[str, object]:
    return {k: v for k, v in plan.model_dump(mode="json")["filters"].items() if v not in (None, [], {})}
