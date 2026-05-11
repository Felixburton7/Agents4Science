"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";

export default function NextActions() {
  const { state, stage } = useDemo();
  const ready = stage >= Stage.NEXT_ACTIONS;
  const items = state.extras.next_actions;
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
        <div className="flex items-center gap-3">
          <span className="smallcaps text-muted">Next</span>
          <span className="text-[12.5px] text-ink">
            {items[0]}
          </span>
        </div>
        <span className="text-mono text-[10px] text-muted">{open ? "−" : `+${items.length - 1}`}</span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.ul
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="px-4 pb-3 pt-1 grid grid-cols-2 gap-x-6 gap-y-1.5 overflow-hidden"
          >
            {items.slice(1).map((item, i) => (
              <li key={i} className="flex gap-2 items-start text-[11.5px] text-body">
                <span className="text-mono text-divider mt-0.5">☐</span>
                <span>{item}</span>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
