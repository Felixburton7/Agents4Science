# Team Task Lists - Quantitative Idea Hater

The project has been refocused. The canonical product is now a quantitative
Idea Hater for Denario: a backend and dashboard that evaluate scientific
hypotheses with metric-backed evidence, generate improved variants, and rank
those variants.

Group emulation is no longer part of the core backend architecture. It remains
only as an optional frontend proof of concept for the hypothesis generator
experience.

---

## Shared Direction

**Core thesis:** Denario can generate candidate research ideas, but its idea
evaluation layer is too qualitative. We are upgrading that layer into a
quantitative, evidence-grounded scoring and improvement system.

**Core user flow:**

1. Denario or a researcher supplies a hypothesis.
2. The system retrieves the relevant literature.
3. Independent scoring agents produce quantitative metrics.
4. The scorecard explains what is weak and why.
5. The mutator generates better variants.
6. Every variant is re-scored.
7. The ranker and strategist recommend which hypothesis to pursue.

**Primary backend contract:** everyone now builds against `backend/`, not a
repo-root `schemas.py`.

**Files to refactor first:**

- `backend/schemas.py`
- `backend/pipeline.py`
- `backend/model_routing.py`
- `backend/agents/*.md`
- `README.md`
- `architecture.md`

---

## Shared Backend Contract

The existing schemas still include group-emulation objects. These should be
deprecated for the core pipeline and replaced or supplemented with quantitative
evaluation objects.

Minimum required models:

```python
class MetricScore(BaseModel):
    name: str
    score: int  # 0-100
    confidence_low: int
    confidence_high: int
    rationale: str
    evidence_ids: list[str]


class IdeaEvaluation(BaseModel):
    hypothesis_text: str
    parsed: ParsedHypothesis
    metrics: list[MetricScore]
    composite_score: int
    verdict: Literal["reject", "revise", "promising", "strong"]
    key_weaknesses: list[str]
    key_strengths: list[str]


class VariantEvaluation(BaseModel):
    variant: Variant
    evaluation: IdeaEvaluation
    improvement_over_original: int
    is_pareto_selected: bool
    dominance_explanation: str
```

Core metrics:

- Novelty
- Saturation / overlap
- Conflict risk
- Feasibility
- Volume
- Velocity
- Reach
- Depth
- Disruption
- Translation
- Evidence quality

All agent outputs should be structured, traceable, and displayable in the
dashboard.

---

## Baron - Presentation, Story, And Demo Narrative

**Owner outcome:** judges understand that this is a quantitative upgrade to
Denario's Idea Hater, not a generic multi-agent demo.

**Tasks**

- Rewrite the 5-minute pitch around the new framing:
  - Problem: generated research ideas are easy; choosing good ones is hard.
  - Gap: qualitative idea-hating is not reliable or auditable enough.
  - Solution: quantitative metric-backed hypothesis steering.
  - Proof: backtest and evidence trace.
  - Denario fit: we improve the decision point before paper generation.
- Build a 7-slide deck:
  - Title: Quantitative Idea Hater for Denario.
  - Problem: idea generation without measurable steering.
  - System: literature-grounded metric scorecard.
  - Architecture: retrieval, scoring, mutation, ranking.
  - Demo: original idea gets scored, improved, and re-ranked.
  - Validation: backtest versus qualitative baselines.
  - Close: Denario should not just write papers; it should know which paper is worth writing.
- Rewrite demo voiceover around the scorecard:
  - Literature map appears.
  - Metric bars fill.
  - Weaknesses are traced to papers.
  - Variants appear.
  - Original is dominated by improved variants.
  - Strategy memo recommends the next hypothesis.
- Prepare Q&A:
  - "Why is this better than a single LLM review?"
  - "How are the metrics computed?"
  - "How do you avoid Goodhart's law?"
  - "How do you prevent future-data leakage in validation?"
  - "Where does this plug into Denario?"
- Coordinate with Felix on visual timing and fallback screen recording.
- Make sure group emulation is described only as an optional generator-side frontend concept.

**Prompt for your AI**

```text
I am the presentation lead for a hackathon project called MAgent4Science.
We have refocused the project into a quantitative Idea Hater for Denario.

Denario can generate candidate research ideas and papers. Our system sits
between idea generation and paper generation. It evaluates a hypothesis using
literature-grounded quantitative metrics, explains the weaknesses, generates
improved variants, re-scores those variants, and recommends which version
Denario should pursue.

The scorecard includes novelty, saturation, conflict risk, feasibility, volume,
velocity, reach, depth, disruption, translation, and evidence quality. We will
validate by backtesting historical 2018 papers using only pre-publication data
and comparing predictions with 2024 outcomes.

Help me write:
1. A 5-minute pitch script.
2. A 7-slide deck outline.
3. A 90-second live demo voiceover.
4. A Q&A crib sheet for academic judges.

Tone: serious, research-focused, concrete, not VC-style.
```

---

## Fred - Orchestration And Pipeline Refactor

**Owner outcome:** `python run.py "hypothesis"` executes the quantitative Idea
Hater pipeline end to end with mock data first, then real agents as they land.

**Tasks**

- Refactor `backend/pipeline.py` away from group emulation as the main path.
- New core node order:
  1. `parser`
  2. `cartographer`
  3. parallel metric scorers:
     - `novelty_scorer`
     - `saturation_scorer`
     - `conflict_scorer`
     - `feasibility_scorer`
     - `impact_forecaster`
     - `evidence_quality_scorer`
  4. `score_aggregator`
  5. `mutator`
  6. variant re-scoring batch
  7. `ranker` / `pareto_curator`
  8. `strategist`
- Keep all nodes async.
- Keep Langfuse tracing on every node.
- Keep `run.py` as the demo CLI.
- Ensure the pipeline can run with mock stubs even before real agents are ready.
- Remove group-emulator dispatch from the critical path.
- Leave group-emulator files behind an experimental flag only if Felix/Harvey need them for frontend proof of concept.
- Own cache warming and demo-run reliability.

**Prompt for your AI**

```text
I am refactoring a LangGraph pipeline for MAgent4Science. The old pipeline
included group identification and group emulation. That is no longer the core
architecture.

The new product is a quantitative Idea Hater for Denario. It takes a hypothesis,
retrieves literature, scores the idea across quantitative metrics, generates
variants, re-scores variants, ranks them, and returns a strategy memo.

Refactor backend/pipeline.py so the critical path is:
parser -> cartographer -> parallel metric scorers -> score_aggregator ->
mutator -> variant re-scoring -> ranker/pareto_curator -> strategist.

Use mock stubs where real agents are missing. Keep async execution, LangGraph,
and Langfuse tracing. Do not include group emulation on the critical path.
```

---

## Harvey - Quantitative Scoring And Evidence Trace

**Owner outcome:** each score in the Idea Hater dashboard has a defensible
metric, rationale, and evidence trail.

**Tasks**

- Build or specify the scoring agents that replace the old emulator workstream:
  - `novelty_scorer`
  - `saturation_scorer`
  - `conflict_scorer`
  - `evidence_quality_scorer`
- Standardize each scorer on a shared structured contract:
  - `score` from 0 to 100
  - `confidence_low`
  - `confidence_high`
  - `rationale`
  - `evidence_ids`
  - `method`
- Reuse existing material where useful:
  - `backend/agents/cartographer.md`
  - `backend/agents/conflict_detector.md`
  - `backend/agents/overlap_auditor.md`
  - `AgentsIdeas.md` for the earlier novelty and literature-coverage concepts
- Define evidence IDs so every score can point back to papers.
- Build a shared retrieval-and-normalization layer for the four scorers:
  - canonical query from parsed hypothesis
  - OpenAlex result counts and work metadata
  - Semantic Scholar abstracts and cross-source metadata
  - DOI-first deduplication
  - stable source provenance per paper
- Make novelty and saturation quantitative:
  - closest-paper similarity
  - number of near neighbours
  - recent publication velocity
  - concept overlap
  - named overlapping papers
- Implement saturation first as the initial deterministic vertical slice:
  - transform OpenAlex result count into a bounded 0-100 crowding score
  - adjust by recent publication velocity
  - attach top overlapping paper IDs as evidence
  - estimate confidence interval from retrieval-count uncertainty
- Implement novelty second on top of the same normalized paper set:
  - inverse saturation contribution
  - earliest relevant-paper year
  - author / institution concentration
  - limited LLM disambiguation only for ambiguous nearest neighbours
  - estimate confidence interval with bootstrap resampling
- Make conflict risk quantitative:
  - contradiction count
  - severity-weighted conflict score
  - disagreement dimensions
- Implement conflict risk as a hybrid metric:
  - deterministic paper weighting by recency and citations per year
  - bounded abstract-level classification into support / contradiction / unclear
  - disagreement labels for mechanism, population, method, or effect direction
  - confidence interval from weighted support-versus-contradiction uncertainty
- Make evidence quality quantitative:
  - retrieval coverage
  - source agreement between OpenAlex and Semantic Scholar
  - proportion of papers with abstracts
  - recency balance
- Implement evidence quality as a trust score over the evidence base:
  - metadata completeness
  - identifier availability
  - citation-normalized paper quality proxy
  - cross-source agreement
  - optional lightweight study-type classification for only the most relevant papers
  - confidence interval from bootstrap variation and missingness penalties
- Provide realistic mock outputs for Felix's dashboard while real scoring is being built.
- Keep group emulation as optional frontend-only concept:
  - no critical backend dependency
  - no validation dependency
  - clearly labelled as experimental

**Execution order for Harvey's lane**

1. Extend schema and evidence-ID contract.
2. Add retrieval normalization notes to the cartographer handoff.
3. Implement saturation metric specification and mock output.
4. Implement novelty metric specification and mock output.
5. Implement conflict-risk metric specification and mock output.
6. Implement evidence-quality metric specification and mock output.
7. Review calibration assumptions with Fred and Funmi before code freeze.

**Definition of done**

- Each of the four score modules has a documented deterministic core.
- Each score returns 0-100, interval, rationale, evidence IDs, and method tag.
- Every rationale can name the quantities used to compute the score.
- Evidence IDs resolve back to retrieved paper records.
- Mock outputs exist for dashboard integration before full implementation lands.

**Prompt for your AI**

```text
I am building the quantitative scoring layer for MAgent4Science, a Denario Idea
Hater. The old system emphasised group emulation; that is now only an optional
frontend concept. My job is to produce defensible metric scores with evidence.

Build agents for novelty, saturation, conflict risk, and evidence quality.
Each must output a 0-100 score, confidence interval, rationale, and evidence
IDs pointing to retrieved papers.

Use OpenAlex and Semantic Scholar metadata. Prefer deterministic metrics where
possible and use the LLM to explain or classify when needed.
```

---

## Basia - Impact Forecasting, Mutation, Ranking, And Validation

**Owner outcome:** the quantitative claim is credible because forecasts and
variant improvements are backtested.

**Tasks**

- Refactor `impact_forecaster` around the scorecard:
  - Volume
  - Velocity
  - Reach
  - Depth
  - Disruption
  - Translation
- Build the `mutator` so it repairs scorecard weaknesses:
  - low novelty -> cross-pollinate or substitute mechanism
  - high saturation -> narrow or shift scale
  - high conflict -> invert or adjust mechanism
  - low feasibility -> narrow method or reduce dependency risk
- Build `ranker` / `pareto_curator`:
  - compare original and variants across all metrics
  - compute non-dominated variants in code
  - produce dominance explanations
  - expose the original as dominated if a variant improves it
- Build `scripts/backtest.py` or equivalent:
  - sample 20-30 historical papers from 2018
  - retrieve only pre-publication evidence
  - predict scorecard and impact dimensions
  - compare with 2024 outcomes
  - produce Spearman correlations and scatter plots
- Define baselines:
  - single qualitative LLM judgement
  - one-year citation count
  - simple bibliometric regression
  - random / mean baseline
- Export validation data for Felix's dashboard.

**Prompt for your AI**

```text
I am building the forecasting, mutation, ranking, and validation layer for
MAgent4Science, a quantitative Idea Hater for Denario.

I need:
1. An impact forecaster for volume, velocity, reach, depth, disruption, and
   translation.
2. A mutator that generates variants targeted at weak scorecard metrics.
3. A Pareto/ranking module that compares original and variants in code.
4. A historical backtest on 2018 papers using only pre-publication information,
   compared with 2024 outcomes.

The validation must show that quantitative scoring beats a qualitative LLM-only
idea judgement baseline.
```

---

## Felix - Dashboard And Frontend Experience

**Owner outcome:** the live demo makes the quantitative Idea Hater obvious,
auditable, and visually convincing.

**Tasks**

- Build the Streamlit dashboard around the new core product:
  - hypothesis input / Denario idea import
  - literature map
  - quantitative scorecard
  - evidence drawer per metric
  - radar or parallel-coordinates view
  - ranked variants table
  - Pareto frontier plot
  - strategy memo
  - backtest scatter plot
- Do not centre the UI on research-group emulation.
- Use group emulation only as an optional side panel labelled as generator
  extension / proof of concept.
- Make the scorecard the hero:
  - metric bars
  - confidence intervals
  - weak metrics highlighted
  - paper evidence links
- Support mock data from Fred/Harvey immediately, then swap to pipeline output.
- Coordinate with Baron on 90-second demo timing.
- Produce a screen-recorded fallback once the dashboard can complete a mock run.

**Prompt for your AI**

```text
I am building the frontend for MAgent4Science, now refocused as a quantitative
Idea Hater for Denario.

The main screen should show a hypothesis, a literature map, a quantitative
scorecard, evidence for each score, generated variants, a Pareto plot, and a
strategy memo. The goal is to show that the system upgrades Denario's idea
evaluation from qualitative judgement to measurable, auditable scoring.

Group emulation may appear only as a small optional proof-of-concept panel for
the hypothesis generator component, not as part of the core score.
```

---

## Funmi - Schemas, LLM Routing, Glue, And Strategy Memo

**Owner outcome:** all teammates can build against stable schemas and route LLM
calls consistently.

**Tasks**

- Refactor `backend/schemas.py`:
  - add `MetricScore`
  - add `IdeaEvaluation`
  - add `VariantEvaluation`
  - update `StrategyMemo`
  - keep legacy group-emulation schemas only if needed for frontend prototype
- Refactor `backend/model_routing.py`:
  - add new score modules
  - remove group-emulation modules from the core route table
  - keep optional routes under an experimental section if necessary
- Define a shared `call_llm` wrapper if not already present:
  - model routing by agent name
  - structured output support
  - Langfuse tracing
  - high reasoning only for strategist
- Build or update the parser.
- Build the score aggregator:
  - combine metrics into composite score
  - assign verdict
  - identify key strengths and weaknesses
  - keep weighting transparent
- Build the strategist:
  - summarize scorecard
  - recommend original or variant
  - explain trade-offs
  - list next actions for Denario
- Help Fred keep the pipeline coherent as files are renamed.

**Prompt for your AI**

```text
I am the glue engineer for MAgent4Science. The project is now a quantitative
Idea Hater for Denario.

Refactor schemas and model routing away from group emulation and toward
MetricScore, IdeaEvaluation, VariantEvaluation, score aggregation, mutation,
ranking, and strategy memo generation.

The strategist should explain which hypothesis Denario should pursue and why,
using the quantitative scorecard and evidence trail.
```

---

## Immediate Integration Checklist

- [ ] `architecture.md` reflects quantitative Idea Hater as the canonical system.
- [ ] `README.md` matches the new positioning.
- [ ] `backend/schemas.py` has metric/evaluation schemas.
- [ ] `backend/model_routing.py` has new scorer routes.
- [ ] `backend/pipeline.py` removes group emulation from the critical path.
- [ ] Mock end-to-end CLI run works.
- [ ] Dashboard can display mock scorecard and variants.
- [ ] Historical backtest script can run on a small sample.
- [ ] Group emulation is clearly labelled optional and frontend-only.

---

## Shared Vocabulary

Use these phrases:

- Quantitative Idea Hater
- Metric-backed hypothesis steering
- Evidence-grounded scorecard
- Variant improvement and re-ranking
- Denario idea evaluation upgrade
- Traceable literature evidence

Avoid making these the core pitch:

- Audience emulator
- Group trajectory simulator
- Persona reasoning
- Research-group response prediction

Those ideas can appear only as optional frontend extensions.
