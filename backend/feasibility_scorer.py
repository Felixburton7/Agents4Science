from __future__ import annotations

import json
from typing import Any

from backend.evidence_utils import make_metric, paper_evidence_id, sorted_papers, tokens_for_text
from backend.llm_client import LLMUnavailable, complete_structured
from backend.schemas import MetricScore


METHOD_TERMS = {
    "experiment",
    "assay",
    "trial",
    "cohort",
    "dataset",
    "benchmark",
    "simulation",
    "model",
    "survey",
    "imaging",
    "sequencing",
    "measurement",
    "evaluation",
}


async def feasibility_scorer(state: dict[str, Any]) -> dict[str, list[MetricScore]]:
    system_prompt = (
        "You are the Feasibility Scorer for the quantitative Idea Hater pipeline. "
        "Score whether the parsed hypothesis can realistically be tested from 0 to 100. "
        "Consider data availability, methods, instruments, timescale, dependency risk, and validation burden. "
        "Return MetricScore-compatible data with name='feasibility'."
    )
    user_prompt = json.dumps(_payload(state), indent=2, default=str)

    try:
        metric = await complete_structured(
            "feasibility_scorer",
            system_prompt,
            user_prompt,
            MetricScore,
            temperature=0.1,
        )
        metric = _repair_metric(metric)
    except (LLMUnavailable, ValueError, TypeError, json.JSONDecodeError):
        metric = _heuristic_metric(state)

    return {"metric_scores": [metric]}


run = feasibility_scorer


def _payload(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_hypothesis": state.get("raw_hypothesis", ""),
        "parsed": _dump(state.get("parsed")),
        "nearby_methods_evidence": [_paper_payload(paper) for paper in state.get("papers", [])[:20]],
        "output_contract": "Return one MetricScore with name='feasibility'. Use supplied evidence_ids only.",
    }


def _heuristic_metric(state: dict[str, Any]) -> MetricScore:
    papers = sorted_papers(state)
    parsed = _dump(state.get("parsed"))
    hypothesis_terms = set(tokens_for_text(" ".join(str(parsed.get(key, "")) for key in parsed)))
    evidence = papers[:8]
    evidence_ids = [paper_evidence_id(paper) for paper in evidence[:6]]

    if not papers:
        return make_metric(
            "feasibility",
            38,
            "Feasibility is low-confidence because no real literature methods evidence was retrieved.",
            [],
            "Retrieve a usable paper neighbourhood before claiming the hypothesis is testable.",
            confidence_span=24,
            method="deterministic:no_methods_evidence_v1",
        )

    method_overlap = 0
    data_signals = 0
    for paper in evidence:
        tokens = set(tokens_for_text(f"{paper.title} {paper.abstract}"))
        if tokens & METHOD_TERMS:
            method_overlap += 1
        if hypothesis_terms and len(tokens & hypothesis_terms) >= 3:
            data_signals += 1

    abstract_ratio = sum(1 for paper in papers if paper.abstract.strip()) / len(papers)
    recent_ratio = sum(1 for paper in papers if paper.year and paper.year >= 2019) / len(papers)
    method_ratio = method_overlap / max(1, len(evidence))
    data_ratio = data_signals / max(1, len(evidence))
    score = 35 + (method_ratio * 24) + (data_ratio * 18) + (abstract_ratio * 13) + (recent_ratio * 10)

    blocker = _blocker(method_ratio, data_ratio, abstract_ratio)
    return make_metric(
        "feasibility",
        score,
        (
            f"Feasibility uses real nearby methods evidence: {method_overlap}/{len(evidence)} top papers contain method signals, "
            f"{data_signals}/{len(evidence)} share at least three hypothesis terms, and abstract coverage is {abstract_ratio:.0%}."
        ),
        evidence_ids,
        blocker,
        confidence_span=max(8, round(20 - min(len(evidence), 8))),
        method="deterministic:methods_overlap_and_evidence_availability_v1",
    )


def _repair_metric(metric: MetricScore) -> MetricScore:
    updates: dict[str, Any] = {}
    if metric.name != "feasibility":
        updates["name"] = "feasibility"
    if not metric.method:
        updates["method"] = "llm:structured_feasibility_v1"
    if hasattr(metric, "model_copy"):
        return metric.model_copy(update=updates)
    return metric.copy(update=updates)


def _blocker(method_ratio: float, data_ratio: float, abstract_ratio: float) -> str:
    if method_ratio < 0.25:
        return "Few nearby papers show reusable methods or instruments for testing the claim."
    if data_ratio < 0.25:
        return "Nearby evidence is methodologically relevant but not tightly matched to the hypothesis terms."
    if abstract_ratio < 0.5:
        return "Feasibility confidence is limited because many records lack abstracts."
    return "Main feasibility risk is validating the claim outside the retrieved evidence neighbourhood."


def _paper_payload(paper: Any) -> dict[str, Any]:
    return {
        "evidence_id": paper_evidence_id(paper),
        "title": getattr(paper, "title", ""),
        "year": getattr(paper, "year", None),
        "abstract": getattr(paper, "abstract", ""),
        "relevance_score": getattr(paper, "relevance_score", 0),
    }


def _dump(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return {}