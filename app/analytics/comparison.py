from __future__ import annotations

from collections import defaultdict

from app.analytics.base import ProcessedVisualizationData, split_for_comparison, study_matches_plan
from app.analytics.distribution import _iter_group_values
from app.citations.engine import CitationEngine
from app.models.analysis_plan import AnalysisPlan
from app.models.enums import ChartType, DataType, GroupByField
from app.models.fetch_plan import FetchPlan
from app.models.visualization import FieldEncoding
from app.normalize.facts import CanonicalFacts


class ComparisonProcessor:
    def __init__(self, citation_engine: CitationEngine) -> None:
        self._citation_engine = citation_engine

    def process(self, facts: CanonicalFacts, plan: AnalysisPlan, fetch_plan: FetchPlan) -> ProcessedVisualizationData:
        group_field = plan.group_by[0] if plan.group_by else GroupByField.PHASE
        cohorts = split_for_comparison(facts.studies, plan)
        rows: list[dict[str, object]] = []
        studies_used: set[str] = set()
        for cohort, studies in cohorts.items():
            buckets: defaultdict[str, set[str]] = defaultdict(set)
            citations: defaultdict[str, list] = defaultdict(list)
            for study in studies:
                if not study_matches_plan(study, plan):
                    continue
                studies_used.add(study.nct_id)
                for key, citation in _iter_group_values(group_field, study):
                    buckets[key].add(study.nct_id)
                    citations[key].append(citation)
            for category, ids in sorted(buckets.items(), key=lambda item: item[0]):
                rows.append(
                    {
                        "category": category,
                        "series": cohort,
                        "trial_count": len(ids),
                        "citations": self._citation_engine.sample(citations[category]),
                    }
                )
        return ProcessedVisualizationData(
            chart_type=ChartType.GROUPED_BAR_CHART,
            title=f"Comparison by {group_field.value.replace('_', ' ').title()}",
            encoding={
                "x": FieldEncoding(field="category", type=DataType.NOMINAL, title=group_field.value.replace("_", " ").title()),
                "y": FieldEncoding(field="trial_count", type=DataType.QUANTITATIVE, title="Trials"),
                "series": FieldEncoding(field="series", type=DataType.NOMINAL, title="Cohort"),
            },
            data=rows,
            filters_applied={k: v for k, v in plan.model_dump(mode="json")["filters"].items() if v not in (None, [], {})},
            studies_used=len(studies_used),
        )
