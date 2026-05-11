"use client";

import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";

interface Macro {
  key: string;
  label: string;
  from: Stage;
  to: Stage;
}

// Collapse the 13-stage internal machine into 5 macro phases for the rail.
const MACROS: Macro[] = [
  { key: "parse", label: "Parse", from: Stage.PARSING, to: Stage.PARSING },
  { key: "literature", label: "Literature", from: Stage.LITERATURE, to: Stage.CONFLICT_OVERLAP },
  { key: "audience", label: "Audience", from: Stage.GROUPS, to: Stage.TRAJECTORY },
  { key: "forecast", label: "Forecast", from: Stage.FORECAST, to: Stage.PARETO },
  { key: "decide", label: "Decide", from: Stage.MEMO, to: Stage.NEXT_ACTIONS },
];

export default function StageRail() {
  const { stage } = useDemo();
  if (stage === Stage.IDLE) return null;

  return (
    <div className="px-8 py-1.5 flex items-center gap-1.5">
      {MACROS.map((m) => {
        const isActive = stage >= m.from && stage <= m.to;
        const isDone = stage > m.to;
        return (
          <span
            key={m.key}
            className={`text-mono text-[10px] tracking-wide px-2.5 py-1 rounded-full border transition-all duration-500 ease-instrument ${
              isActive
                ? "border-accent text-canvas bg-accent"
                : isDone
                ? "border-divider text-ink bg-canvas"
                : "border-divider/60 text-muted/50 bg-canvas/60"
            }`}
          >
            {m.label}
          </span>
        );
      })}
    </div>
  );
}
