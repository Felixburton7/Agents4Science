"use client";

import { motion } from "framer-motion";
import { useDemo } from "@/lib/demoContext";

export default function LandingHero() {
  const { hypothesis, setHypothesis, run, isRunning } = useDemo();

  return (
    <motion.div
      key="landing"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, ease: [0.2, 0.6, 0.2, 1] }}
      className="min-h-screen flex flex-col items-center justify-center px-8"
    >
      <div className="w-full max-w-[640px]">
        <div className="text-mono text-[10px] tracking-[0.2em] uppercase text-muted/70 mb-4 text-center">
          Hypothesis steering engine
        </div>
        <textarea
          value={hypothesis}
          onChange={(e) => setHypothesis(e.target.value)}
          onKeyDown={(e) => {
            if ((e.key === "Enter" && (e.metaKey || e.ctrlKey)) ||
                (e.key === "Enter" && !e.shiftKey)) {
              e.preventDefault();
              if (!isRunning) run();
            }
          }}
          rows={3}
          autoFocus
          className="w-full text-mono text-[15px] leading-relaxed text-ink bg-transparent border-b border-divider focus:border-ink py-3 resize-none outline-none transition-colors"
        />
        <div className="mt-6 flex items-center justify-between">
          <button
            type="button"
            onClick={isRunning ? undefined : run}
            disabled={isRunning}
            className="px-6 py-2 text-mono text-[12px] tracking-wide border border-ink rounded-full text-ink hover:bg-ink hover:text-canvas disabled:opacity-50 transition-colors"
          >
            run
          </button>
          <div className="text-mono text-[11px] text-muted/60">
            Press ⏎ or click run
          </div>
        </div>
      </div>
    </motion.div>
  );
}
