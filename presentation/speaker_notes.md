# One-Slide Pitch Notes

## Slide Title

**Q-H8R**

Subtitle: **Quantitative idea-hating for AI-generated science**

## Demo Hypothesis

```text
QITT-compressed multi-scale substructure features with learned topological
embeddings improve cosmological parameter estimation from dark-matter halo
merger trees.
```

Backup hypothesis:

```text
GraphSAGE-learned topology embeddings and QITT compression provide a compact
202-dimensional representation that preserves enough merger-tree structure to
predict Omega_m and sigma_8.
```

## Source Paper

Title: **QITT-Enhanced Multi-Scale Substructure Analysis with Learned
Topological Embeddings for Cosmological Parameter Estimation**

Authors: Denario Astropilotai, Pablo Bermejo, Boris Bolliet, Francisco
Villaescusa-Navarro, Pablo Villanueva Domingo.

Venue: Open Conference of AI Agents for Science 2025.

Local assets:

- `denario_qitt_paper.pdf`
- `openreview_reviews.json`
- `openreview_review_summary.md`

## Two-Minute Pitch

Start by pasting or selecting the Denario-paper hypothesis and pressing run.

"This hypothesis comes from an actual Denario-authored Agents4Science paper:
QITT-compressed substructure and topology features for cosmological parameter
estimation from dark-matter merger trees.

Denario is powerful because it can generate research ideas and turn them into
papers. But that creates a harder upstream problem: if you can generate many
plausible ideas, which one should you trust enough to write?

Our project is a quantitative Idea Hater for Denario. The original paper was
accepted, but the reviews also exposed exactly the kind of weaknesses Denario
needs to catch earlier: limited improvement over simple aggregate baselines,
methodological inconsistencies, leakage concerns, missing ablations, and weak
uncertainty reporting.

While the demo runs, the system retrieves nearby literature and turns those
review-style concerns into a scorecard: novelty, saturation, conflict risk,
feasibility, volume, velocity, reach, depth, disruption, translation, and
evidence quality. Every score is tied back to evidence, so the judgement is
inspectable rather than rhetorical.

Then it improves the hypothesis. If the QITT claim is too broad, it can narrow
it to sigma_8 where the method may be more useful. If the complexity is not
justified, it can demand PCA, end-to-end GNN, and aggregate-feature ablations.
If leakage is a risk, it can mutate the method around stricter simulation-level
splits.

Each variant is re-scored with the same metrics, so we rank the original
against stronger versions rather than relying on taste.

The validation is historical: we backtest on 2018 papers using only information
available before publication, then compare our predictions with 2024 outcomes.

The point is simple: Denario should not just write papers. It should know which
paper is worth writing."

## 20-Second Backup

"This demo uses a real Denario-authored Agents4Science paper. It was accepted,
but reviews still found weaknesses: complexity, ablations, leakage risk, and
uncertainty. Our system turns that judgement into a quantitative scorecard,
mutates the hypothesis into stronger variants, re-scores them, and tells
Denario which version is worth writing."

## Technical Pillars

- **Literature retrieval:** We map the hypothesis onto nearby papers from
  OpenAlex and Semantic Scholar.
- **Metric scorecard:** We score novelty, saturation, conflict risk,
  feasibility, impact, and evidence quality.
- **Hypothesis mutation:** We generate variants that target the weakest metrics.
- **Ranking:** We re-score variants and select the strongest trade-offs.
- **Validation:** We backtest on historical papers with strict pre-publication
  date filtering.

## Q&A

**Why is this better than a single LLM review?**  
A single LLM review is hard to audit. Our system decomposes the judgement into
separate metrics, attaches evidence to each score, and reuses the same scoring
logic across variants and backtests.

**How are the metrics computed?**  
Some metrics are deterministic from literature metadata, such as near-neighbour
density, citation velocity, concept spread, and evidence coverage. LLMs are used
for bounded classification and explanation, not as the only source of truth.

**Why this Denario paper as the demo case?**  
It is ideal because it was accepted while still receiving concrete technical
criticisms. That lets us show the core product: not rejecting ideas blindly, but
turning review weaknesses into measurable repairs.

**How do you avoid Goodhart's law?**  
We do not optimize one score. The system exposes multiple metrics, confidence,
and trade-offs, then uses Pareto ranking so a variant cannot win by gaming a
single dimension while collapsing elsewhere.

**How do you prevent future-data leakage in validation?**  
The backtest uses 2018 papers and restricts retrieval to information available
before publication. Outcomes are then compared against 2024 evidence only after
prediction.

**Where does this plug into Denario?**  
It sits between idea generation and paper generation. Denario proposes candidate
hypotheses; Q-H8R scores, improves, and ranks them before Denario
commits to writing.

## Demo Checklist

- Freeze exact Denario-paper hypothesis.
- Freeze one backup hypothesis.
- Warm the literature cache for both hypotheses.
- Test the live run from a clean terminal.
- Open `presentation/one_slide.html` in a browser.
- Keep a screenshot or recording of a completed run ready.
