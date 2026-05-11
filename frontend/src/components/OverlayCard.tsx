"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useDemo } from "@/lib/demoContext";
import type { Institution } from "@/lib/institutions";
import type { EmulatorOutput, GroundednessCheck } from "@/types/schemas";

interface Props {
  institution: Institution | null;
}

export default function OverlayCard({ institution }: Props) {
  const { state } = useDemo();
  const emulator: EmulatorOutput | undefined = institution
    ? state.emulator_outputs.find((o) => o.group_id === institution.id)
    : undefined;
  const ground: GroundednessCheck | undefined = institution
    ? state.groundedness_checks.find((g) => g.group_id === institution.id)
    : undefined;

  return (
    <AnimatePresence mode="wait">
      {institution && (
        <motion.div
          key={institution.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.45, ease: [0.2, 0.6, 0.2, 1] }}
          className="absolute top-5 right-5 w-[300px] bg-canvas/70 backdrop-blur-lg border border-divider/80 shadow-[0_8px_32px_rgba(0,0,0,0.08)] rounded-xl z-10 overflow-hidden"
        >
          <div className="px-4 py-3 flex items-center gap-3">
            <div className="w-11 h-11 bg-canvas/80 backdrop-blur-sm rounded-md border border-divider/60 flex items-center justify-center overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={institution.badge}
                alt=""
                className="max-w-[34px] max-h-[34px] object-contain"
              />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-ink font-medium text-[14px] leading-tight truncate">
                {institution.name}
              </div>
              <div className="text-mono text-[11px] text-muted mt-0.5">
                {institution.pi.display}
              </div>
            </div>
          </div>
          {emulator && (
            <div className="px-4 pb-3">
              <div className="text-[12px] leading-snug text-body mb-2.5">
                {emulator.proposed_direction}
              </div>
              <div className="flex items-center gap-3 text-mono text-[10.5px]">
                <Stat label="interest" value={`${emulator.interest_score}`} />
                <Stat
                  label="grounded"
                  value={ground?.is_grounded ? "ok" : "flag"}
                  tone={ground?.is_grounded ? "ok" : "warn"}
                />
                <Stat label="risk" value={`${emulator.competitive_risk}`} />
                <Stat label="mo" value={`${emulator.time_to_publish_months}`} />
              </div>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "ok" | "warn";
}) {
  const cls =
    tone === "warn"
      ? "text-contradicts"
      : tone === "ok"
      ? "text-supports"
      : "text-ink";
  return (
    <div>
      <div className="text-[9px] text-muted uppercase tracking-wider">{label}</div>
      <div className={`${cls} leading-tight mt-0.5`}>{value}</div>
    </div>
  );
}
