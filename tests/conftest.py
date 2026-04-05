from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings
from app.models.analysis_plan import AnalysisPlan, ComparisonSelection, EntitySelection, FilterSelection, MeasureSpec
from app.models.enums import (
    ChartType,
    ComparisonDimension,
    GroupByField,
    MatchMode,
    MeasureKind,
    QueryClass,
    CitationMode,
)
from app.models.fetch_plan import FetchExecutionResult, FetchedStudyBatch, VersionInfo


@pytest.fixture
def settings() -> Settings:
    return Settings(openai_api_key=None)


@pytest.fixture
def sample_plan() -> AnalysisPlan:
    return AnalysisPlan(
        query_class=QueryClass.DISTRIBUTION,
        intent="Show phase distribution for lung cancer trials",
        match_mode=MatchMode.BROAD,
        entities=EntitySelection(condition="Lung cancer"),
        filters=FilterSelection(),
        measure=MeasureSpec(kind=MeasureKind.TRIAL_COUNT),
        group_by=[GroupByField.PHASE],
        chart_type=ChartType.BAR_CHART,
        citation_mode=CitationMode.DEEP,
        confidence=0.95,
    )


@pytest.fixture
def comparison_plan() -> AnalysisPlan:
    return AnalysisPlan(
        query_class=QueryClass.COMPARISON,
        intent="Compare pembrolizumab vs nivolumab by phase",
        match_mode=MatchMode.EXACT,
        entities=EntitySelection(
            condition="Lung cancer",
            comparison=ComparisonSelection(
                dimension=ComparisonDimension.DRUG_NAME,
                left="Pembrolizumab",
                right="Nivolumab",
            ),
        ),
        filters=FilterSelection(),
        measure=MeasureSpec(kind=MeasureKind.TRIAL_COUNT),
        group_by=[GroupByField.PHASE],
        chart_type=ChartType.GROUPED_BAR_CHART,
        citation_mode=CitationMode.DEEP,
        confidence=0.97,
    )


@pytest.fixture
def sample_fetch_result() -> FetchExecutionResult:
    studies = [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT001",
                    "briefTitle": "Pembrolizumab Phase 1 Study",
                },
                "statusModule": {
                    "overallStatus": "RECRUITING",
                    "startDateStruct": {"date": "2020-01-10"},
                    "completionDateStruct": {"date": "2021-04-10"},
                },
                "conditionsModule": {
                    "conditions": ["Lung cancer"],
                },
                "designModule": {
                    "phases": ["PHASE1"],
                    "enrollmentInfo": {"count": 120},
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Merck", "class": "INDUSTRY"},
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {"type": "DRUG", "name": "Pembrolizumab"},
                        {"type": "DRUG", "name": "Carboplatin"},
                    ]
                },
                "contactsLocationsModule": {
                    "locations": [{"country": "United States", "status": "RECRUITING"}]
                },
            }
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT002",
                    "briefTitle": "Nivolumab Phase 2 Study",
                },
                "statusModule": {
                    "overallStatus": "ACTIVE_NOT_RECRUITING",
                    "startDateStruct": {"date": "2021-04-12"},
                    "completionDateStruct": {"date": "2022-08-12"},
                },
                "conditionsModule": {
                    "conditions": ["Lung cancer"],
                },
                "designModule": {
                    "phases": ["PHASE2"],
                    "enrollmentInfo": {"count": 85},
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "BMS", "class": "NIH"},
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {"type": "DRUG", "name": "Nivolumab"},
                    ]
                },
                "contactsLocationsModule": {
                    "locations": [{"country": "China", "status": "ACTIVE_NOT_RECRUITING"}]
                },
            }
        },
    ]
    return FetchExecutionResult(
        batches=[FetchedStudyBatch(purpose="sample", studies=studies, total_count=2)],
        version_info=VersionInfo(api_version="2.0.5", data_timestamp="2026-04-03T09:00:05"),
    )
