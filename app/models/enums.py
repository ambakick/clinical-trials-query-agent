from __future__ import annotations

from enum import Enum


class QueryClass(str, Enum):
    TIME_TREND = "time_trend"
    DISTRIBUTION = "distribution"
    COMPARISON = "comparison"
    GEOGRAPHIC = "geographic"
    RELATIONSHIP_NETWORK = "relationship_network"
    RANKING = "ranking"
    SCATTER = "scatter"


class MatchMode(str, Enum):
    BROAD = "broad"
    EXACT = "exact"


class ChartType(str, Enum):
    BAR_CHART = "bar_chart"
    GROUPED_BAR_CHART = "grouped_bar_chart"
    TIME_SERIES = "time_series"
    NETWORK_GRAPH = "network_graph"
    PIE_CHART = "pie_chart"
    SCATTER_PLOT = "scatter_plot"


class CitationMode(str, Enum):
    NONE = "none"
    SAMPLE = "sample"
    DEEP = "deep"


class TrialPhase(str, Enum):
    EARLY_PHASE1 = "EARLY_PHASE1"
    PHASE1 = "PHASE1"
    PHASE1_PHASE2 = "PHASE1_PHASE2"
    PHASE2 = "PHASE2"
    PHASE2_PHASE3 = "PHASE2_PHASE3"
    PHASE3 = "PHASE3"
    PHASE4 = "PHASE4"
    NA = "NA"


class TrialStatus(str, Enum):
    NOT_YET_RECRUITING = "NOT_YET_RECRUITING"
    RECRUITING = "RECRUITING"
    ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION"
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    COMPLETED = "COMPLETED"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
    WITHDRAWN = "WITHDRAWN"
    UNKNOWN_STATUS = "UNKNOWN_STATUS"


class GroupByField(str, Enum):
    START_YEAR = "start_year"
    PHASE = "phase"
    INTERVENTION_TYPE = "intervention_type"
    COUNTRY = "country"
    OVERALL_STATUS = "overall_status"
    SPONSOR = "sponsor"
    SPONSOR_CLASS = "sponsor_class"
    CONDITION = "condition"


class MeasureKind(str, Enum):
    TRIAL_COUNT = "trial_count"
    EDGE_WEIGHT = "edge_weight"
    SCATTER_POINT = "scatter_point"


class TimeBucket(str, Enum):
    YEAR = "year"


class ComparisonDimension(str, Enum):
    DRUG_NAME = "drug_name"
    CONDITION = "condition"
    SPONSOR = "sponsor"


class RelationshipKind(str, Enum):
    SPONSOR_DRUG = "sponsor_drug"
    DRUG_DRUG = "drug_drug"
    SPONSOR_CONDITION = "sponsor_condition"


class TruncationMode(str, Enum):
    TRUNCATE = "truncate"


class DataType(str, Enum):
    QUANTITATIVE = "quantitative"
    NOMINAL = "nominal"
    ORDINAL = "ordinal"
    TEMPORAL = "temporal"
