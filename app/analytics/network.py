from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations

from app.analytics.base import ProcessedVisualizationData, make_citation, study_matches_plan
from app.citations.engine import CitationEngine
from app.config import Settings
from app.models.analysis_plan import AnalysisPlan
from app.models.enums import ChartType, DataType, RelationshipKind
from app.models.fetch_plan import FetchPlan
from app.models.visualization import FieldEncoding, NetworkData, NetworkEdge, NetworkNode
from app.normalize.facts import CanonicalFacts


class NetworkProcessor:
    def __init__(self, citation_engine: CitationEngine, settings: Settings) -> None:
        self._citation_engine = citation_engine
        self._settings = settings

    def process(self, facts: CanonicalFacts, plan: AnalysisPlan, fetch_plan: FetchPlan) -> ProcessedVisualizationData:
        relationship_kind = plan.entities.relationship_kind or RelationshipKind.SPONSOR_DRUG
        node_counts: Counter[str] = Counter()
        edge_to_studies: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
        edge_citations: defaultdict[tuple[str, str], list] = defaultdict(list)
        node_labels: dict[str, tuple[str, str]] = {}
        studies_used: set[str] = set()

        for study in facts.studies:
            if not study_matches_plan(study, plan):
                continue
            studies_used.add(study.nct_id)
            if relationship_kind == RelationshipKind.DRUG_DRUG:
                drugs = sorted({item.intervention_name for item in study.interventions if item.intervention_name})
                for drug in drugs:
                    node_id = f"drug:{drug}"
                    node_labels[node_id] = (drug, "drug")
                    node_counts[node_id] += 1
                for left, right in combinations(drugs, 2):
                    edge = tuple(sorted((f"drug:{left}", f"drug:{right}")))
                    edge_to_studies[edge].add(study.nct_id)
                    edge_citations[edge].append(
                        make_citation(
                            study.nct_id,
                            f"combination study includes {left} and {right}",
                            title=study.brief_title,
                            field_path="protocolSection.armsInterventionsModule.interventions.name",
                        )
                    )
            else:
                left_items = [sponsor.sponsor_name for sponsor in study.sponsors if sponsor.sponsor_name]
                if relationship_kind == RelationshipKind.SPONSOR_CONDITION:
                    right_items = list(study.conditions)
                    right_prefix = "condition"
                else:
                    right_items = [intervention.intervention_name for intervention in study.interventions if intervention.intervention_name]
                    right_prefix = "drug"
                for left in set(left_items):
                    left_id = f"sponsor:{left}"
                    node_labels[left_id] = (left, "sponsor")
                    node_counts[left_id] += 1
                    for right in set(right_items):
                        right_id = f"{right_prefix}:{right}"
                        node_labels[right_id] = (right, right_prefix)
                        node_counts[right_id] += 1
                        edge = (left_id, right_id)
                        edge_to_studies[edge].add(study.nct_id)
                        edge_citations[edge].append(
                            make_citation(
                                study.nct_id,
                                f"{left} connected to {right}",
                                title=study.brief_title,
                            )
                        )

        top_nodes = {node_id for node_id, _ in node_counts.most_common(self._settings.network_max_nodes)}
        warnings: list[str] = []
        if len(node_counts) > len(top_nodes):
            warnings.append(f"Network pruned to top {self._settings.network_max_nodes} nodes")

        nodes = [
            NetworkNode(id=node_id, label=node_labels[node_id][0], type=node_labels[node_id][1], size=count)
            for node_id, count in node_counts.items()
            if node_id in top_nodes
        ]
        edges = [
            NetworkEdge(
                source=edge[0],
                target=edge[1],
                weight=len(studies),
                citations=self._citation_engine.sample(edge_citations[edge]),
            )
            for edge, studies in edge_to_studies.items()
            if edge[0] in top_nodes and edge[1] in top_nodes
        ]
        return ProcessedVisualizationData(
            chart_type=ChartType.NETWORK_GRAPH,
            title="Relationship Network",
            encoding={
                "node_color": FieldEncoding(field="type", type=DataType.NOMINAL, title="Node Type"),
                "node_size": FieldEncoding(field="size", type=DataType.QUANTITATIVE, title="Frequency"),
                "edge_weight": FieldEncoding(field="weight", type=DataType.QUANTITATIVE, title="Edge Weight"),
            },
            data=NetworkData(nodes=nodes, edges=edges),
            filters_applied={k: v for k, v in plan.model_dump(mode="json")["filters"].items() if v not in (None, [], {})},
            studies_used=len(studies_used),
            warnings=warnings,
        )
