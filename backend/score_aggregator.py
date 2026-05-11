from __future__ import annotations

from typing import Any

from backend.schemas import MetricScore, Scorecard


METRIC_WEIGHTS = {
    "novelty": 0.14,
    "saturation": 0.12,
    "conflict_risk": 0.12,
    "feasibility": 0.12,
    "volume": 0.07,
    "velocity": 0.07,
    "reach": 0.07,
    "depth": 0.07,
    "disruption": 0.07,
    "translation": 0.07,
    "evidence_quality": 0.08,
}


async def score_aggregator(state: dict[str, Any]) -> dict[str, Scorecard]:
    metrics = _dedupe_metrics(state.get("metric_scores", []))
    if not metrics:
        raise ValueError("score_aggregator requires at least one MetricScore")

    present_weights = {name: weight for name, weight in METRIC_WEIGHTS.items() if name in metrics}
    total_weight = sum(present_weights.values())
    if total_weight <= 0:
        raise ValueError("score_aggregator received metrics that are not in the configured weight table")

    weighted_contributions = {
        name: round(metrics[name].score * weight / total_weight, 3)
        for name, weight in present_weights.items()
    }
    composite = round(sum(weighted_contributions.values()))
    ordered_metrics = [metrics[name] for name in METRIC_WEIGHTS if name in metrics]
    missing = [name for name in METRIC_WEIGHTS if name not in metrics]

    scorecard = Scorecard(
        composite_score=composite,
        verdict=_verdict(composite, ordered_metrics),
        metric_scores=ordered_metrics,
        strengths=_strengths(ordered_metrics),
        weaknesses=_weaknesses(ordered_metrics, missing),
        evidence_summary=_evidence_summary(state, ordered_metrics, missing),
        metric_weights=present_weights,
        weighted_contributions=weighted_contributions,
    )
    return {"scorecard": scorecard}


run = score_aggregator


def _dedupe_metrics(metrics: list[Any]) -> dict[str, MetricScore]:
    deduped: dict[str, MetricScore] = {}
    for metric in metrics:
        if not isinstance(metric, MetricScore):
            metric = MetricScore.model_validate(metric)
        name = str(metric.name).lower().replace(" ", "_").replace("-", "_")
        deduped[name] = metric.model_copy(update={"name": name}) if hasattr(metric, "model_copy") else metric.copy(update={"name": name})
    return deduped


def _verdict(composite: int, metrics: list[MetricScore]) -> str:
    floor = min(metric.score for metric in metrics)
    if floor < 35:
        return "reject until the weakest metric is repaired"
    if composite >= 80 and floor >= 55:
        return "strong candidate"
    if composite >= 65:
        return "promising but needs steering"
    if composite >= 50:
        return "risky; mutate before development"
    return "weak idea; substantial repair required"


def _strengths(metrics: list[MetricScore]) -> list[str]:
    return [f"{metric.name}: {metric.score}" for metric in sorted(metrics, key=lambda item: item.score, reverse=True)[:4]]


def _weaknesses(metrics: list[MetricScore], missing: list[str]) -> list[str]:
    weak = [metric.weakness or f"{metric.name} is weak at {metric.score}." for metric in metrics if metric.score < 58]
    if missing:
        weak.append(f"Missing production metric outputs: {', '.join(missing)}.")
    if not weak:
        weak = [metric.weakness for metric in sorted(metrics, key=lambda item: item.score)[:2] if metric.weakness]
    return weak[:6]


def _evidence_summary(state: dict[str, Any], metrics: list[MetricScore], missing: list[str]) -> str:
    evidence_ids = sorted({evidence_id for metric in metrics for evidence_id in metric.evidence_ids})
    paper_count = len(state.get("papers", []) or [])
    missing_note = f" Missing metrics: {', '.join(missing)}." if missing else ""
    return (
        f"Aggregated {len(metrics)} production metric outputs using {len(evidence_ids)} distinct evidence IDs "
        f"from {paper_count} retrieved papers.{missing_note}"
    )