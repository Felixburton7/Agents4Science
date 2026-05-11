"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Core, ElementDefinition, StylesheetJson } from "cytoscape";
import dynamic from "next/dynamic";

import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";
import { getInstitution } from "@/lib/institutions";

const CytoscapeComponent = dynamic(() => import("react-cytoscapejs"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center text-mono text-[10px] text-muted">
      loading graph
    </div>
  ),
});

const STYLESHEET: StylesheetJson = [
  {
    selector: "node",
    style: {
      "background-color": "#888888",
      width: "data(size)",
      height: "data(size)",
      "border-width": 1,
      "border-color": "#FFFFFF",
      label: "data(label)",
      "font-family": "Inter",
      "font-size": 9,
      color: "#3F3F3F",
      "text-margin-y": -6,
      "text-wrap": "wrap",
      "text-max-width": "120px",
      "min-zoomed-font-size": 6,
    },
  },
  {
    selector: "node.hypothesis",
    style: {
      "background-color": "#1A1A1A",
      width: 32,
      height: 32,
      "border-width": 2,
      "border-color": "#FFFFFF",
      label: "data(label)",
      "font-size": 11,
      "font-family": "IBM Plex Mono",
      "text-margin-y": -12,
      "text-wrap": "wrap",
      "text-max-width": "180px",
      color: "#1A1A1A",
    },
  },
  {
    selector: "node.supports",
    style: { "background-color": "#5B8A6A" },
  },
  {
    selector: "node.contradicts",
    style: { "background-color": "#A65151" },
  },
  {
    selector: "node.overlaps",
    style: { "background-color": "#B58A3E" },
  },
  {
    selector: "node.group",
    style: {
      "background-color": "#FFFFFF",
      "background-image": "data(badge)",
      "background-fit": "contain",
      "background-image-containment": "over",
      "background-clip": "none",
      "background-opacity": 1,
      "border-color": "#1E5A8F",
      "border-width": 2,
      width: "data(size)",
      height: "data(size)",
      shape: "ellipse",
      label: "data(label)",
      "font-size": 10,
      "font-family": "Inter",
      "text-margin-y": -10,
      color: "#1A1A1A",
      "text-wrap": "wrap",
      "text-max-width": "120px",
      "text-valign": "bottom",
      "text-halign": "center",
    },
  },
  {
    selector: "node.proposed",
    style: {
      "background-color": "#FFFFFF",
      "background-opacity": 0,
      "border-width": 0,
      width: 6,
      height: 6,
      label: "data(label)",
      "font-size": 9,
      color: "#1E5A8F",
      "text-margin-y": 0,
      "text-wrap": "wrap",
      "text-max-width": "140px",
      "font-family": "IBM Plex Mono",
    },
  },
  {
    selector: "node.flag-race",
    style: {
      "background-color": "#A65151",
      width: 10,
      height: 10,
      shape: "diamond",
      label: "data(label)",
      "font-size": 9,
      color: "#A65151",
      "text-margin-y": -6,
      "font-family": "IBM Plex Mono",
    },
  },
  {
    selector: "node.flag-space",
    style: {
      "background-color": "#5B8A6A",
      width: 10,
      height: 10,
      shape: "diamond",
      label: "data(label)",
      "font-size": 9,
      color: "#5B8A6A",
      "text-margin-y": -6,
      "font-family": "IBM Plex Mono",
    },
  },
  {
    selector: "node.variant",
    style: {
      "background-color": "#1E5A8F",
      "background-opacity": 0.6,
      width: 14,
      height: 14,
      shape: "round-rectangle",
      "border-width": 1,
      "border-color": "#FFFFFF",
      label: "data(label)",
      "font-family": "IBM Plex Mono",
      "font-size": 9,
      "text-margin-y": -6,
      color: "#1A1A1A",
    },
  },
  {
    selector: "node.variant.pareto",
    style: {
      "background-color": "#1E5A8F",
      "background-opacity": 1,
      "border-width": 2,
    },
  },
  {
    selector: "node.variant.dominated",
    style: {
      "background-color": "#6b6b6b",
      "background-opacity": 0.35,
      "border-style": "dashed",
      color: "#6b6b6b",
    },
  },
  {
    selector: "node.variant.recommended",
    style: {
      "border-width": 4,
      "border-color": "#1E5A8F",
      "background-opacity": 1,
      width: 18,
      height: 18,
    },
  },
  {
    selector: "node.hypothesis.dominated",
    style: {
      "background-color": "#A65151",
      "border-color": "#A65151",
      label: "DOMINATED · pick a variant",
      color: "#A65151",
    },
  },
  {
    selector: "edge",
    style: {
      width: 1,
      "line-color": "#E3E3E0",
      "curve-style": "straight",
      "target-arrow-shape": "none",
      opacity: 0.7,
    },
  },
  {
    selector: "edge.hyp-paper",
    style: { "line-color": "#E3E3E0", width: 0.7, opacity: 0.45 },
  },
  {
    selector: "edge.hyp-group",
    style: {
      "line-color": "#1E5A8F",
      "line-opacity": 0.5,
      width: "data(thickness)",
    },
  },
  {
    selector: "edge.group-proposed",
    style: {
      "line-color": "#1E5A8F",
      "target-arrow-shape": "triangle",
      "target-arrow-color": "#1E5A8F",
      "curve-style": "straight",
      width: 1.2,
    },
  },
  {
    selector: "edge.variant",
    style: {
      "line-color": "#1E5A8F",
      "line-style": "dashed",
      width: 1,
      opacity: 0.6,
    },
  },
];

export default function LiteratureMap() {
  const { state, stage } = useDemo();
  const cyRef = useRef<Core | null>(null);
  const hasContent = stage >= Stage.LITERATURE;

  const groupsRevealed = stage >= Stage.TRAJECTORY;
  const variantsRevealed = stage >= Stage.MUTATIONS;
  const paretoRevealed = stage >= Stage.PARETO;

  // Only render the papers we have something meaningful to say about
  // (supports / contradicts / overlaps). Drops the "random dots" noise.
  const classifiedPapers = useMemo(() => {
    type Tag = "supports" | "contradicts" | "overlaps";
    const tagged: Array<{ paper: typeof state.papers[number]; tag: Tag }> = [];
    const seen = new Set<string>();

    // Contradicts (max 2)
    for (const c of state.conflicts.slice(0, 2)) {
      const p = state.papers.find((pp) => pp.paper_id === c.paper_id);
      if (p && !seen.has(p.paper_id)) {
        seen.add(p.paper_id);
        tagged.push({ paper: p, tag: "contradicts" });
      }
    }
    // Overlaps (max 3)
    for (const t of (state.overlaps?.overlapping_papers ?? []).slice(0, 3)) {
      const p = state.papers.find((pp) => pp.title === t);
      if (p && !seen.has(p.paper_id)) {
        seen.add(p.paper_id);
        tagged.push({ paper: p, tag: "overlaps" });
      }
    }
    // Supports = the 5 most relevant remaining papers
    const supports = [...state.papers]
      .sort((a, b) => b.relevance_score - a.relevance_score)
      .filter((p) => !seen.has(p.paper_id))
      .slice(0, 5);
    for (const p of supports) {
      tagged.push({ paper: p, tag: "supports" });
    }
    return tagged;
  }, [state]);

  const elements: ElementDefinition[] = useMemo(() => {
    const els: ElementDefinition[] = [];

    // Center hypothesis node
    els.push({
      data: {
        id: "hypothesis",
        label: paretoRevealed ? "DOMINATED" : "",
        size: 36,
      },
      classes: ["hypothesis", paretoRevealed ? "dominated" : ""].join(" ").trim(),
    });

    // Reveal classified papers as the bloom progresses.
    const totalClassified = classifiedPapers.length;
    const showCount =
      stage < Stage.LITERATURE
        ? 0
        : stage === Stage.LITERATURE
        ? Math.max(3, Math.floor(totalClassified * 0.6))
        : totalClassified;
    classifiedPapers.slice(0, showCount).forEach(({ paper: p, tag }) => {
      const size = Math.round(14 + p.relevance_score * 14);
      els.push({
        data: {
          id: p.paper_id,
          label: shortenTitle(p.title),
          size,
        },
        classes: tag,
      });
      els.push({
        data: {
          id: `e-${p.paper_id}`,
          source: "hypothesis",
          target: p.paper_id,
        },
        classes: "hyp-paper",
      });
    });

    if (groupsRevealed) {
      state.groups.forEach((g) => {
        const inst = getInstitution(g.group_id);
        const emu = state.emulator_outputs.find((o) => o.group_id === g.group_id);
        els.push({
          data: {
            id: `g-${g.group_id}`,
            label: `${inst?.name ?? g.institution}\n${inst?.pi.display ?? ""}`,
            badge: inst?.badge ?? "",
            size: 48,
          },
          classes: "group",
        });
        els.push({
          data: {
            id: `eh-${g.group_id}`,
            source: "hypothesis",
            target: `g-${g.group_id}`,
            thickness: Math.max(0.8, (emu?.interest_score ?? 50) / 25),
          },
          classes: "hyp-group",
        });
        if (emu) {
          const propId = `p-${g.group_id}`;
          els.push({
            data: {
              id: propId,
              label: shortenDirection(emu.proposed_direction),
              size: 6,
            },
            classes: "proposed",
          });
          els.push({
            data: {
              id: `ep-${g.group_id}`,
              source: `g-${g.group_id}`,
              target: propId,
            },
            classes: "group-proposed",
          });
        }
      });

      // Race-condition flag (Toronto + Stanford collide)
      els.push({
        data: { id: "flag-race-1", label: "Toronto × Stanford", size: 12 },
        classes: "flag-race",
      });
      els.push({
        data: { id: "flag-space-1", label: "Multilingual SAEs", size: 12 },
        classes: "flag-space",
      });
      els.push({
        data: { id: "flag-space-2", label: "SAE × anomaly", size: 12 },
        classes: "flag-space",
      });
    }

    if (variantsRevealed) {
      state.variants.forEach((v) => {
        const classes: string[] = ["variant"];
        if (paretoRevealed) {
          if (v.is_pareto_selected) classes.push("pareto");
          else classes.push("dominated");
          if (v.dominance_explanation.toLowerCase().includes("recommended")) {
            classes.push("recommended");
          }
        }
        els.push({
          data: { id: `v-${v.variant_id}`, label: v.operator, size: 18 },
          classes: classes.join(" "),
        });
        els.push({
          data: {
            id: `ev-${v.variant_id}`,
            source: "hypothesis",
            target: `v-${v.variant_id}`,
          },
          classes: "variant",
        });
      });
    }

    return els;
  }, [
    state,
    stage,
    classifiedPapers,
    groupsRevealed,
    variantsRevealed,
    paretoRevealed,
  ]);

  // cose layout tuned for breathing room — high repulsion, generous edge length,
  // less gravity so the graph spreads out and labels don't overlap.
  const layout = useMemo(
    () => ({
      name: "cose",
      animate: true,
      animationDuration: 800,
      randomize: false,
      nodeRepulsion: 12000,
      nodeOverlap: 40,
      idealEdgeLength: 140,
      edgeElasticity: 60,
      gravity: 0.15,
      fit: true,
      padding: 48,
      componentSpacing: 80,
    }),
    [],
  );

  // Re-run layout when elements change.
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.layout(layout).run();
  }, [elements, layout]);

  if (!hasContent) {
    return (
      <div className="h-full w-full flex items-center justify-center text-mono text-[11px] text-muted/40">
        —
      </div>
    );
  }

  return (
    <div className="relative h-full w-full bg-canvas">
      <CytoscapeComponent
        elements={elements}
        layout={layout}
        stylesheet={STYLESHEET}
        cy={(cy) => {
          cyRef.current = cy;
        }}
        style={{ width: "100%", height: "100%" }}
        minZoom={0.4}
        maxZoom={3}
        wheelSensitivity={0.2}
      />
      {paretoRevealed && (
        <div className="absolute bottom-3 right-3 bg-canvas/70 backdrop-blur-md border border-divider rounded-lg px-3 py-2 text-mono text-[11px] text-ink shadow-[0_4px_20px_rgba(0,0,0,0.06)]">
          <span className="text-contradicts">dominated</span>
          {" → "}
          <span className="text-accent">cross-pollinate</span>
        </div>
      )}
    </div>
  );
}

function shortenTitle(t: string): string {
  // First 4-5 meaningful words, then ellipsis.
  const words = t.split(/\s+/).slice(0, 4);
  return words.join(" ") + (t.split(/\s+/).length > 4 ? "…" : "");
}

function shortenDirection(t: string): string {
  if (t.length <= 60) return t;
  return t.slice(0, 57) + "…";
}
