"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import DeckGL from "@deck.gl/react";
import {
  GreatCircleLayer,
  type GreatCircleLayerProps,
} from "@deck.gl/geo-layers";
import { ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import { FlyToInterpolator } from "@deck.gl/core";
import { Map as MapLibreMap } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";

import { useDemo } from "@/lib/demoContext";
import { Stage } from "@/lib/stages";
import {
  INSTITUTIONS,
  ORIGIN,
  getInstitution,
  type Institution,
} from "@/lib/institutions";
import { greatCirclePoint } from "@/lib/geo";
import OverlayCard from "@/components/OverlayCard";
import type { EmulatorOutput } from "@/types/schemas";

const BASEMAP_STYLE = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";

const WORLD_VIEW = {
  longitude: -20,
  latitude: 44,
  zoom: 1.7,
  pitch: 0,
  bearing: 0,
};

const ORIGIN_POSITION: [number, number] = [ORIGIN.lon, ORIGIN.lat];

// User wanted "a bit more time when it zooms into each place so we can read it"
// and "slightly less places it goes to".
const ZOOM_SEGMENT_MS = 5500;
const CAMERA_FLY_IN_MS = 1200;
const OVERLAY_DELAY_MS = 900;
const OVERLAY_EXIT_LEAD_MS = 500;

interface Arc {
  groupId: string;
  source: [number, number];
  target: [number, number];
  thickness: number;
}

interface EnvoyDot {
  groupId: string;
  position: [number, number];
}

export default function WorldMap() {
  const { state, stage } = useDemo();
  const reduceMotion =
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

  const arcs = useMemo<Arc[]>(() => {
    const byId = new Map<string, EmulatorOutput>(
      state.emulator_outputs.map((o) => [o.group_id, o]),
    );
    return INSTITUTIONS.map((inst) => ({
      groupId: inst.id,
      source: ORIGIN_POSITION,
      target: [inst.lon, inst.lat] as [number, number],
      thickness: Math.max(0.6, (byId.get(inst.id)?.interest_score ?? 50) / 30),
    }));
  }, [state.emulator_outputs]);

  // ------------------------------------------------------------------ envoys
  const [envoys, setEnvoys] = useState<EnvoyDot[]>([]);
  const envoyActive = stage >= Stage.GROUPS && stage < Stage.MEMO;
  useEffect(() => {
    if (!envoyActive || reduceMotion) {
      setEnvoys([]);
      return;
    }
    let raf = 0;
    const start = performance.now();
    const cycleMs = 4500;
    const stagger = 220;
    const tick = (now: number) => {
      const elapsed = now - start;
      const next: EnvoyDot[] = arcs.map((arc, idx) => {
        const phase = (elapsed - idx * stagger) / cycleMs;
        const wrapped = ((phase % 2) + 2) % 2;
        const t = wrapped <= 1 ? wrapped : 2 - wrapped;
        const eased = easeInOut(t);
        const pt = greatCirclePoint(arc.source, arc.target, eased);
        return { groupId: arc.groupId, position: pt };
      });
      setEnvoys(next);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [arcs, envoyActive, reduceMotion]);

  // ------------------------------------------------------ narrator zoom-ins
  const headline = state.extras.headline_groups
    .map((id) => getInstitution(id))
    .filter(Boolean) as Institution[];

  const [viewState, setViewState] = useState<
    typeof WORLD_VIEW & {
      transitionDuration?: number;
      transitionInterpolator?: FlyToInterpolator;
    }
  >(WORLD_VIEW);
  const [zoomedGroup, setZoomedGroup] = useState<Institution | null>(null);
  const lastStage = useRef<Stage | null>(null);

  useEffect(() => {
    if (stage !== Stage.GROUPS || reduceMotion) {
      if (lastStage.current === Stage.GROUPS) {
        setViewState({
          ...WORLD_VIEW,
          transitionDuration: 1400,
          transitionInterpolator: new FlyToInterpolator({ speed: 1.4 }),
        });
        setZoomedGroup(null);
      }
      lastStage.current = stage;
      return;
    }
    lastStage.current = stage;
    if (headline.length === 0) return;

    const cancelled = { current: false };

    headline.forEach((inst, i) => {
      setTimeoutSafe(() => {
        if (cancelled.current) return;
        setViewState({
          longitude: inst.lon,
          latitude: inst.lat,
          zoom: 5,
          pitch: 0,
          bearing: 0,
          transitionDuration: CAMERA_FLY_IN_MS,
          transitionInterpolator: new FlyToInterpolator({ speed: 1.6 }),
        });
        setTimeoutSafe(() => {
          if (cancelled.current) return;
          setZoomedGroup(inst);
        }, OVERLAY_DELAY_MS);
        setTimeoutSafe(() => {
          if (cancelled.current) return;
          setZoomedGroup(null);
        }, ZOOM_SEGMENT_MS - OVERLAY_EXIT_LEAD_MS);
      }, i * ZOOM_SEGMENT_MS);
    });

    setTimeoutSafe(() => {
      if (cancelled.current) return;
      setViewState({
        ...WORLD_VIEW,
        transitionDuration: 1300,
        transitionInterpolator: new FlyToInterpolator({ speed: 1.4 }),
      });
    }, headline.length * ZOOM_SEGMENT_MS);

    return () => {
      cancelled.current = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  const layers = useMemo(
    () => [
      new GreatCircleLayer<Arc>({
        id: "arcs",
        data: arcs,
        getSourcePosition: (d) => d.source,
        getTargetPosition: (d) => d.target,
        getWidth: (d) => d.thickness,
        getSourceColor: [26, 26, 26, 230],
        getTargetColor: [26, 26, 26, 230],
        widthUnits: "pixels",
        widthMinPixels: 1,
        pickable: false,
      } satisfies GreatCircleLayerProps<Arc>),
      new ScatterplotLayer<{ position: [number, number]; id: string }>({
        id: "pins",
        data: [
          { position: ORIGIN_POSITION, id: ORIGIN.id },
          ...INSTITUTIONS.map((i) => ({
            position: [i.lon, i.lat] as [number, number],
            id: i.id,
          })),
        ],
        getPosition: (d) => d.position,
        getRadius: 5,
        radiusUnits: "pixels",
        getFillColor: [26, 26, 26, 255],
        stroked: true,
        getLineColor: [255, 255, 255, 255],
        lineWidthUnits: "pixels",
        getLineWidth: 1.5,
        pickable: true,
      }),
      new TextLayer<{ position: [number, number]; text: string; id: string }>({
        id: "labels",
        data: [
          { position: ORIGIN_POSITION, text: ORIGIN.city, id: ORIGIN.id },
          ...INSTITUTIONS.map((i) => ({
            position: [i.lon, i.lat] as [number, number],
            text: i.name,
            id: i.id,
          })),
        ],
        getPosition: (d) => d.position,
        getText: (d) => d.text,
        getColor: [26, 26, 26, 230],
        getSize: 11,
        sizeUnits: "pixels",
        fontFamily: "Inter, system-ui, sans-serif",
        fontWeight: 500,
        getTextAnchor: "start",
        getAlignmentBaseline: "center",
        getPixelOffset: [10, 0],
        outlineWidth: 2,
        outlineColor: [255, 255, 255, 255],
        fontSettings: { sdf: true },
      }),
      new ScatterplotLayer<EnvoyDot>({
        id: "envoys",
        data: envoys,
        getPosition: (d) => d.position,
        getRadius: 3.5,
        radiusUnits: "pixels",
        getFillColor: [30, 90, 143, 255],
        stroked: false,
        pickable: false,
        updateTriggers: { getPosition: envoys },
      }),
    ],
    [arcs, envoys],
  );

  return (
    <div className="relative h-full w-full">
      <DeckGL
        viewState={viewState}
        controller={false}
        layers={layers}
        onViewStateChange={({ viewState: vs }) => {
          setViewState(vs as typeof WORLD_VIEW);
        }}
        getCursor={() => "default"}
      >
        <MapLibreMap
          mapStyle={BASEMAP_STYLE}
          reuseMaps
          attributionControl={false}
        />
      </DeckGL>
      <OverlayCard institution={zoomedGroup} />
    </div>
  );
}

function setTimeoutSafe(fn: () => void, ms: number): number {
  return window.setTimeout(fn, ms) as unknown as number;
}

function easeInOut(t: number) {
  return t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
}
