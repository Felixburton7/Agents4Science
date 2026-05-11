"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";

export default function TrajectoryPanel() {
  const { state, stage } = useDemo();
  const ready = stage >= Stage.TRAJECTORY;
  const [open, setOpen] = useState(false);

  if (!ready) return null;

  const consensusCites = consensusCitations(state);
  const groundedMean = groundednessMean(state);
  const consensusVerdict = consensusVerdictText(state);

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="bg-canvas/70 backdrop-blur-md border border-divider rounded-md"
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-4">
          <span className="smallcaps text-muted">Trajectory</span>
          <span className="text-mono text-[11px] text-ink">
            ~{consensusCites} cites
          </span>
          <span className="text-mono text-[11px] text-muted">·</span>
          <span className="text-mono text-[11px] text-ink">{consensusVerdict}</span>
          <span className="text-mono text-[11px] text-muted">·</span>
          <span className="text-mono text-[11px] text-ink">
            {groundedMean.toFixed(2)} grounded
          </span>
        </div>
        <span className="text-mono text-[10px] text-muted">{open ? "−" : "+"}</span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="grid grid-cols-3 gap-3 px-4 pb-3 pt-1 text-[11.5px]">
              <Column heading="Scenarios">
                {state.scenarios.map((s) => (
                  <div
                    key={s.scenario_id}
                    className="border border-divider rounded-sm px-2 py-1.5 bg-canvas/50"
                  >
                    <div className="text-ink font-medium">{s.name}</div>
                    <div className="text-muted text-[10px] mt-0.5">
                      {(s.probability * 100).toFixed(0)}% likely
                    </div>
                  </div>
                ))}
              </Column>
              <Column heading="Race conditions">
                {(state.overlaps?.risk_notes ?? []).slice(0, 2).map((n, i) => (
                  <div
                    key={i}
                    className="border border-contradicts/30 bg-contradicts/5 text-contradicts rounded-sm px-2 py-1.5"
                  >
                    {n}
                  </div>
                ))}
              </Column>
              <Column heading="White space">
                <div className="border border-supports/30 bg-supports/5 text-supports rounded-sm px-2 py-1.5">
                  {state.overlaps?.whitespace_summary ?? "—"}
                </div>
              </Column>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function Column({
  heading,
  children,
}: {
  heading: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="smallcaps text-muted mb-1">{heading}</div>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function consensusCitations(state: ReturnType<typeof useDemo>["state"]): number {
  if (state.emulator_outputs.length === 0) return 0;
  const cites = state.emulator_outputs.map((o) =>
    Math.round(40 + o.interest_score * 2.5 - o.competitive_risk * 0.6),
  );
  cites.sort((a, b) => a - b);
  return cites[Math.floor(cites.length / 2)];
}

function groundednessMean(state: ReturnType<typeof useDemo>["state"]): number {
  if (state.groundedness_checks.length === 0) return 0;
  const grounded = state.groundedness_checks.filter((g) => g.is_grounded).length;
  return grounded / state.groundedness_checks.length;
}

function consensusVerdictText(state: ReturnType<typeof useDemo>["state"]): string {
  const counts = { accept: 0, borderline: 0, reject: 0 };
  state.emulator_outputs.forEach((o) => {
    if (o.interest_score >= 75) counts.accept++;
    else if (o.interest_score < 40) counts.reject++;
    else counts.borderline++;
  });
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "borderline";
  return top;
}
