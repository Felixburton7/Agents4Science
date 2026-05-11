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
    EmulatorOutput,
    GroundednessCheck,
    ImpactDimension,
    ImpactForecast,
    OverlapReport,
    Paper,
    ParsedHypothesis,
    ResearchGroup,
    Scenario,
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
    groups: List[ResearchGroup]
    current_group: ResearchGroup
    emulator_outputs: Annotated[List[EmulatorOutput], operator.add]
    scenarios: List[Scenario]
    forecast: ImpactForecast
    variants: List[Variant]
    groundedness_checks: List[GroundednessCheck]
    final_memo: StrategyMemo


PartialState = dict[str, Any]
AgentFn = Callable[[PipelineState], PartialState | Any]


async def _call_agent(agent_name: str, fallback: AgentFn, state: PipelineState) -> PartialState:
    func = _load_agent(agent_name, fallback)
    result = func(state)
    if inspect.isawaitable(result):
        result = await result
    return result


def _load_agent(agent_name: str, fallback: AgentFn) -> AgentFn:
    module_name = f"backend.agents.{agent_name}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            return fallback
        raise

    implementation = getattr(module, agent_name, None) or getattr(module, "run", None)
    if implementation is None:
        return fallback
    return implementation


@observe(name="parser")
async def parser(state: PipelineState) -> PartialState:
    return await _call_agent("parser", _parser_stub, state)


@observe(name="cartographer")
async def cartographer(state: PipelineState) -> PartialState:
    return await _call_agent("cartographer", _cartographer_stub, state)


@observe(name="conflict_detector")
async def conflict_detector(state: PipelineState) -> PartialState:
    return await _call_agent("conflict_detector", _conflict_detector_stub, state)


@observe(name="overlap_auditor")
async def overlap_auditor(state: PipelineState) -> PartialState:
    return await _call_agent("overlap_auditor", _overlap_auditor_stub, state)


@observe(name="group_identifier")
async def group_identifier(state: PipelineState) -> PartialState:
    return await _call_agent("group_identifier", _group_identifier_stub, state)


@observe(name="group_emulator")
async def group_emulator(state: PipelineState) -> PartialState:
    return await _call_agent("group_emulator", _group_emulator_stub, state)


@observe(name="trajectory_synth")
async def trajectory_synth(state: PipelineState) -> PartialState:
    return await _call_agent("trajectory_synth", _trajectory_synth_stub, state)


@observe(name="impact_forecaster")
async def impact_forecaster(state: PipelineState) -> PartialState:
    return await _call_agent("impact_forecaster", _impact_forecaster_stub, state)


@observe(name="mutator")
async def mutator(state: PipelineState) -> PartialState:
    return await _call_agent("mutator", _mutator_stub, state)


@observe(name="pareto_curator")
async def pareto_curator(state: PipelineState) -> PartialState:
    return await _call_agent("pareto_curator", _pareto_curator_stub, state)


@observe(name="strategist")
async def strategist(state: PipelineState) -> PartialState:
    return await _call_agent("strategist", _strategist_stub, state)


@observe(name="groundedness_check")
async def groundedness_check(state: PipelineState) -> PartialState:
    return await _call_agent("groundedness_check", _groundedness_check_stub, state)


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("parser", parser)
    graph.add_node("cartographer", cartographer)
    graph.add_node("conflict_detector", conflict_detector)
    graph.add_node("overlap_auditor", overlap_auditor)
    graph.add_node("group_identifier", group_identifier)
    graph.add_node("group_emulator", group_emulator)
    graph.add_node("trajectory_synth", trajectory_synth)
    graph.add_node("impact_forecaster", impact_forecaster)
    graph.add_node("mutator", mutator)
    graph.add_node("pareto_curator", pareto_curator)
    graph.add_node("strategist", strategist)
    graph.add_node("groundedness_check", groundedness_check)

    graph.set_entry_point("parser")

    graph.add_edge("parser", "cartographer")
    graph.add_edge("parser", "conflict_detector")
    graph.add_edge("parser", "overlap_auditor")

    graph.add_edge(
        ["cartographer", "conflict_detector", "overlap_auditor"],
        "group_identifier",
    )

    graph.add_conditional_edges(
        "group_identifier",
        _dispatch_group_emulators,
        ["group_emulator"],
    )
    graph.add_edge("group_emulator", "trajectory_synth")
    graph.add_edge("group_emulator", "groundedness_check")
    graph.add_edge("trajectory_synth", "impact_forecaster")
    graph.add_edge("impact_forecaster", "mutator")
    graph.add_edge("mutator", "pareto_curator")
    graph.add_edge(["pareto_curator", "groundedness_check"], "strategist")
    graph.add_edge("strategist", END)

    return graph.compile()


async def run_pipeline(raw_hypothesis: str) -> PipelineState:
    app = build_graph()
    initial_state: PipelineState = {
        "raw_hypothesis": raw_hypothesis,
        "emulator_outputs": [],
    }
    return await app.ainvoke(initial_state)


def _dispatch_group_emulators(state: PipelineState) -> list[Send]:
    return [
        Send(
            "group_emulator",
            {
                "raw_hypothesis": state["raw_hypothesis"],
                "parsed": state["parsed"],
                "papers": state.get("papers", []),
                "conflicts": state.get("conflicts", []),
                "overlaps": state.get("overlaps"),
                "groups": state.get("groups", []),
                "current_group": group,
            },
        )
        for group in state.get("groups", [])
    ]


async def _parser_stub(state: PipelineState) -> PartialState:
    hypothesis = state["raw_hypothesis"]
    return {
        "parsed": ParsedHypothesis(
            claim=f"Mock structured claim extracted from: {hypothesis}",
            mechanism="Mock mechanism: obvious-fake mechanism 42.",
            context="Mock context: simulated literature landscape.",
            population="Mock population: synthetic researchers.",
            method="Mock method: placeholder causal inference assay.",
        )
    }


async def _cartographer_stub(state: PipelineState) -> PartialState:
    papers = [
        Paper(
            paper_id=f"mock-paper-{idx:02d}",
            title=f"Mock nearest-neighbor paper {idx:02d}",
            authors=[f"Fake Author {idx}", f"Demo Collaborator {idx}"],
            year=2020 + (idx % 5),
            abstract=f"Obviously fake abstract for cartography paper {idx}.",
            url=f"https://example.test/mock-paper-{idx:02d}",
            citation_count=idx * 7,
            relevance_score=round(1.0 - (idx * 0.01), 3),
            cluster=f"mock-cluster-{(idx % 5) + 1}",
        )
        for idx in range(1, 51)
    ]
    return {"papers": papers}


async def _conflict_detector_stub(state: PipelineState) -> PartialState:
    return {
        "conflicts": [
            Conflict(
                paper_id="mock-paper-03",
                title="Mock nearest-neighbor paper 03",
                disagreement_dimension="mechanism",
                explanation="Fake contradiction: paper claims the mock mechanism runs backwards.",
                severity=0.72,
            ),
            Conflict(
                paper_id="mock-paper-17",
                title="Mock nearest-neighbor paper 17",
                disagreement_dimension="population",
                explanation="Fake contradiction: paper only supports a toy population.",
                severity=0.41,
            ),
        ]
    }


async def _overlap_auditor_stub(state: PipelineState) -> PartialState:
    return {
        "overlaps": OverlapReport(
            crowding_score=64,
            overlapping_papers=[
                "Mock nearest-neighbor paper 08",
                "Mock nearest-neighbor paper 21",
                "Mock nearest-neighbor paper 34",
            ],
            whitespace_summary="Fake whitespace: the narrow timing question is under-explored.",
            risk_notes=[
                "Mock race-condition risk from two adjacent labs.",
                "Mock novelty risk if the population stays too broad.",
            ],
        )
    }


async def _group_identifier_stub(state: PipelineState) -> PartialState:
    groups = [
        ResearchGroup(
            group_id=f"mock-group-{idx}",
            name=f"Mock Research Group {idx}",
            institution=f"Demo Institute {idx}",
            principal_investigators=[f"Prof. Placeholder {idx}"],
            recent_paper_ids=[f"mock-paper-{idx:02d}", f"mock-paper-{idx + 10:02d}"],
            methods=[f"mock-method-{idx}", "placeholder assay"],
            grounding_evidence=f"Fake co-authorship cluster around papers {idx} and {idx + 10}.",
        )
        for idx in range(1, 5)
    ]
    return {"groups": groups}


async def _group_emulator_stub(state: PipelineState) -> PartialState:
    group = state["current_group"]
    group_number = int(group.group_id.rsplit("-", 1)[-1])
    output = EmulatorOutput(
        group_id=group.group_id,
        group_name=group.name,
        interest_score=55 + group_number * 8,
        engagement_type="mock follow-up study",
        proposed_direction=f"{group.name} would fake-test the hypothesis with {group.methods[0]}.",
        method_they_use=group.methods[0],
        time_to_publish_months=6 + group_number * 2,
        competitive_risk=35 + group_number * 10,
        grounding_paper_ids=group.recent_paper_ids,
    )
    return {"emulator_outputs": [output]}


async def _trajectory_synth_stub(state: PipelineState) -> PartialState:
    outputs = state.get("emulator_outputs", [])
    leading_groups = [output.group_name for output in outputs[:2]]
    return {
        "scenarios": [
            Scenario(
                scenario_id="mock-scenario-1",
                name="Fast convergence",
                probability=0.46,
                description="Fake scenario: several groups converge on the same obvious next experiment.",
                leading_groups=leading_groups,
                implications=["Mock priority pressure rises.", "Mock replication arrives quickly."],
            ),
            Scenario(
                scenario_id="mock-scenario-2",
                name="Method split",
                probability=0.34,
                description="Fake scenario: groups split by preferred method and generate comparable variants.",
                leading_groups=[output.group_name for output in outputs[1:3]],
                implications=["Mock synthesis opportunity appears.", "Mock standards question emerges."],
            ),
            Scenario(
                scenario_id="mock-scenario-3",
                name="Slow uptake",
                probability=0.20,
                description="Fake scenario: the field waits for a cleaner benchmark before moving.",
                leading_groups=[output.group_name for output in outputs[2:4]],
                implications=["Mock first-mover advantage improves.", "Mock translation lags."],
            ),
        ]
    }


async def _impact_forecaster_stub(state: PipelineState) -> PartialState:
    return {
        "forecast": ImpactForecast(
            volume=_impact_dimension(72, "Fake volume score: many adjacent papers can cite it."),
            velocity=_impact_dimension(68, "Fake velocity score: obvious demo buzz, modest validation lag."),
            reach=_impact_dimension(61, "Fake reach score: crosses one neighboring field."),
            depth=_impact_dimension(57, "Fake depth score: useful but not yet foundational."),
            disruption=_impact_dimension(49, "Fake disruption score: more steering than displacement."),
            translation=_impact_dimension(44, "Fake translation score: needs a bridge dataset."),
            overall_summary="Mock forecast: promising, crowded, and best steered toward a sharper niche.",
        )
    }


async def _mutator_stub(state: PipelineState) -> PartialState:
    raw = state["raw_hypothesis"]
    mutation_specs = [
        ("Generalise", {"volume": 55, "velocity": 65, "reach": 54, "depth": 49, "disruption": 43, "translation": 43}),
        ("Narrow", {"volume": 62, "velocity": 64, "reach": 60, "depth": 53, "disruption": 50, "translation": 46}),
        (
            "Substitute mechanism",
            {"volume": 58, "velocity": 54, "reach": 58, "depth": 50, "disruption": 45, "translation": 42},
        ),
        ("Shift scale", {"volume": 70, "velocity": 58, "reach": 72, "depth": 61, "disruption": 64, "translation": 52}),
        (
            "Cross-pollinate",
            {"volume": 75, "velocity": 61, "reach": 78, "depth": 65, "disruption": 71, "translation": 55},
        ),
        ("Invert", {"volume": 68, "velocity": 70, "reach": 58, "depth": 70, "disruption": 52, "translation": 70}),
    ]
    variants = [
        Variant(
            variant_id=f"mock-variant-{idx}",
            hypothesis_text=f"{raw} [mock {operator.lower()} variant]",
            operator=operator,
            rationale=f"Fake rationale for applying {operator}.",
            impact_scores=impact_scores,
        )
        for idx, (operator, impact_scores) in enumerate(mutation_specs, start=1)
    ]
    return {"variants": variants}


async def _pareto_curator_stub(state: PipelineState) -> PartialState:
    variants = state.get("variants", [])
    selected_ids = _pareto_variant_ids(variants)
    updated = []
    for variant in variants:
        is_selected = variant.variant_id in selected_ids
        explanation = (
            "Mock Pareto-selected: no fake variant beats it on every impact dimension."
            if is_selected
            else "Mock dominated: another fake variant is at least as strong across the scorecard."
        )
        updated.append(
            _copy_model(
                variant,
                is_pareto_selected=is_selected,
                dominance_explanation=explanation,
            )
        )
    return {"variants": updated}


async def _strategist_stub(state: PipelineState) -> PartialState:
    selected = [
        f"{variant.variant_id}: {variant.operator}"
        for variant in state.get("variants", [])
        if variant.is_pareto_selected
    ]
    memo = StrategyMemo(
        recommendation="Proceed with the narrowest Pareto-selected mock variant for the demo.",
        executive_summary=(
            "The mock pipeline completed end-to-end. It found a crowded but steerable "
            "hypothesis space, highlighted fake group interest, and selected variants "
            "that improve the obvious-fake impact profile."
        ),
        key_findings=[
            f"Parsed claim: {state['parsed'].claim}",
            f"Mapped {len(state.get('papers', []))} mock papers.",
            f"Identified {len(state.get('groups', []))} mock research groups and "
            f"{len(state.get('emulator_outputs', []))} emulator outputs.",
            f"Generated {len(state.get('scenarios', []))} field-response scenarios.",
        ],
        selected_variants=selected,
        risks=[
            "Mock overlap score is high enough to require tighter positioning.",
            "Mock groundedness check should be replaced before external use.",
        ],
        next_steps=[
            "Swap in real Parser, Cartographer, and Group Identifier implementations first.",
            "Warm the SQLite literature cache before the stage run.",
            "Keep Strategist as the only high-reasoning GPT-5 call.",
        ],
    )
    return {"final_memo": memo}


async def _groundedness_check_stub(state: PipelineState) -> PartialState:
    checks = [
        GroundednessCheck(
            group_id=output.group_id,
            group_name=output.group_name,
            is_grounded=True,
            flagged_inconsistencies=[],
            evidence=(
                f"Fake groundedness pass: {output.method_they_use} appears in "
                f"{', '.join(output.grounding_paper_ids)}."
            ),
        )
        for output in state.get("emulator_outputs", [])
    ]
    return {"groundedness_checks": checks}


def _impact_dimension(score: int, rationale: str) -> ImpactDimension:
    return ImpactDimension(
        score=score,
        confidence_low=max(0, score - 12),
        confidence_high=min(100, score + 12),
        rationale=rationale,
    )


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
    return all(left.impact_scores[dim] >= right.impact_scores[dim] for dim in dimensions) and any(
        left.impact_scores[dim] > right.impact_scores[dim] for dim in dimensions
    )


def _copy_model(model: Any, **updates: Any) -> Any:
    if hasattr(model, "model_copy"):
        return model.model_copy(update=updates)
    return model.copy(update=updates)
