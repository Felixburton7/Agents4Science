# OpenReview Demo Paper Summary

## Paper

**Title:** QITT-Enhanced Multi-Scale Substructure Analysis with Learned
Topological Embeddings for Cosmological Parameter Estimation

**Authors:** Denario Astropilotai, Pablo Bermejo, Boris Bolliet, Francisco
Villaescusa-Navarro, Pablo Villanueva Domingo

**Venue:** Open Conference of AI Agents for Science 2025

**OpenReview ID:** `LENY7OWxmN`

**Local files:**

- `denario_qitt_paper.pdf`
- `openreview_reviews.json`

## Demo Hypothesis

QITT-compressed multi-scale substructure features with learned topological
embeddings improve cosmological parameter estimation from dark-matter halo
merger trees.

## Why This Is A Good Demo Case

The paper is useful because it is neither obviously bad nor uncritically strong.
It was accepted, but reviews and checks identified concrete repair targets:

- The QITT/GNN combination is novel and technically interesting.
- Simple aggregate features reportedly outperform the proposed method for
  `Omega_m`, weakening the practical claim.
- Reviewers ask for stronger ablations, including PCA, end-to-end GNNs, and
  runtime/resource comparisons.
- Correctness checks flag internal inconsistencies around tensor reshaping,
  feature dimensionality, substructure thresholds, GNN architecture, and
  hyperparameter tuning.
- There are leakage concerns around GNN pretraining and train/test simulation
  separation.
- Statistical reporting needs uncertainty estimates and multiple-comparison
  corrections.
- A related-work check reported no hallucinated references.

## Suggested Mutations

- Narrow the claim to `sigma_8`, where fine-grained substructure information may
  be more valuable than global aggregates.
- Add a strict ablation requirement: QITT versus PCA, autoencoder compression,
  end-to-end GNN, and aggregate-feature baselines.
- Replace the broad "QITT improves parameter estimation" claim with a more
  testable claim about compactness under equal predictive performance.
- Add leakage-proof pretraining: train GraphSAGE only on training simulations
  and freeze all preprocessing before test evaluation.
- Add robustness analysis over tensor ordering, truncation, padding, and TT
  rank settings.

## Pitch Use

Use this paper to show that MAgent4Science is not just a rejection machine. It
takes a promising Denario idea, identifies measurable weaknesses, and proposes a
better version of the hypothesis before paper generation.
