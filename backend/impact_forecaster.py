from __future__ import annotations

import json
import math
from typing import Any, Callable

from pydantic import BaseModel

from backend.llm_client import LLMUnavailable, complete_structured
from backend.schemas import ImpactDimension, ImpactForecast


DIMENSIONS = ("volume", "velocity", "reach", "depth", "disruption", "translation")


async def impact_forecaster(state: dict[str, Any]) -> dict[str, ImpactForecast]:
    """Forecast six-dimensional hypothesis impact.

    In production this uses the routed gpt-5-mini structured-output call. In
    local environments without OpenAI credentials it falls back to a deterministic
    bibliometric/text heuristic, which keeps the demo and backtest runnable.
    """

    cutoff_year = state.get("information_cutoff_year") or state.get("cutoff_year")
    system_prompt = (
        "You are the Impact Forecaster agent for the Hypothesis Steering Engine. "
        "You MUST predict all six impact dimensions with calibrated confidence "
        "intervals and concise evidence-based rationales. DO NOT use information "
        "after the provided cutoff year."
    )
    user_prompt = json.dumps(_forecast_payload(state, cutoff_year), indent=2, default=str)

    try:
        forecast = await complete_structured(
            "impact_forecaster",
            system_prompt,
            user_prompt,
            ImpactForecast,
            temperature=0.15,
        )
        forecast = _repair_forecast(forecast)
    except (LLMUnavailable, ValueError, TypeError):
        forecast = _heuristic_forecast(state, cutoff_year)

    return {"forecast": forecast}


run = impact_forecaster


def _forecast_payload(state: dict[str, Any], cutoff_year: int | None) -> dict[str, Any]:
    return {
        "raw_hypothesis": state.get("raw_hypothesis", ""),
        "parsed": _dump(state.get("parsed")),
        "information_cutoff_year": cutoff_year,
        "date_filtering_rule": (
            f"Only use evidence available through {cutoff_year}."
            if cutoff_year
            else "No historical cutoff provided; use the supplied context only."
        ),
        "literature_context": [
            _paper_for_prompt(paper, cutoff_year) for paper in state.get("papers", [])[:30]
        ],
        "conflicts": [_dump(conflict) for conflict in state.get("conflicts", [])[:10]],
        "overlap_report": _dump(state.get("overlaps")),
        "audience_signals": [_dump(output) for output in state.get("emulator_outputs", [])[:12]],
        "scenarios": [_dump(scenario) for scenario in state.get("scenarios", [])[:4]],
        "required_dimensions": {
            "volume": "total citations at 5 years",
            "velocity": "citations in first 24 months",
            "reach": "distinct OpenAlex concepts citing it",
            "depth": "foundational value proxy",
            "disruption": "CD-index style displacement proxy",
            "translation": "citations from clinical, patent, policy, or deployment contexts",
        },
        "output_contract": "Return an ImpactForecast object. Each dimension MUST include score, confidence_low, confidence_high, rationale, predicted_value, predicted_low, predicted_high, and units.",
    }


def _paper_for_prompt(paper: Any, cutoff_year: int | None) -> dict[str, Any]:
    payload = _dump(paper)
    if cutoff_year:
        year = payload.get("year")
        if year and year > cutoff_year:
            return {}
        payload.pop("citation_count", None)
        payload.pop("counts_by_year", None)
        payload["date_filter_note"] = f"citation and post-{cutoff_year} fields removed"
    return {
        key: payload.get(key)
        for key in (
            "paper_id",
            "title",
            "authors",
            "year",
            "abstract",
            "url",
            "relevance_score",
            "cluster",
            "venue",
            "concepts",
            "publication_date",
            "date_filter_note",
        )
        if payload.get(key) not in (None, "", [], {})
    }


def _heuristic_forecast(state: dict[str, Any], cutoff_year: int | None) -> ImpactForecast:
    parsed = _dump(state.get("parsed"))
    metadata = state.get("backtest_metadata") or {}
    text_parts = [
        state.get("raw_hypothesis", ""),
        parsed.get("claim", ""),
        parsed.get("mechanism", ""),
        parsed.get("context", ""),
        parsed.get("population", ""),
        parsed.get("method", ""),
        metadata.get("title", ""),
        metadata.get("abstract", ""),
        metadata.get("venue", ""),
        " ".join(metadata.get("concepts", []) if isinstance(metadata.get("concepts"), list) else []),
    ]
    text = " ".join(str(part) for part in text_parts if part).lower()
    abstract_len = len((metadata.get("abstract") or "").split())
    venue_bonus = _venue_bonus(metadata.get("venue", ""))
    author_bonus = min(8, len(metadata.get("authors", []) or []) // 2)
    evidence_bonus = min(10, abstract_len / 35)
    crowding = _crowding_penalty(state)
    interest = _audience_interest(state)

    volume = _clamp(
        34
        + venue_bonus
        + author_bonus
        + evidence_bonus
        + _keyword_score(text, VOLUME_KEYWORDS)
        + interest * 0.10
        - crowding * 0.10
    )
    velocity = _clamp(
        volume * 0.78
        + _keyword_score(text, VELOCITY_KEYWORDS)
        + venue_bonus * 0.35
        + interest * 0.08
    )
    reach = _clamp(
        30
        + min(22, _concept_count(state, metadata) * 3.5)
        + _keyword_score(text, REACH_KEYWORDS)
        + interest * 0.07
    )
    depth = _clamp(
        32
        + venue_bonus * 0.45
        + _keyword_score(text, DEPTH_KEYWORDS)
        + min(12, abstract_len / 45)
        - crowding * 0.05
    )
    disruption = _clamp(
        34
        + _keyword_score(text, DISRUPTION_KEYWORDS)
        + max(0, 12 - crowding * 0.18)
        + _conflict_bonus(state)
    )
    translation = _clamp(
        22
        + _keyword_score(text, TRANSLATION_KEYWORDS)
        + _keyword_score(text, MATERIALS_KEYWORDS) * 0.8
        + interest * 0.04
    )

    uncertainty = _uncertainty_width(abstract_len, bool(metadata.get("venue")), cutoff_year)
    note = "historical cutoff applied" if cutoff_year else "live-context heuristic"

    return ImpactForecast(
        volume=_dimension(
            volume,
            uncertainty,
            "5-year citations",
            _citations_from_score,
            f"Estimated from venue signal, abstract specificity, AI-topic momentum, and {note}.",
        ),
        velocity=_dimension(
            velocity,
            uncertainty,
            "citations in first 24 months",
            lambda score: _citations_from_score(score) * 0.42,
            "Fast-recognition estimate based on benchmark/model keywords and publication venue.",
        ),
        reach=_dimension(
            reach,
            uncertainty,
            "distinct OpenAlex concepts",
            lambda score: max(1.0, score / 3.2),
            "Cross-field spread estimate based on concept diversity and adjacent-domain language.",
        ),
        depth=_dimension(
            depth,
            uncertainty,
            "depth proxy",
            lambda score: score,
            "Foundational-value estimate based on theory, benchmark, review, and method signals.",
        ),
        disruption=_dimension(
            disruption,
            uncertainty,
            "CD-index proxy",
            lambda score: (score / 50.0) - 1.0,
            "Displacement estimate based on novelty, substitution, and conflict signals.",
        ),
        translation=_dimension(
            translation,
            uncertainty,
            "translation citations/proxy",
            lambda score: max(0.0, _citations_from_score(score) * 0.06),
            "Real-world uptake estimate based on clinical, policy, patent, deployment, and materials cues.",
        ),
        overall_summary=(
            "Deterministic fallback forecast produced because the routed OpenAI "
            "structured-output client is unavailable in this environment."
        ),
    )


def _dimension(
    score: float,
    width: int,
    units: str,
    raw_transform: Callable[[float], float],
    rationale: str,
) -> ImpactDimension:
    score_int = int(_clamp(score))
    low = max(0, score_int - width)
    high = min(100, score_int + width)
    raw_value = raw_transform(score_int)
    raw_low = raw_transform(low)
    raw_high = raw_transform(high)
    return ImpactDimension(
        score=score_int,
        confidence_low=low,
        confidence_high=high,
        rationale=rationale,
        predicted_value=round(raw_value, 3),
        predicted_low=round(min(raw_low, raw_high), 3),
        predicted_high=round(max(raw_low, raw_high), 3),
        units=units,
    )


def _repair_forecast(forecast: ImpactForecast) -> ImpactForecast:
    updates: dict[str, ImpactDimension] = {}
    for name in DIMENSIONS:
        dimension = getattr(forecast, name)
        low = min(dimension.confidence_low, dimension.score)
        high = max(dimension.confidence_high, dimension.score)
        updates[name] = _copy_model(dimension, confidence_low=low, confidence_high=high)
    if hasattr(forecast, "model_copy"):
        return forecast.model_copy(update=updates)
    return forecast.copy(update=updates)


def _dump(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, BaseModel):
        if hasattr(value, "model_dump"):
            return value.model_dump()
        return value.dict()
    return {
        key: getattr(value, key)
        for key in dir(value)
        if not key.startswith("_") and not callable(getattr(value, key))
    }


def _copy_model(model: Any, **updates: Any) -> Any:
    if hasattr(model, "model_copy"):
        return model.model_copy(update=updates)
    return model.copy(update=updates)


def _clamp(value: float, low: int = 0, high: int = 100) -> int:
    return int(max(low, min(high, round(value))))


def _citations_from_score(score: float) -> float:
    return math.pow(max(score, 0) / 100.0, 2.25) * 2500.0


def _keyword_score(text: str, weights: dict[str, int]) -> int:
    return min(34, sum(weight for keyword, weight in weights.items() if keyword in text))


def _venue_bonus(venue: str) -> int:
    venue_text = venue.lower()
    top_venues = (
        "neurips",
        "nips",
        "icml",
        "iclr",
        "cvpr",
        "acl",
        "emnlp",
        "aaai",
        "ijcai",
        "nature",
        "science",
        "cell",
    )
    strong_venues = ("kdd", "eccv", "iccv", "uai", "aistats", "siggraph", "jmlr", "pmlr")
    if any(venue in venue_text for venue in top_venues):
        return 20
    if any(venue in venue_text for venue in strong_venues):
        return 14
    return 6 if venue_text else 0


def _concept_count(state: dict[str, Any], metadata: dict[str, Any]) -> int:
    concepts: set[str] = set()
    for concept in metadata.get("concepts", []) or []:
        concepts.add(str(concept).lower())
    for paper in state.get("papers", [])[:20]:
        payload = _dump(paper)
        for concept in payload.get("concepts", []) or []:
            concepts.add(str(concept).lower())
    return len(concepts)


def _crowding_penalty(state: dict[str, Any]) -> float:
    overlap = _dump(state.get("overlaps"))
    score = overlap.get("crowding_score", 0) or 0
    paper_count = min(50, len(state.get("papers", []) or []))
    return min(100.0, float(score) * 0.65 + paper_count * 0.35)


def _audience_interest(state: dict[str, Any]) -> float:
    outputs = state.get("emulator_outputs", []) or []
    if not outputs:
        return 0.0
    scores = [_dump(output).get("interest_score", 0) or 0 for output in outputs]
    return sum(scores) / max(1, len(scores))


def _conflict_bonus(state: dict[str, Any]) -> float:
    conflicts = state.get("conflicts", []) or []
    if not conflicts:
        return 0.0
    severity = sum(float(_dump(conflict).get("severity", 0) or 0) for conflict in conflicts)
    return min(10.0, severity * 4.0)


def _uncertainty_width(abstract_len: int, has_venue: bool, cutoff_year: int | None) -> int:
    width = 22
    if abstract_len > 80:
        width -= 4
    if has_venue:
        width -= 3
    if cutoff_year:
        width += 3
    return max(10, min(28, width))


VOLUME_KEYWORDS = {
    "transformer": 14,
    "attention": 8,
    "bert": 18,
    "gpt": 14,
    "diffusion": 12,
    "convolutional": 8,
    "cnn": 8,
    "graph neural": 10,
    "self-supervised": 11,
    "representation learning": 9,
    "benchmark": 7,
    "dataset": 6,
    "state-of-the-art": 8,
}

VELOCITY_KEYWORDS = {
    "benchmark": 8,
    "dataset": 8,
    "state-of-the-art": 10,
    "transformer": 8,
    "bert": 12,
    "code": 4,
    "efficient": 5,
    "scalable": 5,
}

REACH_KEYWORDS = {
    "multimodal": 10,
    "cross-domain": 9,
    "transfer": 8,
    "general": 6,
    "language": 6,
    "vision": 6,
    "biology": 7,
    "protein": 8,
    "materials": 8,
    "robot": 7,
}

DEPTH_KEYWORDS = {
    "theory": 10,
    "theoretical": 10,
    "framework": 8,
    "representation": 8,
    "causal": 8,
    "foundation": 10,
    "survey": 4,
    "review": 4,
    "benchmark": 6,
    "ablation": 4,
}

DISRUPTION_KEYWORDS = {
    "outperform": 8,
    "state-of-the-art": 7,
    "replace": 8,
    "without": 5,
    "novel": 6,
    "new architecture": 10,
    "end-to-end": 6,
    "unsupervised": 8,
    "self-supervised": 10,
    "attention": 6,
}

TRANSLATION_KEYWORDS = {
    "clinical": 15,
    "trial": 12,
    "patient": 10,
    "policy": 12,
    "patent": 12,
    "deployment": 10,
    "production": 8,
    "robot": 8,
    "autonomous": 8,
    "medical": 12,
    "diagnosis": 12,
}

MATERIALS_KEYWORDS = {
    "materials": 10,
    "molecule": 9,
    "protein": 10,
    "chemistry": 9,
    "drug": 12,
    "crystal": 8,
}
