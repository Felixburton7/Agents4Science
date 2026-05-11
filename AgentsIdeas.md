Core agent roles and metrics
I’d structure the panel roughly like this, with each agent owning one metric:

1. Literature‑Coverage Agent (“What already exists?”)

Uses RAG over arXiv/Semantic Scholar to pull the closest existing work to the hypothesis.

Outputs:

A short list of most similar papers.

A textual judgement: “This is basically X with minor Y twist” vs. “Combines A and B with no obvious close analogue.”

Mirrors Chain‑of‑Ideas / CoI‑style agents that explicitly organise prior work to judge where a new idea sits in the landscape.

2. Novelty Agent (“How new is it?”)

Consumes the hypothesis + the retrieved papers.

Rates novelty on a discrete scale (e.g., 1–5) and explains which parts are actually new vs. rephrasings.

You can draw on Deep Ideation–style critic engines that evaluate novelty vs. feasibility in generated ideas.

3. Citation‑Potential Agent (“Will anyone care?”)
Two implementation tiers:

Simple hackathon tier:

Prompt an LLM with the hypothesis + retrieved similar works + some priors (“transformer architectures in 2017 got big; incremental tweaks to dead areas don’t”) to rate expected impact / citations qualitatively: low / medium / high, with justification.

Fancy tier (if you prep beforehand):

Use a small citation‑prediction model or heuristic inspired by HLM‑Cite / recent “predict highly cited papers” work, where embeddings + an LLM reason about similarity to historically highly cited papers and hot topics.

4. Methodology/Soundness Agent (“Is this scientifically sane?”)

Checks whether the hypothesis is well‑formed, testable, and aligned with the available data or methods.

Inspired by PaperEval‑type multi‑agent evaluation of scientific quality (soundness, clarity, contribution).

5. Feasibility & Risk Agent (“Could a PhD student actually do this?”)

Comments on required resources, data availability, time‑to‑prototype, and major risks.

This draws on findings that LLM ideas tend to be more novel but weaker on feasibility, so an explicit feasibility critic is valuable.

6. Meta‑Reviewer / Panel Chair Agent

Aggregates scores and rationales from the above agents.

Produces:

A short “panel decision” (accept / borderline / reject).

A one‑paragraph review summarising impact, novelty, overlap, and feasibility.

Very close to what multi‑agent “paper evaluation” systems like PaperEval and VirSci do.

