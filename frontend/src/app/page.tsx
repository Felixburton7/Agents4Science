"use client";

import { AnimatePresence, motion } from "framer-motion";
import { DemoProvider, useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";
import HypothesisBar from "@/components/HypothesisBar";
import StageRail from "@/components/StageRail";
import CenterVisual from "@/components/CenterVisual";
import ImpactRadar from "@/components/ImpactRadar";
import ParetoPlot from "@/components/ParetoPlot";
import GroupStrip from "@/components/GroupStrip";
import BacktestCorner from "@/components/BacktestCorner";
import StrategyMemo from "@/components/StrategyMemo";
import TrajectoryPanel from "@/components/TrajectoryPanel";
import DenarioHandoff from "@/components/DenarioHandoff";
import NextActions from "@/components/NextActions";
import LandingHero from "@/components/LandingHero";

export default function Home() {
  return (
    <DemoProvider>
      <Surface />
    </DemoProvider>
  );
}

function Surface() {
  const { stage } = useDemo();
  const inDashboard = stage !== Stage.IDLE;

  return (
    <div className="min-h-screen bg-canvas text-body flex flex-col">
      <AnimatePresence mode="wait">
        {!inDashboard && <LandingHero key="landing" />}
        {inDashboard && (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, ease: [0.2, 0.6, 0.2, 1] }}
            className="flex flex-col"
          >
            <HypothesisBar />
            <StageRail />
            <main className="px-6 py-3 grid grid-cols-12 gap-3 grid-rows-[minmax(440px,_56vh)_minmax(120px,_15vh)_minmax(160px,_18vh)]">
              <section className="col-span-8 row-span-2 min-h-0">
                <CenterVisual />
              </section>
              <section className="col-span-4 min-h-0">
                <ImpactRadar />
              </section>
              <section className="col-span-4 min-h-0">
                <ParetoPlot />
              </section>
              <section className="col-span-8 min-h-0">
                <GroupStrip />
              </section>
              <section className="col-span-3 min-h-0">
                <BacktestCorner />
              </section>
              <section className="col-span-9 min-h-0">
                <StrategyMemo />
              </section>
            </main>
            <section className="px-6 py-2">
              <TrajectoryPanel />
            </section>
            <section className="px-6 py-2">
              <DenarioHandoff />
            </section>
            <section className="px-6 py-2 pb-6">
              <NextActions />
            </section>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
