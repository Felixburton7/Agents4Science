from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.evidence_utils import make_metric, no_papers_metric, paper_evidence_id, sorted_papers, tokens_for_text
from backend.schemas import OverlapReport


async def saturation_scorer(state: dict[str, Any]) -> dict[str, Any]:
    papers = sorted_papers(state)
    if not papers:
        return {
            "overlaps": OverlapReport(
                crowding_score=0,
                overlapping_papers=[],
                whitespace_summary="No real papers were retrieved, so saturation cannot be estimated.",
                risk_notes=["Cartographer returned no usable literature records."],
            ),
            "metric_scores": [no_papers_metric("saturation")],
        }

    current_year = datetime.now().year
    relevant = [paper for paper in papers if paper.relevance_score >= 0.35]
    recent = [paper for paper in relevant if paper.year and paper.year >= current_year - 3]
    high_overlap = [paper for paper in relevant if paper.relevance_score >= 0.55]
    top_overlaps = (high_overlap or relevant or papers)[:8]

    density = min(1.0, len(relevant) / 35)
    recent_velocity = len(recent) / max(1, len(relevant))
    overlap_intensity = min(1.0, len(high_overlap) / 12)
    crowding = round((density * 42) + (recent_velocity * 28) + (overlap_intensity * 30))
    saturation_score = 100 - crowding
    evidence_ids = [paper_evidence_id(paper) for paper in top_overlaps[:6]]

    overlaps = OverlapReport(
        crowding_score=crowding,
        overlapping_papers=[f"{paper_evidence_id(paper)} | {paper.title}" for paper in top_overlaps[:8]],
        whitespace_summary=_whitespace_summary(top_overlaps),
        risk_notes=[
            f"{len(relevant)} relevant real papers and {len(high_overlap)} high-overlap neighbours were found.",
            f"{len(recent)} relevant papers are from the last three years, indicating {recent_velocity:.0%} recent velocity.",
        ],
    )
    return {
        "overlaps": overlaps,
        "metric_scores": [
            make_metric(
                "saturation",
                saturation_score,
                (
                    f"Saturation is scored from real retrieval density: {len(relevant)} relevant papers, "
                    f"{len(high_overlap)} high-overlap papers, and {recent_velocity:.0%} recent share."
                ),
                evidence_ids,
                "Crowding risk is high unless the hypothesis narrows to a clearer whitespace pocket.",
                confidence_span=max(8, min(22, 24 - len(evidence_ids))),
                method="deterministic:retrieval_density_recent_velocity_v1",
            )
        ],
    }


run = saturation_scorer


def _whitespace_summary(papers: list[Any]) -> str:
    cluster_tokens: list[str] = []
    for paper in papers:
        cluster_tokens.extend(tokens_for_text(paper.cluster))
    if cluster_tokens:
        dominant = ", ".join(dict.fromkeys(cluster_tokens[:4]))
        return f"Likely whitespace is outside the dominant overlap clusters around {dominant}, or in a narrower population/method slice."
    return "Likely whitespace comes from narrowing the claim to a more specific mechanism, population, or measurement context."
