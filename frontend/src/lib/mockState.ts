import { INSTITUTIONS } from "@/lib/institutions";
import type {
  Conflict,
  DemoState,
  EmulatorOutput,
  GroundednessCheck,
  ImpactDimension,
  ImpactForecast,
  OverlapReport,
  Paper,
  ParsedHypothesis,
  ResearchGroup,
  Scenario,
  StrategyMemo,
  Variant,
} from "@/types/schemas";

export const DEFAULT_HYPOTHESIS =
  "Sparse autoencoders trained on residual streams of frontier language models will reveal monosemantic features that are predictive of out-of-distribution generalization.";

const PARSED: ParsedHypothesis = {
  claim:
    "Monosemantic SAE features predict out-of-distribution generalization in frontier LMs.",
  mechanism:
    "Sparse autoencoders disentangle superposed directions in residual streams.",
  context: "Mechanistic interpretability for safety-critical model behavior.",
  population: "Frontier transformer language models (≥7B parameters).",
  method:
    "Train SAEs on residual stream activations; correlate feature firing with OOD evaluation suites.",
};

const PAPER_TITLES: string[] = [
  "Towards Monosemanticity: Decomposing Language Models With Dictionary Learning",
  "Sparse Feature Circuits: Discovering and Editing Interpretable Causal Graphs",
  "Scaling Monosemanticity: Extracting Interpretable Features From Claude 3",
  "Polysemanticity and Capacity in Neural Networks",
  "Toy Models of Superposition",
  "Anthropic's Universal Features Across Models",
  "Activation Patching for Localized Edits",
  "The Geometry of Concepts in Transformer Residuals",
  "Probing Subspaces for Interpretable Directions",
  "Goodfire: Dense Sparse Coding for Production Models",
  "Gemma-Scope: A Library of Sparse Autoencoders",
  "Logit Lens Revisited",
  "Mechanistic Anomaly Detection via SAE Features",
  "Feature Pruning Improves Out-of-Distribution Robustness",
  "Crosscoders: Comparing Features Between Model Generations",
  "Top-K SAEs for Token-Level Interpretation",
  "Steering Vectors and Activation Engineering",
  "Behavioural Signatures of Refusal Circuits",
  "Causal Scrubbing of Hypothesised Circuits",
  "Direct Logit Attribution at Scale",
  "Feature Splitting Across Layers",
  "Eliciting Latent Knowledge from Activations",
  "Decoder Bottleneck Analysis in Transformers",
  "Concept Erasure with Counterfactual SAEs",
  "Pythia: A Suite for Mechanistic Analysis",
  "TinyStories: A Test-Bed for Circuit Discovery",
  "Interpretable Heads in Multi-Query Attention",
  "Sparse Coding of Visual Features in CLIP",
  "Probing for Numerical Reasoning",
  "Linear Probes are Insufficient: A Cautionary Tale",
  "When Features Aren't Linear",
  "Capability Suppression in Aligned Models",
  "Quanta of Computation in MLPs",
  "Tracing Refusals Across Architectures",
  "Distributional Shift and Internal Representations",
  "The Refusal Direction Across Model Families",
  "OOD Probing Suites for SAE Evaluation",
  "Dataset Cartography for Mechanistic Generalization",
  "Why Interpretability Tools Disagree",
  "Auditing Hidden Goals via Internal Representations",
  "Circuit Decomposition Without Activation Patching",
  "Cross-Layer Feature Comparison Methods",
  "Faithfulness Metrics for Interpretability",
  "Adversarial Features in SAE Latents",
  "Probing for Honesty Without Behaviour",
  "Causal Mediation of Toxicity",
  "Universal Features in Multilingual Models",
  "Activation Norm and Generalization",
  "Probing Composition in Long-Context Reasoning",
  "Feature Density and Polysemanticity Trade-Offs",
];

const CLUSTERS = ["interpretability", "sae", "generalization", "circuits", "safety"];

function buildPapers(): Paper[] {
  return PAPER_TITLES.map((title, idx) => ({
    paper_id: `paper-${String(idx + 1).padStart(2, "0")}`,
    title,
    authors: [`Author ${idx + 1}`, `Co-author ${((idx + 7) % 11) + 1}`],
    year: 2020 + ((idx * 7) % 5),
    abstract: `Abstract for ${title}.`,
    url: `https://example.test/${idx + 1}`,
    citation_count: 30 + ((idx * 37) % 500),
    relevance_score: Math.max(0.05, 1 - idx * 0.018),
    cluster: CLUSTERS[idx % CLUSTERS.length],
  }));
}

const CONFLICTS: Conflict[] = [
  {
    paper_id: "paper-12",
    title: "Logit Lens Revisited",
    disagreement_dimension: "mechanism",
    explanation:
      "Argues residual stream directions are not faithfully decomposable into independent features.",
    severity: 0.78,
  },
  {
    paper_id: "paper-30",
    title: "Linear Probes are Insufficient: A Cautionary Tale",
    disagreement_dimension: "method",
    explanation:
      "Shows that linear-probe based evaluation overestimates feature monosemanticity.",
    severity: 0.62,
  },
  {
    paper_id: "paper-44",
    title: "Adversarial Features in SAE Latents",
    disagreement_dimension: "claim",
    explanation:
      "Demonstrates SAE latents can be steered to mispredict OOD splits without changing weights.",
    severity: 0.55,
  },
];

const OVERLAPS: OverlapReport = {
  crowding_score: 71,
  overlapping_papers: [
    "Towards Monosemanticity: Decomposing Language Models With Dictionary Learning",
    "Scaling Monosemanticity: Extracting Interpretable Features From Claude 3",
    "Gemma-Scope: A Library of Sparse Autoencoders",
  ],
  whitespace_summary:
    "Multilingual SAE feature alignment, and the link from feature density to instruction-following robustness, remain under-explored.",
  risk_notes: [
    "Toronto and Stanford both queued large-scale SAE training on Llama-3 70B for Q3 2026.",
    "Anthropic-flavoured 'scaling monosemanticity' subsumes the headline claim unless the OOD predictor is concrete.",
    "Methodology-purity arguments (Oxford probe-critique line) will be cited against any non-causal evaluation.",
  ],
};

function buildGroups(): ResearchGroup[] {
  return INSTITUTIONS.map((inst, idx) => ({
    group_id: inst.id,
    name: `${inst.name} interpretability group`,
    institution: inst.name,
    principal_investigators: [inst.pi.display],
    recent_paper_ids: [
      `paper-${String((idx * 3 + 1) % 50 + 1).padStart(2, "0")}`,
      `paper-${String((idx * 5 + 7) % 50 + 1).padStart(2, "0")}`,
      `paper-${String((idx * 11 + 3) % 50 + 1).padStart(2, "0")}`,
    ],
    methods: [
      "sparse autoencoders",
      idx % 2 === 0 ? "activation patching" : "linear probing",
      idx % 3 === 0 ? "causal scrubbing" : "feature ablation",
    ],
    grounding_evidence: `Co-authorship cluster around ${inst.name}'s mech-interp output (2023-2026).`,
  }));
}

// Tuned so the demo reads: one strong "accept", one hostile "reject",
// rest borderline; varied scores across institutions; race conditions
// between Toronto and Stanford; white space around multilingual SAEs.
const EMULATOR_TEMPLATES: Array<{
  id: string;
  interest: number;
  risk: number;
  monthsToPublish: number;
  engagement: string;
  direction: string;
  method: string;
}> = [
  {
    id: "mit",
    interest: 64,
    risk: 55,
    monthsToPublish: 9,
    engagement: "build_on",
    direction:
      "Extend SAE feature-circuit work to a public OOD probing suite (HumanEval-OOD + SVAMP-OOD).",
    method: "sparse feature circuits",
  },
  {
    id: "stanford",
    interest: 82,
    risk: 75,
    monthsToPublish: 6,
    engagement: "build_on",
    direction:
      "Train SAEs on Llama-3 70B residual streams and ship a public OOD predictor by Q3.",
    method: "scaled SAEs",
  },
  {
    id: "oxford",
    interest: 38,
    risk: 30,
    monthsToPublish: 14,
    engagement: "contradict",
    direction:
      "Stress-test the monosemanticity claim with adversarial probe construction; argue features mislabel OOD samples.",
    method: "adversarial linear probing",
  },
  {
    id: "toronto",
    interest: 88,
    risk: 80,
    monthsToPublish: 5,
    engagement: "build_on",
    direction:
      "Lead a head-to-head between top-K SAEs and Gated SAEs on a unified OOD eval set; race Stanford.",
    method: "Top-K vs Gated SAEs",
  },
  {
    id: "berkeley",
    interest: 56,
    risk: 45,
    monthsToPublish: 11,
    engagement: "collaborate",
    direction:
      "Use SAE features as inputs to RL reward models and test OOD reward hacking signatures.",
    method: "SAE-conditioned reward models",
  },
  {
    id: "eth",
    interest: 49,
    risk: 35,
    monthsToPublish: 13,
    engagement: "build_on",
    direction:
      "Calibrated uncertainty over SAE feature attribution; bound the OOD claim with frequentist guarantees.",
    method: "conformal feature attribution",
  },
  {
    id: "tum",
    interest: 33,
    risk: 28,
    monthsToPublish: 16,
    engagement: "ignore",
    direction:
      "Pursue model-internal causal abstraction instead; treat SAEs as a secondary lens.",
    method: "causal abstraction discovery",
  },
  {
    id: "tsinghua",
    interest: 71,
    risk: 60,
    monthsToPublish: 8,
    engagement: "build_on",
    direction:
      "Train multilingual SAEs and evaluate cross-lingual OOD generalization on FLORES-X.",
    method: "multilingual SAEs",
  },
  {
    id: "tokyo",
    interest: 46,
    risk: 40,
    monthsToPublish: 12,
    engagement: "build_on",
    direction:
      "SAE feature density vs instruction-following degradation under OOD prompts.",
    method: "feature-density curves",
  },
  {
    id: "ucl",
    interest: 69,
    risk: 65,
    monthsToPublish: 7,
    engagement: "collaborate",
    direction:
      "Mechanistic anomaly detection: use SAE features to flag OOD inputs before a model commits.",
    method: "mechanistic anomaly detection",
  },
  {
    id: "cambridge_group",
    interest: 84,
    risk: 50,
    monthsToPublish: 6,
    engagement: "collaborate",
    direction:
      "Co-author the OOD eval suite and pair it with the local interpretability programme.",
    method: "cross-method comparative evaluation",
  },
];

function buildEmulatorOutputs(groups: ResearchGroup[]): EmulatorOutput[] {
  const byId = new Map(groups.map((g) => [g.group_id, g]));
  return EMULATOR_TEMPLATES.map((t) => {
    const group = byId.get(t.id);
    if (!group) throw new Error(`Mock template references unknown group ${t.id}`);
    return {
      group_id: group.group_id,
      group_name: group.name,
      interest_score: t.interest,
      engagement_type: t.engagement,
      proposed_direction: t.direction,
      method_they_use: t.method,
      time_to_publish_months: t.monthsToPublish,
      competitive_risk: t.risk,
      grounding_paper_ids: group.recent_paper_ids,
    };
  });
}

function buildGroundednessChecks(outputs: EmulatorOutput[]): GroundednessCheck[] {
  return outputs.map((o, idx) => ({
    group_id: o.group_id,
    group_name: o.group_name,
    is_grounded: idx % 7 !== 3, // one ungrounded for visual variety
    flagged_inconsistencies:
      idx % 7 === 3 ? ["Method appears in no recent paper from this group."] : [],
    evidence: `Method "${o.method_they_use}" appears in ${o.grounding_paper_ids
      .slice(0, 2)
      .join(", ")}.`,
  }));
}

const SCENARIOS: Scenario[] = [
  {
    scenario_id: "scenario-converge",
    name: "Field converges on SAE-on-frontier-LM",
    probability: 0.52,
    description:
      "Toronto, Stanford, and Tsinghua all push large-scale SAE training on 70B-class models within 12 months. Outputs converge methodologically; the field standardises on one of two SAE flavours.",
    leading_groups: [
      "Toronto interpretability group",
      "Stanford interpretability group",
      "Tsinghua interpretability group",
    ],
    implications: [
      "Race-to-publish pressure rises; first concrete OOD predictor wins disproportionate citations.",
      "Methodological standards calcify around whichever SAE variant ships first.",
    ],
  },
  {
    scenario_id: "scenario-critique",
    name: "Methodological backlash splits the field",
    probability: 0.28,
    description:
      "Oxford and ETH-led critiques argue monosemanticity is a probe artefact, not a representational fact. A second camp publishes adversarial counter-evidence.",
    leading_groups: [
      "Oxford interpretability group",
      "ETH Zürich interpretability group",
    ],
    implications: [
      "Reviewers demand causal evidence beyond probing.",
      "Citation pile-on around the critique papers.",
    ],
  },
  {
    scenario_id: "scenario-translate",
    name: "Translation via anomaly detection",
    probability: 0.20,
    description:
      "UCL and Berkeley reframe SAE features as a detection layer for production deployment. Industry uptake outpaces academic theory.",
    leading_groups: [
      "UCL interpretability group",
      "UC Berkeley interpretability group",
    ],
    implications: [
      "Translation citations climb faster than depth citations.",
      "Open-source mech-interp tooling becomes infrastructural.",
    ],
  },
];

const FORECAST: ImpactForecast = {
  volume: dim(72, "Lots of adjacent SAE work primed to cite a concrete OOD predictor."),
  velocity: dim(78, "Hot topic; Anthropic + DeepMind + OSS will cite within 6 months of release."),
  reach: dim(55, "Mostly interpretability + alignment; limited reach into NLP/perception fields."),
  depth: dim(48, "Useful, not foundational on its own. Foundational only if OOD predictor holds up."),
  disruption: dim(41, "Steers the SAE program rather than displacing prior work."),
  translation: dim(33, "Translation requires the anomaly-detection variant to mature first."),
  overall_summary:
    "Crowded near-term, with strong velocity but only middling depth and translation. The variant that combines SAE features with anomaly detection sits on a richer Pareto frontier.",
};

function dim(score: number, rationale: string): ImpactDimension {
  return {
    score,
    confidence_low: Math.max(0, score - 11),
    confidence_high: Math.min(100, score + 11),
    rationale,
  };
}

const VARIANTS: Variant[] = [
  {
    variant_id: "variant-1",
    hypothesis_text:
      "Sparse autoencoders trained on residual streams of frontier LMs will reveal monosemantic features predictive of OOD generalization across model scales (1B → 70B → 400B).",
    operator: "Generalise",
    rationale: "Broaden population from a fixed scale to a scaling-law claim.",
    impact_scores: { volume: 70, velocity: 62, reach: 54, depth: 45, disruption: 39, translation: 31 },
    is_pareto_selected: false,
    dominance_explanation:
      "Dominated by the cross-pollinated anomaly-detection variant on depth, disruption, and translation.",
  },
  {
    variant_id: "variant-2",
    hypothesis_text:
      "SAE features extracted from instruction-tuned 8B-class LMs predict OOD refusal failures specifically.",
    operator: "Narrow",
    rationale: "Tighten the claim to a single behavior the field can audit.",
    impact_scores: { volume: 58, velocity: 73, reach: 47, depth: 56, disruption: 49, translation: 60 },
    is_pareto_selected: true,
    dominance_explanation:
      "On the frontier: trades volume for translation and disruption. Most likely to ship a falsifiable claim.",
  },
  {
    variant_id: "variant-3",
    hypothesis_text:
      "Transcoder networks (not SAEs) reveal monosemantic features predictive of OOD generalization.",
    operator: "Substitute mechanism",
    rationale: "Swap SAEs for transcoders; same outcome variable.",
    impact_scores: { volume: 55, velocity: 50, reach: 52, depth: 52, disruption: 47, translation: 35 },
    is_pareto_selected: false,
    dominance_explanation:
      "Dominated by the original on volume and velocity; doesn't recover anywhere else.",
  },
  {
    variant_id: "variant-4",
    hypothesis_text:
      "SAEs on long-context attention activations (not residuals) predict OOD reasoning failures.",
    operator: "Shift scale",
    rationale: "Move from residuals to attention; from short context to long.",
    impact_scores: { volume: 64, velocity: 58, reach: 67, depth: 61, disruption: 58, translation: 44 },
    is_pareto_selected: true,
    dominance_explanation:
      "On the frontier: stronger reach and depth via long-context relevance; only slightly behind on velocity.",
  },
  {
    variant_id: "variant-5",
    hypothesis_text:
      "Combining SAE features with anomaly-detection scoring predicts OOD generalization AND flags failures at inference time.",
    operator: "Cross-pollinate",
    rationale:
      "Fuse with the mechanistic-anomaly-detection thread; ship a deployable artifact.",
    impact_scores: { volume: 68, velocity: 71, reach: 70, depth: 64, disruption: 62, translation: 75 },
    is_pareto_selected: true,
    dominance_explanation:
      "Strict Pareto winner overall: best translation and disruption, near-best on every other axis. Recommended.",
  },
  {
    variant_id: "variant-6",
    hypothesis_text:
      "Sparse autoencoders trained on frontier LM residual streams will NOT reveal monosemantic features predictive of OOD generalization; OOD is overdetermined by data statistics.",
    operator: "Invert",
    rationale: "Aggressively test the null. Publishable either way.",
    impact_scores: { volume: 60, velocity: 66, reach: 55, depth: 68, disruption: 51, translation: 38 },
    is_pareto_selected: true,
    dominance_explanation:
      "On the frontier on depth; the highest-information experiment if it lands a clean negative.",
  },
];

const STRATEGY_MEMO: StrategyMemo = {
  recommendation:
    "Pursue Variant 5 (Cross-pollinate): combine SAE features with mechanistic anomaly detection. Frame it as a deployable artifact and a falsifiable claim about OOD generalization.",
  executive_summary:
    "The headline hypothesis sits in a crowded research front. Toronto and Stanford both have large-scale SAE programs queued for Q3, and any non-causal evaluation will be cited against by Oxford-led probe critiques. The Cross-pollinate variant (Variant 5) wins the Pareto frontier on every dimension except raw volume; it converts a methodological claim into an industrial artifact, and that's where translation citations live.",
  key_findings: [
    "Crowding score 71/100: three groups (Toronto, Stanford, Tsinghua) are within 8 months of publishing in this space.",
    "Methodological risk: Oxford and ETH will challenge any non-causal probing evaluation.",
    "Whitespace: multilingual SAE feature alignment, and SAE-feature × anomaly-detection fusion, remain uncontested.",
    "The Narrow variant (OOD refusal failures) is the cheapest preregistration target; the Cross-pollinate variant is the highest-leverage one.",
  ],
  selected_variants: [
    "variant-5: Cross-pollinate — SAE features × anomaly detection",
    "variant-2: Narrow — refusal-failure OOD probe",
    "variant-4: Shift scale — long-context attention SAEs",
    "variant-6: Invert — test the null aggressively",
  ],
  risks: [
    "Race condition with Toronto and Stanford: 4-month collision window on the headline SAE-on-Llama-3-70B claim.",
    "Methodological backlash from Oxford/ETH if the OOD predictor is probing-only.",
    "Translation depends on the anomaly-detection thread reaching production maturity.",
  ],
  next_steps: [
    "Pivot from Variant 1 (the original) to Variant 5; preregister an OOD eval suite on OSF.",
    "Open a collaboration conversation with the UCL anomaly-detection thread (PI: Bemis Trassabis).",
    "Acquire residual stream activations for Pythia-70m and a 7B-class open model as the cheap pilot.",
    "Reach out to Deoff Trinton at Toronto before Q3 2026 to coordinate scope, not race.",
    "Draft a falsifier section: what observation would invalidate Variant 5?",
  ],
};

const DENARIO_OUTLINE = {
  title:
    "SAE-Conditioned Anomaly Detection: A Deployable Predictor of Out-of-Distribution Generalization in Frontier Language Models",
  abstract:
    "We fuse sparse autoencoder (SAE) feature representations with mechanistic anomaly detection to produce a single artifact that both predicts and flags out-of-distribution (OOD) failures in frontier language models. On a controlled OOD evaluation suite spanning refusal failures, long-context reasoning, and multilingual prompts, our SAE-conditioned anomaly score achieves a higher rank correlation with held-out OOD loss than either method alone. We argue the gain comes from SAE features acting as a low-dimensional sufficient statistic for distributional shift.",
  methods:
    "We train top-K sparse autoencoders on residual streams of Pythia-70m and a 7B-class open model. We feed SAE activation vectors into a lightweight anomaly-detection head trained on in-distribution activations only. We evaluate against a public OOD probing suite that we release alongside the paper, comprising refusal-failure prompts, long-context reasoning splits, and FLORES-X-derived multilingual prompts.",
  experiments:
    "Three experiments. (1) Predictive: rank correlation between SAE-conditioned anomaly score and held-out OOD loss. (2) Deployable: detection AUC on inference-time flagging of OOD inputs. (3) Falsifier: a controlled negative — generate synthetic OOD splits whose statistics differ but whose SAE activations should not — confirm that the predictor degrades.",
  discussion:
    "We discuss the relationship to the Toronto/Stanford SAE-scaling thread and to the Oxford-led probe critique. The SAE-conditioned variant survives both pressures: it operates causally enough to dodge probe critique, and it ships a deployable artifact that the SAE-scaling community can integrate. We close on multilingual SAE alignment as the next whitespace.",
};

const NEXT_ACTIONS: string[] = [
  "Preregister the OOD eval suite on OSF — refusal failures, long-context reasoning, FLORES-X multilingual splits.",
  "Acquire Pythia-70m + Llama-3-8B residual stream activations from EleutherAI and HuggingFace.",
  "Open a collaboration conversation with the UCL anomaly-detection thread (PI: Bemis Trassabis).",
  "Reach out to Deoff Trinton at Toronto before Q3 2026 — coordinate scope so we don't race head-to-head.",
  "Draft the falsifier section first: what observation would invalidate the SAE-conditioned anomaly score?",
  "Set up a Goodfire-style sparsity baseline as a credible comparator in the experiments section.",
  "Block out 2 weeks for the methodology-purity review (probe-critique camp) before submission.",
];

export function buildMockState(hypothesis?: string): DemoState {
  const groups = buildGroups();
  const emulatorOutputs = buildEmulatorOutputs(groups);
  const groundednessChecks = buildGroundednessChecks(emulatorOutputs);
  return {
    raw_hypothesis: hypothesis?.trim() || DEFAULT_HYPOTHESIS,
    parsed: PARSED,
    papers: buildPapers(),
    conflicts: CONFLICTS,
    overlaps: OVERLAPS,
    groups,
    emulator_outputs: emulatorOutputs,
    scenarios: SCENARIOS,
    forecast: FORECAST,
    variants: VARIANTS,
    groundedness_checks: groundednessChecks,
    final_memo: STRATEGY_MEMO,
    extras: {
      headline_groups: ["stanford", "cambridge_group", "eth"],
      denario_outline: DENARIO_OUTLINE,
      next_actions: NEXT_ACTIONS,
    },
  };
}
