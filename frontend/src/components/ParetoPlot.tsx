"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";
import { IMPACT_DIMENSIONS, type ImpactDimensionKey } from "@/types/schemas";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const DEFAULT_X: ImpactDimensionKey = "volume";
const DEFAULT_Y: ImpactDimensionKey = "disruption";

export default function ParetoPlot() {
  const { state, stage } = useDemo();
  const [xAxis, setXAxis] = useState<ImpactDimensionKey>(DEFAULT_X);
  const [yAxis, setYAxis] = useState<ImpactDimensionKey>(DEFAULT_Y);
  const showVariants = stage >= Stage.MUTATIONS;
  const paretoRevealed = stage >= Stage.PARETO;

  const traces = useMemo(() => {
    if (!showVariants || !state.forecast) return [];

    const originalX = state.forecast[xAxis].score;
    const originalY = state.forecast[yAxis].score;

    const list: Plotly.Data[] = [];

    // Original hypothesis as a distinct trace (crossed out at PARETO)
    list.push({
      type: "scatter",
      mode: "text+markers",
      x: [originalX],
      y: [originalY],
      text: paretoRevealed ? ["YOUR HYPOTHESIS · DOMINATED"] : ["YOUR HYPOTHESIS"],
      textposition: "top right",
      textfont: {
        family: "IBM Plex Mono",
        size: 10,
        color: paretoRevealed ? "#A65151" : "#1A1A1A",
      },
      marker: {
        symbol: paretoRevealed ? "x" : "circle",
        size: 14,
        color: paretoRevealed ? "#A65151" : "#1A1A1A",
        line: { color: paretoRevealed ? "#A65151" : "#1A1A1A", width: 2 },
      },
      hovertemplate: "<b>Your hypothesis</b><br>%{x}, %{y}<extra></extra>",
      name: "Your hypothesis",
    });

    const variants = state.variants;
    const dominated = variants.filter((v) => paretoRevealed && !v.is_pareto_selected);
    const pareto = variants.filter((v) => v.is_pareto_selected || !paretoRevealed);

    if (dominated.length) {
      list.push({
        type: "scatter",
        mode: "markers",
        x: dominated.map((v) => v.impact_scores[xAxis] ?? 0),
        y: dominated.map((v) => v.impact_scores[yAxis] ?? 0),
        marker: {
          symbol: "x",
          size: 10,
          color: "#6b6b6b",
          line: { color: "#6b6b6b", width: 1.5 },
        },
        text: dominated.map((v) => v.operator),
        hovertemplate: "<b>%{text}</b> (dominated)<br>%{x}, %{y}<extra></extra>",
        name: "Dominated",
      });
    }

    if (pareto.length) {
      const recommended = pareto.find((v) =>
        v.dominance_explanation.toLowerCase().includes("recommended"),
      );
      const others = pareto.filter((v) => v.variant_id !== recommended?.variant_id);
      if (others.length) {
        list.push({
          type: "scatter",
          mode: "markers",
          x: others.map((v) => v.impact_scores[xAxis] ?? 0),
          y: others.map((v) => v.impact_scores[yAxis] ?? 0),
          marker: {
            symbol: "circle",
            size: 11,
            color: "#1A1A1A",
            line: { color: "#FFFFFF", width: 2 },
          },
          text: others.map((v) => v.operator),
          hovertemplate: "<b>%{text}</b> (Pareto)<br>%{x}, %{y}<extra></extra>",
          name: "Pareto",
        });
      }
      if (recommended && paretoRevealed) {
        list.push({
          type: "scatter",
          mode: "text+markers",
          x: [recommended.impact_scores[xAxis] ?? 0],
          y: [recommended.impact_scores[yAxis] ?? 0],
          text: ["RECOMMENDED"],
          textposition: "top center",
          textfont: { family: "IBM Plex Mono", size: 10, color: "#1E5A8F" },
          marker: {
            symbol: "circle",
            size: 16,
            color: "#1E5A8F",
            line: { color: "#FFFFFF", width: 3 },
          },
          hovertemplate: `<b>${recommended.operator}</b> (recommended)<br>%{x}, %{y}<extra></extra>`,
          name: "Recommended",
        });
      }
    }
    return list;
  }, [state, xAxis, yAxis, paretoRevealed, showVariants]);

  const layout: Partial<Plotly.Layout> = {
    margin: { l: 36, r: 18, t: 6, b: 30 },
    xaxis: {
      title: { text: xAxis, font: { family: "IBM Plex Mono", size: 10, color: "#6b6b6b" } },
      range: [0, 100],
      gridcolor: "#E3E3E0",
      zerolinecolor: "#E3E3E0",
      tickfont: { family: "IBM Plex Mono", size: 9, color: "#6b6b6b" },
    },
    yaxis: {
      title: { text: yAxis, font: { family: "IBM Plex Mono", size: 10, color: "#6b6b6b" } },
      range: [0, 100],
      gridcolor: "#E3E3E0",
      zerolinecolor: "#E3E3E0",
      tickfont: { family: "IBM Plex Mono", size: 9, color: "#6b6b6b" },
    },
    showlegend: false,
    paper_bgcolor: "#FFFFFF",
    plot_bgcolor: "#FFFFFF",
    font: { family: "Inter" },
  };

  return (
    <div className="h-full w-full bg-canvas/70 backdrop-blur-md border border-divider rounded-md overflow-hidden flex flex-col">
      <div className="px-3 pt-2 pb-1 flex items-center justify-between gap-2">
        <span className="smallcaps text-muted">Pareto</span>
        <div className="flex items-center gap-1 text-mono text-[10px]">
          <DimSelect value={xAxis} onChange={setXAxis} label="x" />
          <DimSelect value={yAxis} onChange={setYAxis} label="y" />
        </div>
      </div>
      <div className="flex-1 min-h-0">
        {showVariants ? (
          <Plot
            data={traces}
            layout={layout}
            config={{ displayModeBar: false, responsive: true }}
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

function DimSelect({
  value,
  onChange,
  label,
}: {
  value: ImpactDimensionKey;
  onChange: (v: ImpactDimensionKey) => void;
  label: string;
}) {
  return (
    <label className="flex items-center gap-1">
      <span className="text-muted">{label}:</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as ImpactDimensionKey)}
        className="bg-canvas border border-divider rounded-sm px-1 py-0.5 text-ink"
      >
        {IMPACT_DIMENSIONS.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </select>
    </label>
  );
}
