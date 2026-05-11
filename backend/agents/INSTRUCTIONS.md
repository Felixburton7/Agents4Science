EACH SECTION OF THE PROMPT SHOULD START WITH <{name of section}> AND END WITH </{name of section}>

Make sure agent prompts are clear and concise.

Specific instructions to the agents must be capitalised, for example 'you MUST do' and 'DO NOT'.

Each agent should have their own md prompt file.

All quantitative scoring agents MUST follow one shared output contract wherever applicable:

- `score` on a 0-100 scale.
- `confidence_low` and `confidence_high` on the same 0-100 scale.
- `rationale` explaining the evidence and formula used.
- `evidence_ids` pointing to retrieved papers.
- `method` naming the scoring procedure or version.

Evidence IDs MUST be stable across reruns. Prefer:

1. DOI.
2. OpenAlex work ID.
3. Semantic Scholar paper ID.

Agents MUST prefer deterministic metrics and code-computable signals where possible.

LLMs MUST be used only where they add clear value, such as:

- structuring a hypothesis for retrieval
- classifying support versus contradiction from abstracts
- disambiguating ambiguous near-neighbour matches
- explaining a computed score in plain language

Agents MUST NOT fabricate papers, identifiers, counts, citations, or confidence intervals.

Agents that consume retrieved literature MUST preserve source provenance and missingness so downstream scorers can reason about source agreement and evidence quality.
