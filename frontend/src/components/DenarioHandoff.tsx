"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";

const SECTION_ORDER = ["title", "abstract", "methods", "experiments", "discussion"] as const;
const SECTION_LABEL: Record<(typeof SECTION_ORDER)[number], string> = {
  title: "Title",
  abstract: "Abstract",
  methods: "Methods",
  experiments: "Experiments",
  discussion: "Discussion",
};

export default function DenarioHandoff() {
  const { state, stage } = useDemo();
  const ready = stage >= Stage.DENARIO_HANDOFF;
  const outline = state.extras.denario_outline;
  const [open, setOpen] = useState(false);

  if (!ready) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="bg-canvas/70 backdrop-blur-md border border-divider rounded-md"
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-mono text-[10px] text-canvas bg-ink rounded-full px-2 py-0.5 shrink-0">
            Piped to Denario →
          </span>
          <span className="text-[12.5px] text-ink truncate">
            {outline.title}
          </span>
        </div>
        <span className="text-mono text-[10px] text-muted ml-3">{open ? "−" : "+"}</span>
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
            <div className="px-4 pb-3 pt-1 space-y-2">
              {SECTION_ORDER.slice(1).map((key) => (
                <div key={key}>
                  <div className="smallcaps text-muted mb-0.5">{SECTION_LABEL[key]}</div>
                  <div className="text-[11.5px] leading-snug text-body">
                    {outline[key]}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
