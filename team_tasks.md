# Team Task Lists + AI Prompts

I've factored in your existing repo. Quick note: your `agents/` folder has some specs that don't 1:1 match the architecture (e.g. `meta-reviewer-panel-chair`, `methodology-soundness`). For speed, the prompts below treat the architecture's 12 agents as canonical and reference the existing files where they map. Anyone whose work overlaps an existing markdown spec should read that file first and reuse or supersede it.

**Critical shared contract (Person 6 publishes this in the first 30 minutes — everyone codes against it):**
- `schemas.py` in repo root with Pydantic models for: `ParsedHypothesis`, `Paper`, `ResearchGroup`, `EmulatorOutput`, `ImpactForecast`, `Variant`, `StrategyMemo`

Everything below assumes this exists. Person 6 — that's your first task before anything else.

---

## Baron — Presentation & Marketing Lead

**Tasks**
- Write the 5-minute pitch script (opening, problem, solution, demo voiceover, validation, close)
- Memorise the opening 30 seconds and the Denario closer word-for-word
- Build the slide deck: title / problem / positioning / architecture / live demo / validation / close
- Storyboard the demo arc with timings — must land in 90 seconds
- Pick the headline demo hypothesis + 2 backups
- Coordinate with Person 5 on demo trigger timing
- Get a screen-recorded fallback of a successful run by 16:00
- Run 3 full rehearsals before 17:00
- Anticipate Q&A: "How is this different from Denario?", "How do you avoid Goodhart?", "Why multi-agent?"

**Prompt for your AI**

```
I'm the presentation and marketing lead for a 7-hour hackathon team building 
a multi-agent system for scientific research. The hackathon is judged on 
originality, technical implementation, systematic validation, traceability, 
explainability, and user experience.

Our project: a 12-agent pipeline that takes a researcher's hypothesis and 
helps them steer it before they commit years to it. It maps the hypothesis 
onto the live scientific literature, predicts its impact across six 
dimensions (volume, velocity, reach, depth, disruption, translation), 
simulates how 8-12 real research groups in the field would respond and 
where they'd take it next, and mutates the hypothesis into Pareto-optimal 
variants. Backtested on 30 papers from 2018 against their 2024 citation 
outcomes.

Positioning: "Denario writes papers from data. We help researchers pick 
which paper is worth writing." (Denario is our professor's existing system 
that generates papers — we sit upstream of it.)

I need you to help me with three deliverables:

1. A 5-minute pitch script with these beats: 30-second opening hook, 
problem framing, our solution, live-demo voiceover, validation story, 
Denario-positioning close. The opening line must be punchy. The close 
must be memorable.

2. A 7-slide deck outline (title, problem, positioning, architecture 
overview, demo placeholder, validation, close). Each slide should have one 
idea, sparse text. Tell me what to put on each.

3. A storyboard for the live demo: a researcher types in a hypothesis, 
then over ~90 seconds the audience sees the literature map bloom, group 
portraits light up with interest scores, proposed directions fan out as 
arrows, the impact radar fills, variants spawn, the Pareto frontier 
reveals, and a strategy memo appears. Tell me exactly what to say during 
each beat.

The audience is academic (Cambridge Accelerate Programme staff, possibly 
the Denario authors) plus Infosys sponsors. Keep it serious-research-toned, 
not VC-pitchy. No fluff words. Lead with the unsolved problem, not the 
technology.

Ask me clarifying questions before drafting if you need to.
```

---

## Fred — Orchestration Lead

**Tasks**
- Set up LangGraph project structure
- Define the shared state object covering all 12 agents
- Stub all 12 agent nodes returning mock data — get end-to-end mock run completing first
- Implement parallel branches (Cartographer/Conflict/Overlap; the N Group Emulators)
- Wrap every node with Langfuse tracing
- Replace stubs with real implementations as teammates finish
- Own the demo-day "run" command and OpenAlex/Semantic Scholar cache warming

**Prompt for your AI**

```
I'm the orchestration lead for a 7-hour hackathon team. We're building a 
12-agent pipeline in LangGraph that helps researchers steer their hypotheses.

Repo structure:
  agents/           (markdown specs per agent — read these for prompts)
  tools/
    semantic_scholar.py  (existing tool)
  schemas.py        (shared Pydantic models — to be created by Person 6)
  architecture.md   (full spec — read this first)

The 12 agents (in execution order):
  1.  Parser              - structures hypothesis text
  2.  Cartographer        - pulls ~50 nearest papers
  3.  Conflict Detector   - finds contradicting work       (parallel with 2, 4)
  4.  Overlap Auditor     - finds work already doing this
  5.  Group Identifier    - clusters real research groups
  6.  Group Emulators ×N  - one per identified group (parallel)
  7.  Trajectory Synth    - clusters group responses into scenarios
  8.  Impact Forecaster   - 6-dim impact prediction
  9.  Mutator             - generates 5-7 variants
  10. Pareto Curator      - filters non-dominated variants
  11. Strategist          - final strategy memo
  12. Groundedness Check  - verifies emulator outputs (side branch from 6)

Tech stack:
- LangGraph for orchestration (parallel branches, state machine)
- OpenAI client (we have GPT-5 family access only for now: gpt-5-nano, 
  gpt-5-mini, gpt-5). Model routing config table in architecture.md.
- Langfuse for tracing — wrap every node call
- Python 3.11+

Your job, in order:

1. Read architecture.md and schemas.py. Confirm the shared schemas exist.

2. Create a LangGraph StateGraph with a state object that holds: 
   raw_hypothesis (str), parsed (ParsedHypothesis), papers (list[Paper]), 
   conflicts, overlaps, groups (list[ResearchGroup]), emulator_outputs, 
   scenarios, forecast (ImpactForecast), variants (list[Variant]), 
   final_memo (StrategyMemo). Define carefully — every agent reads/writes 
   to this state.

3. Stub every one of the 12 nodes as async functions that return mock data 
   matching the schema. Use placeholder strings and obvious-fake numbers. 
   Get the graph compiling and executing end-to-end with all mock data.

4. Wire up the parallel branches correctly: agents 2/3/4 run in parallel; 
   the N group emulators (6) run in parallel; agent 12 is a side branch 
   that runs alongside the trajectory synthesiser.

5. Wrap every node with Langfuse tracing using `@observe()` or equivalent.

6. Build a simple CLI: `python run.py "my hypothesis text"` that runs the 
   pipeline end-to-end and prints the final memo. This is what we'll use 
   on stage.

7. As teammates land real implementations of individual agents, swap out 
   the stubs. Each teammate will commit a file at agents/<name>.py 
   exporting a function with the same signature as the stub.

8. Add a local SQLite cache for all Semantic Scholar / OpenAlex API calls 
   keyed by query hash, so re-runs are instant.

Non-goals: do not write the agent prompts yourself — your teammates own 
those. Your job is the plumbing.

Critical constraint: the graph must execute in under 120 seconds end-to-end 
on the demo. Parallelise everything that can be parallelised. Do not 
build sequential first and parallelise later.
```

---

## Harvey — Audience Emulator Lead

**Tasks**
- Build Group Identifier (cluster authors via Semantic Scholar / OpenAlex)
- Build Group Emulator with grounded persona prompts (last 20 papers each)
- Build Groundedness Checker (verify proposed methods are in actual paper history)
- Build Trajectory Synthesiser (cluster directions into scenarios, flag race conditions)
- Tune prompts on the demo hypothesis for visible, distinctive group outputs

**Prompt for your AI**

```
I'm building the audience emulator subsystem for our hackathon team — the 
signature feature of our project. We help researchers steer their 
hypotheses; my job is to simulate how real research groups in the 
surrounding field would respond to a given hypothesis and where they'd 
take it next.

Repo structure:
  agents/               (markdown specs per agent — read INSTRUCTIONS.md)
  tools/
    semantic_scholar.py (use this for paper/author lookups)
  schemas.py            (shared Pydantic models — read first)
  architecture.md       (full spec — read this first)

I own four agents:

1. Group Identifier (agents/group_identifier.py)
   - Input: list of papers from the literature neighbourhood (~50 papers)
   - Process: extract all authors, build co-authorship graph from their 
     recent publications, cluster into 8-12 distinct research groups 
     (greedy modularity or connected components is fine)
   - LLM step: name each cluster ("the Hassabis group at DeepMind", 
     "the Vaughan lab at UCSF") using gpt-5-nano
   - Output: list[ResearchGroup] where each group has: name, institution, 
     member_authors, recent_papers (last 20 titles + abstracts)

2. Group Emulator (agents/group_emulator.py)
   - Input: a single ResearchGroup + the user's hypothesis
   - This is the GROUNDED PERSONA agent — it must stay tethered to the 
     group's actual publication history. Use gpt-5-mini.
   - System prompt template: "You are a senior researcher in the {name} 
     group at {institution}. Here is your group's recent work: {20 paper 
     titles and abstracts}. A hypothesis has been proposed: {hypothesis}. 
     Based on your actual research history, evaluate it."
   - Structured output (EmulatorOutput in schemas.py): 
     interest_score (1-10), engagement_type (build_on / contradict / 
     ignore / collaborate), proposed_direction (string), 
     method_they_would_use (must reference their actual methods), 
     estimated_time_to_publish (months), competitive_risk_to_user (str)
   - Run in parallel for all N groups via asyncio.gather

3. Groundedness Checker (agents/groundedness_checker.py)
   - Input: an EmulatorOutput + the ResearchGroup it came from
   - Uses gpt-5-nano to check whether the proposed_direction and 
     method_they_would_use are consistent with the group's actual recent 
     papers
   - Output: boolean valid + reason. If invalid, the emulator is 
     re-prompted with explicit feedback.

4. Trajectory Synthesiser (agents/trajectory_synthesiser.py)
   - Input: all N EmulatorOutputs
   - Uses gpt-5 to cluster proposed_directions into 2-4 distinct 
     field-response scenarios
   - Identifies: race conditions (groups proposing similar follow-ups), 
     white space (no group proposing a direction)
   - Output: list of scenarios + race_conditions list + white_space list

Tech:
- Python async/await for parallel emulator calls
- OpenAI client wrapper from Person 6 (handles model routing)
- tools/semantic_scholar.py for author and paper lookups

Critical:
- Groundedness is the single biggest failure mode. If a group "proposes" 
  using methods they've never used, the whole demo falls apart. Test 
  rigorously.
- Test on a real demo hypothesis ASAP and verify the groups identified 
  are real, named, and recognisably distinct.
- Keep emulator prompts strict about citing the group's actual work in 
  the reasoning.

Non-goals: I am not building the literature retrieval (Person 6) or the 
impact forecaster (Person 4). I am not running the orchestration (Person 2).

Read agents/INSTRUCTIONS.md and any existing relevant markdown specs in 
agents/ before starting. Build incrementally — get one emulator working 
end-to-end on one hypothesis before parallelising.
```

---

## Basia — Impact Forecaster & Mutation Lead

**Tasks**
- Pull 30-paper historical backtest dataset from 2018 with 2024 ground truth
- Build Impact Forecaster (6 dimensions, structured output)
- Build Mutator with 7 operators
- Build Pareto Curator (non-dominated set + dominance explanations)
- Run backtest, compute Spearman correlations, produce the scatter plot

**Prompt for your AI**

```
I'm the impact forecasting and mutation lead for our hackathon team. Our 
project helps researchers steer their hypotheses; my job is to predict 
the multi-dimensional impact of a hypothesis and then mutate it into 
better variants.

Repo structure:
  agents/               (markdown specs per agent — note that 
                         citation-potential-agent.md exists; this 
                         supersedes/extends it)
  tools/
    semantic_scholar.py (use this for citation lookups)
  schemas.py            (shared Pydantic models — read first)
  architecture.md       (full spec — read this first)

I own three agents plus the validation harness:

1. Impact Forecaster (agents/impact_forecaster.py)
   - Input: hypothesis + parsed structure + literature context + audience 
     signals (from emulator outputs)
   - Uses gpt-5-mini with structured output
   - Predicts 6 dimensions, each with value + confidence interval:
       * Volume     - total citations at 5y (raw attention)
       * Velocity   - citations in first 24 months (speed of recognition)
       * Reach      - distinct OpenAlex concepts citing it 
                      (cross-disciplinary spread)
       * Depth      - h-index of citing authors, citations from reviews 
                      (foundational vs incremental)
       * Disruption - CD-index proxy (Funk-Owen-Smith / Wu et al. Nature 
                      2019) — does it displace prior work?
       * Translation- citations from clinical trials, patents, policy 
                      (real-world uptake)
   - Output: ImpactForecast object in schemas.py

2. Mutator (agents/mutator.py)
   - Input: original hypothesis + literature context
   - Uses gpt-5 to apply 7 mutation operators and produce 5-7 variants:
       * Generalise        (broaden population)
       * Narrow            (focus context)
       * Substitute        (different mechanism, same outcome)
       * Shift scale       (acute/chronic, in vitro/in vivo)
       * Cross-pollinate   (apply method from adjacent field)
       * Invert            (test the null aggressively)
       * Combine           (fuse with adjacent open question)
   - Output: list[Variant], each tagged with the operator applied
   - After mutation, each variant gets re-scored by the Forecaster 
     (Person 2 handles this routing)

3. Pareto Curator (agents/pareto_curator.py)
   - Input: list of all variants with their 6-dim impact forecasts
   - Algorithm: compute non-dominated set across the 6 dimensions (pure 
     code, no LLM needed)
   - One gpt-5-nano call: for each non-dominated variant, explain in 
     one sentence why it's not dominated and what it trades off
   - Output: Pareto front + dominance explanations

4. Historical Backtest Harness (scripts/backtest.py)
   - Pull 30 papers from 2018 across CS / bio / materials via Semantic 
     Scholar / OpenAlex
   - For each: collect 2018 metadata (abstract, authors, venue) — date 
     filtering CRITICAL, no post-publication info
   - For each: collect 2024 ground truth (total citations, citations by 
     year, fields citing, citing-paper h-indices)
   - Run the full pipeline on each paper's hypothesis (extracted from 
     abstract via gpt-5-nano)
   - Compare predicted 6-dim impact to actual 2024 metrics
   - Compute Spearman correlations
   - Three baselines for comparison: 
       a) raw citation-at-1-year
       b) single GPT-5 call ("predict impact of this paper")
       c) linear regression on bibliometric features (h-index of authors, 
          venue impact factor, abstract length)
   - Produce scatter plot of predicted vs actual for each dimension
   - This scatter plot is our credibility anchor — it MUST be ready 
     before the slides are finalised

Tech:
- OpenAI client wrapper from Person 6 (model routing)
- Use tools/semantic_scholar.py and OpenAlex (free, no key) for citations
- Cache all API calls in a local SQLite — backtest is the longest-running 
  part of the day, do not rerun
- matplotlib or plotly for the scatter plot

Critical:
- DATE FILTERING IS NON-NEGOTIABLE. When running on 2018 papers, the 
  agents must not see any post-2018 information. Pass date filters into 
  every literature query. This is the single thing that will make our 
  validation look credible or fraudulent.
- Start the backtest as soon as the forecaster is working (probably 
  before lunch). It will run unattended for an hour or two.
- Keep the dataset small if needed (drop to 20 papers) rather than 
  rushing and producing noisy results.

Non-goals: I am not building literature retrieval (Person 6) or the 
audience emulator (Person 3) or orchestration (Person 2).

Read agents/citation-potential-agent.md and agents/INSTRUCTIONS.md first.
```

---

## Felix — Dashboard Lead

**Tasks**
- Streamlit skeleton with all panel placeholders
- Literature map with cytoscape.js or vis-network — papers as nodes, hypothesis at centre, bloom animation
- Group portrait cards with interest scores and proposed-direction arrows
- 6-dim impact radar (Plotly)
- 2D Pareto scatter
- Strategy memo panel
- Backtest scatter plot in the corner (from Person 4's data)
- Reveal animations and timing tuned with Person 1
- Dark-mode friendly (projector)
- One-button demo trigger

**Prompt for your AI**

```
I'm the dashboard lead for a 7-hour hackathon team. The judges will watch 
a 5-minute live demo — my work is what they actually see. The visual 
quality of this dashboard is the single biggest determinant of whether 
we win.

Repo structure:
  app/                  (Streamlit app — create this)
  schemas.py            (shared Pydantic models — read first)
  architecture.md       (full spec — read this first, especially the 
                         "Demo Arc" section)

What the demo looks like (60-120 seconds):
1. User types in a hypothesis. The hypothesis displays as a header.
2. Literature map "blooms" in the centre — ~50 papers as small nodes in 
   a force-directed layout, colour-coded green/red/yellow for 
   support/conflict/overlap. The user's hypothesis sits at the centre 
   as a larger node.
3. 8-12 research group portraits light up around the periphery of the 
   map. Each shows the group name, institution, and an interest score 
   (0-10) that animates filling up.
4. Lines from the hypothesis to each group, thickness = interest score.
5. Each group spawns an arrow outward to their "proposed direction" 
   (short text label). Race-condition flags appear where multiple arrows 
   converge.
6. A 6-dimension radar chart fills in (right side): Volume, Velocity, 
   Reach, Depth, Disruption, Translation.
7. Variant satellites spawn around the original hypothesis on the map 
   (Mutator output).
8. A 2D Pareto plot reveals: dominated variants get crossed out, 
   non-dominated ones get highlighted.
9. The strategy memo appears (bottom panel): recommended path, 
   alternatives, race conditions, white space.
10. Throughout, a small scatter plot in the corner shows the backtest 
    results (predicted vs actual impact on 30 historical papers) — 
    permanent credibility anchor.

Tech stack:
- Streamlit for the app shell
- streamlit-cytoscapejs or st-link-analysis for the force-directed 
  literature map (cytoscape.js is the powerhouse here)
- Plotly for radar and Pareto scatter
- streamlit-extras for smooth animations / reveals
- Built-in dark mode (projector will be dark)

Layout (single page, no scrolling):
- Top: hypothesis input box + run button + hypothesis display
- Centre-left (large): literature map with group portraits around 
  periphery
- Top-right: 6-dim impact radar
- Bottom-right: Pareto scatter
- Bottom-centre: strategy memo (streams in)
- Bottom-left corner (small, always visible): backtest validation 
  scatter plot

Your job, in order:

1. Read architecture.md and schemas.py. Confirm shared schemas exist.

2. Build the Streamlit skeleton with all panels showing mock data. 
   Layout must work without scrolling on a typical projector (1920x1080).

3. Get the literature map rendering with cytoscape.js, fed by a 
   list[Paper] from schemas. Get the BLOOM animation — papers appear 
   one by one in a sweeping motion. This is the signature visual; 
   invest time.

4. Build the group portrait cards. Each card has: name, institution, 
   animated interest score (use a progress bar or a counting number), 
   short proposed-direction text. Cards positioned around the perimeter 
   of the literature map.

5. Add the interest-strength lines from hypothesis to each group, and 
   the outgoing proposed-direction arrows.

6. Build the radar chart (Plotly) with original hypothesis as one trace, 
   variants as additional traces fading in.

7. Build the Pareto scatter with dominated variants crossed out.

8. Build the strategy memo panel — streams text in (or fades in if 
   streaming is too hard).

9. Add the backtest scatter plot to the corner (static image from 
   Person 4 is fine — does not need to be live).

10. Wire to the LangGraph pipeline output (Person 2 owns the pipeline; 
    you consume its state object).

11. Demo trigger: a single button that runs the whole thing, with each 
    panel revealing as its corresponding agent completes. Polished 
    timing.

Critical:
- Dark mode mandatory. The projector room will be dim.
- No clutter. If a panel is empty before its data arrives, show a subtle 
  placeholder, not a loading spinner that screams "waiting".
- Animation timing matters. Don't reveal everything at once. Stagger.
- TEST ON A PROJECTOR if possible before the demo — colours and 
  contrast change.
- If a live run fails on stage, have a pre-recorded screen capture ready 
  to play (Person 1 will coordinate).

Non-goals: I am not building any agents or running the pipeline. I 
consume its outputs and display them.

Read architecture.md "Demo Arc" section first. That's your spec.
```

---

## Funmi — Strategist & Glue (the linchpin)

**Tasks**
- Define shared `schemas.py` in first 30 minutes — UNBLOCKS EVERYONE
- Build OpenAI client wrapper with model routing (nano/mini/full)
- Build Parser, Cartographer, Conflict Detector, Overlap Auditor (light agents)
- Build Strategist (the final memo, reasoning_effort=high)
- Floating support for whoever's stuck
- Backup technical Q&A during the presentation

**Prompt for your AI**

```
I'm the glue engineer for a 7-hour hackathon team. My role is to define 
shared contracts (which unblock the whole team) and to own the simpler 
upstream agents plus the final strategist.

Repo structure:
  agents/               (markdown specs — read INSTRUCTIONS.md and the 
                         existing specs first)
  tools/
    semantic_scholar.py (existing — use as data source)
  schemas.py            (I CREATE THIS — see below)
  llm_client.py         (I CREATE THIS — see below)
  architecture.md       (full spec — read first)

My job, in strict order:

== PHASE 1: UNBLOCK THE TEAM (first 30 minutes — critical) ==

1. Create schemas.py with Pydantic models. Every other team member is 
   waiting for this. Define:

   class ParsedHypothesis(BaseModel):
       claim: str
       mechanism: str
       context: str
       population: str
       method: str

   class Paper(BaseModel):
       id: str
       title: str
       abstract: str
       year: int
       authors: list[str]
       venue: str | None
       citation_count: int | None
       concepts: list[str]
       relation_to_hypothesis: Literal["supports", "contradicts", 
                                       "overlaps", "adjacent"] | None

   class ResearchGroup(BaseModel):
       name: str
       institution: str
       member_authors: list[str]
       recent_papers: list[Paper]

   class EmulatorOutput(BaseModel):
       group: ResearchGroup
       interest_score: int  # 1-10
       engagement_type: Literal["build_on", "contradict", "ignore", 
                                 "collaborate"]
       proposed_direction: str
       method_they_would_use: str
       estimated_time_to_publish_months: int
       competitive_risk_to_user: Literal["low", "medium", "high"]

   class ImpactDimension(BaseModel):
       value: float
       confidence_low: float
       confidence_high: float

   class ImpactForecast(BaseModel):
       volume: ImpactDimension
       velocity: ImpactDimension
       reach: ImpactDimension
       depth: ImpactDimension
       disruption: ImpactDimension
       translation: ImpactDimension

   class Variant(BaseModel):
       hypothesis: str
       operator: Literal["generalise", "narrow", "substitute", 
                          "shift_scale", "cross_pollinate", "invert", 
                          "combine"]
       parent_hypothesis: str
       forecast: ImpactForecast | None

   class StrategyMemo(BaseModel):
       recommended_variant: Variant
       reasoning: str
       race_conditions: list[str]
       white_space: list[str]
       next_actions: list[str]

2. Create llm_client.py — wraps the OpenAI client with model routing:

   - Single function: call_llm(agent_name: str, system: str, user: str, 
     response_model: BaseModel | None = None)
   - Reads MODEL_ROUTING dict from a config file mapping agent names to 
     model SKUs ('gpt-5-nano', 'gpt-5-mini', 'gpt-5')
   - For 'strategist', sets reasoning_effort='high'
   - Returns parsed Pydantic object if response_model provided
   - Wraps every call in a Langfuse @observe() decorator

3. Push both files to the repo immediately and message the team.

== PHASE 2: BUILD THE LIGHT AGENTS ==

4. Parser (agents/parser.py): takes raw hypothesis text, returns 
   ParsedHypothesis. Uses gpt-5-nano. Simple structured output call.

5. Cartographer (agents/cartographer.py): takes ParsedHypothesis, 
   queries Semantic Scholar / OpenAlex for ~50 nearest papers via 
   embedding similarity or keyword search. Returns list[Paper] with 
   relation_to_hypothesis field left blank.

6. Conflict Detector (agents/conflict_detector.py): takes 
   ParsedHypothesis + the paper list from Cartographer. For each paper, 
   gpt-5-nano call classifying as contradicting/supporting/orthogonal. 
   Returns subset of papers tagged "contradicts" with one-sentence 
   reason each.

7. Overlap Auditor (agents/overlap_auditor.py): takes ParsedHypothesis + 
   paper list. gpt-5-nano: which papers already do this? Returns 
   crowding score 0-100 + named overlapping papers.

   Agents 5, 6, 7 should be designed to run in parallel — they share 
   the same paper pull. The Cartographer pulls once, the other two 
   re-use.

== PHASE 3: BUILD THE STRATEGIST ==

8. Strategist (agents/strategist.py): takes the full pipeline state — 
   hypothesis, literature analysis, emulator outputs, trajectory 
   scenarios, impact forecast, Pareto variants — and produces a 
   StrategyMemo.
   - Uses gpt-5 with reasoning_effort='high'
   - This is the highest-stakes prompt in the system — spend time on it
   - Output must explicitly reference: the recommended variant, why it 
     wins on the Pareto frontier, named race conditions from the 
     trajectory synthesiser, named white-space opportunities, and 
     concrete next actions
   - This memo is what the audience sees at the end of the demo. Make 
     it crisp, specific, and actionable.

== PHASE 4: FLOATING SUPPORT ==

9. Help whoever's stuck. Likely candidates:
   - Person 3 debugging grounded-persona prompts for Group Emulator
   - Person 2 wrestling with LangGraph parallel branches
   - Person 4 chasing date-filtering bugs in the backtest

10. Be ready to handle technical Q&A during the presentation.

Tech:
- Pydantic v2 for schemas
- OpenAI Python client (latest)
- Langfuse for tracing
- Semantic Scholar via tools/semantic_scholar.py (existing)

Critical:
- Schemas FIRST. Nothing else matters in the first 30 minutes. The 
  whole team is blocked on this.
- Push to repo and announce in team chat the moment schemas.py and 
  llm_client.py are ready.
- Keep the agent implementations minimal and readable — clarity 
  matters more than cleverness today.

Read agents/INSTRUCTIONS.md and all existing markdown specs in agents/ 
before writing the implementations. Some of those specs may be reusable 
as system prompts.
```

---

## Shared contracts cheat-sheet (pin in your team chat)

- `schemas.py` published in repo by Person 6, ~30 minutes after start
- All agents are `async` functions named `run_<agent_name>(state) -> state_update`
- All agents wrapped with `@observe()` for Langfuse
- Model routing happens in `llm_client.py` — don't hardcode model names in agents
- All Semantic Scholar / OpenAlex calls go through `tools/` modules — never raw HTTP
- Pipeline state object lives in Person 2's LangGraph definition — everyone reads/writes the same schema