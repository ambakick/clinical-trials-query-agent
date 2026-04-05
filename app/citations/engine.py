from __future__ import annotations

from app.models.visualization import Citation


class CitationEngine:
    def __init__(self, max_citations_per_bucket: int) -> None:
        self._max_citations_per_bucket = max_citations_per_bucket

    def sample(self, citations: list[Citation]) -> list[Citation]:
        deduped: list[Citation] = []
        seen: set[tuple[str, str]] = set()
        for citation in citations:
            key = (citation.nct_id, citation.excerpt)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(citation)
            if len(deduped) >= self._max_citations_per_bucket:
                break
        return deduped

