from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from backend.evidence_utils import make_metric, no_papers_metric, paper_evidence_id, sorted_papers
from backend.llm_client import LLMUnavailable, complete_structured
from backend.schemas import Conflict


CONFLICT_TERMS = {
    "effect_direction": ("contradict", "contradictory", "opposite", "negative effect", "no effect", "null effect"),
    "mechanism": ("inconsistent", "inconsistency", "fails to explain", "alternative mechanism", "not mediated"),
    "population": ("heterogeneous", "subgroup", "boundary condition", "context dependent", "mixed results"),
    "method": ("failed to replicate", "replication", "bias", "confound", "underpowered", "not robust"),
}

_SYSTEM_PROMPT = (
    "You are the Conflict Scorer for a scientific hypothesis evaluation system. "
    "Given a hypothesis and a paper title + abstract, classify the paper's stance. "
    "Be precise: only mark 'contradiction' when the paper's findings directly oppose the hypothesis claim."
)


class _PaperStance(BaseModel):
    stance: Literal["support", "contradiction", "unclear"]
    disagreement_dimension: Literal["effect_direction", "mechanism", "population", "method", "none"]
    explanation: str
    severity: float


class _StanceBatch(BaseModel):
    assessments: list[_PaperStance]


async def conflict_scorer(state: dict[str, Any]) -> dict[str, Any]:
    papers = sorted_papers(state)
    if not papers:
        return {"conflicts": [], "metric_scores": [no_papers_metric("conflict_risk")]}

    # Keyword pre-filter over all top-25 papers (fast, no LLM cost)
    keyword_conflicts: list[Conflict] = _keyword_scan(papers[:25])

    # LLM classification over the 6 highest-relevance papers
    llm_conflicts = await _llm_classify(state, papers[:6])
    conflicts = _merge_conflicts(llm_conflicts, keyword_conflicts) if llm_conflicts else keyword_conflicts

    if not conflicts:
        conflicts = _similarity_risks(papers)

    weighted_conflict = sum(conflict.severity for conflict in conflicts)
    high_severity = sum(1 for conflict in conflicts if conflict.severity >= 0.55)
    penalty = min(65, (weighted_conflict * 18) + (high_severity * 6))
    conflict_score = 100 - penalty
    evidence_ids = [conflict.paper_id for conflict in conflicts[:6]]
    method = "hybrid:llm_classification+keyword_scan_v2" if llm_conflicts else "heuristic:real_abstract_conflict_scan_v1"

    return {
        "conflicts": conflicts,
        "metric_scores": [
            make_metric(
                "conflict_risk",
                conflict_score,
                (
                    f"Conflict risk uses {'LLM abstract classification + ' if llm_conflicts else ''}keyword scans "
                    f"over real papers: {len(conflicts)} conflicts, {high_severity} high-severity, "
                    f"weighted severity {weighted_conflict:.2f}."
                ),
                evidence_ids,
                "The hypothesis should explicitly handle the strongest disagreement or boundary-condition evidence.",
                confidence_span=8 if llm_conflicts else (10 if conflicts else 18),
                method=method,
            )
        ],
    }


run = conflict_scorer


async def _llm_classify(state: dict[str, Any], papers: list[Any]) -> list[Conflict]:
    if not papers:
        return []
    hypothesis = state.get("raw_hypothesis", "") or ""
    paper_snippets = []
    for paper in papers:
        abstract_preview = (paper.abstract or "")[:400]
        paper_snippets.append(
            f"Paper ID: {paper_evidence_id(paper)}\nTitle: {paper.title}\nAbstract: {abstract_preview}"
        )
    user_prompt = (
        f"Hypothesis: {hypothesis}\n\n"
        f"Classify each paper's stance toward this hypothesis.\n\n"
        + "\n\n---\n\n".join(paper_snippets)
    )
    try:
        batch = await complete_structured(
            "conflict_scorer",
            _SYSTEM_PROMPT,
            user_prompt,
            _StanceBatch,
            temperature=0.1,
        )
    except (LLMUnavailable, ValueError, TypeError):
        return []

    conflicts: list[Conflict] = []
    for assessment, paper in zip(batch.assessments, papers):
        if assessment.stance != "contradiction":
            continue
        dimension = assessment.disagreement_dimension if assessment.disagreement_dimension != "none" else "effect_direction"
        severity = min(1.0, max(0.0, float(assessment.severity)) * 0.5 + paper.relevance_score * 0.5)
        conflicts.append(
            Conflict(
                paper_id=paper_evidence_id(paper),
                title=paper.title,
                disagreement_dimension=dimension,
                explanation=assessment.explanation[:300],
                severity=round(severity, 3),
            )
        )
    return conflicts


def _keyword_scan(papers: list[Any]) -> list[Conflict]:
    conflicts: list[Conflict] = []
    for paper in papers:
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
    return conflicts


def _merge_conflicts(llm_conflicts: list[Conflict], keyword_conflicts: list[Conflict]) -> list[Conflict]:
    """Prefer LLM classifications; supplement with keyword hits not already covered."""
    llm_ids = {c.paper_id for c in llm_conflicts}
    extras = [c for c in keyword_conflicts if c.paper_id not in llm_ids]
    return llm_conflicts + extras


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
