from __future__ import annotations

from collections import defaultdict

from app.analytics.base import ProcessedVisualizationData, make_citation, normalize_label, study_matches_plan
from app.citations.engine import CitationEngine
from app.models.analysis_plan import AnalysisPlan
from app.models.enums import ChartType, DataType
from app.models.fetch_plan import FetchPlan
from app.models.visualization import FieldEncoding
from app.normalize.facts import CanonicalFacts


class GeographicProcessor:
    def __init__(self, citation_engine: CitationEngine) -> None:
        self._citation_engine = citation_engine

    def process(self, facts: CanonicalFacts, plan: AnalysisPlan, fetch_plan: FetchPlan) -> ProcessedVisualizationData:
        buckets: defaultdict[str, set[str]] = defaultdict(set)
        citations: defaultdict[str, list] = defaultdict(list)
        studies_used: set[str] = set()
        for study in facts.studies:
            if not study_matches_plan(study, plan):
                continue
            studies_used.add(study.nct_id)
            seen_countries: set[str] = set()
            for location in study.locations:
                if not location.country or location.country in seen_countries:
                    continue
                seen_countries.add(location.country)
                buckets[location.country].add(study.nct_id)
                citations[location.country].append(
                    make_citation(
                        study.nct_id,
                        f"locations.country = {location.country}",
                        title=study.brief_title,
                        field_path="protocolSection.contactsLocationsModule.locations.country",
                        field_value=location.country,
                    )
                )
        data = [
            {"country": country, "trial_count": len(ids), "citations": self._citation_engine.sample(citations[country])}
            for country, ids in sorted(buckets.items(), key=lambda item: (-len(item[1]), item[0]))
        ]
        return ProcessedVisualizationData(
            chart_type=ChartType.BAR_CHART,
            title="Trials by Country",
            encoding={
                "x": FieldEncoding(field="country", type=DataType.NOMINAL, title=normalize_label("country")),
                "y": FieldEncoding(field="trial_count", type=DataType.QUANTITATIVE, title="Trials"),
            },
            data=data,
            filters_applied={k: v for k, v in plan.model_dump(mode="json")["filters"].items() if v not in (None, [], {})},
            studies_used=len(studies_used),
        )
