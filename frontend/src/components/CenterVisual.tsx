"use client";

import { Stage } from "@/lib/stages";
import { useDemo } from "@/lib/demoContext";
import dynamic from "next/dynamic";
import { Placeholder } from "@/components/Placeholder";
import WebGLErrorBoundary from "@/components/WebGLErrorBoundary";

// deck.gl + maplibre touch window — dynamic-import so they only run client-side.
const WorldMap = dynamic(() => import("@/components/WorldMap"), {
  ssr: false,
  loading: () => <Placeholder label="World map loading" />,
});
const LiteratureMap = dynamic(() => import("@/components/LiteratureMap"), {
  ssr: false,
  loading: () => <Placeholder label="Literature map loading" />,
});

export default function CenterVisual() {
  const { stage } = useDemo();

  // Choose which visual is foreground based on stage.
  const showWorld = stage >= Stage.GROUPS && stage < Stage.TRAJECTORY;
  const showLit = !showWorld;

  return (
    <div className="relative h-full w-full overflow-hidden border border-divider rounded-md bg-canvas">
      <div
        className={`absolute inset-0 transition-opacity duration-700 ease-instrument ${
          showLit ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
      >
        <LiteratureMap />
      </div>
      <div
        className={`absolute inset-0 transition-opacity duration-700 ease-instrument ${
          showWorld ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
      >
        <WebGLErrorBoundary label="Audience map">
          <WorldMap />
        </WebGLErrorBoundary>
      </div>
    </div>
  );
}
