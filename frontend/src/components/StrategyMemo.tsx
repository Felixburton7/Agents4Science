"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";

export default function StrategyMemo() {
  const { state, stage } = useDemo();
  const memo = state.final_memo;
  const ready = stage >= Stage.MEMO;

  return (
    <div className="h-full w-full bg-canvas/70 backdrop-blur-md border border-divider rounded-md overflow-hidden flex flex-col">
      <div className="px-3 pt-2 pb-1 flex items-center justify-between">
        <span className="smallcaps text-muted">Memo</span>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto px-4 pb-3">
        {!ready || !memo ? (
          <div className="h-full flex items-center justify-center text-mono text-[10px] text-muted/40">
            —
          </div>
        ) : (
          <Body memo={memo} />
        )}
      </div>
    </div>
  );
}

function Body({ memo }: { memo: NonNullable<ReturnType<typeof useDemo>["state"]["final_memo"]> }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="text-[12.5px] leading-relaxed text-body pt-1">
      <Typewriter text={memo.recommendation} chunkMs={14} />
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="mt-2 text-mono text-[10px] tracking-wide text-muted hover:text-ink transition-colors"
      >
        {open ? "− less" : "+ more"}
      </button>
      {open && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          transition={{ duration: 0.3 }}
          className="mt-3 space-y-3 overflow-hidden"
        >
          <Bullets label="Findings" items={memo.key_findings} />
          <Bullets label="Risks" items={memo.risks} />
        </motion.div>
      )}
    </div>
  );
}

function Bullets({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <div className="smallcaps text-muted mb-1">{label}</div>
      <ul className="list-disc list-outside pl-4 space-y-0.5 text-[11.5px]">
        {items.map((t, i) => (
          <li key={i}>{t}</li>
        ))}
      </ul>
    </div>
  );
}

function Typewriter({ text, chunkMs = 14 }: { text: string; chunkMs?: number }) {
  const [shown, setShown] = useState("");
  useEffect(() => {
    let i = 0;
    setShown("");
    const id = setInterval(() => {
      i += 2;
      setShown(text.slice(0, i));
      if (i >= text.length) clearInterval(id);
    }, chunkMs);
    return () => clearInterval(id);
  }, [text, chunkMs]);
  return (
    <AnimatePresence>
      <motion.p
        key="t"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
      >
        {shown}
        <span className="inline-block w-1.5 h-3 bg-ink/30 align-middle ml-px" />
      </motion.p>
    </AnimatePresence>
  );
}
