from __future__ import annotations

from typing import Any

from backend.schemas import Scorecard, Variant


ALL_METRICS = (
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


async def ranker(state: dict[str, Any]) -> dict[str, list[Variant]]:
    variants = list(state.get("pareto_variants") or state.get("rescored_variants") or state.get("variants", []) or [])
    original = _original_variant(state)
    candidates = [original, *variants]
    selected_ids, dominators = _pareto_front(candidates)

    ranked = sorted(
        candidates,
        key=lambda variant: (
            variant.composite_score,
            variant.impact_scores.get("evidence_quality", 0),
            variant.impact_scores.get("feasibility", 0),
            variant.impact_scores.get("novelty", 0),
        ),
        reverse=True,
    )

    updated: list[Variant] = []
    for idx, variant in enumerate(ranked, start=1):
        is_selected = variant.variant_id in selected_ids
        explanation = _dominance_explanation(variant, idx, is_selected, dominators.get(variant.variant_id))
        updated.append(
            _copy_model(
                variant,
                rank=idx,
                is_pareto_selected=is_selected,
                dominance_explanation=explanation,
            )
        )

    generated = [variant for variant in updated if variant.variant_id != "original"]
    return {
        "ranked_variants": updated,
        "variants": generated,
    }


run = ranker


def _original_variant(state: dict[str, Any]) -> Variant:
    scorecard = state.get("scorecard")
    scores = _scorecard_scores(scorecard)
    composite = int(getattr(scorecard, "composite_score", scores.get("composite", 0)) or 0)
    scores["composite"] = composite
    return Variant(
        variant_id="original",
        hypothesis_text=state.get("raw_hypothesis", ""),
        operator="Original",
        rationale="Original submitted hypothesis before mutation.",
        impact_scores=scores,
        composite_score=composite,
        scorecard=scorecard,
    )


def _scorecard_scores(scorecard: Scorecard | Any) -> dict[str, int]:
    metrics = getattr(scorecard, "metric_scores", []) or []
    return {
        _metric_name(metric): int(getattr(metric, "score", 50))
        for metric in metrics
        if _metric_name(metric) in ALL_METRICS
    }


def _pareto_front(candidates: list[Variant]) -> tuple[set[str], dict[str, Variant]]:
    selected: set[str] = set()
    dominators: dict[str, Variant] = {}
    for candidate in candidates:
        dominated_by = None
        candidate_scores = _scores(candidate)
        for challenger in candidates:
            if challenger.variant_id == candidate.variant_id:
                continue
            if _dominates(_scores(challenger), candidate_scores):
                dominated_by = challenger
                break
        if dominated_by is None:
            selected.add(candidate.variant_id)
        else:
            dominators[candidate.variant_id] = dominated_by
    original = next((candidate for candidate in candidates if candidate.variant_id == "original"), None)
    variants = [candidate for candidate in candidates if candidate.variant_id != "original"]
    if original and variants:
        best_variant = max(variants, key=lambda candidate: candidate.composite_score)
        if best_variant.composite_score > original.composite_score:
            selected.discard("original")
            dominators["original"] = best_variant
    return selected, dominators


def _dominates(challenger: dict[str, int], candidate: dict[str, int]) -> bool:
    dimensions = [metric for metric in ALL_METRICS if metric in challenger and metric in candidate]
    if len(dimensions) < 6:
        return False
    challenger_composite = challenger.get("composite", 0)
    candidate_composite = candidate.get("composite", 0)
    return (
        challenger_composite >= candidate_composite
        and all(challenger[metric] >= candidate[metric] for metric in dimensions)
        and (
            challenger_composite > candidate_composite
            or any(challenger[metric] > candidate[metric] for metric in dimensions)
        )
    )


def _scores(variant: Variant) -> dict[str, int]:
    scores = {
        key.lower().replace(" ", "_").replace("-", "_"): int(value)
        for key, value in (variant.impact_scores or {}).items()
    }
    if variant.scorecard:
        scores.update(_scorecard_scores(variant.scorecard))
        scores.setdefault("composite", int(variant.scorecard.composite_score))
    scores.setdefault("composite", int(variant.composite_score))
    return scores


def _dominance_explanation(
    variant: Variant,
    rank: int,
    is_selected: bool,
    dominator: Variant | None,
) -> str:
    if variant.variant_id == "original" and dominator is not None:
        return f"Rank {rank}; original is dominated by {dominator.variant_id} on composite and scorecard trade-offs."
    if is_selected:
        return f"Rank {rank}; Pareto-selected because no candidate dominates its scorecard trade-off."
    if dominator is None:
        return f"Rank {rank}; not Pareto-selected."
    return f"Rank {rank}; dominated by {dominator.variant_id} on the shared scorecard metrics."


def _metric_name(metric: Any) -> str:
    return str(getattr(metric, "metric_name", None) or getattr(metric, "name", "")).lower()


def _copy_model(model: Any, **updates: Any) -> Any:
    if hasattr(model, "model_copy"):
        return model.model_copy(update=updates)
    return model.copy(update=updates)
