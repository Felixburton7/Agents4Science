from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from backend.llm_client import LLMUnavailable, complete_structured
from backend.schemas import ImpactForecast, MetricScore, Variant


DIMENSIONS = ("volume", "velocity", "reach", "depth", "disruption", "translation")
CORE_METRICS = (
    "novelty",
    "saturation",
    "conflict_risk",
    "feasibility",
    "volume",
    "velocity",
    "reach",
    "depth",
    "disruption",
    "translation",
    "evidence_quality",
)
WEAK_SCORE_THRESHOLD = 58


class MutationResponse(BaseModel):
    variants: list[Variant] = Field(min_length=5, max_length=7)


async def mutator(state: dict[str, Any]) -> dict[str, list[Variant]]:
    raw_hypothesis = state.get("raw_hypothesis", "")
    system_prompt = (
        "You are the Mutator agent for the Hypothesis Steering Engine. "
        "You MUST generate 5 to 7 testable variants, each tagged with exactly "
        "one mutation operator from: Generalise, Narrow, Substitute, Shift scale, "
        "Cross-pollinate, Invert, Combine. DO NOT write full abstracts."
    )
    user_prompt = json.dumps(_mutation_payload(state), indent=2, default=str)

    try:
        response = await complete_structured(
            "mutator",
            system_prompt,
            user_prompt,
            MutationResponse,
            temperature=0.55,
        )
        variants = [_repair_variant(idx, variant) for idx, variant in enumerate(response.variants, start=1)]
    except (LLMUnavailable, ValueError, TypeError):
        variants = _heuristic_variants(raw_hypothesis, state)

    return {"variants": variants}


run = mutator


def _mutation_payload(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_hypothesis": state.get("raw_hypothesis", ""),
        "parsed": _dump(state.get("parsed")),
        "scorecard": _scorecard_payload(state),
        "weak_metrics": _weak_metrics(state),
        "literature_context": [_compact_paper(paper) for paper in state.get("papers", [])[:20]],
        "overlap_report": _dump(state.get("overlaps")),
        "conflicts": [_dump(conflict) for conflict in state.get("conflicts", [])[:8]],
        "impact_forecast": _dump(state.get("forecast")),
        "operators": {
            "Generalise": "broaden population or setting",
            "Narrow": "focus context or subgroup",
            "Substitute": "different mechanism, same outcome",
            "Shift scale": "move between acute/chronic, in vitro/in vivo, or small/large scale",
            "Cross-pollinate": "apply a method from an adjacent field",
            "Invert": "test the null or opposite claim aggressively",
            "Combine": "fuse with an adjacent open question",
        },
        "output_contract": "Return MutationResponse with 5 to 7 Variant objects.",
    }


def _heuristic_variants(raw_hypothesis: str, state: dict[str, Any]) -> list[Variant]:
    parsed = _dump(state.get("parsed"))
    claim = parsed.get("claim") or raw_hypothesis or "the proposed hypothesis"
    mechanism = parsed.get("mechanism") or "the proposed mechanism"
    context = parsed.get("context") or "the target research setting"
    population = parsed.get("population") or "the target population"
    method = parsed.get("method") or "the proposed method"
    base_scores = _scorecard_scores(state)
    weak_metrics = _weak_metrics(state)
    specs = _ordered_specs(
        [
            {
                "operator": "Generalise",
                "text": (
                    f"Test whether {claim} generalises across broader datasets, populations, and deployment contexts "
                    f"beyond {population}."
                ),
                "rationale": "Targets weak volume or reach by widening the addressable evidence and audience.",
                "targets": ("volume", "reach", "velocity"),
                "delta": {"volume": 8, "velocity": 3, "reach": 10, "depth": -4, "saturation": -6, "evidence_quality": -2},
            },
            {
                "operator": "Narrow",
                "text": f"Test {claim} in a sharply defined high-uncertainty subgroup within {context}.",
                "rationale": "Targets high saturation or low feasibility by making the claim cleaner and less crowded.",
                "targets": ("saturation", "feasibility", "depth"),
                "delta": {"volume": -5, "reach": -2, "saturation": 12, "feasibility": 7, "depth": 7, "translation": 3},
            },
            {
                "operator": "Substitute",
                "text": (
                    f"Keep the same outcome as {claim}, but replace {mechanism} with a competing mechanism that could "
                    "explain the effect."
                ),
                "rationale": "Targets low novelty and conflict risk through a head-to-head mechanism test.",
                "targets": ("novelty", "conflict_risk", "disruption"),
                "delta": {"novelty": 10, "conflict_risk": 9, "depth": 5, "disruption": 9, "feasibility": -3},
            },
            {
                "operator": "Shift scale",
                "text": (
                    f"Move the test of {claim} from {method} to a larger-scale, longer-horizon, or more realistic "
                    "evaluation setting."
                ),
                "rationale": "Targets saturation and translation by changing the scale at which the evidence is measured.",
                "targets": ("saturation", "translation", "reach"),
                "delta": {"volume": 5, "velocity": -3, "reach": 6, "saturation": 8, "depth": 4, "translation": 12},
            },
            {
                "operator": "Cross-pollinate",
                "text": f"Apply evaluation or modelling techniques from an adjacent field to test {claim} in {context}.",
                "rationale": "Targets low novelty by importing a less crowded method lens and widening field reach.",
                "targets": ("novelty", "reach", "disruption"),
                "delta": {"novelty": 13, "velocity": 3, "reach": 14, "depth": 4, "disruption": 10, "feasibility": -4},
            },
            {
                "operator": "Invert",
                "text": (
                    f"Aggressively test the null: identify conditions where {claim} should fail and measure whether "
                    f"{mechanism} is unnecessary."
                ),
                "rationale": "Targets conflict risk by turning disagreement into an explicit boundary-condition test.",
                "targets": ("conflict_risk", "depth", "feasibility"),
                "delta": {"volume": -2, "velocity": 4, "conflict_risk": 14, "feasibility": 5, "depth": 10, "disruption": 7},
            },
            {
                "operator": "Combine",
                "text": f"Combine {claim} with a neighbouring open question about robustness, generalisation, or deployment.",
                "rationale": "Targets low translation or depth by pairing the claim with a second strategic bottleneck.",
                "targets": ("translation", "depth", "evidence_quality"),
                "delta": {"volume": 7, "reach": 7, "depth": 7, "translation": 11, "evidence_quality": 5, "feasibility": -4},
            },
        ],
        weak_metrics,
    )

    return [
        Variant(
            variant_id=f"variant-{idx}",
            hypothesis_text=spec["text"],
            operator=spec["operator"],
            rationale=_targeted_rationale(spec["rationale"], spec["targets"], weak_metrics),
            impact_scores=_apply_delta(base_scores, spec["delta"], spec["targets"], weak_metrics),
        )
        for idx, spec in enumerate(specs, start=1)
    ]


def _scorecard_payload(state: dict[str, Any]) -> dict[str, Any]:
    scorecard = _dump(state.get("scorecard"))
    metrics = _metric_payloads(state)
    return {
        "composite_score": scorecard.get("composite_score"),
        "verdict": scorecard.get("verdict"),
        "metrics": metrics,
        "weaknesses": scorecard.get("weaknesses", []),
        "strengths": scorecard.get("strengths", []),
    }


def _metric_payloads(state: dict[str, Any]) -> list[dict[str, Any]]:
    scorecard = state.get("scorecard")
    metrics = getattr(scorecard, "metric_scores", None) or state.get("metric_scores", [])
    return [
        {
            "name": _metric_name(metric),
            "score": int(getattr(metric, "score", 50)),
            "confidence_low": getattr(metric, "confidence_low", None),
            "confidence_high": getattr(metric, "confidence_high", None),
            "weakness": getattr(metric, "weakness", ""),
            "evidence_ids": list(getattr(metric, "evidence_ids", []) or getattr(metric, "evidence", []) or []),
            "method": getattr(metric, "method", ""),
        }
        for metric in metrics
    ]


def _scorecard_scores(state: dict[str, Any]) -> dict[str, int]:
    scores = _forecast_scores(state.get("forecast"))
    for metric in _metric_payloads(state):
        name = metric["name"]
        if name:
            scores[name] = int(metric["score"])
    return {metric: int(scores.get(metric, 50)) for metric in CORE_METRICS}


def _weak_metrics(state: dict[str, Any]) -> list[str]:
    metrics = _metric_payloads(state)
    weak = [
        metric["name"]
        for metric in sorted(metrics, key=lambda item: item["score"])
        if metric["name"] and metric["score"] < WEAK_SCORE_THRESHOLD
    ]
    if weak:
        return weak[:6]
    scores = _scorecard_scores(state)
    return [name for name, _score in sorted(scores.items(), key=lambda item: item[1])[:4]]


def _ordered_specs(specs: list[dict[str, Any]], weak_metrics: list[str]) -> list[dict[str, Any]]:
    weak_set = set(weak_metrics)
    priority = {metric: len(weak_metrics) - idx for idx, metric in enumerate(weak_metrics)}
    return sorted(
        specs,
        key=lambda spec: (
            len(weak_set.intersection(spec["targets"])),
            sum(priority.get(metric, 0) for metric in spec["targets"]),
        ),
        reverse=True,
    )


def _targeted_rationale(rationale: str, targets: tuple[str, ...], weak_metrics: list[str]) -> str:
    matched = [metric for metric in weak_metrics if metric in targets]
    if not matched:
        return rationale
    return f"{rationale} It directly repairs weak scorecard metrics: {', '.join(matched)}."


def _forecast_scores(forecast: Any) -> dict[str, int]:
    payload = _dump(forecast)
    scores: dict[str, int] = {}
    for dimension in DIMENSIONS:
        value = payload.get(dimension, {})
        if isinstance(value, dict):
            scores[dimension] = int(value.get("score", 50))
        else:
            scores[dimension] = int(getattr(value, "score", 50))
    return scores or {dimension: 50 for dimension in DIMENSIONS}


def _apply_delta(
    base_scores: dict[str, int],
    delta: dict[str, int],
    targets: tuple[str, ...] = (),
    weak_metrics: list[str] | None = None,
) -> dict[str, int]:
    weak_set = set(weak_metrics or [])
    scores = {}
    for metric in CORE_METRICS:
        targeted_bonus = 4 if metric in targets and metric in weak_set else 0
        scores[metric] = max(0, min(100, int(base_scores.get(metric, 50) + delta.get(metric, 0) + targeted_bonus)))
    return scores


def _repair_variant(index: int, variant: Variant) -> Variant:
    updates: dict[str, Any] = {}
    if not variant.variant_id:
        updates["variant_id"] = f"variant-{index}"
    if variant.operator == "Substitute mechanism":
        updates["operator"] = "Substitute"
    if variant.impact_forecast and not variant.impact_scores:
        updates["impact_scores"] = _forecast_scores(variant.impact_forecast)
    if hasattr(variant, "model_copy"):
        return variant.model_copy(update=updates)
    return variant.copy(update=updates)


def _compact_paper(paper: Any) -> dict[str, Any]:
    payload = _dump(paper)
    return {
        key: payload.get(key)
        for key in ("paper_id", "title", "authors", "year", "abstract", "cluster", "relevance_score", "citation_count")
        if payload.get(key) not in (None, "", [], {})
    }


def _metric_name(metric: MetricScore | Any) -> str:
    return str(getattr(metric, "metric_name", None) or getattr(metric, "name", "")).lower()


def _dump(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return {
        key: getattr(value, key)
        for key in dir(value)
        if not key.startswith("_") and not callable(getattr(value, key))
    }
