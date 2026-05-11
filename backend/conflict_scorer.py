from __future__ import annotations

from typing import Any

from backend.evidence_utils import make_metric, no_papers_metric, paper_evidence_id, sorted_papers
from backend.schemas import Conflict


CONFLICT_TERMS = {
    "effect_direction": ("contradict", "contradictory", "opposite", "negative effect", "no effect", "null effect"),
    "mechanism": ("inconsistent", "inconsistency", "fails to explain", "alternative mechanism", "not mediated"),
    "population": ("heterogeneous", "subgroup", "boundary condition", "context dependent", "mixed results"),
    "method": ("failed to replicate", "replication", "bias", "confound", "underpowered", "not robust"),
}


async def conflict_scorer(state: dict[str, Any]) -> dict[str, Any]:
    papers = sorted_papers(state)
    if not papers:
        return {"conflicts": [], "metric_scores": [no_papers_metric("conflict_risk")]}

    conflicts: list[Conflict] = []
    for paper in papers[:25]:
        text = f"{paper.title} {paper.abstract}".lower()
        for dimension, terms in CONFLICT_TERMS.items():
            matched = [term for term in terms if term in text]
            if not matched:
                continue
            severity = min(1.0, 0.18 + (paper.relevance_score * 0.55) + min(0.18, len(matched) * 0.06))
            conflicts.append(
                Conflict(
                    paper_id=paper_evidence_id(paper),
                    title=paper.title,
                    disagreement_dimension=dimension,
                    explanation=f"Abstract/title contains conflict signals: {', '.join(matched[:3])}.",
                    severity=round(severity, 3),
                )
            )
            break

    if not conflicts:
        conflicts = _similarity_risks(papers)

    weighted_conflict = sum(conflict.severity for conflict in conflicts)
    high_severity = sum(1 for conflict in conflicts if conflict.severity >= 0.55)
    penalty = min(65, (weighted_conflict * 18) + (high_severity * 6))
    conflict_score = 100 - penalty
    evidence_ids = [conflict.paper_id for conflict in conflicts[:6]]

    return {
        "conflicts": conflicts,
        "metric_scores": [
            make_metric(
                "conflict_risk",
                conflict_score,
                (
                    f"Conflict risk uses abstract/title contradiction scans over real papers: "
                    f"{len(conflicts)} conflicts, {high_severity} high-severity, weighted severity {weighted_conflict:.2f}."
                ),
                evidence_ids,
                "The hypothesis should explicitly handle the strongest disagreement or boundary-condition evidence.",
                confidence_span=10 if conflicts else 18,
                method="heuristic:real_abstract_conflict_scan_v1",
            )
        ],
    }


run = conflict_scorer


def _similarity_risks(papers: list[Any]) -> list[Conflict]:
    risks: list[Conflict] = []
    for paper in papers[:3]:
        if paper.relevance_score < 0.7:
            continue
        risks.append(
            Conflict(
                paper_id=paper_evidence_id(paper),
                title=paper.title,
                disagreement_dimension="positioning",
                explanation="No explicit contradiction was detected, but very close prior work creates positioning risk.",
                severity=0.22,
            )
        )
    return risks
