"use client";

import { useMemo } from "react";
import dynamic from "next/dynamic";
import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";
import { IMPACT_DIMENSIONS, type ImpactDimensionKey } from "@/types/schemas";

const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center text-mono text-[10px] text-muted">
      loading radar
    </div>
  ),
});

const DIM_LABELS: Record<ImpactDimensionKey, string> = {
  volume: "Volume",
  velocity: "Velocity",
  reach: "Reach",
  depth: "Depth",
  disruption: "Disruption",
  translation: "Translation",
};

export default function ImpactRadar() {
  const { state, stage } = useDemo();
  const ready = stage >= Stage.FORECAST;
  const showVariants = stage >= Stage.PARETO;

  const dimsLabels = useMemo(
    () => IMPACT_DIMENSIONS.map((d) => DIM_LABELS[d]),
    [],
  );

  const traces = useMemo(() => {
    if (!ready || !state.forecast) return [];
    const baseline = IMPACT_DIMENSIONS.map((d) => state.forecast![d].score);
    const baselineLow = IMPACT_DIMENSIONS.map(
      (d) => state.forecast![d].confidence_low,
    );
    const baselineHigh = IMPACT_DIMENSIONS.map(
      (d) => state.forecast![d].confidence_high,
    );

    const list: Plotly.Data[] = [
      {
        type: "scatterpolar",
        r: [...baselineHigh, baselineHigh[0]],
        theta: [...dimsLabels, dimsLabels[0]],
        fill: "toself",
        fillcolor: "rgba(30, 90, 143, 0.08)",
        line: { color: "rgba(30, 90, 143, 0.15)", width: 0 },
        showlegend: false,
        hoverinfo: "skip",
        name: "CI high",
      },
      {
        type: "scatterpolar",
        r: [...baselineLow, baselineLow[0]],
        theta: [...dimsLabels, dimsLabels[0]],
        fill: "toself",
        fillcolor: "#ffffff",
        line: { color: "rgba(30, 90, 143, 0.15)", width: 0 },
        showlegend: false,
        hoverinfo: "skip",
        name: "CI low",
      },
      {
        type: "scatterpolar",
        r: [...baseline, baseline[0]],
        theta: [...dimsLabels, dimsLabels[0]],
        fill: "toself",
        fillcolor: "rgba(26, 26, 26, 0.04)",
        line: { color: "#1A1A1A", width: 1.5 },
        marker: { color: "#1A1A1A", size: 5 },
        name: "Your hypothesis",
      },
    ];

    if (showVariants) {
      const recommended = state.variants.find((v) =>
        v.dominance_explanation.toLowerCase().includes("recommended"),
      );
      const others = state.variants.filter(
        (v) => v.is_pareto_selected && v.variant_id !== recommended?.variant_id,
      );
      others.forEach((v) => {
        const r = IMPACT_DIMENSIONS.map((d) => v.impact_scores[d] ?? 0);
        list.push({
          type: "scatterpolar",
          r: [...r, r[0]],
          theta: [...dimsLabels, dimsLabels[0]],
          line: { color: "#6b6b6b", width: 1, dash: "dot" },
          marker: { color: "#6b6b6b", size: 3 },
          name: v.operator,
        });
      });
      if (recommended) {
        const r = IMPACT_DIMENSIONS.map(
          (d) => recommended.impact_scores[d] ?? 0,
        );
        list.push({
          type: "scatterpolar",
          r: [...r, r[0]],
          theta: [...dimsLabels, dimsLabels[0]],
          line: { color: "#1E5A8F", width: 2 },
          marker: { color: "#1E5A8F", size: 6 },
          fill: "toself",
          fillcolor: "rgba(30, 90, 143, 0.12)",
          name: `${recommended.operator} (recommended)`,
        });
      }
    }
    return list;
  }, [state, ready, showVariants, dimsLabels]);

  const layout: Partial<Plotly.Layout> = {
    polar: {
      domain: { x: [0.08, 0.92], y: [0.05, 0.95] },
      radialaxis: {
        visible: true,
        range: [0, 100],
        showline: false,
        gridcolor: "#E3E3E0",
        tickfont: { family: "IBM Plex Mono", size: 9, color: "#6b6b6b" },
        tickvals: [25, 50, 75, 100],
      },
      angularaxis: {
        gridcolor: "#E3E3E0",
        tickfont: { family: "Inter", size: 10, color: "#1A1A1A" },
      },
      bgcolor: "#FFFFFF",
    },
    margin: { l: 70, r: 70, t: 20, b: 20 },
    showlegend: false,
    paper_bgcolor: "#FFFFFF",
    plot_bgcolor: "#FFFFFF",
    font: { family: "Inter" },
    transition: { duration: 900, easing: "cubic-in-out" },
  };

  return (
    <div className="h-full w-full bg-canvas/70 backdrop-blur-md border border-divider rounded-md overflow-hidden flex flex-col">
      <div className="px-3 pt-2 pb-1 flex items-center justify-between">
        <span className="smallcaps text-muted">Impact</span>
      </div>
      <div className="flex-1 min-h-0">
        {ready ? (
          <Plot
            data={traces}
            layout={layout}
            config={{ displayModeBar: false, responsive: true, staticPlot: false }}
            style={{ width: "100%", height: "100%" }}
            useResizeHandler
          />
        ) : (
          <div className="h-full flex items-center justify-center text-mono text-[10px] text-muted/40">
            —
          </div>
        )}
      </div>
    </div>
  );
}
