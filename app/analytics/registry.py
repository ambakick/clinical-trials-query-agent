from __future__ import annotations

from app.analytics.comparison import ComparisonProcessor
from app.analytics.distribution import DistributionProcessor
from app.analytics.geographic import GeographicProcessor
from app.analytics.network import NetworkProcessor
from app.analytics.ranking import RankingProcessor
from app.analytics.scatter import ScatterProcessor
from app.analytics.time_trend import TimeTrendProcessor
from app.citations.engine import CitationEngine
from app.config import Settings
from app.models.enums import QueryClass


class ProcessorRegistry:
    def __init__(self, citation_engine: CitationEngine, settings: Settings) -> None:
        self._processors = {
            QueryClass.TIME_TREND: TimeTrendProcessor(citation_engine),
            QueryClass.DISTRIBUTION: DistributionProcessor(citation_engine),
            QueryClass.COMPARISON: ComparisonProcessor(citation_engine),
            QueryClass.GEOGRAPHIC: GeographicProcessor(citation_engine),
            QueryClass.RELATIONSHIP_NETWORK: NetworkProcessor(citation_engine, settings),
            QueryClass.RANKING: RankingProcessor(citation_engine),
            QueryClass.SCATTER: ScatterProcessor(citation_engine),
        }

    def get(self, query_class: QueryClass):
        return self._processors[query_class]
