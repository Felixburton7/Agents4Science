export enum Stage {
  IDLE = 0,
  PARSING = 1,
  LITERATURE = 2,
  CONFLICT_OVERLAP = 3,
  GROUPS = 4,
  EMULATORS = 5,
  TRAJECTORY = 6,
  FORECAST = 7,
  MUTATIONS = 8,
  PARETO = 9,
  MEMO = 10,
  DENARIO_HANDOFF = 11,
  NEXT_ACTIONS = 12,
  DONE = 13,
}

export const STAGE_NAMES: Record<Stage, string> = {
  [Stage.IDLE]: "Idle",
  [Stage.PARSING]: "Parsing hypothesis",
  [Stage.LITERATURE]: "Mapping the literature",
  [Stage.CONFLICT_OVERLAP]: "Flagging conflicts and overlaps",
  [Stage.GROUPS]: "Identifying research groups",
  [Stage.EMULATORS]: "Simulating group responses",
  [Stage.TRAJECTORY]: "Synthesising field trajectories",
  [Stage.FORECAST]: "Forecasting impact (6 dimensions)",
  [Stage.MUTATIONS]: "Mutating hypothesis variants",
  [Stage.PARETO]: "Curating the Pareto frontier",
  [Stage.MEMO]: "Writing the strategy memo",
  [Stage.DENARIO_HANDOFF]: "Generating Denario paper outline",
  [Stage.NEXT_ACTIONS]: "Listing next actions",
  [Stage.DONE]: "Done",
};

// Time the demo so the whole arc runs in ~70-80 seconds.
export const STAGE_DURATIONS_MS: Record<Stage, number> = {
  [Stage.IDLE]: 0,
  [Stage.PARSING]: 1500,
  [Stage.LITERATURE]: 6000,
  [Stage.CONFLICT_OVERLAP]: 3000,
  [Stage.GROUPS]: 12000,
  [Stage.EMULATORS]: 8000,
  [Stage.TRAJECTORY]: 6000,
  [Stage.FORECAST]: 4000,
  [Stage.MUTATIONS]: 4000,
  [Stage.PARETO]: 5000,
  [Stage.MEMO]: 8000,
  [Stage.DENARIO_HANDOFF]: 6000,
  [Stage.NEXT_ACTIONS]: 5000,
  [Stage.DONE]: 0,
};

export const ORDERED_STAGES: Stage[] = [
  Stage.IDLE,
  Stage.PARSING,
  Stage.LITERATURE,
  Stage.CONFLICT_OVERLAP,
  Stage.GROUPS,
  Stage.EMULATORS,
  Stage.TRAJECTORY,
  Stage.FORECAST,
  Stage.MUTATIONS,
  Stage.PARETO,
  Stage.MEMO,
  Stage.DENARIO_HANDOFF,
  Stage.NEXT_ACTIONS,
  Stage.DONE,
];

export function nextStage(s: Stage): Stage | null {
  if (s === Stage.DONE) return null;
  return (s + 1) as Stage;
}
