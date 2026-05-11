# Hypothesis Steering Engine — Architecture

**One-liner:** Take a researcher's hypothesis, map it onto the live literature, predict its multi-dimensional impact, simulate how real research groups in the field would respond and where they'd take it next, then mutate it into Pareto-optimal variants.

**Positioning:** Denario generates papers from data. We help researchers pick which paper is worth writing.

---

## Pipeline

```
                          USER HYPOTHESIS (text)
                                   │
                                   ▼
                          ┌────────────────┐
                          │  1. PARSER     │   gpt-5-nano
                          └────────┬───────┘
                                   ▼
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
      ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
      │ 2. CARTO-    │    │ 3. CONFLICT  │    │ 4. OVERLAP   │
      │    GRAPHER   │    │   DETECTOR   │    │   AUDITOR    │
      └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
             └────────────────────┼────────────────────┘
                                  │  gpt-5-nano (parallel)
                                  │  ← OpenAlex API
                                  ▼
                         ┌────────────────┐
                         │ 5. GROUP       │   gpt-5-nano
                         │  IDENTIFIER    │
                         └────────┬───────┘
                                  ▼
                    ┌──────────────────────────────┐
                    │  6. GROUP EMULATORS (×8–12)  │   gpt-5-mini
                    │     parallel, grounded       │
                    └──────────────┬───────────────┘
                                   ▼
                          ┌────────────────┐
                          │ 7. TRAJECTORY  │   gpt-5
                          │   SYNTHESISER  │
                          └────────┬───────┘
                                   ▼
                          ┌────────────────┐
                          │ 8. IMPACT      │   gpt-5-mini
                          │   FORECASTER   │   (6 dims, structured)
                          └────────┬───────┘
                                   ▼
                          ┌────────────────┐
                          │  9. MUTATOR    │   gpt-5
                          └────────┬───────┘   (7 mutation operators)
                                   │
                                   │  per variant ▼
                          ┌────────────────┐
                          │ Re-score via   │   gpt-5-mini
                          │ Forecaster     │   (parallel batch)
                          └────────┬───────┘
                                   ▼
                          ┌────────────────┐
                          │ 10. PARETO     │   code + 1 LLM call
                          │     CURATOR    │   (gpt-5-nano)
                          └────────┬───────┘
                                   ▼
                          ┌────────────────┐
                          │ 11. STRATEGIST │   gpt-5 (reasoning high)
                          └────────┬───────┘
                                   │
            ┌──────────────────────┘
            ▼
   ┌────────────────┐
   │ 12. GROUNDED-  │   gpt-5-nano
   │     NESS CHECK │   (runs alongside emulators)
   └────────────────┘

                                   ▼
                         DASHBOARD (Streamlit + Plotly + cytoscape.js)
                         literature map • radar • Pareto plot • memo
```

---

## The 12 Agents

| # | Agent | Model | Input | Output |
|---|---|---|---|---|
| 1 | **Parser** | gpt-5-nano | Raw hypothesis text | `{claim, mechanism, context, population, method}` |
| 2 | **Cartographer** | gpt-5-nano | Parsed hypothesis + OpenAlex | ~50 nearest papers, clustered |
| 3 | **Conflict Detector** | gpt-5-nano | Paper cluster | List of contradicting papers with dimension of disagreement |
| 4 | **Overlap Auditor** | gpt-5-nano | Paper cluster | Crowding score 0–100 + named overlapping papers |
| 5 | **Group Identifier** | gpt-5-nano | Paper cluster authors via OpenAlex | 8–12 named research groups + co-authorship grounding |
| 6 | **Group Emulator** (×N) | gpt-5-mini | Hypothesis + group's last 20 papers | `{interest_score, engagement_type, proposed_direction, method_they_use, time_to_publish, competitive_risk}` |
| 7 | **Trajectory Synthesiser** | gpt-5 | All group outputs | 2–4 field-response scenarios |
| 8 | **Impact Forecaster** | gpt-5-mini | All upstream signals | 6-dim impact profile with confidence intervals |
| 9 | **Mutator** | gpt-5 | Hypothesis + literature map | 5–7 variants, each tagged with which operator was applied |
| 10 | **Pareto Curator** | code + gpt-5-nano | All variants with impact scores | Non-dominated set + dominance explanations |
| 11 | **Strategist** | gpt-5 (reasoning high) | Everything | Final strategy memo with recommendation |
| 12 | **Groundedness Checker** | gpt-5-nano | Group emulator outputs vs. their actual papers | Boolean + flagged inconsistencies |

**Runtime instance count:** 12 distinct roles, ~20 agent instances per run (emulator multiplied).

---

## Six Impact Dimensions

| Dimension | What it captures | Ground truth (for backtest) |
|---|---|---|
| **Volume** | Total attention | Citations at 5y |
| **Velocity** | Speed of recognition | Citations in first 24 months |
| **Reach** | Cross-disciplinary spread | Number of distinct OpenAlex concepts citing it |
| **Depth** | Foundational vs. incremental | h-index of citing authors; cited by reviews |
| **Disruption** | Displaces prior work? | CD-index (Funk & Owen-Smith / Wu et al. *Nature* 2019) |
| **Translation** | Real-world uptake | Citations from clinical trials, patents, policy |

---

## Seven Mutation Operators

1. **Generalise** — broaden population (mice → humans)
2. **Narrow** — focus context (general → early-stage disease)
3. **Substitute mechanism** — same outcome via different pathway
4. **Shift scale** — acute ↔ chronic, in vitro ↔ in vivo
5. **Cross-pollinate** — apply method from adjacent field
6. **Invert** — test the null aggressively
7. **Combine** — fuse with adjacent open question

Each operator is a prompt template the Mutator applies.

---

## Model Allocation (GPT-5 family, tiered)

- **gpt-5-nano** — bulk parallel literature reasoning, structured extraction, lightweight verification (agents 1–5, 10, 12)
- **gpt-5-mini** — grounded persona reasoning and calibrated forecasting (agents 6, 8, variant re-scoring)
- **gpt-5** — creative synthesis and strategic reasoning (agents 7, 9, 11). Reasoning mode (`reasoning_effort="high"`) enabled for Strategist only.

The architecture is **provider-agnostic**: models route via a single config table. When Claude / Gemini keys arrive, swap models per agent without changing the pipeline. Plan: emulators → Claude Sonnet, parallel light agents → Gemini Flash. One-line swap each.

---

## Routing Config

```python
MODEL_ROUTING = {
    "parser":              "gpt-5-nano",
    "cartographer":        "gpt-5-nano",
    "conflict_detector":   "gpt-5-nano",
    "overlap_auditor":     "gpt-5-nano",
    "group_identifier":    "gpt-5-nano",
    "group_emulator":      "gpt-5-mini",
    "trajectory_synth":    "gpt-5",
    "impact_forecaster":   "gpt-5-mini",
    "mutator":             "gpt-5",
    "pareto_curator":      "gpt-5-nano",
    "strategist":          "gpt-5",  # reasoning_effort="high"
    "groundedness_check":  "gpt-5-nano",
}
```

---

## Data Sources

- **OpenAlex API** (free, no key required; use email in headers for polite pool)
  - Papers, abstracts, citations, authors, concepts
  - Co-authorship graph (for Group Identifier)
  - Date-filtered queries (critical for backtest integrity)
- **Semantic Scholar API** (fallback for full-text where OpenAlex is thin)

**Caching:** All OpenAlex pulls cached locally by query hash. Demo runs with warm cache.

---

## Validation

**Backtest harness:**
- 200 papers from 2018, sampled across CS / bio / materials (drop to 30 if time-constrained)
- All data sources date-filtered to pre-publication
- Predict 6 dimensions; compare to actual 2024 outcomes
- Report Spearman correlation per dimension
- Three baselines: citation-at-1-year, single GPT-5 call, linear regression on bibliometric features

**Scatter plot of predicted vs. actual** is the permanent credibility anchor in the dashboard corner.

**Groundedness audit:** for the audience emulator, verify each group's proposed direction uses methods that appear in their actual paper history. Reject and re-prompt if not.

---

## Stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph (state machine, native parallel branches) |
| LLM provider | OpenAI (GPT-5 family) |
| Tracing | Langfuse, wrapping every node |
| Frontend | Streamlit + Plotly + cytoscape.js |
| Caching | Local SQLite for OpenAlex responses |
| Sandbox | Not needed — no code execution in this pipeline |

---

## Performance Targets

| Metric | Target |
|---|---|
| End-to-end latency (demo) | ≤ 120 seconds |
| LLM calls per run | ~55–70 |
| OpenAlex calls per run | ~30–40 |
| Cost per run | $0.15–0.40 |
| Cost of 200-paper backtest | ~$30–50 |

**Mandatory:** parallelise from the start (LangGraph parallel branches). Don't build sequential first. Reasoning mode is expensive — restrict to the Strategist only.

---

## Build Order (priority — drop in reverse if time-constrained)

1. **End-to-end skeleton with one demo hypothesis** — non-negotiable
2. **Audience emulator with 4 grounded groups + Trajectory Synthesiser** — the signature feature
3. **Mutation + Pareto curation** — the steering loop
4. **Dashboard with literature map and reveal animations**
5. **Historical backtest on 30 papers + scatter plot** — start before lunch, runs unattended

---

## Demo Arc (60–120 seconds)

1. Hypothesis goes in (audience-supplied or pre-prepared)
2. Literature map blooms (50 papers, colour-coded by conflict / overlap / support)
3. Research-group portraits light up around the periphery, interest scores fill
4. Each group's proposed direction radiates outward as arrows from the centre
5. Race-condition and white-space flags appear
6. Six-dimension radar chart fills
7. Mutator spawns variants as satellites on the map
8. Pareto frontier highlights — original hypothesis crossed out as dominated
9. Strategy memo appears

Backtest scatter plot stays in the corner throughout as the credibility anchor.

---

## What This Is Not

- Not a hypothesis generator (Denario does that)
- Not a paper writer (Denario does that too)
- Not a peer reviewer
- Not a citation count predictor (we explicitly refuse to collapse impact to one number)

This system sits **strictly upstream** of Denario and complements it. Output can be piped directly into Denario's idea module as a steered, ranked input.
