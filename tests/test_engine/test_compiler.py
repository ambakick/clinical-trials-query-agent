from __future__ import annotations

from app.engine.compiler import PlanCompiler
from app.models.analysis_plan import EntitySelection, FilterSelection
from app.models.enums import ChartType, GroupByField, MeasureKind, QueryClass, TrialPhase, TrialStatus
from app.models.analysis_plan import AnalysisPlan, MeasureSpec


def test_compiler_builds_exact_comparison(settings, comparison_plan) -> None:
    compiler = PlanCompiler(settings)
    fetch_plan = compiler.compile(comparison_plan, request=type("Req", (), {"max_results": 3000})())
    assert len(fetch_plan.requests) == 2
    assert "query.term" in fetch_plan.requests[0].params
    assert "AREA[InterventionName]Pembrolizumab" in fetch_plan.requests[0].params["query.term"]
    assert "AREA[Condition]Lung cancer" in fetch_plan.requests[0].params["query.term"]


def test_compiler_builds_broad_distribution(settings, sample_plan) -> None:
    compiler = PlanCompiler(settings)
    fetch_plan = compiler.compile(sample_plan, request=type("Req", (), {"max_results": 3000})())
    request = fetch_plan.requests[0]
    assert request.params["query.cond"] == "Lung cancer"
    assert "Phase" in request.fields


def test_compiler_adds_matching_fields_and_api_filters(settings, sample_plan) -> None:
    compiler = PlanCompiler(settings)
    plan = sample_plan.model_copy(
        update={
            "entities": EntitySelection(
                condition="Melanoma",
                drug_name="Pembrolizumab",
                sponsor="Merck",
                country="United States",
            ),
            "filters": FilterSelection(
                status=[TrialStatus.RECRUITING, TrialStatus.COMPLETED],
                trial_phase=[TrialPhase.PHASE1, TrialPhase.PHASE2],
            ),
        }
    )
    fetch_plan = compiler.compile(plan, request=type("Req", (), {"max_results": 3000})())
    request = fetch_plan.requests[0]

    assert "Condition" in request.fields
    assert "InterventionName" in request.fields
    assert "InterventionType" in request.fields
    assert "LeadSponsorName" in request.fields
    assert "LocationCountry" in request.fields
    assert "OverallStatus" in request.fields
    assert "Phase" in request.fields

    assert request.params["filter.overallStatus"] == "RECRUITING,COMPLETED"
    assert request.params["filter.advanced"] == "AREA[Phase](PHASE1 OR PHASE2)"


def test_compiler_combines_date_and_phase_into_filter_advanced(settings, sample_plan) -> None:
    compiler = PlanCompiler(settings)
    plan = sample_plan.model_copy(
        update={
            "filters": FilterSelection(
                start_year=2015,
                trial_phase=[TrialPhase.PHASE3],
            )
        }
    )
    fetch_plan = compiler.compile(plan, request=type("Req", (), {"max_results": 3000})())
    request = fetch_plan.requests[0]
    assert request.params["filter.advanced"] == "AREA[StartDate]RANGE[01/01/2015, MAX] AND AREA[Phase]PHASE3"
    assert "filter.phase" not in request.params


def test_compiler_maps_sponsor_class_to_lead_sponsor_class(settings, sample_plan) -> None:
    compiler = PlanCompiler(settings)
    plan = sample_plan.model_copy(update={"group_by": [GroupByField.SPONSOR_CLASS]})
    fetch_plan = compiler.compile(plan, request=type("Req", (), {"max_results": 3000})())
    assert "LeadSponsorClass" in fetch_plan.requests[0].fields


def test_compiler_builds_scatter_fetch_plan(settings) -> None:
    compiler = PlanCompiler(settings)
    plan = AnalysisPlan(
        query_class=QueryClass.SCATTER,
        intent="Plot enrollment versus duration for lung cancer trials",
        match_mode="broad",
        entities=EntitySelection(condition="Lung cancer"),
        filters=FilterSelection(trial_phase=[TrialPhase.PHASE1]),
        measure=MeasureSpec(kind=MeasureKind.SCATTER_POINT),
        group_by=[],
        chart_type=ChartType.SCATTER_PLOT,
        citation_mode="deep",
        confidence=0.9,
    )
    fetch_plan = compiler.compile(plan, request=type("Req", (), {"max_results": 3000})())
    request = fetch_plan.requests[0]
    assert "EnrollmentCount" in request.fields
    assert "CompletionDate" in request.fields
    assert "StartDate" in request.fields
