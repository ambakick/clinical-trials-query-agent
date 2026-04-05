from __future__ import annotations

from app.analytics.network import NetworkProcessor
from app.analytics.ranking import RankingProcessor
from app.analytics.comparison import ComparisonProcessor
from app.analytics.scatter import ScatterProcessor
from app.citations.engine import CitationEngine
from app.config import Settings
from app.models.analysis_plan import AnalysisPlan, EntitySelection, FilterSelection, MeasureSpec
from app.models.enums import ChartType, CitationMode, GroupByField, MatchMode, MeasureKind, QueryClass, RelationshipKind, TrialPhase, TrialStatus
from app.models.fetch_plan import FetchPlan
from app.visualization.builder import VisualizationBuilder
from app.normalize.studies import normalize_fetch_result


def test_ranking_processor_limits_top_n(sample_plan, sample_fetch_result) -> None:
    facts = normalize_fetch_result(sample_fetch_result)
    plan = sample_plan.model_copy(update={"query_class": QueryClass.RANKING, "filters": FilterSelection(top_n=1)})
    processor = RankingProcessor(CitationEngine(5))
    result = processor.process(facts, plan, FetchPlan(requests=[], max_results=3000))
    assert len(result.data) == 1
    assert result.chart_type == ChartType.BAR_CHART


def test_network_processor_builds_edges(sample_fetch_result) -> None:
    facts = normalize_fetch_result(sample_fetch_result)
    plan = AnalysisPlan(
        query_class=QueryClass.RELATIONSHIP_NETWORK,
        intent="Build sponsor drug network",
        match_mode=MatchMode.BROAD,
        entities=EntitySelection(condition="Lung cancer", relationship_kind=RelationshipKind.SPONSOR_DRUG),
        filters=FilterSelection(),
        measure=MeasureSpec(kind=MeasureKind.EDGE_WEIGHT),
        group_by=[],
        chart_type=ChartType.NETWORK_GRAPH,
        citation_mode=CitationMode.DEEP,
        confidence=0.9,
    )
    processor = NetworkProcessor(CitationEngine(5), Settings(openai_api_key=None))
    result = processor.process(facts, plan, FetchPlan(requests=[], max_results=3000))
    assert len(result.data.edges) >= 1
    assert any(node.type == "sponsor" for node in result.data.nodes)


def test_comparison_processor_respects_plan_filters(comparison_plan, sample_fetch_result) -> None:
    facts = normalize_fetch_result(sample_fetch_result)
    plan = comparison_plan.model_copy(
        update={"filters": FilterSelection(status=[TrialStatus.RECRUITING])}
    )
    processor = ComparisonProcessor(CitationEngine(5))
    result = processor.process(facts, plan, FetchPlan(requests=[], max_results=3000))
    assert isinstance(result.data, list)
    assert len(result.data) == 1
    assert result.data[0]["series"] == "Pembrolizumab"


def test_distribution_processor_supports_sponsor_class_grouping(sample_plan, sample_fetch_result) -> None:
    facts = normalize_fetch_result(sample_fetch_result)
    plan = sample_plan.model_copy(update={"group_by": [GroupByField.SPONSOR_CLASS]})
    processor = RankingProcessor(CitationEngine(5))._distribution
    result = processor.process(facts, plan, FetchPlan(requests=[], max_results=3000))
    assert isinstance(result.data, list)
    assert {row["category"] for row in result.data} == {"Industry", "Nih"}


def test_visualization_builder_uses_filtered_studies_used(sample_plan, sample_fetch_result) -> None:
    facts = normalize_fetch_result(sample_fetch_result)
    plan = sample_plan.model_copy(update={"filters": FilterSelection(status=[TrialStatus.RECRUITING])})
    processed = RankingProcessor(CitationEngine(5))._distribution.process(
        facts,
        plan,
        FetchPlan(requests=[], max_results=3000),
    )
    builder = VisualizationBuilder()
    response = builder.build(processed, plan, sample_fetch_result, processing_started_at=0.0)
    assert response.meta.studies_analyzed == 1


def test_scatter_processor_builds_points(sample_fetch_result) -> None:
    facts = normalize_fetch_result(sample_fetch_result)
    plan = AnalysisPlan(
        query_class=QueryClass.SCATTER,
        intent="Plot enrollment versus duration for phase 1 lung cancer trials",
        match_mode=MatchMode.BROAD,
        entities=EntitySelection(condition="Lung cancer"),
        filters=FilterSelection(trial_phase=[TrialPhase.PHASE1]),
        measure=MeasureSpec(kind=MeasureKind.SCATTER_POINT),
        group_by=[],
        chart_type=ChartType.SCATTER_PLOT,
        citation_mode=CitationMode.DEEP,
        confidence=0.91,
    )
    processor = ScatterProcessor(CitationEngine(5))
    result = processor.process(facts, plan, FetchPlan(requests=[], max_results=3000))
    assert result.chart_type == ChartType.SCATTER_PLOT
    assert isinstance(result.data, list)
    assert len(result.data) == 1
    assert result.data[0]["enrollment_count"] == 120
    assert result.data[0]["duration_months"] == 15
