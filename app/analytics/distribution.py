from __future__ import annotations

from collections import defaultdict

from app.analytics.base import ProcessedVisualizationData, make_citation, normalize_label, study_matches_plan
from app.citations.engine import CitationEngine
from app.models.analysis_plan import AnalysisPlan
from app.models.enums import ChartType, DataType, GroupByField
from app.models.fetch_plan import FetchPlan
from app.models.visualization import FieldEncoding
from app.normalize.facts import CanonicalFacts, StudyRecord


class DistributionProcessor:
    def __init__(self, citation_engine: CitationEngine) -> None:
        self._citation_engine = citation_engine

    def process(self, facts: CanonicalFacts, plan: AnalysisPlan, fetch_plan: FetchPlan) -> ProcessedVisualizationData:
        group_field = plan.group_by[0] if plan.group_by else GroupByField.PHASE
        buckets: defaultdict[str, set[str]] = defaultdict(set)
        citations: defaultdict[str, list] = defaultdict(list)
        studies_used: set[str] = set()
        for study in facts.studies:
            if not study_matches_plan(study, plan):
                continue
            studies_used.add(study.nct_id)
            for key, citation in _iter_group_values(group_field, study):
                buckets[key].add(study.nct_id)
                citations[key].append(citation)
        data = [
            {"category": label, "trial_count": len(ids), "citations": self._citation_engine.sample(citations[label])}
            for label, ids in sorted(buckets.items(), key=lambda item: (-len(item[1]), item[0]))
        ]
        chart_type = plan.chart_type
        warnings: list[str] = []
        if chart_type == ChartType.PIE_CHART and len(data) > 6:
            chart_type = ChartType.BAR_CHART
            warnings.append("Pie chart downgraded to bar chart because category count was too high.")
        return ProcessedVisualizationData(
            chart_type=chart_type,
            title=f"Trials by {normalize_label(group_field.value)}",
            encoding={
                "x": FieldEncoding(field="category", type=DataType.NOMINAL, title=normalize_label(group_field.value)),
                "y": FieldEncoding(field="trial_count", type=DataType.QUANTITATIVE, title="Trials"),
            },
            data=data,
            filters_applied={k: v for k, v in plan.model_dump(mode="json")["filters"].items() if v not in (None, [], {})},
            studies_used=len(studies_used),
            warnings=warnings,
        )


def _iter_group_values(group_field: GroupByField, study: StudyRecord) -> list[tuple[str, object]]:
    items: list[tuple[str, object]] = []
    if group_field == GroupByField.PHASE:
        for phase in study.phases or ["Unknown"]:
            items.append(
                (
                    normalize_label(phase),
                    make_citation(
                        study.nct_id,
                        f"phases includes {phase}",
                        title=study.brief_title,
                        field_path="protocolSection.designModule.phases",
                        field_value=phase,
                    ),
                )
            )
    elif group_field == GroupByField.INTERVENTION_TYPE:
        for intervention in study.interventions or []:
            value = normalize_label(intervention.intervention_type)
            items.append(
                (
                    value,
                    make_citation(
                        study.nct_id,
                        f"intervention.type = {intervention.intervention_type}",
                        title=study.brief_title,
                        field_path="protocolSection.armsInterventionsModule.interventions.type",
                        field_value=intervention.intervention_type,
                    ),
                )
            )
    elif group_field == GroupByField.OVERALL_STATUS:
        value = normalize_label(study.overall_status)
        items.append(
            (
                value,
                make_citation(
                    study.nct_id,
                    f"overallStatus = {study.overall_status}",
                    title=study.brief_title,
                    field_path="protocolSection.statusModule.overallStatus",
                    field_value=study.overall_status,
                ),
            )
        )
    elif group_field == GroupByField.COUNTRY:
        for location in study.locations or []:
            value = normalize_label(location.country)
            items.append(
                (
                    value,
                    make_citation(
                        study.nct_id,
                        f"locations.country = {location.country}",
                        title=study.brief_title,
                        field_path="protocolSection.contactsLocationsModule.locations.country",
                        field_value=location.country,
                    ),
                )
            )
    elif group_field == GroupByField.SPONSOR:
        for sponsor in study.sponsors or []:
            items.append(
                (
                    sponsor.sponsor_name,
                    make_citation(
                        study.nct_id,
                        f"sponsor = {sponsor.sponsor_name}",
                        title=study.brief_title,
                        field_path="protocolSection.sponsorCollaboratorsModule.leadSponsor.name",
                        field_value=sponsor.sponsor_name,
                    ),
                )
            )
    elif group_field == GroupByField.SPONSOR_CLASS:
        for sponsor in study.sponsors or []:
            value = normalize_label(sponsor.sponsor_class)
            items.append(
                (
                    value,
                    make_citation(
                        study.nct_id,
                        f"leadSponsor.class = {sponsor.sponsor_class}",
                        title=study.brief_title,
                        field_path="protocolSection.sponsorCollaboratorsModule.leadSponsor.class",
                        field_value=sponsor.sponsor_class,
                    ),
                )
            )
    elif group_field == GroupByField.CONDITION:
        for condition in study.conditions or []:
            items.append(
                (
                    condition,
                    make_citation(
                        study.nct_id,
                        f"condition = {condition}",
                        title=study.brief_title,
                        field_path="protocolSection.conditionsModule.conditions",
                        field_value=condition,
                    ),
                )
            )
    return items
