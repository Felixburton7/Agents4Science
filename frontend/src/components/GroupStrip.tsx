"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";
import { getInstitution } from "@/lib/institutions";
import type { EmulatorOutput, GroundednessCheck } from "@/types/schemas";

export default function GroupStrip() {
  const { state, stage } = useDemo();
  const showAny = stage >= Stage.GROUPS;
  const metricsReady = stage >= Stage.EMULATORS;
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!showAny) {
    return (
      <div className="h-full w-full rounded-md flex items-center justify-center text-mono text-[10px] text-muted/40">
        —
      </div>
    );
  }

  const groundByGroup = new Map<string, GroundednessCheck>(
    state.groundedness_checks.map((g) => [g.group_id, g]),
  );
  const emulatorByGroup = new Map<string, EmulatorOutput>(
    state.emulator_outputs.map((o) => [o.group_id, o]),
  );

  return (
    <div className="h-full w-full overflow-hidden">
      <div className="flex gap-2 overflow-x-auto h-full pb-1">
        {state.groups.map((g, idx) => {
          const inst = getInstitution(g.group_id);
          const emu = emulatorByGroup.get(g.group_id);
          const gc = groundByGroup.get(g.group_id);
          const expanded = expandedId === g.group_id;
          return (
            <motion.button
              key={g.group_id}
              type="button"
              onClick={() => setExpandedId(expanded ? null : g.group_id)}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: metricsReady ? 1 : 0.4, y: 0 }}
              transition={{ duration: 0.4, delay: idx * 0.05, ease: [0.2, 0.6, 0.2, 1] }}
              className={`shrink-0 text-left border border-divider rounded-md bg-canvas/70 backdrop-blur-md px-2.5 py-2 transition-all ${
                expanded ? "w-[260px] border-accent" : "w-[150px] hover:border-ink"
              }`}
            >
              <div className="flex items-center gap-2">
                {inst && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={inst.badge}
                    alt=""
                    className="w-6 h-6 object-contain shrink-0"
                  />
                )}
                <div className="min-w-0">
                  <div className="text-ink text-[12px] font-medium truncate leading-tight">
                    {inst?.name ?? g.institution}
                  </div>
                  <div className="text-mono text-[10px] text-muted truncate">
                    {inst?.pi.display ?? g.principal_investigators[0]}
                  </div>
                </div>
              </div>
              {emu && (
                <InterestBar value={metricsReady ? emu.interest_score : 0} />
              )}
              <AnimatePresence>
                {expanded && emu && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.25 }}
                    className="mt-2 overflow-hidden"
                  >
                    <div className="grid grid-cols-3 gap-1 text-mono text-[9.5px]">
                      <Cell label="cite" value={`${derivedCites(emu)}`} />
                      <Cell
                        label="grnd"
                        value={gc?.is_grounded ? "ok" : "flag"}
                        tone={gc?.is_grounded ? "ok" : "warn"}
                      />
                      <Cell label="risk" value={`${emu.competitive_risk}`} />
                      <Cell label="novel" value={`${derivedNovelty(emu)}/5`} />
                      <Cell label="sound" value={`${derivedSoundness(emu, gc)}/5`} />
                      <Cell label="feas" value={`${derivedFeasibility(emu)}/5`} />
                    </div>
                    <div className="mt-1.5 text-[10.5px] text-body leading-snug">
                      {emu.proposed_direction}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

function InterestBar({ value }: { value: number }) {
  return (
    <div className="relative h-1 mt-2 bg-divider rounded-full overflow-hidden">
      <motion.div
        className="absolute inset-y-0 left-0 bg-accent rounded-full"
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.8, ease: [0.2, 0.6, 0.2, 1] }}
      />
    </div>
  );
}

function Cell({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "ok" | "warn";
}) {
  const cls =
    tone === "ok"
      ? "text-supports"
      : tone === "warn"
      ? "text-contradicts"
      : "text-ink";
  return (
    <div className="bg-canvas/60 border border-divider rounded-sm px-1 py-0.5">
      <div className="text-[8px] text-muted uppercase tracking-wider">{label}</div>
      <div className={`${cls} leading-tight`}>{value}</div>
    </div>
  );
}

function derivedCites(o: EmulatorOutput): number {
  return Math.round(40 + o.interest_score * 2.5 - o.competitive_risk * 0.6);
}

function derivedNovelty(o: EmulatorOutput): number {
  const score = 5 - Math.round(o.competitive_risk / 22);
  return Math.max(1, Math.min(5, score));
}

function derivedSoundness(o: EmulatorOutput, gc?: GroundednessCheck): number {
  const base = Math.round(o.interest_score / 25);
  return Math.max(1, Math.min(5, base + (gc?.is_grounded ? 1 : -1)));
}

function derivedFeasibility(o: EmulatorOutput): number {
  const score = 6 - Math.round(o.time_to_publish_months / 3.5);
  return Math.max(1, Math.min(5, score));
}
