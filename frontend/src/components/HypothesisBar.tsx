"use client";

import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";

export default function HypothesisBar() {
  const { hypothesis, setHypothesis, run, reset, isRunning, stage } = useDemo();
  if (stage === Stage.IDLE) return null;

  return (
    <header className="border-b border-divider bg-canvas/70 backdrop-blur-md">
      <div className="px-8 py-2.5 flex items-center gap-4">
        <div className="flex-1 min-w-0">
          <div className="smallcaps text-muted/70 text-[9px]">Hypothesis</div>
          <div className="text-mono text-[13px] text-ink leading-snug truncate">
            {hypothesis}
          </div>
        </div>
        <button
          type="button"
          onClick={isRunning ? undefined : run}
          disabled={isRunning}
          className="px-4 py-1.5 text-mono text-[11px] tracking-wide border border-divider rounded-full text-ink hover:border-ink disabled:opacity-50 transition-colors"
        >
          {isRunning ? "running" : stage === Stage.DONE ? "run again" : "rerun"}
        </button>
        {!isRunning && (
          <button
            type="button"
            onClick={reset}
            className="text-mono text-[11px] text-muted hover:text-ink transition-colors"
          >
            reset
          </button>
        )}
      </div>
    </header>
  );
}
