# Speaker Notes — Q-H8R

## Demo hypothesis

```
QITT-compressed multi-scale substructure features with learned topological
embeddings improve cosmological parameter estimation from dark-matter halo
merger trees.
```

Backup:

```
GraphSAGE-learned topology embeddings and QITT compression provide a compact
202-dimensional representation that preserves enough merger-tree structure to
predict Omega_m and sigma_8.
```

---

## Baron — intro (30–45 sec)

> Paste the hypothesis and start the demo before speaking.

"Denario can generate research ideas and turn them into papers — that's
powerful. But it creates a harder upstream problem: if you can generate
hundreds of plausible hypotheses, which one is actually worth writing?

This is a real paper authored by Denario. It was accepted. But the reviews
still flagged concrete weaknesses — complexity, ablations, leakage risk.
Q-H8R is designed to catch those before Denario commits to writing.

I'll hand over to the team to walk through how it works."

---

## Backend team — technical walkthrough (75–90 sec)

**Suggested beats — distribute across the team:**

1. **Literature retrieval** — we map the hypothesis onto nearby papers from
   OpenAlex and Semantic Scholar, cached locally for reproducibility.

2. **Scorecard** — the system produces a 0–100 score across novelty,
   saturation, conflict risk, feasibility, impact, and evidence quality.
   Every score links back to the papers that drove it.

3. **Mutation** — we target the weakest metrics and generate hypothesis
   variants: narrow the claim, substitute the mechanism, cross-pollinate
   from adjacent fields, or demand stricter ablations.

4. **Ranking** — variants are re-scored by the same pipeline. Pareto
   selection picks the strongest trade-offs — no single number to game.

5. **Validation** — we backtest on 2018 papers using only pre-publication
   information, then compare predictions against 2024 outcomes. Spearman
   correlations, predicted-vs-actual plots. This is what beats a single
   LLM opinion.

---

## Q&A

**Why better than a single LLM review?**
Decomposed metrics, evidence attached to every score, same logic reused
across variants and backtests — auditable, not rhetorical.

**How are metrics computed?**
Deterministic where possible (near-neighbour density, citation velocity,
concept spread). LLMs handle bounded classification and explanation only.

**How do you avoid Goodhart's law?**
Multiple metrics + Pareto ranking. A variant can't win by gaming one
dimension while collapsing elsewhere.

**Where does this plug into Denario?**
Between idea generation and paper generation. Denario proposes; Q-H8R
scores, repairs, and ranks before Denario commits to writing.

---

## Demo checklist

- [ ] Hypothesis pasted and cache warmed
- [ ] Live run tested from clean terminal
- [ ] `one_slide.html` open in browser, full-screen
- [ ] Screenshot/recording of completed run ready as backup
