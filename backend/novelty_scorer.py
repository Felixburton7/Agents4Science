from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.evidence_utils import make_metric, no_papers_metric, paper_evidence_id, sorted_papers


async def novelty_scorer(state: dict[str, Any]) -> dict[str, list[Any]]:
    papers = sorted_papers(state)
    if not papers:
        return {"metric_scores": [no_papers_metric("novelty")]}

    close_neighbours = [paper for paper in papers if paper.relevance_score >= 0.45][:8]
    if not close_neighbours:
        close_neighbours = papers[:5]

    current_year = datetime.now().year
    mean_relevance = sum(paper.relevance_score for paper in close_neighbours) / len(close_neighbours)
    recent_share = sum(1 for paper in close_neighbours if paper.year and paper.year >= current_year - 5) / len(close_neighbours)
    dense_penalty = min(45, len(close_neighbours) * 5.5)
    similarity_penalty = mean_relevance * 42
    recency_penalty = recent_share * 13
    novelty = 100 - dense_penalty - similarity_penalty - recency_penalty
    evidence_ids = [paper_evidence_id(paper) for paper in close_neighbours[:6]]

    closest = close_neighbours[0]
    return {
        "metric_scores": [
            make_metric(
                "novelty",
                novelty,
                (
                    f"Novelty compares the parsed hypothesis against {len(close_neighbours)} real nearest papers. "
                    f"The closest analogue is '{closest.title}' with relevance {closest.relevance_score:.2f}; "
                    f"recent close-neighbour share is {recent_share:.0%}."
                ),
                evidence_ids,
                "Closest prior work should be differentiated by mechanism, context, or method before development.",
                confidence_span=max(8, 18 - len(evidence_ids)),
                method="deterministic:real_neighbour_density_v1",
            )
        ]
    }


run = novelty_scorer
