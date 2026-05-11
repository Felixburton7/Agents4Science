"use client";

import { useEffect, useMemo, useRef } from "react";
import { motion } from "framer-motion";
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
      "text-valign": "bottom",
      "text-halign": "center",
      "text-margin-y": 6,
      "text-wrap": "wrap",
      "text-max-width": "110px",
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
      "text-valign": "top",
      "text-halign": "center",
      "text-margin-y": -8,
      "text-wrap": "wrap",
      "text-max-width": "180px",
      color: "#1A1A1A",
      "transition-property": "background-color border-color color",
      "transition-duration": 600,
      "transition-timing-function": "ease-in-out",
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
      "text-margin-y": 10,
      color: "#1A1A1A",
      "text-wrap": "wrap",
      "text-max-width": "110px",
      "text-valign": "bottom",
      "text-halign": "center",
      "line-height": 1.15,
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
      "text-valign": "center",
      "text-halign": "center",
      "text-margin-y": 0,
      "text-wrap": "wrap",
      "text-max-width": "130px",
      "font-family": "IBM Plex Mono",
      "line-height": 1.15,
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
      "text-valign": "top",
      "text-halign": "center",
      "text-margin-y": -4,
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
      "text-valign": "top",
      "text-halign": "center",
      "text-margin-y": -4,
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
      "text-valign": "bottom",
      "text-halign": "center",
      "text-margin-y": 4,
      color: "#1A1A1A",
      "transition-property":
        "background-color background-opacity border-color border-width width height",
      "transition-duration": 600,
      "transition-timing-function": "ease-in-out",
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

    // Papers all reveal at LITERATURE in one deliberate animation rather than
    // 60% then 100% — the two-step caused a second jarring re-layout.
    const showCount = stage < Stage.LITERATURE ? 0 : classifiedPapers.length;
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
  // less gravity so the graph spreads out and labels don't overlap. Slow
  // animation so nodes glide instead of strobing into place.
  const layout = useMemo(
    () => ({
      name: "cose",
      animate: "end" as const,
      animationDuration: 1500,
      animationEasing: "ease-in-out-cubic" as const,
      randomize: false,
      nodeRepulsion: 32000,
      nodeOverlap: 80,
      idealEdgeLength: 180,
      edgeElasticity: 45,
      gravity: 0.25,
      fit: true,
      padding: 60,
      componentSpacing: 140,
      nestingFactor: 1.2,
      numIter: 2500,
    }),
    [],
  );

  // Stable key for the element ID set. Re-runs layout only when the set of
  // nodes/edges changes — class flips at PARETO no longer trigger a re-layout,
  // which was the source of the "jiggy" feel.
  const structureKey = useMemo(
    () =>
      elements
        .map((el) => el.data?.id ?? "")
        .filter(Boolean)
        .sort()
        .join("|"),
    [elements],
  );

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.layout(layout).run();
  }, [structureKey, layout]);

  if (!hasContent) {
    return <ParsingVisual active={stage === Stage.PARSING} />;
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

// Explicit "we are parsing your hypothesis" visualisation. Replaces the
// previous em-dash placeholder so the Parse stage has a clear, slow animation
// of its own rather than feeling like dead time before the graph appears.
const PARSE_TAGS = [
  "claim",
  "method",
  "domain",
  "predicate",
  "scope",
  "evidence",
];

function ParsingVisual({ active }: { active: boolean }) {
  return (
    <div className="relative h-full w-full overflow-hidden flex items-center justify-center">
      <div className="absolute top-3 left-3 text-mono text-[10px] uppercase tracking-[0.2em] text-muted">
        Parse
      </div>
      <div className="relative w-[260px] h-[260px] flex items-center justify-center">
        {/* Slow concentric pulses around the hypothesis node. */}
        {active && [0, 1, 2].map((ring) => (
          <motion.span
            key={ring}
            className="absolute rounded-full border border-accent/40"
            initial={{ width: 36, height: 36, opacity: 0.5 }}
            animate={{ width: 240, height: 240, opacity: 0 }}
            transition={{
              duration: 2.6,
              delay: ring * 0.85,
              repeat: Infinity,
              ease: "easeOut",
            }}
          />
        ))}
        {/* Center node. */}
        <motion.div
          className="relative w-9 h-9 rounded-full bg-ink border-2 border-canvas shadow-[0_0_0_2px_rgba(30,90,143,0.25)]"
          animate={active ? { scale: [1, 1.08, 1] } : { scale: 1 }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
        />
        {/* Concept tags fade in around the dot — staggered & slow. */}
        {active &&
          PARSE_TAGS.map((tag, i) => {
            const angle = (i / PARSE_TAGS.length) * Math.PI * 2 - Math.PI / 2;
            const r = 100;
            const x = Math.cos(angle) * r;
            const y = Math.sin(angle) * r;
            return (
              <motion.div
                key={tag}
                className="absolute text-mono text-[10px] uppercase tracking-wider text-muted"
                style={{ left: "50%", top: "50%" }}
                initial={{ opacity: 0, x: 0, y: 0 }}
                animate={{
                  opacity: [0, 1, 1],
                  x: [0, x],
                  y: [0, y],
                }}
                transition={{
                  duration: 1.6,
                  delay: 0.25 + i * 0.18,
                  ease: [0.2, 0.6, 0.2, 1],
                }}
              >
                <span className="-translate-x-1/2 -translate-y-1/2 inline-block px-1.5 py-0.5 bg-canvas/80 border border-divider rounded-sm whitespace-nowrap">
                  {tag}
                </span>
              </motion.div>
            );
          })}
      </div>
      <div className="absolute bottom-3 right-3 text-mono text-[10px] text-muted">
        parsing hypothesis…
      </div>
    </div>
  );
}
