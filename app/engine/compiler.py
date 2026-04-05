from __future__ import annotations

from typing import Any

from app.config import Settings
from app.engine.errors import CompilerValidationError
from app.models.analysis_plan import AnalysisPlan, ComparisonSelection
from app.models.enums import (
    ChartType,
    ComparisonDimension,
    GroupByField,
    MatchMode,
    QueryClass,
    RelationshipKind,
)
from app.models.fetch_plan import CompiledRequest, FetchPlan, TruncationPolicy
from app.models.request import QueryRequest


def _format_date_range(start_year: int | None, end_year: int | None) -> str | None:
    if start_year is None and end_year is None:
        return None
    start = f"01/01/{start_year}" if start_year is not None else "MIN"
    end = f"12/31/{end_year}" if end_year is not None else "MAX"
    return f"AREA[StartDate]RANGE[{start}, {end}]"


def _format_phase_filter(phases: list[str]) -> str | None:
    if not phases:
        return None
    if len(phases) == 1:
        return f"AREA[Phase]{phases[0]}"
    joined = " OR ".join(phases)
    return f"AREA[Phase]({joined})"


class PlanCompiler:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def compile(self, plan: AnalysisPlan, request: QueryRequest) -> FetchPlan:
        if len(plan.group_by) > 2:
            raise CompilerValidationError("v1 supports at most two grouping dimensions")
        if plan.query_class == QueryClass.COMPARISON and not plan.entities.comparison:
            raise CompilerValidationError("comparison queries require explicit comparison values")

        if plan.query_class == QueryClass.TIME_TREND:
            requests, required_fields = self._compile_standard(plan, default_fields=["NCTId", "BriefTitle", "StartDate"])
        elif plan.query_class == QueryClass.DISTRIBUTION:
            requests, required_fields = self._compile_distribution(plan)
        elif plan.query_class == QueryClass.COMPARISON:
            requests, required_fields = self._compile_comparison(plan)
        elif plan.query_class == QueryClass.GEOGRAPHIC:
            requests, required_fields = self._compile_standard(
                plan,
                default_fields=["NCTId", "BriefTitle", "LocationCountry", "LocationStatus", "OverallStatus"],
            )
        elif plan.query_class == QueryClass.RELATIONSHIP_NETWORK:
            requests, required_fields = self._compile_network(plan)
        elif plan.query_class == QueryClass.RANKING:
            requests, required_fields = self._compile_distribution(plan)
        elif plan.query_class == QueryClass.SCATTER:
            requests, required_fields = self._compile_scatter(plan)
        else:
            raise CompilerValidationError(f"unsupported query class: {plan.query_class}")

        if plan.chart_type == ChartType.PIE_CHART and plan.query_class not in {QueryClass.DISTRIBUTION, QueryClass.RANKING}:
            raise CompilerValidationError("pie_chart is only supported for distribution and ranking queries")

        return FetchPlan(
            requests=requests,
            required_fields=required_fields,
            max_results=min(request.max_results, self._settings.max_studies_per_query),
            truncation_policy=TruncationPolicy(max_results=min(request.max_results, self._settings.max_studies_per_query)),
        )

    def _compile_standard(self, plan: AnalysisPlan, default_fields: list[str]) -> tuple[list[CompiledRequest], list[str]]:
        fields = sorted(
            set(
                default_fields
                + self._fields_for_group_by(plan.group_by)
                + self._fields_for_plan_matching(plan)
            )
        )
        params = self._build_base_params(plan)
        return [
            CompiledRequest(
                purpose=plan.intent,
                params=params,
                fields=fields,
                page_size=self._settings.ctgov_page_size,
            )
        ], fields

    def _compile_distribution(self, plan: AnalysisPlan) -> tuple[list[CompiledRequest], list[str]]:
        fields = ["NCTId", "BriefTitle"]
        fields.extend(self._fields_for_group_by(plan.group_by))
        fields.extend(self._fields_for_plan_matching(plan))
        fields = sorted(set(fields))
        params = self._build_base_params(plan)
        return [
            CompiledRequest(
                purpose=plan.intent,
                params=params,
                fields=fields,
                page_size=self._settings.ctgov_page_size,
            )
        ], fields

    def _compile_network(self, plan: AnalysisPlan) -> tuple[list[CompiledRequest], list[str]]:
        relationship_kind = plan.entities.relationship_kind or RelationshipKind.SPONSOR_DRUG
        fields = ["NCTId", "BriefTitle"]
        if relationship_kind in {RelationshipKind.SPONSOR_DRUG, RelationshipKind.SPONSOR_CONDITION}:
            fields.extend(["LeadSponsorName", "CollaboratorName"])
        if relationship_kind in {RelationshipKind.SPONSOR_DRUG, RelationshipKind.DRUG_DRUG}:
            fields.extend(["InterventionName", "InterventionType"])
        if relationship_kind == RelationshipKind.SPONSOR_CONDITION:
            fields.append("Condition")
        fields.extend(self._fields_for_plan_matching(plan))
        fields = sorted(set(fields))
        params = self._build_base_params(plan)
        return [
            CompiledRequest(
                purpose=plan.intent,
                params=params,
                fields=fields,
                page_size=self._settings.ctgov_page_size,
            )
        ], fields

    def _compile_comparison(self, plan: AnalysisPlan) -> tuple[list[CompiledRequest], list[str]]:
        comparison = plan.entities.comparison
        assert comparison is not None
        fields = ["NCTId", "BriefTitle"]
        fields.extend(self._fields_for_group_by(plan.group_by))
        fields.extend(self._fields_for_plan_matching(plan))
        fields = sorted(set(fields))
        left_params = self._build_base_params(plan, comparison_override=("left", comparison))
        right_params = self._build_base_params(plan, comparison_override=("right", comparison))
        return [
            CompiledRequest(
                purpose=f"{plan.intent} ({comparison.left})",
                label=comparison.left,
                params=left_params,
                fields=fields,
                page_size=self._settings.ctgov_page_size,
            ),
            CompiledRequest(
                purpose=f"{plan.intent} ({comparison.right})",
                label=comparison.right,
                params=right_params,
                fields=fields,
                page_size=self._settings.ctgov_page_size,
            ),
        ], fields

    def _compile_scatter(self, plan: AnalysisPlan) -> tuple[list[CompiledRequest], list[str]]:
        fields = [
            "NCTId",
            "BriefTitle",
            "StartDate",
            "CompletionDate",
            "EnrollmentCount",
        ]
        fields.extend(self._fields_for_plan_matching(plan))
        fields = sorted(set(fields))
        params = self._build_base_params(plan)
        return [
            CompiledRequest(
                purpose=plan.intent,
                params=params,
                fields=fields,
                page_size=self._settings.ctgov_page_size,
            )
        ], fields

    def _build_base_params(
        self,
        plan: AnalysisPlan,
        comparison_override: tuple[str, ComparisonSelection] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        entity_drug = plan.entities.drug_name
        entity_condition = plan.entities.condition
        entity_sponsor = plan.entities.sponsor
        entity_country = plan.entities.country

        if comparison_override:
            side, comparison = comparison_override
            value = comparison.left if side == "left" else comparison.right
            if comparison.dimension == ComparisonDimension.DRUG_NAME:
                entity_drug = value
            elif comparison.dimension == ComparisonDimension.CONDITION:
                entity_condition = value
            elif comparison.dimension == ComparisonDimension.SPONSOR:
                entity_sponsor = value

        if plan.match_mode == MatchMode.EXACT:
            clauses: list[str] = []
            if entity_drug:
                clauses.append(f"AREA[InterventionName]{entity_drug}")
            if entity_condition:
                clauses.append(f"AREA[Condition]{entity_condition}")
            if entity_sponsor:
                clauses.append(f"AREA[LeadSponsorName]{entity_sponsor}")
            if entity_country:
                clauses.append(f"AREA[LocationCountry]{entity_country}")
            if clauses:
                params["query.term"] = " AND ".join(clauses)
        else:
            if entity_drug:
                params["query.intr"] = entity_drug
            if entity_condition:
                params["query.cond"] = entity_condition
            if entity_sponsor:
                params["query.spons"] = entity_sponsor
            if entity_country:
                params["query.locn"] = entity_country

        if plan.filters.status:
            params["filter.overallStatus"] = ",".join(status.value for status in plan.filters.status)

        advanced_clauses: list[str] = []
        date_range = _format_date_range(plan.filters.start_year, plan.filters.end_year)
        if date_range:
            advanced_clauses.append(date_range)
        phase_filter = _format_phase_filter([phase.value for phase in plan.filters.trial_phase or []])
        if phase_filter:
            advanced_clauses.append(phase_filter)
        if advanced_clauses:
            params["filter.advanced"] = " AND ".join(advanced_clauses)
        return params

    @staticmethod
    def _fields_for_plan_matching(plan: AnalysisPlan) -> list[str]:
        fields: list[str] = []
        if plan.entities.condition:
            fields.append("Condition")
        if plan.entities.drug_name:
            fields.extend(["InterventionName", "InterventionType"])
        if plan.entities.sponsor:
            fields.append("LeadSponsorName")
        if plan.entities.country:
            fields.append("LocationCountry")
        if plan.filters.status:
            fields.append("OverallStatus")
        if plan.filters.trial_phase:
            fields.append("Phase")

        comparison = plan.entities.comparison
        if comparison:
            if comparison.dimension == ComparisonDimension.DRUG_NAME:
                fields.extend(["InterventionName", "InterventionType"])
            elif comparison.dimension == ComparisonDimension.CONDITION:
                fields.append("Condition")
            elif comparison.dimension == ComparisonDimension.SPONSOR:
                fields.append("LeadSponsorName")
        return fields

    @staticmethod
    def _fields_for_group_by(group_by: list[GroupByField]) -> list[str]:
        mapping = {
            GroupByField.START_YEAR: "StartDate",
            GroupByField.PHASE: "Phase",
            GroupByField.INTERVENTION_TYPE: "InterventionType",
            GroupByField.COUNTRY: "LocationCountry",
            GroupByField.OVERALL_STATUS: "OverallStatus",
            GroupByField.SPONSOR: "LeadSponsorName",
            GroupByField.SPONSOR_CLASS: "LeadSponsorClass",
            GroupByField.CONDITION: "Condition",
        }
        return [mapping[field] for field in group_by if field in mapping]
