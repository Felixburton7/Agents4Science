# 🧪 MAgent4Science

<p align="center">
  <a href="https://science.ai.cam.ac.uk/events/hackathon-multi-agent-systems-for-scientific-research">
    <img alt="Cambridge–Infosys Hackathon 2026" src="https://img.shields.io/badge/Cambridge--Infosys-Hackathon%202026-0a66c2?style=for-the-badge" />
  </a>
</p>

<sub>🥇 1st place at the [Cambridge–Infosys Hackathon 2026](https://science.ai.cam.ac.uk/events/hackathon-multi-agent-systems-for-scientific-research) · built on top of [Denario](https://github.com/AstroPilot-AI/Denario).</sub>

MAgent4Science is a quantitative **Idea Hater** for [Denario](https://github.com/AstroPilot-AI/Denario). It evaluates
scientific hypotheses with literature-grounded metrics, explains what is weak,
generates improved variants, and ranks those variants before Denario commits to
writing a paper from them.

[Denario](https://github.com/AstroPilot-AI/Denario) can generate candidate research ideas. MAgent4Science helps decide
which ideas are worth developing.

## 🎯 What The System Does

Given a Denario-generated or user-written hypothesis, MAgent4Science produces:

- A structured parse of the claim, mechanism, context, population, and method.
- A literature neighbourhood from OpenAlex and Semantic Scholar.
- Quantitative scores for novelty, saturation, conflict risk, feasibility,
  impact, and evidence quality.
- Evidence links showing which papers support each score.
- A verdict on whether the idea should be rejected, revised, pursued, or
  strengthened.
- Mutated hypothesis variants targeted at the weakest metrics.
- Re-scored variants ranked against the original.
- A Pareto frontier showing which variants dominate others.
- A final strategy memo recommending the next hypothesis Denario should pursue.

The goal is to upgrade Denario's qualitative idea evaluation into a measurable,
auditable, and repeatable hypothesis steering layer.

## 🏗️ Core Architecture

The canonical architecture is defined in [architecture.md](architecture.md).

```text
Hypothesis
  -> Parser
  -> Literature Retriever / Cartographer
  -> Quantitative Scorers
       novelty
       saturation
       conflict risk
       feasibility
       impact
       evidence quality
  -> Score Aggregator
  -> Mutator
  -> Variant Re-scoring
  -> Ranker / Pareto Curator
  -> Strategist
  -> Dashboard / Denario integration
```

This replaces the previous research-group-emulation-first architecture. Group
emulation is now only an optional frontend proof of concept for the hypothesis
generator experience, not part of the core Idea Hater score.

## 📊 Quantitative Scorecard

Every hypothesis is evaluated using a transparent 0-100 scorecard.

| Metric | Meaning |
| --- | --- |
| Novelty | How different the hypothesis is from nearest prior work. |
| Saturation | How crowded the surrounding literature already is. |
| Conflict Risk | How strongly existing papers contradict or weaken the claim. |
| Feasibility | Whether the hypothesis can realistically be tested. |
| Volume | Expected total research attention. |
| Velocity | Expected speed of recognition. |
| Reach | Likely cross-disciplinary spread. |
| Depth | Foundational value versus incremental value. |
| Disruption | Potential to displace existing assumptions. |
| Translation | Real-world uptake potential. |
| Evidence Quality | Confidence in the retrieved evidence and scoring basis. |

The system should not hide behind a single opaque number. The composite verdict
is shown alongside metric rationales, confidence intervals, and linked evidence.

## 🧬 Hypothesis Improvement

The Mutator uses scorecard weaknesses to generate better variants. It applies
explicit operators:

- Generalise: broaden the population, setting, or domain.
- Narrow: focus on a sharper context, subgroup, or mechanism.
- Substitute mechanism: keep the outcome but change the causal pathway.
- Shift scale: move between in vitro / in vivo, acute / chronic, local / systemic.
- Cross-pollinate: import a method or framing from an adjacent field.
- Invert: test the null, opposite, or boundary condition directly.
- Combine: fuse with an adjacent open question.

Each variant is evaluated by the same scorecard, then ranked by composite
improvement, Pareto dominance, feasibility, and evidence quality.

## ✅ Validation

The validation plan is designed to prove that the quantitative Idea Hater beats
a single qualitative LLM judgement.

The backtest will:

- Sample historical papers from 2018 across multiple fields.
- Convert abstracts into pre-publication hypotheses.
- Restrict retrieval to information available before publication.
- Predict scorecard and impact metrics.
- Compare predictions with 2024 outcomes.
- Report Spearman correlations and predicted-versus-actual plots.

Baselines include a single qualitative LLM judgement, one-year citation count,
simple bibliometric regression, and random or mean-field baselines.

Date filtering is mandatory. The validation must not leak future evidence into
historical prediction runs.

## 🖥️ Dashboard

The dashboard should make the quantitative upgrade obvious:

- Hypothesis input or Denario idea import.
- Literature map with nearest papers.
- Metric scorecard with confidence intervals.
- Evidence drawer for each score.
- Radar or parallel-coordinates view.
- Ranked variants table.
- Pareto frontier plot.
- Strategy memo.
- Backtest scatter plot as the credibility anchor.

Optional frontend concept: a small "who might care" group-emulation panel can
be shown as a future extension for the hypothesis generator. It should be kept
visually and conceptually separate from the validated Idea Hater scorecard.

## 🛠️ Technical Stack

| Layer | Current / Target choice |
| --- | --- |
| Orchestration | LangGraph |
| Backend | Python 3.11+ |
| Schemas | Pydantic |
| LLM routing | `backend/model_routing.py` |
| Tracing | Langfuse |
| Literature data | OpenAlex and Semantic Scholar |
| Cache | Local SQLite keyed by query hash |
| Dashboard | Streamlit, Plotly, cytoscape.js |

## 🚀 Running The Integrated Demo

The backend exposes an HTTP API in [backend/api.py](backend/api.py) and the
Next.js dashboard in [frontend/](frontend/) calls it from
[frontend/src/lib/demoContext.tsx](frontend/src/lib/demoContext.tsx). Start each
service in its own terminal.

```bash
# Terminal 1 — backend (port 8000)
pip install -r requirements.txt
uvicorn backend.api:app --reload --port 8000

# Terminal 2 — frontend (port 3000)
cd frontend
pnpm install
pnpm dev
```

Then open http://localhost:3000 and click **Run**. The staged animation runs as
before; in parallel the frontend POSTs the hypothesis to
`http://localhost:8000/api/run` and merges the resulting `PipelineState` into
the dashboard. If the backend is offline, the demo falls back to mock data and
logs a warning to the browser console.

To point the frontend at a different host, copy
[frontend/.env.local.example](frontend/.env.local.example) to
`frontend/.env.local` and edit `NEXT_PUBLIC_API_BASE`.

`OPENAI_API_KEY` is required for non-stubbed agents. All agents currently run as
stubs, so the integrated demo works without keys.

## 📦 Repository Status

The repo now contains a backend skeleton under `backend/`, including pipeline
scaffolding, schemas, model routing, tracing, literature tools, and agent prompt
files. The demo CLI runs the quantitative Idea Hater path end to end with mock
data while real agents land.

The immediate scoring implementation priority is the first defensible
quantitative layer:

- `novelty_scorer`
- `saturation_scorer`
- `conflict_scorer`
- `evidence_quality_scorer`

These four modules should share one literature neighbourhood, one evidence-ID
contract, and one structured score format so the dashboard and validation code
can inspect every metric in the same way.

Immediate implementation targets from [team_tasks.md](team_tasks.md):

- Replace mock metric scorer stubs with retrieval-backed implementations.
- Improve score aggregation weights and calibration.
- Connect mutation and variant re-scoring to the real scorecard.
- Build a dashboard around the scorecard, evidence trace, ranked variants, and
  validation plots.
- Build a historical backtest harness.

For the first scoring pass, the working plan is:

1. Normalize OpenAlex and Semantic Scholar records into one paper format.
2. Use DOI-first evidence IDs for reproducible metric traces.
3. Implement deterministic saturation and novelty before hybrid metrics.
4. Use bounded LLM calls only for explanation and abstract-level
   support-versus-contradiction classification.
5. Return every score with rationale, confidence interval, and evidence IDs.

## 🗂️ Repository Layout

```text
.
|-- architecture.md              # Canonical quantitative Idea Hater architecture
|-- team_tasks.md                # Current implementation workstreams
|-- backend/
|   |-- pipeline.py              # LangGraph pipeline skeleton
|   |-- schemas.py               # Pydantic contracts
|   |-- model_routing.py         # Agent-to-model routing
|   |-- agents/                  # Agent prompt specs and stubs
|   `-- tools/                   # Literature APIs and caching
|-- run.py                       # CLI entry point
|-- pyproject.toml
|-- requirements.txt
|-- AgentsIdeas.md               # Earlier concept notes
|-- README.md
`-- LICENCE
```

## 👥 Team

🥇 **Team 17 — Winners, [Cambridge–Infosys Hackathon 2026](https://science.ai.cam.ac.uk/events/hackathon-multi-agent-systems-for-scientific-research)**

- Basia Koch
- Baron Gracias
- Felix Burton
- Fred Lawrence
- Funmi Looi-Somoye
- Harvey Bermingham

## 🙏 Acknowledgements

- The [Cambridge AI for Science](https://science.ai.cam.ac.uk/) programme and Infosys, for hosting the [Multi-Agent Systems for Scientific Research hackathon](https://science.ai.cam.ac.uk/events/hackathon-multi-agent-systems-for-scientific-research).
- The [Denario](https://github.com/AstroPilot-AI/Denario) team — Boris Bolliet, Pablo Villanueva-Domingo, Francisco Villaescusa-Navarro, and collaborators — whose multi-agent scientific research system this project plugs into.

## 📄 Licence

See [LICENCE](LICENCE).
