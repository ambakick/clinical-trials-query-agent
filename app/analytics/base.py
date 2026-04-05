from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from app.models.analysis_plan import AnalysisPlan
from app.models.enums import ChartType, ComparisonDimension, GroupByField, MatchMode
from app.models.visualization import Citation, FieldEncoding, NetworkData
from app.normalize.facts import StudyRecord


@dataclass(slots=True)
class ProcessedVisualizationData:
    chart_type: ChartType
    title: str
    encoding: dict[str, FieldEncoding]
    data: list[dict[str, Any]] | NetworkData
    filters_applied: dict[str, Any]
    studies_used: int | None = None
    warnings: list[str] = field(default_factory=list)
    description: str | None = None
    render_hints: dict[str, Any] | None = None


def normalize_label(value: str | None) -> str:
    if not value:
        return "Unknown"
    if value == "NA":
        return "N/A"
    if value.startswith("EARLY_"):
        return "Early Phase 1"
    if value.startswith("PHASE"):
        label = value.replace("PHASE", "Phase ")
        return label.replace("_", "/").strip()
    return value.replace("_", " ").title()


def is_low_cardinality(data: list[dict[str, Any]], limit: int = 6) -> bool:
    return len(data) <= limit


def study_matches_plan(study: StudyRecord, plan: AnalysisPlan) -> bool:
    if plan.filters.start_year and (study.start_date is None or study.start_date.year is None or study.start_date.year < plan.filters.start_year):
        return False
    if plan.filters.end_year and (study.start_date is None or study.start_date.year is None or study.start_date.year > plan.filters.end_year):
        return False
    if plan.filters.status and study.overall_status not in {status.value for status in plan.filters.status}:
        return False
    if plan.filters.country:
        countries = {location.country for location in study.locations if location.country}
        if plan.filters.country not in countries:
            return False
    if plan.filters.trial_phase:
        phases = set(study.phases)
        if not phases.intersection({phase.value for phase in plan.filters.trial_phase}):
            return False
    if plan.entities.condition:
        match = _match_values(plan.match_mode, plan.entities.condition, study.conditions)
        if not match:
            return False
    if plan.entities.drug_name:
        match = _match_values(plan.match_mode, plan.entities.drug_name, [item.intervention_name for item in study.interventions])
        if not match:
            return False
    if plan.entities.sponsor:
        match = _match_values(plan.match_mode, plan.entities.sponsor, [item.sponsor_name for item in study.sponsors])
        if not match:
            return False
    return True


def _match_values(mode: MatchMode, needle: str, haystack: list[str]) -> bool:
    needle_norm = needle.casefold()
    values = [value.casefold() for value in haystack]
    if mode == MatchMode.EXACT:
        return needle_norm in values
    return any(needle_norm in value for value in values)


def count_distinct_pairs(pairs: list[tuple[str, str]]) -> Counter[str]:
    grouped: defaultdict[str, set[str]] = defaultdict(set)
    for key, nct_id in pairs:
        grouped[key].add(nct_id)
    return Counter({key: len(ids) for key, ids in grouped.items()})


def split_for_comparison(studies: list[StudyRecord], plan: AnalysisPlan) -> dict[str, list[StudyRecord]]:
    if not plan.entities.comparison:
        return {}
    output: dict[str, list[StudyRecord]] = defaultdict(list)
    comparison = plan.entities.comparison
    for study in studies:
        if study.cohort_label:
            output[study.cohort_label].append(study)
            continue
        target_values: list[str] = []
        if comparison.dimension == ComparisonDimension.DRUG_NAME:
            target_values = [item.intervention_name for item in study.interventions]
        elif comparison.dimension == ComparisonDimension.CONDITION:
            target_values = list(study.conditions)
        elif comparison.dimension == ComparisonDimension.SPONSOR:
            target_values = [item.sponsor_name for item in study.sponsors]
        if _match_values(MatchMode.EXACT, comparison.left, target_values):
            output[comparison.left].append(study)
        if _match_values(MatchMode.EXACT, comparison.right, target_values):
            output[comparison.right].append(study)
    return output


def make_citation(
    nct_id: str,
    excerpt: str,
    *,
    title: str | None = None,
    field_path: str | None = None,
    field_value: str | int | float | bool | None = None,
) -> Citation:
    return Citation(
        nct_id=nct_id,
        title=title,
        field_path=field_path,
        field_value=field_value,
        excerpt=excerpt,
    )
