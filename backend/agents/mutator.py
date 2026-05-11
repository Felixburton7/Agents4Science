from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from backend.llm_client import LLMUnavailable, complete_structured
from backend.schemas import ImpactForecast, Variant


DIMENSIONS = ("volume", "velocity", "reach", "depth", "disruption", "translation")


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
    base_scores = _forecast_scores(state.get("forecast"))

    specs = [
        (
            "Generalise",
            f"Test whether {claim} holds across broader datasets, populations, and deployment contexts beyond {population}.",
            "Broadens the addressable audience and citation surface while preserving the core claim.",
            {"volume": 8, "velocity": 2, "reach": 12, "depth": -4, "disruption": 1, "translation": 3},
        ),
        (
            "Narrow",
            f"Test {claim} in a sharply defined high-uncertainty subgroup within {context}.",
            "Reduces crowding and makes the causal or empirical test cleaner.",
            {"volume": -5, "velocity": 2, "reach": -2, "depth": 10, "disruption": 5, "translation": 6},
        ),
        (
            "Substitute",
            f"Keep the same outcome as {claim}, but replace {mechanism} with a competing mechanism that could explain the effect.",
            "Creates a head-to-head mechanism test instead of only elaborating the original story.",
            {"volume": 1, "velocity": -1, "reach": 3, "depth": 6, "disruption": 10, "translation": 1},
        ),
        (
            "Shift scale",
            f"Move the test of {claim} from {method} to a larger-scale, longer-horizon, or more realistic evaluation setting.",
            "Checks whether the hypothesis survives a more consequential scale of evidence.",
            {"volume": 5, "velocity": -3, "reach": 7, "depth": 4, "disruption": 4, "translation": 10},
        ),
        (
            "Cross-pollinate",
            f"Apply evaluation or modelling techniques from an adjacent AI field to test {claim} in {context}.",
            "Imports a less crowded method lens and may expose a wider research audience.",
            {"volume": 7, "velocity": 3, "reach": 14, "depth": 4, "disruption": 9, "translation": 2},
        ),
        (
            "Invert",
            f"Aggressively test the null: identify conditions where {claim} should fail and measure whether {mechanism} is unnecessary.",
            "Turns a positive claim into a falsification-first experiment with high interpretability.",
            {"volume": 0, "velocity": 5, "reach": 0, "depth": 12, "disruption": 7, "translation": 3},
        ),
        (
            "Combine",
            f"Combine {claim} with a neighbouring open question about robustness, generalisation, or resource efficiency.",
            "Fuses the hypothesis with a second bottleneck that could improve strategic value.",
            {"volume": 9, "velocity": -2, "reach": 9, "depth": 5, "disruption": 6, "translation": 5},
        ),
    ]

    return [
        Variant(
            variant_id=f"variant-{idx}",
            hypothesis_text=text,
            operator=operator,
            rationale=rationale,
            impact_scores=_apply_delta(base_scores, delta),
        )
        for idx, (operator, text, rationale, delta) in enumerate(specs, start=1)
    ]


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


def _apply_delta(base_scores: dict[str, int], delta: dict[str, int]) -> dict[str, int]:
    return {
        dimension: max(0, min(100, int(base_scores.get(dimension, 50) + delta.get(dimension, 0))))
        for dimension in DIMENSIONS
    }


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
        for key in ("paper_id", "title", "authors", "year", "abstract", "cluster")
        if payload.get(key) not in (None, "", [], {})
    }


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
