from __future__ import annotations

import importlib
import inspect
import operator
import warnings
from typing import Annotated, Any, Callable, List, TypedDict

try:
    from langchain_core._api.deprecation import (
        LangChainDeprecationWarning,
        LangChainPendingDeprecationWarning,
    )

    warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
    warnings.filterwarnings("ignore", category=LangChainPendingDeprecationWarning)
except ImportError:
    pass

from langgraph.graph import END, StateGraph

try:
    from langgraph.types import Send
except ImportError:
    from langgraph.constants import Send

from backend.schemas import (
    Conflict,
    ImpactDimension,
    ImpactForecast,
    MetricScore,
    OverlapReport,
    Paper,
    ParsedHypothesis,
    Scorecard,
    StrategyMemo,
    Variant,
)
from backend.tracing import observe


class PipelineState(TypedDict, total=False):
    raw_hypothesis: str
    parsed: ParsedHypothesis
    papers: List[Paper]
    conflicts: List[Conflict]
    overlaps: OverlapReport
    forecast: ImpactForecast
    metric_scores: Annotated[List[MetricScore], operator.add]
    scorecard: Scorecard
    variants: List[Variant]
    current_variant: Variant
    rescored_variants: Annotated[List[Variant], operator.add]
    ranked_variants: List[Variant]
    final_memo: StrategyMemo


PartialState = dict[str, Any]
AgentFn = Callable[[PipelineState], PartialState | Any]


async def _call_agent(
    agent_name: str,
    fallback: AgentFn,
    state: PipelineState,
    aliases: tuple[str, ...] = (),
) -> PartialState:
    func = _load_agent(agent_name, fallback, aliases)
    result = func(state)
    if inspect.isawaitable(result):
        result = await result
    return result


def _load_agent(agent_name: str, fallback: AgentFn, aliases: tuple[str, ...] = ()) -> AgentFn:
    for candidate in (agent_name, *aliases):
        module_name = f"backend.{candidate}"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                continue
            raise

        implementation = (
            getattr(module, candidate, None)
            or getattr(module, agent_name, None)
            or getattr(module, "run", None)
        )
        if implementation is not None:
            return implementation
    return fallback


@observe(name="parser")
async def parser(state: PipelineState) -> PartialState:
    return await _call_agent("parser", _parser_stub, state)


@observe(name="cartographer")
async def cartographer(state: PipelineState) -> PartialState:
    return await _call_agent("cartographer", _cartographer_stub, state)


@observe(name="novelty_scorer")
async def novelty_scorer(state: PipelineState) -> PartialState:
    return await _call_agent("novelty_scorer", _novelty_scorer_stub, state)


@observe(name="saturation_scorer")
async def saturation_scorer(state: PipelineState) -> PartialState:
    return await _call_agent("saturation_scorer", _saturation_scorer_stub, state)


@observe(name="conflict_scorer")
async def conflict_scorer(state: PipelineState) -> PartialState:
    return await _call_agent("conflict_scorer", _conflict_scorer_stub, state)


@observe(name="feasibility_scorer")
async def feasibility_scorer(state: PipelineState) -> PartialState:
    return await _call_agent("feasibility_scorer", _feasibility_scorer_stub, state)


@observe(name="impact_forecaster")
async def impact_forecaster(state: PipelineState) -> PartialState:
    return await _call_agent("impact_forecaster", _impact_forecaster_stub, state)


@observe(name="evidence_quality_scorer")
async def evidence_quality_scorer(state: PipelineState) -> PartialState:
    return await _call_agent("evidence_quality_scorer", _evidence_quality_scorer_stub, state)


@observe(name="score_aggregator")
async def score_aggregator(state: PipelineState) -> PartialState:
    return await _call_agent("score_aggregator", _score_aggregator_stub, state)


@observe(name="mutator")
async def mutator(state: PipelineState) -> PartialState:
    return await _call_agent("mutator", _mutator_stub, state)


@observe(name="variant_rescorer")
async def variant_rescorer(state: PipelineState) -> PartialState:
    return await _call_agent("variant_rescorer", _variant_rescorer_stub, state)


@observe(name="ranker")
async def ranker(state: PipelineState) -> PartialState:
    return await _call_agent("ranker", _ranker_stub, state, aliases=("pareto_curator",))


@observe(name="strategist")
async def strategist(state: PipelineState) -> PartialState:
    return await _call_agent("strategist", _strategist_stub, state)


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("parser", parser)
    graph.add_node("cartographer", cartographer)
    graph.add_node("novelty_scorer", novelty_scorer)
    graph.add_node("saturation_scorer", saturation_scorer)
    graph.add_node("conflict_scorer", conflict_scorer)
    graph.add_node("feasibility_scorer", feasibility_scorer)
    graph.add_node("impact_forecaster", impact_forecaster)
    graph.add_node("evidence_quality_scorer", evidence_quality_scorer)
    graph.add_node("score_aggregator", score_aggregator)
    graph.add_node("mutator", mutator)
    graph.add_node("variant_rescorer", variant_rescorer)
    graph.add_node("ranker", ranker)
    graph.add_node("strategist", strategist)

    graph.set_entry_point("parser")

    graph.add_edge("parser", "cartographer")

    metric_nodes = [
        "novelty_scorer",
        "saturation_scorer",
        "conflict_scorer",
        "feasibility_scorer",
        "impact_forecaster",
        "evidence_quality_scorer",
    ]
    for node in metric_nodes:
        graph.add_edge("cartographer", node)

    graph.add_edge(metric_nodes, "score_aggregator")
    graph.add_edge("score_aggregator", "mutator")
    graph.add_conditional_edges(
        "mutator",
        _dispatch_variant_rescorers,
        ["variant_rescorer"],
    )
    graph.add_edge("variant_rescorer", "ranker")
    graph.add_edge("ranker", "strategist")
    graph.add_edge("strategist", END)

    return graph.compile()


async def run_pipeline(raw_hypothesis: str) -> PipelineState:
    app = build_graph()
    initial_state: PipelineState = {
        "raw_hypothesis": raw_hypothesis,
        "metric_scores": [],
        "rescored_variants": [],
    }
    return await app.ainvoke(initial_state)


def _dispatch_variant_rescorers(state: PipelineState) -> list[Send]:
    return [
        Send(
            "variant_rescorer",
            {
                "raw_hypothesis": state["raw_hypothesis"],
                "parsed": state["parsed"],
                "papers": state.get("papers", []),
                "conflicts": state.get("conflicts", []),
                "overlaps": state.get("overlaps"),
                "forecast": state.get("forecast"),
                "metric_scores": state.get("metric_scores", []),
                "scorecard": state["scorecard"],
                "variants": state.get("variants", []),
                "current_variant": variant,
            },
        )
        for variant in state.get("variants", [])
    ]


async def _parser_stub(state: PipelineState) -> PartialState:
    hypothesis = state["raw_hypothesis"]
    return {
        "parsed": ParsedHypothesis(
            claim=f"Mock structured claim extracted from: {hypothesis}",
            mechanism="Mock mechanism: quantitative pathway 42.",
            context="Mock context: literature-backed Idea Hater demo.",
            population="Mock population: target research setting.",
            method="Mock method: measurable intervention and outcome.",
        )
    }


async def _cartographer_stub(state: PipelineState) -> PartialState:
    papers = [
        Paper(
            paper_id=f"mock-paper-{idx:02d}",
            title=f"Mock literature neighbour {idx:02d}",
            authors=[f"Fake Author {idx}", f"Demo Collaborator {idx}"],
            year=2020 + (idx % 5),
            abstract=f"Obviously fake abstract for quantitative scoring paper {idx}.",
            url=f"https://example.test/mock-paper-{idx:02d}",
            citation_count=idx * 9,
            relevance_score=round(1.0 - (idx * 0.012), 3),
            cluster=f"mock-evidence-cluster-{(idx % 6) + 1}",
        )
        for idx in range(1, 51)
    ]
    return {"papers": papers}


async def _novelty_scorer_stub(state: PipelineState) -> PartialState:
    return {
        "metric_scores": [
            _metric(
                "novelty",
                58,
                "Mock novelty is moderate: several close analogues exist, but the mechanism framing is shifted.",
                ["Closest analogue: mock-paper-04", "Nearest cluster: mock-evidence-cluster-2"],
                "Closest papers make the base idea feel only partly new.",
            )
        ]
    }


async def _saturation_scorer_stub(state: PipelineState) -> PartialState:
    overlaps = OverlapReport(
        crowding_score=67,
        overlapping_papers=[
            "Mock literature neighbour 08",
            "Mock literature neighbour 21",
            "Mock literature neighbour 34",
        ],
        whitespace_summary="Mock whitespace: narrower timing and population constraints remain under-tested.",
        risk_notes=[
            "Mock saturation risk: recent publication velocity is high.",
            "Mock overlap risk: three close analogue papers already cover broad framing.",
        ],
    )
    return {
        "overlaps": overlaps,
        "metric_scores": [
            _metric(
                "saturation",
                33,
                "Mock saturation score is low because the area is visibly crowded.",
                overlaps.overlapping_papers,
                "The hypothesis needs sharper positioning to avoid crowded territory.",
            )
        ],
    }


async def _conflict_scorer_stub(state: PipelineState) -> PartialState:
    conflicts = [
        Conflict(
            paper_id="mock-paper-03",
            title="Mock literature neighbour 03",
            disagreement_dimension="mechanism",
            explanation="Fake contradiction: the paper claims the proposed mechanism runs backwards.",
            severity=0.72,
        ),
        Conflict(
            paper_id="mock-paper-17",
            title="Mock literature neighbour 17",
            disagreement_dimension="population",
            explanation="Fake contradiction: the paper only supports a narrower toy population.",
            severity=0.41,
        ),
    ]
    return {
        "conflicts": conflicts,
        "metric_scores": [
            _metric(
                "conflict_risk",
                46,
                "Mock conflict risk is material: two nearby papers challenge mechanism and population assumptions.",
                [conflict.title for conflict in conflicts],
                "The current claim should address mechanism reversal and population scope.",
            )
        ],
    }


async def _feasibility_scorer_stub(state: PipelineState) -> PartialState:
    return {
        "metric_scores": [
            _metric(
                "feasibility",
                74,
                "Mock feasibility is strong: the method is common in nearby papers and dependencies look modest.",
                ["Methods appear in mock-paper-11", "Benchmark data appears in mock-paper-26"],
                "The main feasibility risk is validation across a second context.",
            )
        ]
    }


async def _impact_forecaster_stub(state: PipelineState) -> PartialState:
    forecast = ImpactForecast(
        volume=_impact_dimension(72, "Fake volume score: many adjacent papers can cite it."),
        velocity=_impact_dimension(68, "Fake velocity score: obvious demo buzz, modest validation lag."),
        reach=_impact_dimension(61, "Fake reach score: crosses one neighboring field."),
        depth=_impact_dimension(57, "Fake depth score: useful but not yet foundational."),
        disruption=_impact_dimension(49, "Fake disruption score: more steering than displacement."),
        translation=_impact_dimension(44, "Fake translation score: needs a bridge dataset."),
        overall_summary="Mock impact forecast: promising, crowded, and best steered toward a sharper niche.",
    )
    return {
        "forecast": forecast,
        "metric_scores": [
            _metric("volume", forecast.volume.score, forecast.volume.rationale, ["Citation analogue: mock-paper-02"]),
            _metric("velocity", forecast.velocity.score, forecast.velocity.rationale, ["Recent analogue: mock-paper-06"]),
            _metric("reach", forecast.reach.score, forecast.reach.rationale, ["Adjacent concept: mock cluster 4"]),
            _metric("depth", forecast.depth.score, forecast.depth.rationale, ["Review-adjacent paper: mock-paper-14"]),
            _metric("disruption", forecast.disruption.score, forecast.disruption.rationale, ["Conflict cluster: mock cluster 3"]),
            _metric("translation", forecast.translation.score, forecast.translation.rationale, ["Bridge dataset missing"]),
        ],
    }


async def _evidence_quality_scorer_stub(state: PipelineState) -> PartialState:
    return {
        "metric_scores": [
            _metric(
                "evidence_quality",
                69,
                "Mock evidence quality is adequate: retrieval coverage is broad, but several abstracts are thin.",
                ["50 mock papers retrieved", "6 mock clusters represented"],
                "Confidence is limited by abstract-only evidence in the demo stub.",
            )
        ]
    }


async def _score_aggregator_stub(state: PipelineState) -> PartialState:
    metrics = state.get("metric_scores", [])
    metric_map = {metric.metric_name: metric for metric in metrics}
    weights = {
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
    composite = _weighted_score(metric_map, weights)
    weaknesses = [metric.weakness for metric in metrics if metric.weakness]
    strengths = [
        f"{metric.metric_name}: {metric.score}"
        for metric in sorted(metrics, key=lambda item: item.score, reverse=True)[:3]
    ]
    scorecard = Scorecard(
        composite_score=composite,
        verdict=_verdict(composite),
        metric_scores=metrics,
        strengths=strengths,
        weaknesses=weaknesses[:5],
        evidence_summary=(
            f"Mock scorecard aggregated {len(metrics)} metrics from "
            f"{len(state.get('papers', []))} retrieved papers."
        ),
    )
    return {"scorecard": scorecard}


async def _mutator_stub(state: PipelineState) -> PartialState:
    raw = state["raw_hypothesis"]
    mutation_specs = [
        ("Narrow", 6, "Focus the claim on the less crowded subgroup flagged by saturation scoring."),
        ("Substitute mechanism", 3, "Avoid the highest-severity mechanism conflict with an alternate pathway."),
        ("Cross-pollinate", 10, "Borrow a method from the strongest adjacent evidence cluster."),
        ("Invert", 4, "Turn the conflict into a boundary-condition test."),
        ("Combine", 8, "Pair the claim with the missing bridge dataset needed for translation."),
    ]
    variants = [
        Variant(
            variant_id=f"mock-variant-{idx}",
            hypothesis_text=f"{raw} [{operator.lower()} quantitative repair]",
            operator=operator,
            rationale=f"{rationale} Obvious-fake expected gain: +{expected_gain}.",
            composite_score=min(100, state["scorecard"].composite_score + expected_gain),
            impact_scores={
                "novelty": 58 + idx,
                "saturation": 33 + expected_gain,
                "conflict_risk": 46 + (idx % 3) * 4,
                "feasibility": 74 - idx,
                "evidence_quality": 69 + idx,
            },
        )
        for idx, (operator, expected_gain, rationale) in enumerate(mutation_specs, start=1)
    ]
    return {"variants": variants}


async def _variant_rescorer_stub(state: PipelineState) -> PartialState:
    variant = state["current_variant"]
    score_adjustment = {
        "Narrow": 7,
        "Substitute mechanism": 5,
        "Cross-pollinate": 11,
        "Invert": 4,
        "Combine": 9,
    }.get(variant.operator, 0)
    original_score = state["scorecard"].composite_score
    composite = min(100, original_score + score_adjustment)
    scores = {
        **variant.impact_scores,
        "composite": composite,
        "volume": 65 + score_adjustment,
        "velocity": 60 + score_adjustment // 2,
        "reach": 58 + score_adjustment,
        "depth": 55 + score_adjustment,
        "disruption": 48 + score_adjustment,
        "translation": 45 + score_adjustment,
    }
    scorecard = Scorecard(
        composite_score=composite,
        verdict=_verdict(composite),
        metric_scores=[
            _metric("novelty", scores.get("novelty", 50), f"Mock re-score for {variant.variant_id}: novelty adjusted."),
            _metric("saturation", scores.get("saturation", 50), f"Mock re-score for {variant.variant_id}: saturation adjusted."),
            _metric(
                "evidence_quality",
                scores.get("evidence_quality", 50),
                f"Mock re-score for {variant.variant_id}: evidence confidence adjusted.",
            ),
        ],
        strengths=[f"Improves composite score by {score_adjustment} points."],
        weaknesses=["Still requires real literature scoring before demo claims become credible."],
        evidence_summary=f"Mock variant re-score reused {len(state.get('papers', []))} retrieved papers.",
    )
    return {
        "rescored_variants": [
            _copy_model(
                variant,
                composite_score=composite,
                impact_scores=scores,
                scorecard=scorecard,
            )
        ]
    }


async def _ranker_stub(state: PipelineState) -> PartialState:
    variants = state.get("rescored_variants") or state.get("variants", [])
    selected_ids = _pareto_variant_ids(variants)
    ranked = sorted(
        variants,
        key=lambda variant: (
            variant.composite_score,
            variant.impact_scores.get("evidence_quality", 0),
            variant.impact_scores.get("feasibility", 0),
        ),
        reverse=True,
    )
    updated = []
    for rank, variant in enumerate(ranked, start=1):
        is_selected = variant.variant_id in selected_ids
        explanation = (
            f"Rank {rank}; Pareto-selected because no mock variant dominates its score trade-off."
            if is_selected
            else f"Rank {rank}; dominated by a higher-scoring mock variant on the quantitative scorecard."
        )
        updated.append(
            _copy_model(
                variant,
                rank=rank,
                is_pareto_selected=is_selected,
                dominance_explanation=explanation,
            )
        )
    return {"ranked_variants": updated, "variants": updated}


async def _strategist_stub(state: PipelineState) -> PartialState:
    ranked = state.get("ranked_variants", [])
    best = ranked[0] if ranked else None
    selected = [
        f"#{variant.rank}: {variant.variant_id} ({variant.operator}) - score {variant.composite_score}"
        for variant in ranked
        if variant.is_pareto_selected
    ]
    recommendation = (
        f"Develop {best.variant_id} via {best.operator}; it has the strongest mock composite score."
        if best
        else "Do not proceed until variants can be generated and scored."
    )
    scorecard = state["scorecard"]
    memo = StrategyMemo(
        recommendation=recommendation,
        executive_summary=(
            f"The quantitative Idea Hater pipeline completed end-to-end. "
            f"The original idea scored {scorecard.composite_score}/100 ({scorecard.verdict}), "
            f"then variants were re-scored and ranked."
        ),
        key_findings=[
            f"Parsed claim: {state['parsed'].claim}",
            f"Retrieved {len(state.get('papers', []))} mock literature neighbours.",
            f"Aggregated {len(scorecard.metric_scores)} quantitative metric scores.",
            f"Generated and re-scored {len(state.get('rescored_variants', []))} variants.",
        ],
        selected_variants=selected,
        risks=scorecard.weaknesses[:3],
        next_steps=[
            "Replace mock metric scorers with real retrieval-backed implementations.",
            "Warm the SQLite cache before any demo run.",
            "Keep group emulation out of the core backend validation path.",
        ],
    )
    return {"final_memo": memo}


def _metric(
    metric_name: str,
    score: int,
    rationale: str,
    evidence: list[str] | None = None,
    weakness: str = "",
) -> MetricScore:
    return MetricScore(
        metric_name=metric_name,
        score=score,
        confidence_low=max(0, score - 10),
        confidence_high=min(100, score + 10),
        rationale=rationale,
        evidence=evidence or [],
        weakness=weakness,
    )


def _impact_dimension(score: int, rationale: str) -> ImpactDimension:
    return ImpactDimension(
        score=score,
        confidence_low=max(0, score - 12),
        confidence_high=min(100, score + 12),
        rationale=rationale,
    )


def _weighted_score(metric_map: dict[str, MetricScore], weights: dict[str, float]) -> int:
    present_weights = {
        metric_name: weight
        for metric_name, weight in weights.items()
        if metric_name in metric_map
    }
    total_weight = sum(present_weights.values())
    if total_weight == 0:
        return 0
    weighted = sum(metric_map[metric_name].score * weight for metric_name, weight in present_weights.items())
    return round(weighted / total_weight)


def _verdict(score: int) -> str:
    if score >= 80:
        return "strong candidate"
    if score >= 65:
        return "promising but needs steering"
    if score >= 50:
        return "risky; mutate before development"
    return "weak idea; substantial repair required"


def _pareto_variant_ids(variants: list[Variant]) -> set[str]:
    selected: set[str] = set()
    for candidate in variants:
        dominated = False
        for challenger in variants:
            if challenger.variant_id == candidate.variant_id:
                continue
            if _dominates(challenger, candidate):
                dominated = True
                break
        if not dominated:
            selected.add(candidate.variant_id)
    return selected


def _dominates(left: Variant, right: Variant) -> bool:
    dimensions = set(left.impact_scores) & set(right.impact_scores)
    if not dimensions:
        return False
    left_score = left.composite_score
    right_score = right.composite_score
    if "composite" in left.impact_scores and "composite" in right.impact_scores:
        left_score = left.impact_scores["composite"]
        right_score = right.impact_scores["composite"]

    return (
        left_score >= right_score
        and all(left.impact_scores[dim] >= right.impact_scores[dim] for dim in dimensions)
        and (
            left_score > right_score
            or any(left.impact_scores[dim] > right.impact_scores[dim] for dim in dimensions)
        )
    )


def _copy_model(model: Any, **updates: Any) -> Any:
    if hasattr(model, "model_copy"):
        return model.model_copy(update=updates)
    return model.copy(update=updates)
