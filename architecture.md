# Quantitative Idea Hater - Architecture

**One-liner:** Take a Denario-generated or user-written research hypothesis,
score it against quantitative evidence from the literature, explain what is
weak, generate stronger variants, and rank those variants with reproducible
metrics.

**Positioning:** Denario can generate candidate research ideas. MAgent4Science
upgrades the "Idea Hater" layer from qualitative judgement to metric-backed
hypothesis steering.

---

## Product Focus

The core system is no longer a research-group emulator. The core system is a
quantitative evaluator and improver for scientific hypotheses.

The user flow is:

1. Denario or a researcher proposes a hypothesis.
2. MAgent4Science retrieves the relevant literature neighbourhood.
3. The hypothesis is scored across quantitative dimensions.
4. Weaknesses are traced back to papers, metrics, and evidence.
5. The system mutates the hypothesis into improved variants.
6. Variants are re-scored and ranked.
7. A final memo recommends which version Denario should develop further.

Group emulation is retained only as a frontend proof of concept for the
hypothesis generator experience. It can show "who might care about this idea"
or "which labs might respond", but it is not part of the core Idea Hater score,
not required for validation, and not on the critical backend path.

---

## Core Pipeline

```text
                         HYPOTHESIS
                Denario-generated or user-written
                              |
                              v
                     +----------------+
                     | 1. Parser      |
                     +--------+-------+
                              |
                              v
                     +----------------+
                     | 2. Literature  |
                     |    Retriever   |
                     +--------+-------+
                              |
         +--------------------+--------------------+
         |                    |                    |
         v                    v                    v
+----------------+   +----------------+   +----------------+
| 3. Novelty     |   | 4. Saturation   |   | 5. Conflict    |
|    Scorer      |   |    Scorer       |   |    Scorer      |
+--------+-------+   +--------+-------+   +--------+-------+
         |                    |                    |
         +--------------------+--------------------+
                              |
         +--------------------+--------------------+
         |                    |                    |
         v                    v                    v
+----------------+   +----------------+   +----------------+
| 6. Feasibility |   | 7. Impact      |   | 8. Evidence    |
|    Scorer      |   |    Forecaster  |   |    Quality     |
+--------+-------+   +--------+-------+   +--------+-------+
         |                    |                    |
         +--------------------+--------------------+
                              |
                              v
                     +----------------+
                     | 9. Score       |
                     |    Aggregator  |
                     +--------+-------+
                              |
                              v
                     +----------------+
                     | 10. Mutator    |
                     +--------+-------+
                              |
                              v
                   Re-score all variants
                              |
                              v
                     +----------------+
                     | 11. Ranker /   |
                     |     Pareto     |
                     +--------+-------+
                              |
                              v
                     +----------------+
                     | 12. Strategist |
                     +--------+-------+
                              |
                              v
             DASHBOARD + DENARIO INTEGRATION
     scorecard, evidence trace, ranked variants, memo
```

---

## Core Agents And Modules

| # | Module | Model / Method | Input | Output |
|---|---|---|---|---|
| 1 | **Parser** | gpt-5-nano | Raw hypothesis | Structured claim, mechanism, context, population, method |
| 2 | **Literature Retriever / Cartographer** | OpenAlex + Semantic Scholar + gpt-5-nano | Parsed hypothesis | Nearby papers, citation metadata, concepts, clusters |
| 3 | **Novelty Scorer** | Metrics + gpt-5-nano | Hypothesis + nearest papers | Novelty score, closest analogues, novelty explanation |
| 4 | **Saturation Scorer** | Metrics + gpt-5-nano | Paper neighbourhood | Crowding score, overlap papers, whitespace summary |
| 5 | **Conflict Scorer** | Metrics + gpt-5-nano | Hypothesis + papers | Contradiction score, conflicting papers, severity |
| 6 | **Feasibility Scorer** | gpt-5-mini + structured heuristics | Hypothesis + methods evidence | Feasibility score, required resources, risk flags |
| 7 | **Impact Forecaster** | gpt-5-mini + bibliometrics | Hypothesis + evidence | Six-dimensional impact forecast |
| 8 | **Evidence Quality Scorer** | Code + gpt-5-nano | All metric evidence | Confidence score, evidence coverage, missing data |
| 9 | **Score Aggregator** | Code | Metric scores | Composite scorecard and weighted Idea Hater verdict |
| 10 | **Mutator** | gpt-5 | Original hypothesis + weaknesses | Improved variants tagged by mutation operator |
| 11 | **Ranker / Pareto Curator** | Code + gpt-5-nano | Re-scored variants | Ranked list, Pareto set, dominance explanations |
| 12 | **Strategist** | gpt-5, high reasoning | Full scorecard + variants | Final recommendation memo |

The backend should be deterministic where possible. LLM calls should explain,
structure, and synthesize. Metric calculation, ranking, and Pareto selection
should be implemented in code.

---

## Quantitative Scorecard

Every hypothesis receives a metric-backed scorecard. Scores should be reported
on a 0-100 scale, with confidence intervals where appropriate.

| Metric | What it captures | Candidate signals |
|---|---|---|
| **Novelty** | How different the idea is from the nearest prior work | Embedding distance, lexical overlap, closest-paper similarity, concept novelty |
| **Saturation** | How crowded the area already is | Number of near-neighbour papers, recent publication velocity, overlap count |
| **Conflict Risk** | How strongly existing papers challenge the claim | Contradictory findings, disagreement dimensions, severity-weighted conflict count |
| **Feasibility** | Whether the idea can realistically be tested | Availability of data, methods, instruments, timescale, dependency risk |
| **Volume** | Expected total attention | 5-year citation forecast |
| **Velocity** | Expected speed of recognition | First-24-month citation forecast |
| **Reach** | Cross-disciplinary spread | Number and diversity of OpenAlex concepts likely to cite |
| **Depth** | Foundational versus incremental value | Review citations, high-authority citing authors, field-centrality proxies |
| **Disruption** | Whether it may displace prior assumptions | CD-index proxy, conflict with dominant clusters, backward citation pattern |
| **Translation** | Real-world uptake potential | Patent, policy, clinical, industrial, or standards-adjacent signals |
| **Evidence Quality** | How much to trust the scorecard | Retrieval coverage, source agreement, recency balance, confidence calibration |

The Idea Hater verdict should not be a single opaque number. The dashboard
should show the composite score alongside the contributing metrics and the
evidence behind each score.

---

## Hypothesis Mutation And Improvement

The Mutator converts the scorecard into concrete improvement operations. It
does not generate ideas in the abstract; it repairs weaknesses identified by
the quantitative evaluation.

Seven mutation operators:

1. **Generalise** - broaden population, setting, or domain.
2. **Narrow** - focus on a sharper context, subgroup, or mechanism.
3. **Substitute mechanism** - keep the outcome but change the causal pathway.
4. **Shift scale** - move between in vitro / in vivo, acute / chronic, local / systemic.
5. **Cross-pollinate** - import a method or framing from an adjacent field.
6. **Invert** - test the null, opposite, or boundary condition directly.
7. **Combine** - fuse with an adjacent open question.

Each variant is re-scored by the same quantitative pipeline. The Ranker then
selects variants using:

- Composite score improvement over the original.
- Pareto dominance across the metric set.
- Evidence quality and uncertainty.
- Practical feasibility.
- A short explanation of what trade-off each variant makes.

---

## Group Emulation Frontend Concept

Group emulation is now explicitly out of scope for the core backend pipeline.
It can remain as a frontend proof of concept attached to the hypothesis
generator component.

Purpose:

- Make the generator demo feel alive.
- Show possible audiences for a generated idea.
- Visualize which research communities might be interested.
- Suggest future collaboration or competition narratives.

Constraints:

- Do not feed group-emulator outputs into the quantitative Idea Hater score.
- Do not make group emulation part of the validation story.
- Do not block the backend on group identification, groundedness checks, or
  trajectory synthesis.
- Use mock or lightly grounded data if needed for the frontend demonstration.

The legacy backend files for `group_identifier`, `group_emulator`,
`trajectory_synth`, and `groundedness_check` should either be moved behind an
experimental frontend flag or left as non-critical prototype stubs.

---

## Model Allocation

| Workload | Model / Method |
|---|---|
| Parsing, classification, extraction | gpt-5-nano |
| Literature explanations and metric rationales | gpt-5-nano |
| Feasibility and impact forecasting | gpt-5-mini |
| Hypothesis mutation | gpt-5 |
| Final strategy memo | gpt-5 with high reasoning |
| Ranking, aggregation, Pareto selection | Code |

The architecture remains provider-agnostic. Model names should be routed
through `backend/model_routing.py`, not hardcoded inside individual agents.

Suggested routing:

```python
MODEL_ROUTING = {
    "parser": "gpt-5-nano",
    "cartographer": "gpt-5-nano",
    "novelty_scorer": "gpt-5-nano",
    "saturation_scorer": "gpt-5-nano",
    "conflict_scorer": "gpt-5-nano",
    "feasibility_scorer": "gpt-5-mini",
    "impact_forecaster": "gpt-5-mini",
    "evidence_quality_scorer": "gpt-5-nano",
    "mutator": "gpt-5",
    "ranker": "gpt-5-nano",
    "strategist": "gpt-5",
}
```

---

## Data Sources

- **OpenAlex API**
  - Papers, concepts, authors, venues, citation counts, references.
  - Date-filtered queries for validation.
  - Concept diversity and field-spread signals.
- **Semantic Scholar API**
  - Paper search, abstracts, citation counts, authors, external IDs.
  - Fallback and cross-check for OpenAlex retrieval.
- **Local cache**
  - SQLite cache keyed by query hash.
  - Required for repeatable demos and validation runs.

No code execution sandbox is required. The pipeline evaluates hypotheses and
literature metadata; it does not execute arbitrary generated code.

---

## Validation

The validation story should prove that the quantitative Idea Hater is more
useful than a qualitative LLM judgement.

Backtest harness:

- Sample historical papers from 2018 across computer science, biology, and
  materials.
- Convert each abstract into a pre-publication hypothesis.
- Restrict retrieval to information available before publication.
- Predict the scorecard and impact dimensions.
- Compare against 2024 outcomes.
- Report Spearman correlation per measurable dimension.

Baselines:

- Single qualitative LLM judgement.
- One-year citation count.
- Simple bibliometric regression.
- Random or mean-field baseline for sanity checking.

Primary validation outputs:

- Predicted-versus-actual scatter plots.
- Correlation table by metric.
- Calibration plot for confidence intervals.
- Example cases where mutation improves the scorecard.

Critical rule: date filtering is non-negotiable. The system must not see
post-publication evidence during historical prediction runs.

---

## Dashboard

The dashboard should sell the quantitative upgrade clearly.

Core Idea Hater panels:

- Hypothesis input or Denario idea import.
- Literature map with nearest papers and evidence links.
- Quantitative scorecard with 0-100 metric bars.
- Radar or parallel-coordinates plot across metrics.
- Evidence drawer for each score.
- Ranked variants table.
- Pareto frontier plot.
- Final strategy memo.
- Backtest scatter plot as the credibility anchor.

Optional generator-side concept:

- Research-group interest mockup or proof of concept.
- Kept visually separate from the Idea Hater scorecard.
- Labelled as an extension concept, not a validated backend signal.

---

## Performance Targets

| Metric | Target |
|---|---|
| End-to-end latency for demo run | <= 90 seconds |
| LLM calls per original hypothesis | 15-30 before variants |
| Variants generated per run | 5-7 |
| OpenAlex / Semantic Scholar calls | 20-40 with cache |
| Demo cost per run | Low enough for repeated live runs |
| Backtest size for hackathon | 20-30 papers if time-constrained |

Parallelize independent score modules from the start. Do not put optional group
emulation on the critical path.

---

## Build Order

1. Refactor schemas around quantitative `MetricScore`, `IdeaEvaluation`,
   `VariantEvaluation`, and `StrategyMemo`.
2. Get an end-to-end mock Idea Hater run working from CLI.
3. Implement literature retrieval and caching.
4. Implement novelty, saturation, conflict, feasibility, and evidence-quality
   scoring.
5. Implement impact forecasting and variant re-scoring.
6. Implement mutation, ranking, and Pareto selection.
7. Build the dashboard around scorecard, evidence trace, and ranked variants.
8. Run the historical backtest and produce validation plots.
9. Add optional group-emulation frontend proof of concept only if the core path
   is stable.

---

## Demo Arc

1. Denario proposes a candidate hypothesis.
2. Idea Hater maps the nearby literature.
3. Quantitative scorecard fills in: novelty, saturation, conflict risk,
   feasibility, impact, and evidence quality.
4. The system highlights why the idea is weak or promising.
5. Mutator generates improved variants targeted at the weak metrics.
6. Variants are re-scored with the same quantitative pipeline.
7. Pareto frontier reveals which variants dominate the original.
8. Strategy memo recommends the best next hypothesis for Denario.
9. Backtest plot stays visible as the credibility anchor.

Optional frontend flourish: a separate "who might care" panel can show mock
research-group reactions for the generator component, but the pitch should make
clear this is not the validated quantitative Idea Hater.

---

## What This Is Not

- Not a paper writer.
- Not a peer reviewer.
- Not a raw citation-count predictor.
- Not a research-group simulator as the main product.
- Not a single qualitative LLM opinion.

MAgent4Science is the quantitative steering layer between idea generation and
paper generation. It tells Denario which hypotheses are weak, why they are
weak, and how to make them stronger.
