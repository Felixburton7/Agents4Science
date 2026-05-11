"use client";

import { useMemo } from "react";
import { DemoProvider, useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";
import {
  CircularGauge,
  DimensionRadar,
  ScoreDistribution,
  SparkLine,
  EvidenceQualityCard,
  ImpactProjections,
  ConceptSpread,
  SimilarLandscape,
  Logo,
} from "@/components/Scorecard";
import type { DemoState } from "@/types/schemas";

export default function Home() {
  return (
    <DemoProvider>
      <Surface />
    </DemoProvider>
  );
}

function Surface() {
  const { stage, isRunning } = useDemo();
  const showResults = stage === Stage.DONE;

  if (!showResults) {
    return <Hero isRunning={isRunning} />;
  }
  return <ResultsLayout />;
}

function Hero({ isRunning }: { isRunning: boolean }) {
  const { hypothesis, setHypothesis, run } = useDemo();
  const max = 3000;
  const count = hypothesis.length;
  const canSubmit = count > 0 && count <= max && !isRunning;

  const example =
    "Self-supervised world models with action chunking will substantially outperform transformer predictors on long-horizon robot manipulation.";

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <TopNav />
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-16">
        <div className="w-full max-w-[640px] flex flex-col items-center">
          <h1 className="display-tight text-[56px] sm:text-[64px] leading-[1.04] text-[color:var(--color-ink)] text-center">
            A reality check for your hypothesis.
          </h1>
          <p className="mt-5 text-[17px] text-[color:var(--color-muted)] tracking-tight text-center max-w-md">
            Paste a research claim. Get a multi-dimensional scorecard grounded in the literature.
          </p>

          <div className="w-full mt-12">
            <div className="relative bg-white border border-[color:var(--color-border)] rounded-xl shadow-[0_1px_2px_rgba(0,0,0,0.03)] focus-within:border-[color:var(--color-ink)] transition-colors">
              <textarea
                value={hypothesis}
                onChange={(e) => setHypothesis(e.target.value.slice(0, max))}
                placeholder="e.g. Sparse autoencoders trained on residual streams of frontier language models will reveal monosemantic features predictive of out-of-distribution generalization."
                className="w-full h-36 bg-transparent text-[15px] text-[color:var(--color-ink)] placeholder:text-[color:var(--color-muted-2)] resize-none outline-none scrollbar-thin leading-relaxed px-5 py-4"
                maxLength={max}
              />
              <div className="flex items-center justify-between px-5 py-2.5 border-t border-[color:var(--color-hairline)]">
                <button
                  className="text-[12px] text-[color:var(--color-muted)] hover:text-[color:var(--color-ink)] transition-colors flex items-center gap-1.5"
                  onClick={() => setHypothesis(example)}
                  disabled={isRunning}
                  type="button"
                >
                  <SparkIcon /> Try an example
                </button>
                <div className="flex items-center gap-3">
                  <span className="text-[11px] text-[color:var(--color-muted-2)] text-mono">
                    {count} / {max}
                  </span>
                  <button
                    onClick={run}
                    disabled={!canSubmit}
                    className="btn-primary text-[13px] px-4 py-1.5"
                  >
                    {isRunning ? "Analyzing…" : "Analyze"}
                  </button>
                </div>
              </div>
            </div>
            <p className="mt-3 text-[12px] text-[color:var(--color-muted-2)] text-center flex items-center justify-center gap-1.5">
              <LockIcon /> Your hypothesis is private and only used for analysis.
            </p>
          </div>

          {isRunning && (
            <div className="mt-10 flex gap-1.5">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-[color:var(--color-ink)] animate-pulse"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultsLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-[color:var(--color-canvas-2)]">
      <TopNav />
      <CompactHypothesisBar />
      <Scorecard />
    </div>
  );
}

function CompactHypothesisBar() {
  const { hypothesis, setHypothesis, run, isRunning, reset } = useDemo();
  const max = 3000;
  const count = hypothesis.length;

  return (
    <section className="px-8 py-4 bg-white hairline-b">
      <div className="max-w-[1400px] mx-auto flex items-center gap-4">
        <div className="flex-1 relative bg-[color:var(--color-canvas-2)] border border-[color:var(--color-hairline)] rounded-xl px-4 py-2.5 focus-within:border-[color:var(--color-blue)] transition-colors">
          <textarea
            value={hypothesis}
            onChange={(e) => setHypothesis(e.target.value.slice(0, max))}
            placeholder="Paste your hypothesis here..."
            className="w-full h-10 bg-transparent text-[13.5px] text-[color:var(--color-ink)] placeholder:text-[color:var(--color-muted-2)] resize-none outline-none scrollbar-thin leading-snug"
            maxLength={max}
          />
        </div>
        <div className="text-[11px] text-mono text-[color:var(--color-muted-2)] w-20 text-right">
          {count} / {max}
        </div>
        <button
          onClick={reset}
          className="btn-ghost"
          disabled={isRunning}
        >
          New
        </button>
        <button
          onClick={run}
          disabled={isRunning || count === 0}
          className="btn-primary px-5 py-2 text-[13.5px]"
        >
          {isRunning ? "Analyzing…" : "Re-analyze"}
        </button>
      </div>
    </section>
  );
}

function TopNav() {
  return (
    <header className="h-14 hairline-b px-8 flex items-center justify-between bg-white/85 backdrop-blur-md sticky top-0 z-20">
      <div className="flex items-center gap-2.5">
        <Logo size={20} />
        <span className="text-[color:var(--color-ink)] font-medium text-[14px] tracking-tight">
          Hypothesis Hater
        </span>
      </div>
      <nav className="flex items-center gap-6">
        <span className="nav-link">History</span>
        <span className="nav-link">Saved</span>
        <span className="nav-link">Docs</span>
        <div className="w-7 h-7 rounded-full bg-[color:var(--color-canvas-2)] text-[color:var(--color-ink)] flex items-center justify-center text-[10.5px] font-medium border border-[color:var(--color-hairline)]">
          AH
        </div>
      </nav>
    </header>
  );
}

function Scorecard() {
  const { state } = useDemo();
  const scorecardData = useMemo(() => deriveScorecard(state), [state]);

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin px-8 py-7">
      <div className="max-w-[1400px] mx-auto">
        <header className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="display-tight text-[40px] text-[color:var(--color-ink)] leading-tight">
                Hypothesis Scorecard
              </h1>
              <span className="badge-beta">Beta</span>
            </div>
            <p className="mt-1 text-[15px] text-[color:var(--color-muted)] tracking-tight">
              A multi-dimensional reality check.
            </p>
          </div>
          <button className="btn-ghost flex items-center gap-1.5">
            <InfoIcon /> How to read this
          </button>
        </header>

        <section className="panel p-8 mb-4">
          <div className="grid grid-cols-12 gap-8 items-center">
            <div className="col-span-4 flex flex-col items-center">
              <CircularGauge value={scorecardData.overall} label="Overall Signal" />
              <p className="mt-3 text-[13px] text-[color:var(--color-muted)]">
                {scorecardData.tier}
              </p>
            </div>
            <div className="col-span-4">
              <h3 className="text-[16px] font-semibold text-[color:var(--color-ink)] mb-2 tracking-tight">
                Takeaway
              </h3>
              <p className="text-[14px] text-[color:var(--color-body)] leading-relaxed tracking-tight">
                {scorecardData.takeaway}
              </p>
              <div className="mt-5 flex gap-3">
                <div className="flex-1 panel-inner p-3">
                  <div className="text-[10px] uppercase tracking-wider text-[color:var(--color-muted)] mb-1">
                    Upside
                  </div>
                  <div className="text-[13px] text-[color:var(--color-green)] font-semibold tracking-tight">
                    {scorecardData.upside}
                  </div>
                </div>
                <div className="flex-1 panel-inner p-3">
                  <div className="text-[10px] uppercase tracking-wider text-[color:var(--color-muted)] mb-1">
                    Watchouts
                  </div>
                  <div className="text-[13px] text-[color:var(--color-red)] font-semibold tracking-tight">
                    {scorecardData.watchouts}
                  </div>
                </div>
              </div>
            </div>
            <div className="col-span-4">
              <DimensionRadar dimensions={scorecardData.radar} />
            </div>
          </div>
        </section>

        <div className="grid grid-cols-12 gap-4 mb-4">
          <section className="col-span-3 panel p-5">
            <h3 className="text-[13px] font-semibold text-[color:var(--color-ink)] mb-3 tracking-tight">
              Score distribution
            </h3>
            <ScoreDistribution value={scorecardData.overall} />
          </section>
          <section className="col-span-6 panel p-5">
            <h3 className="text-[13px] font-semibold text-[color:var(--color-ink)] mb-4 tracking-tight">
              Dimension scores
            </h3>
            <div className="grid grid-cols-5 gap-3">
              {scorecardData.dimensions.map((d) => {
                const { key, ...rest } = d;
                return <DimensionTile key={key} {...rest} />;
              })}
            </div>
          </section>
          <section className="col-span-3 panel p-5">
            <EvidenceQualityCard
              score={scorecardData.evidenceQuality.score}
              tier={scorecardData.evidenceQuality.tier}
              submetrics={scorecardData.evidenceQuality.submetrics}
            />
          </section>
        </div>

        <div className="grid grid-cols-12 gap-4 mb-4">
          <section className="col-span-5 panel p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[13px] font-semibold text-[color:var(--color-ink)] flex items-center gap-1.5 tracking-tight">
                Impact projections <InfoIcon />
              </h3>
              <div className="flex gap-1 bg-[color:var(--color-canvas-2)] rounded-full p-0.5">
                {["5Y", "3Y", "1Y"].map((y, i) => (
                  <button
                    key={y}
                    className={`px-2.5 py-0.5 text-[11px] rounded-full font-medium ${
                      i === 0
                        ? "bg-white text-[color:var(--color-ink)] shadow-sm"
                        : "text-[color:var(--color-muted)]"
                    }`}
                  >
                    {y}
                  </button>
                ))}
              </div>
            </div>
            <ImpactProjections data={scorecardData.projections} />
          </section>
          <section className="col-span-4 panel p-5">
            <h3 className="text-[13px] font-semibold text-[color:var(--color-ink)] flex items-center gap-1.5 mb-3 tracking-tight">
              Concept spread{" "}
              <span className="text-[color:var(--color-muted)] text-[11px] font-normal">
                (predicted)
              </span>
              <InfoIcon />
            </h3>
            <ConceptSpread clusters={scorecardData.clusters} />
          </section>
          <section className="col-span-3 panel p-5">
            <h3 className="text-[13px] font-semibold text-[color:var(--color-ink)] tracking-tight">
              Similar landscape
            </h3>
            <p className="text-[11px] text-[color:var(--color-muted)] mb-3">
              Closest prior work
            </p>
            <SimilarLandscape items={scorecardData.similar} />
            <button className="btn-ghost w-full mt-3">
              View all ({scorecardData.similarTotal})
            </button>
          </section>
        </div>

        <footer className="panel p-3.5 flex items-center justify-between text-[12px]">
          <div className="flex items-center gap-2 text-[color:var(--color-muted)]">
            <span className="px-1.5 py-0.5 rounded bg-[color:var(--color-ink)] text-white text-[9px] font-semibold">
              AI
            </span>
            <span>
              AI note: Scores are probabilistic estimates based on current literature and models. They are not guarantees.
            </span>
          </div>
          <button className="btn-ghost flex items-center gap-1.5">
            <DownloadIcon /> Export full report
          </button>
        </footer>
      </div>
    </div>
  );
}

function DimensionTile({
  label,
  value,
  tier,
  trend,
  color,
  icon,
}: {
  label: string;
  value: number;
  tier: string;
  trend: number[];
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="panel-inner p-3">
      <div className="flex items-center gap-1.5 text-[color:var(--color-muted)] text-[11px] mb-1.5">
        <span style={{ color }}>{icon}</span>
        <span className="tracking-tight">{label}</span>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="display-tight text-[26px] text-[color:var(--color-ink)] leading-none">
          {value}
        </span>
      </div>
      <div className="text-[10px] text-[color:var(--color-muted-2)] mb-1.5 mt-1">
        {tier}
      </div>
      <SparkLine values={trend} color={color} />
    </div>
  );
}

function SparkIcon() {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 3l1.9 5.8L20 10l-5.6 2.8L13 19l-2-5.8L5 11l5.8-1.9L12 3z" />
    </svg>
  );
}

function InfoIcon() {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="text-[color:var(--color-muted)]"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4M12 8h.01" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg
      width="11"
      height="11"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="11" width="18" height="11" rx="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
    </svg>
  );
}

// ---------- derivation ----------

function deriveScorecard(state: DemoState) {
  const metricByKey = new Map<string, number>();
  if (state.forecast) {
    metricByKey.set("volume", state.forecast.volume.score);
    metricByKey.set("velocity", state.forecast.velocity.score);
    metricByKey.set("reach", state.forecast.reach.score);
    metricByKey.set("depth", state.forecast.depth.score);
    metricByKey.set("disruption", state.forecast.disruption.score);
    metricByKey.set("translation", state.forecast.translation.score);
  }
  if (state.overlaps) {
    metricByKey.set("saturation", state.overlaps.crowding_score);
  }
  if (state.conflicts && state.conflicts.length > 0) {
    const avgSev =
      state.conflicts.reduce((acc, c) => acc + c.severity, 0) /
      state.conflicts.length;
    metricByKey.set("conflict_risk", Math.round((1 - avgSev) * 100));
  } else {
    metricByKey.set("conflict_risk", 50);
  }
  if (!metricByKey.has("novelty")) {
    const avgRel =
      state.papers && state.papers.length > 0
        ? state.papers.reduce((a, p) => a + (p.relevance_score || 0), 0) /
          state.papers.length
        : 0.4;
    metricByKey.set("novelty", Math.round((1 - avgRel) * 100));
  }
  if (!metricByKey.has("feasibility")) metricByKey.set("feasibility", 75);
  if (!metricByKey.has("evidence_quality")) metricByKey.set("evidence_quality", 76);

  const get = (k: string, def = 50) => metricByKey.get(k) ?? def;

  const overall = Math.round(
    get("novelty") * 0.14 +
      get("saturation") * 0.12 +
      get("conflict_risk") * 0.12 +
      get("feasibility") * 0.12 +
      get("volume") * 0.07 +
      get("velocity") * 0.07 +
      get("reach") * 0.07 +
      get("depth") * 0.07 +
      get("disruption") * 0.07 +
      get("translation") * 0.07 +
      get("evidence_quality") * 0.08,
  );

  const tier =
    overall >= 80
      ? "Strong Potential"
      : overall >= 65
      ? "Moderate Potential"
      : overall >= 50
      ? "Risky"
      : "Weak";

  const sorted = [...metricByKey.entries()].sort((a, b) => b[1] - a[1]);
  const topName = sorted[0]?.[0] ?? "velocity";
  const lowTwo = [...sorted]
    .reverse()
    .slice(0, 2)
    .map(([k]) => prettify(k));

  const takeaway =
    state.final_memo?.executive_summary ||
    `Promising idea with room to sharpen. Strong on ${prettify(topName).toLowerCase()}, but faces ${lowTwo.join(" and ").toLowerCase()} challenges. Focus on de-risking the core claim and strengthening evidence.`;

  return {
    overall,
    tier,
    takeaway,
    upside: `High ${prettify(topName)}`,
    watchouts: lowTwo.join(", "),
    radar: [
      { label: "Novelty", value: get("novelty") },
      { label: "Saturation", value: get("saturation") },
      { label: "Conflict Risk", value: get("conflict_risk") },
      { label: "Feasibility", value: get("feasibility") },
      { label: "Evidence Quality", value: get("evidence_quality") },
      {
        label: "Impact",
        value: Math.round((get("volume") + get("velocity") + get("reach")) / 3),
      },
    ],
    dimensions: [
      { key: "novelty", label: "Novelty", value: get("novelty"), tier: tierLabel(get("novelty")), trend: spark(get("novelty")), color: dimColor(get("novelty")), icon: "◆" },
      { key: "saturation", label: "Saturation", value: get("saturation"), tier: tierLabel(get("saturation")), trend: spark(get("saturation")), color: dimColor(get("saturation")), icon: "◉" },
      { key: "conflict_risk", label: "Conflict Risk", value: get("conflict_risk"), tier: tierLabel(get("conflict_risk")), trend: spark(get("conflict_risk")), color: dimColor(get("conflict_risk")), icon: "▲" },
      { key: "feasibility", label: "Feasibility", value: get("feasibility"), tier: tierLabel(get("feasibility")), trend: spark(get("feasibility")), color: dimColor(get("feasibility")), icon: "⚙" },
      { key: "volume", label: "Volume", value: get("volume"), tier: tierLabel(get("volume")), trend: spark(get("volume")), color: dimColor(get("volume")), icon: "▮" },
      { key: "velocity", label: "Velocity", value: get("velocity"), tier: tierLabel(get("velocity")), trend: spark(get("velocity")), color: dimColor(get("velocity")), icon: "↗" },
      { key: "reach", label: "Reach", value: get("reach"), tier: tierLabel(get("reach")), trend: spark(get("reach")), color: dimColor(get("reach")), icon: "◎" },
      { key: "depth", label: "Depth", value: get("depth"), tier: tierLabel(get("depth")), trend: spark(get("depth")), color: dimColor(get("depth")), icon: "▼" },
      { key: "disruption", label: "Disruption", value: get("disruption"), tier: tierLabel(get("disruption")), trend: spark(get("disruption")), color: dimColor(get("disruption")), icon: "⚡" },
      { key: "translation", label: "Translation", value: get("translation"), tier: tierLabel(get("translation")), trend: spark(get("translation")), color: dimColor(get("translation")), icon: "⇄" },
    ],
    evidenceQuality: {
      score: get("evidence_quality"),
      tier: tierLabel(get("evidence_quality")),
      submetrics: [
        { label: "Retrieval coverage", value: Math.min(100, get("evidence_quality") + 6) },
        { label: "Source agreement", value: Math.max(40, get("evidence_quality") - 2) },
        { label: "Recency balance", value: Math.max(40, get("evidence_quality") - 5) },
        { label: "Confidence calibration", value: Math.min(100, get("evidence_quality") + 1) },
      ],
    },
    projections: buildProjections(overall, get("velocity"), get("volume")),
    clusters: buildClusters(state),
    similar: buildSimilar(state),
    similarTotal: state.papers?.length || 23,
  };
}

function prettify(s: string) {
  return s
    .split("_")
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(" ");
}

function tierLabel(v: number) {
  if (v >= 75) return "High";
  if (v >= 55) return "Moderate";
  if (v >= 35) return "Low";
  return "Very Low";
}

function dimColor(v: number) {
  if (v >= 65) return "#16a34a"; // green
  if (v >= 45) return "#9ca3af"; // neutral gray
  return "#6b7280"; // dim gray
}

function spark(seed: number): number[] {
  const out: number[] = [];
  let v = Math.max(20, seed - 25);
  for (let i = 0; i < 18; i++) {
    const wave = Math.sin((seed + i) * 0.7) * 6;
    const drift = (seed - 50) * 0.04 * i;
    v = Math.max(5, Math.min(95, seed + wave + drift - 10 + i * 0.5));
    out.push(v);
  }
  return out;
}

function buildProjections(
  overall: number,
  velocity: number,
  volume: number,
) {
  void volume;
  const points: { year: number; total: number; vel: number; baseline: number }[] = [];
  for (let y = 0; y <= 5; y++) {
    const growth = 1 + y * (velocity / 200);
    const total = Math.round(20 + overall * 0.7 * growth * 0.9);
    const vel = Math.round(15 + velocity * 0.6 * growth * 0.85);
    const baseline = Math.round(50 - y * 1);
    points.push({ year: y, total, vel, baseline });
  }
  return points;
}

function buildClusters(state: DemoState) {
  const labels = [
    { name: "Robotics", color: "#1d1d1f" },
    { name: "Machine Learning", color: "#525252" },
    { name: "Cognitive Science", color: "#737373" },
    { name: "Control Theory", color: "#a3a3a3" },
    { name: "Materials Science", color: "#d4d4d4" },
    { name: "Other", color: "#e5e5e5" },
  ];
  const papers = state.papers ?? [];
  const counts = labels.map((l, i) => ({
    ...l,
    count: Math.max(3, Math.round((papers.length || 50) / labels.length) + ((i * 3) % 5)),
  }));
  return counts;
}

function buildSimilar(state: DemoState) {
  const papers = (state.papers ?? []).slice(0, 3);
  if (papers.length === 0) {
    return [
      { title: "World Models are Simply Context", similarity: 78 },
      { title: "Efficient Online Reinforcement Learning…", similarity: 72 },
      { title: "Action Chunking for Long Horizon Learning…", similarity: 67 },
    ];
  }
  return papers.map((p, i) => ({
    title: p.title.length > 50 ? p.title.slice(0, 48) + "…" : p.title,
    similarity: Math.round(78 - i * 6),
  }));
}
