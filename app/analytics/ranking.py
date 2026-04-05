from __future__ import annotations

from app.analytics.base import ProcessedVisualizationData
from app.analytics.distribution import DistributionProcessor
from app.citations.engine import CitationEngine
from app.models.analysis_plan import AnalysisPlan
from app.models.enums import ChartType
from app.models.fetch_plan import FetchPlan
from app.normalize.facts import CanonicalFacts


class RankingProcessor:
    def __init__(self, citation_engine: CitationEngine) -> None:
        self._distribution = DistributionProcessor(citation_engine)

    def process(self, facts: CanonicalFacts, plan: AnalysisPlan, fetch_plan: FetchPlan) -> ProcessedVisualizationData:
        result = self._distribution.process(facts, plan, fetch_plan)
        if isinstance(result.data, list):
            top_n = plan.filters.top_n or 10
            result.data = sorted(result.data, key=lambda item: (-int(item["trial_count"]), str(item["category"])))[:top_n]
        result.chart_type = ChartType.BAR_CHART
        result.title = f"Top {plan.filters.top_n or 10} {result.title.replace('Trials by ', '')}"
        return result

