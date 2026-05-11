from __future__ import annotations

from typing import Any

from backend.evidence_utils import make_metric, no_papers_metric, paper_evidence_id, sorted_papers


async def evidence_quality_scorer(state: dict[str, Any]) -> dict[str, list[Any]]:
    papers = sorted_papers(state)
    if not papers:
        return {"metric_scores": [no_papers_metric("evidence_quality")]}

    total = len(papers)
    abstract_ratio = sum(1 for paper in papers if paper.abstract.strip()) / total
    doi_ratio = sum(1 for paper in papers if paper.doi) / total
    stable_id_ratio = sum(1 for paper in papers if paper_evidence_id(paper) != paper.paper_id or paper.paper_id.startswith(("doi:", "openalex:", "s2:"))) / total
    cross_source_ratio = sum(1 for paper in papers if len(set(paper.source_provenance)) > 1) / total
    strong_relevance_ratio = sum(1 for paper in papers if paper.relevance_score >= 0.45) / total
    citation_signal_ratio = sum(1 for paper in papers if paper.citation_count > 0) / total

    score = (
        abstract_ratio * 24
        + stable_id_ratio * 22
        + cross_source_ratio * 16
        + strong_relevance_ratio * 18
        + citation_signal_ratio * 12
        + doi_ratio * 8
    )
    top_supported = sorted(
        papers,
        key=lambda paper: (
            len(set(paper.source_provenance)),
            bool(paper.abstract.strip()),
            paper.relevance_score,
            paper.citation_count,
        ),
        reverse=True,
    )[:8]
    evidence_ids = [paper_evidence_id(paper) for paper in top_supported[:6]]
    weakness = _weakness(total, abstract_ratio, cross_source_ratio, strong_relevance_ratio)

    return {
        "metric_scores": [
            make_metric(
                "evidence_quality",
                score,
                (
                    f"Evidence quality reflects {total} real papers with abstract coverage {abstract_ratio:.0%}, "
                    f"stable identifiers {stable_id_ratio:.0%}, cross-source agreement {cross_source_ratio:.0%}, "
                    f"and strong relevance coverage {strong_relevance_ratio:.0%}."
                ),
                evidence_ids,
                weakness,
                confidence_span=max(7, round(20 - min(total, 30) / 3)),
                method="deterministic:retrieval_completeness_v1",
            )
        ]
    }


run = evidence_quality_scorer


def _weakness(total: int, abstract_ratio: float, cross_source_ratio: float, strong_relevance_ratio: float) -> str:
    if total < 15:
        return "Evidence set is small; broaden retrieval before making strong production claims."
    if abstract_ratio < 0.55:
        return "Many records lack abstracts, limiting mechanism and conflict interpretation."
    if cross_source_ratio < 0.2:
        return "Few records were confirmed across both OpenAlex and Semantic Scholar."
    if strong_relevance_ratio < 0.35:
        return "Retrieved papers are broad; scores may reflect field context more than close analogues."
    return "Remaining risk comes from metadata incompleteness and heuristic scoring limits."
