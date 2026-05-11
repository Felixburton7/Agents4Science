from __future__ import annotations

import json
from statistics import median
from typing import Any

from pydantic import BaseModel, Field

from backend.llm_client import LLMUnavailable, complete_structured
from backend.schemas import Variant


DIMENSIONS = (
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


class ParetoExplanation(BaseModel):
    variant_id: str
    explanation: str


class ParetoExplanationResponse(BaseModel):
    explanations: list[ParetoExplanation] = Field(default_factory=list)


async def pareto_curator(state: dict[str, Any]) -> dict[str, list[Variant]]:
    variants = list(state.get("rescored_variants") or state.get("variants", []) or [])
    selected_ids, dominators = _pareto_front(variants)

    selected_explanations = _fallback_selected_explanations(variants, selected_ids)
    if selected_ids:
        try:
            selected_explanations.update(await _llm_selected_explanations(variants, selected_ids))
        except (LLMUnavailable, ValueError, TypeError):
            pass

    updated: list[Variant] = []
    for variant in variants:
        scores = _scores(variant)
        is_selected = variant.variant_id in selected_ids
        if is_selected:
            explanation = selected_explanations.get(
                variant.variant_id,
                "Pareto-selected: no other variant is at least as strong across every available scorecard metric.",
            )
        else:
            dominator = dominators.get(variant.variant_id)
            explanation = _dominated_explanation(variant, dominator) if dominator else _missing_scores_explanation(scores)
        updated.append(_copy_model(variant, is_pareto_selected=is_selected, dominance_explanation=explanation))

    return {"pareto_variants": updated, "variants": updated}


run = pareto_curator


def _pareto_front(variants: list[Variant]) -> tuple[set[str], dict[str, Variant]]:
    selected: set[str] = set()
    dominators: dict[str, Variant] = {}
    for candidate in variants:
        candidate_scores = _scores(candidate)
        if not candidate_scores:
            dominators[candidate.variant_id] = candidate
            continue

        dominated_by: Variant | None = None
        for challenger in variants:
            if challenger.variant_id == candidate.variant_id:
                continue
            if _dominates(_scores(challenger), candidate_scores):
                dominated_by = challenger
                break

        if dominated_by is None:
            selected.add(candidate.variant_id)
        else:
            dominators[candidate.variant_id] = dominated_by
    return selected, dominators


def _dominates(challenger: dict[str, int], candidate: dict[str, int]) -> bool:
    dimensions = [dimension for dimension in DIMENSIONS if dimension in challenger and dimension in candidate]
    if len(dimensions) < 6:
        return False
    return all(challenger[dimension] >= candidate[dimension] for dimension in dimensions) and any(
        challenger[dimension] > candidate[dimension] for dimension in dimensions
    )


async def _llm_selected_explanations(variants: list[Variant], selected_ids: set[str]) -> dict[str, str]:
    payload = {
        "task": "For each Pareto-selected variant, write one sentence explaining why it is non-dominated across the scorecard and what it trades off.",
        "selected_variants": [
            {
                "variant_id": variant.variant_id,
                "operator": variant.operator,
                "hypothesis_text": variant.hypothesis_text,
                "scorecard_scores": _scores(variant),
            }
            for variant in variants
            if variant.variant_id in selected_ids
        ],
        "all_scores": [
            {"variant_id": variant.variant_id, "operator": variant.operator, "scorecard_scores": _scores(variant)}
            for variant in variants
        ],
    }
    response = await complete_structured(
        "pareto_curator",
        "You are the Pareto Curator. You MUST explain only non-dominated scorecard variants in one sentence each.",
        json.dumps(payload, indent=2),
        ParetoExplanationResponse,
        temperature=0.1,
    )
    return {item.variant_id: item.explanation for item in response.explanations}


def _fallback_selected_explanations(variants: list[Variant], selected_ids: set[str]) -> dict[str, str]:
    medians = _dimension_medians(variants)
    explanations: dict[str, str] = {}
    for variant in variants:
        if variant.variant_id not in selected_ids:
            continue
        scores = _scores(variant)
        strengths = sorted(scores, key=lambda dim: scores[dim], reverse=True)[:2]
        tradeoffs = [dim for dim in DIMENSIONS if dim in scores and scores[dim] < medians.get(dim, 0)]
        strength_text = " and ".join(strengths) if strengths else "its strongest dimensions"
        tradeoff_text = f" while trading off {tradeoffs[0]}" if tradeoffs else " without a clear below-median trade-off"
        explanations[variant.variant_id] = (
            f"Pareto-selected: it remains non-dominated through stronger {strength_text}{tradeoff_text}."
        )
    return explanations


def _dominated_explanation(variant: Variant, dominator: Variant | None) -> str:
    if dominator is None or dominator.variant_id == variant.variant_id:
        return "Not selected: no usable impact scores were available for dominance comparison."
    left = _scores(dominator)
    right = _scores(variant)
    better = [dimension for dimension in DIMENSIONS if dimension in left and dimension in right and left[dimension] > right[dimension]]
    equal = [dimension for dimension in DIMENSIONS if dimension in left and dimension in right and left[dimension] == right[dimension]]
    better_text = ", ".join(better[:3]) if better else "at least one dimension"
    equal_text = f" and matches on {', '.join(equal[:2])}" if equal else ""
    return f"Dominated by {dominator.variant_id}: it is stronger on {better_text}{equal_text}."


def _missing_scores_explanation(scores: dict[str, int]) -> str:
    if scores:
        return "Not selected: available scores were insufficient for a full scorecard Pareto comparison."
    return "Not selected: no usable impact scores were available."


def _scores(variant: Variant) -> dict[str, int]:
    scores = {
        key.lower().replace(" ", "_").replace("-", "_"): int(value)
        for key, value in (variant.impact_scores or {}).items()
        if key.lower().replace(" ", "_").replace("-", "_") in DIMENSIONS
    }
    if variant.scorecard:
        for metric in variant.scorecard.metric_scores:
            metric_name = str(getattr(metric, "metric_name", None) or getattr(metric, "name", "")).lower()
            if metric_name in DIMENSIONS:
                scores[metric_name] = int(metric.score)
    if scores:
        return scores
    if variant.impact_forecast:
        forecast = variant.impact_forecast
        return {
            dimension: int(getattr(forecast, dimension).score)
            for dimension in ("volume", "velocity", "reach", "depth", "disruption", "translation")
        }
    return {}


def _dimension_medians(variants: list[Variant]) -> dict[str, float]:
    medians: dict[str, float] = {}
    for dimension in DIMENSIONS:
        values = [_scores(variant)[dimension] for variant in variants if dimension in _scores(variant)]
        if values:
            medians[dimension] = float(median(values))
    return medians


def _copy_model(model: Any, **updates: Any) -> Any:
    if hasattr(model, "model_copy"):
        return model.model_copy(update=updates)
    return model.copy(update=updates)
