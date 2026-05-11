from __future__ import annotations

import json
from typing import Any

from backend.llm_client import LLMUnavailable, complete_structured
from backend.schemas import StrategyMemo, Variant


async def strategist(state: dict[str, Any]) -> dict[str, StrategyMemo]:
    system_prompt = (
        "You are the Strategist agent for the Hypothesis Steering Engine. "
        "Make one clear decision-oriented recommendation from the scorecard, evidence, variants, and Pareto status. "
        "Do not recommend a dominated variant unless you state the strategic reason. Keep uncertainty visible."
    )
    user_prompt = json.dumps(_payload(state), indent=2, default=str)

    try:
        memo = await complete_structured("strategist", system_prompt, user_prompt, StrategyMemo, temperature=0.2)
        memo = _repair_memo(memo, state)
    except (LLMUnavailable, ValueError, TypeError, json.JSONDecodeError):
        memo = _deterministic_memo(state)

    return {"final_memo": memo}


run = strategist


def _payload(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_hypothesis": state.get("raw_hypothesis", ""),
        "parsed": _dump(state.get("parsed")),
        "scorecard": _dump(state.get("scorecard")),
        "ranked_variants": [_variant_payload(variant) for variant in state.get("ranked_variants", [])[:8]],
        "conflicts": [_dump(conflict) for conflict in state.get("conflicts", [])[:8]],
        "overlap_report": _dump(state.get("overlaps")),
        "evidence_ids": _evidence_ids(state),
        "output_contract": "Return a StrategyMemo object with a clear recommendation, risks, next_steps, and evidence_trail.",
    }


def _deterministic_memo(state: dict[str, Any]) -> StrategyMemo:
    scorecard = state.get("scorecard")
    ranked = list(state.get("ranked_variants", []) or [])
    best = ranked[0] if ranked else None
    original_score = int(getattr(scorecard, "composite_score", 0) or 0)
    best_score = int(getattr(best, "composite_score", original_score) or original_score) if best else original_score
    recommendation = _recommendation(best, original_score, best_score)

    return StrategyMemo(
        recommendation=recommendation,
        recommended_hypothesis_text=getattr(best, "hypothesis_text", "") if best else state.get("raw_hypothesis", ""),
        recommended_variant_id=None if not best or best.variant_id == "original" else best.variant_id,
        original_verdict=getattr(scorecard, "verdict", None),
        recommended_verdict=getattr(getattr(best, "scorecard", None), "verdict", None),
        executive_summary=(
            f"The production pipeline parsed the hypothesis, retrieved {len(state.get('papers', []) or [])} papers, "
            f"aggregated {len(getattr(scorecard, 'metric_scores', []) or [])} metrics, and ranked "
            f"{len(ranked)} candidates. The top candidate scores {best_score}/100."
        ),
        scorecard_summary=_scorecard_summary(scorecard),
        key_findings=_key_findings(state, best),
        selected_variants=_selected_variants(ranked),
        trade_offs=[variant.dominance_explanation for variant in ranked[:5] if variant.dominance_explanation],
        evidence_trail=_evidence_ids(state)[:12],
        risks=list(getattr(scorecard, "weaknesses", []) or [])[:5],
        next_steps=_next_steps(scorecard, best),
        denario_next_actions=[
            "Use the recommended hypothesis text as the next Denario drafting input.",
            "Carry forward the listed weak metrics as constraints for the next generation pass.",
        ],
    )


def _repair_memo(memo: StrategyMemo, state: dict[str, Any]) -> StrategyMemo:
    updates: dict[str, Any] = {}
    if not memo.evidence_trail:
        updates["evidence_trail"] = _evidence_ids(state)[:12]
    if not memo.recommended_hypothesis_text:
        ranked = list(state.get("ranked_variants", []) or [])
        updates["recommended_hypothesis_text"] = ranked[0].hypothesis_text if ranked else state.get("raw_hypothesis", "")
    if hasattr(memo, "model_copy"):
        return memo.model_copy(update=updates)
    return memo.copy(update=updates)


def _recommendation(best: Variant | None, original_score: int, best_score: int) -> str:
    if best is None:
        return "Delay development until variants can be generated and ranked."
    if best.variant_id == "original" or best_score <= original_score:
        return "Proceed cautiously with the original hypothesis, focusing first on the weakest scorecard metrics."
    return f"Develop {best.variant_id} ({best.operator}); it improves the composite score by {best_score - original_score} points."


def _scorecard_summary(scorecard: Any) -> list[str]:
    metrics = list(getattr(scorecard, "metric_scores", []) or [])
    return [f"{metric.name}: {metric.score} ({metric.confidence_low}-{metric.confidence_high})" for metric in metrics]


def _key_findings(state: dict[str, Any], best: Variant | None) -> list[str]:
    parsed = _dump(state.get("parsed"))
    findings = [
        f"Parsed claim: {parsed.get('claim', 'unspecified')}",
        f"Literature retrieval returned {len(state.get('papers', []) or [])} records.",
        f"Generated {len(state.get('variants', []) or [])} variants and re-scored {len(state.get('rescored_variants', []) or [])} variants.",
    ]
    if best:
        findings.append(f"Top ranked candidate: {best.variant_id} with composite score {best.composite_score}.")
    return findings


def _selected_variants(ranked: list[Variant]) -> list[str]:
    return [
        f"#{variant.rank}: {variant.variant_id} ({variant.operator}) - score {variant.composite_score}"
        for variant in ranked
        if variant.is_pareto_selected
    ]


def _next_steps(scorecard: Any, best: Variant | None) -> list[str]:
    weak_metrics = [metric.name for metric in getattr(scorecard, "metric_scores", []) or [] if metric.score < 58]
    steps = ["Validate the top-ranked hypothesis against the cited evidence before drafting."]
    if weak_metrics:
        steps.append(f"Repair or bound the weakest metrics first: {', '.join(weak_metrics[:4])}.")
    if best and best.variant_id != "original":
        steps.append(f"Run a fresh retrieval pass for {best.variant_id} before treating the improvement as final.")
    return steps


def _evidence_ids(state: dict[str, Any]) -> list[str]:
    scorecard = state.get("scorecard")
    ids = {
        evidence_id
        for metric in getattr(scorecard, "metric_scores", []) or []
        for evidence_id in getattr(metric, "evidence_ids", [])
    }
    return sorted(ids)


def _variant_payload(variant: Variant) -> dict[str, Any]:
    return {
        "variant_id": variant.variant_id,
        "rank": variant.rank,
        "operator": variant.operator,
        "hypothesis_text": variant.hypothesis_text,
        "composite_score": variant.composite_score,
        "is_pareto_selected": variant.is_pareto_selected,
        "dominance_explanation": variant.dominance_explanation,
    }


def _dump(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return {}