// Mirror of backend/schemas.py. Field names and ranges must match exactly so
// the frontend can consume real pipeline output without translation.

export interface ParsedHypothesis {
  claim: string;
  mechanism: string;
  context: string;
  population: string;
  method: string;
}

export interface Paper {
  paper_id: string;
  title: string;
  authors: string[];
  year: number | null;
  abstract: string;
  url: string;
  citation_count: number;
  relevance_score: number;
  cluster: string;
}

export interface Conflict {
  paper_id: string;
  title: string;
  disagreement_dimension: string;
  explanation: string;
  severity: number; // 0..1
}

export interface OverlapReport {
  crowding_score: number; // 0..100
  overlapping_papers: string[];
  whitespace_summary: string;
  risk_notes: string[];
}

export interface ResearchGroup {
  group_id: string;
  name: string;
  institution: string;
  principal_investigators: string[];
  recent_paper_ids: string[];
  methods: string[];
  grounding_evidence: string;
}

export interface EmulatorOutput {
  group_id: string;
  group_name: string;
  interest_score: number; // 0..100
  engagement_type: string;
  proposed_direction: string;
  method_they_use: string;
  time_to_publish_months: number;
  competitive_risk: number; // 0..100
  grounding_paper_ids: string[];
}

export interface Scenario {
  scenario_id: string;
  name: string;
  probability: number; // 0..1
  description: string;
  leading_groups: string[];
  implications: string[];
}

export interface ImpactDimension {
  score: number; // 0..100
  confidence_low: number;
  confidence_high: number;
  rationale: string;
}

export interface ImpactForecast {
  volume: ImpactDimension;
  velocity: ImpactDimension;
  reach: ImpactDimension;
  depth: ImpactDimension;
  disruption: ImpactDimension;
  translation: ImpactDimension;
  overall_summary: string;
}

export type ImpactDimensionKey =
  | "volume"
  | "velocity"
  | "reach"
  | "depth"
  | "disruption"
  | "translation";

export const IMPACT_DIMENSIONS: ImpactDimensionKey[] = [
  "volume",
  "velocity",
  "reach",
  "depth",
  "disruption",
  "translation",
];

export interface Variant {
  variant_id: string;
  hypothesis_text: string;
  operator: string;
  rationale: string;
  impact_scores: Partial<Record<ImpactDimensionKey, number>>;
  is_pareto_selected: boolean;
  dominance_explanation: string;
}

export interface GroundednessCheck {
  group_id: string;
  group_name: string;
  is_grounded: boolean;
  flagged_inconsistencies: string[];
  evidence: string;
}

export interface StrategyMemo {
  recommendation: string;
  executive_summary: string;
  key_findings: string[];
  selected_variants: string[];
  risks: string[];
  next_steps: string[];
}

// Mirrors backend.pipeline.PipelineState. Frontend-only display extras
// (denario_outline, next_actions, headline_groups) are deliberately separate
// so they don't clash with the backend's authoritative shape.
export interface PipelineState {
  raw_hypothesis: string;
  parsed?: ParsedHypothesis;
  papers: Paper[];
  conflicts: Conflict[];
  overlaps?: OverlapReport;
  groups: ResearchGroup[];
  emulator_outputs: EmulatorOutput[];
  scenarios: Scenario[];
  forecast?: ImpactForecast;
  variants: Variant[];
  groundedness_checks: GroundednessCheck[];
  final_memo?: StrategyMemo;
}

// Frontend-only additions used for demo presentation; not produced by the backend.
export interface DenarioOutline {
  title: string;
  abstract: string;
  methods: string;
  experiments: string;
  discussion: string;
}

export interface DemoExtras {
  headline_groups: string[]; // group_ids the narrator zooms into
  denario_outline: DenarioOutline;
  next_actions: string[];
}

export interface DemoState extends PipelineState {
  extras: DemoExtras;
}
